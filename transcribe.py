import os
import queue
import sys
import time
import requests
import speech_recognition as sr
from pydub import AudioSegment
from openai import OpenAI
from dotenv import load_dotenv
import json
import redis

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("未找到 OPENAI_API_KEY。請確保 .env 文件中已正確設置。")

client = OpenAI(api_key=OPENAI_API_KEY)

REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = int(os.getenv('REDIS_PORT'))
REDIS_DB = int(os.getenv('REDIS_DB'))

from openai import RateLimitError
import backoff

@backoff.on_exception(backoff.expo, RateLimitError)
def completions_with_backoff(**kwargs):
    response = client.chat.completions.create(**kwargs)
    return response

CHUNK_SIZE = 1024
RATE = 16000
SILENCE_THRESHOLD = 500
SILENCE_DURATION = 4

recognizer = sr.Recognizer()
audio_queue = queue.Queue()
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

is_processing = False

def process_audio(audio):
    audio_segment = AudioSegment(
        data=audio.get_wav_data(),
        sample_width=audio.sample_width,
        frame_rate=audio.sample_rate,
        channels=1
    )
    temp_file = "temp_audio.wav"
    audio_segment.export(temp_file, format="wav")

    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }
    data = {
        "model": "whisper-1",
        "language": "en",
    }
    files = {
        "file": (temp_file, open(temp_file, "rb")),
    }
    response = requests.post(url=url, headers=headers, data=data, files=files)

    # 刪除臨時音訊文件
    os.remove(temp_file)

    # 解析 API 響應
    if response.status_code == 200:
        result = response.json()
        en_text = result["text"]
        print(f"英文轉錄結果: {en_text}")

        # 將英文文本翻譯為中文
        translation_data = {
          "model": "gpt-4o",
          "messages": [
            {
              "role": "system",
              "content": "You are a helpful assistant that translates English to Taiwan Tranditional Chinese."
            },
            {
              "role": "user",
              "content": f"Translate the following English text to Chinese:\n\n{en_text}"
            }
          ],
          "max_tokens": 300,
          "temperature": 0.3,
          "n": 1
        }

        # 解析翻譯 API 響應
        try:
            translation_response = completions_with_backoff(**translation_data)
            zh_text = translation_response.choices[0].message.content.strip()
            print(f"中文翻譯結果: {zh_text}")

            # 將轉錄和翻譯結果存儲到 Redis 中
            timestamp = int(time.time())
            data = {
                'timestamp': timestamp,
                'en_text': en_text,
                'zh_text': zh_text
            }
            redis_client.rpush('transcript_history', json.dumps(data))

        except Exception as e:
            print(f"翻譯請求失敗: {str(e)}")
    else:
        print(f"請求失敗,狀態碼: {response.status_code}")

# 定義回調函數,將音訊數據放入隊列
def callback(_, audio:sr.AudioData):
  global is_processing
  if is_processing:
    audio_queue.put(audio)

def start_audio_processing():
  global is_processing
  is_processing = True
  print("開始錄音,請說話...")

  # 開始錄音並進行實時轉錄
  with sr.Microphone(sample_rate=RATE, chunk_size=CHUNK_SIZE) as source:
    recognizer.adjust_for_ambient_noise(source, duration=1)

    try:
      while is_processing:
        # 開始錄音
        audio = recognizer.listen(source, phrase_time_limit=SILENCE_DURATION)
        if not is_processing:
           break

        # 將音訊數據放入隊列
        audio_queue.put(audio)

        # 處理隊列中的音訊數據
        while not audio_queue.empty():
          audio = audio_queue.get()
          process_audio(audio)
    except KeyboardInterrupt:
      print("錄音已手動停止")
      sys.exit(0)
    finally:
            print("錄音循環結束")  # 確保您知道錄音循環已經被終止

def stop_audio_processing():
  global is_processing
  is_processing = False
  print("錄音已停止")

# 啟動音訊處理
if __name__ == '__main__':
  start_audio_processing()
    