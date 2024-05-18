from flask import Flask, render_template
from flask_socketio import SocketIO
import json
import redis
from threading import Thread
import transcribe
import os
from dotenv import load_dotenv

load_dotenv()
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = int(os.getenv('REDIS_PORT'))
REDIS_DB = int(os.getenv('REDIS_DB'))
FLASK_HOST = os.getenv('FLASK_HOST')
FLASK_PORT = int(os.getenv('FLASK_PORT'))

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

transcribe_thread = None

#Route
@app.route('/')
def index():
  return render_template('index.html')

# build WebSocket
@socketio.on('connect')
def handle_connect():
  history = redis_client.lrange('transcript_history', 0, -1)
  history = [json.loads(item) for item in history]
  socketio.emit('history', history)

# build WebSocket for "start_transcription" event
@socketio.on('start_transcription')
def handle_start_transcription():
  global transcribe_thread
  if transcribe_thread is None or not transcribe_thread.is_alive():
    transcribe_thread = Thread(target=transcribe.start_audio_processing)
    transcribe_thread.start()

# build WebSocket for "stop_transcription" event
@socketio.on('stop_transcription')
def handle_stop_transcription():
  transcribe.stop_audio_processing()

# start Flask and SocketIO
if __name__ == '__main__':
  socketio.run(app, host=FLASK_HOST, port=FLASK_PORT)