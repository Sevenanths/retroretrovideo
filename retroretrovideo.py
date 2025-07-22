from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify
#from flask_socketio import SocketIO, emit
import os
import json
import time
import argparse
import subprocess
import base64
import threading
import subprocess

from retroretrovideo.flashback import FlashbackRecorder

app = Flask(__name__)
app.secret_key = 'secret_key_for_sessions'
#socketio = SocketIO(app)

SCREENSHOT_PATH = "/tmp/output.png"
VIDEO_PATH = "/tmp/output.mp4"

#
# Argument parsing
#

parser = argparse.ArgumentParser(description='retroretrovideo - screenshots and retroactive recording for any video source')
parser.add_argument("stream_url", type=str, help='recording URL')
parser.add_argument('--port', type=int, nargs='?', default="5000", help='Port to run the application on')
args = parser.parse_args()

recording_process = None
flashback_process = None

def is_ffmpeg_installed():
    try:
        # Run the ffmpeg command with the help option
        subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

@app.route('/', methods=['GET', 'POST'])
def capture():
    screenshot = False
    error = False
        
    if not is_ffmpeg_installed():
        error = "ffmpeg is not installed!"

    if request.method == 'POST':
        screenshot = True

        if args.mode == "live":
            # Open an ffmpeg subprocess and capture ONE frame to take a screenshot
            subprocess.run(["ffmpeg", "-video_size", "1280x720", "-framerate", "30", "-f", "v4l2", "-i", "/dev/video0", "-y", "-vframes", "1", SCREENSHOT_PATH])
        elif args.mode == "test":
            # Test image for testing
            subprocess.run(["ffmpeg", "-f", "lavfi", "-i", "color=c=blue:s=1280x720", "-y", "-frames:v", "1", SCREENSHOT_PATH])

    return render_template('capture.html', screenshot=screenshot, error=error)

@app.route('/record', methods=['GET', 'POST'])
def record():
    video = False
    recording_ongoing = False
    error = False
        
    if not is_ffmpeg_installed():
        error = "ffmpeg is not installed!"

    if request.method == 'POST':
        screenshot = True

        if recording_process is None:
            if os.path.exists(VIDEO_PATH):
                os.remove(VIDEO_PATH)
                
            record_start()
            recording_ongoing = True
        else:
            record_stop()
            time.sleep(1)
            video = True
            recording_ongoing = False

    return render_template('record.html', video=video, error=error, recording_ongoing=recording_ongoing)

def start_recording():
    global recording_process
    recording_process = subprocess.Popen(
        ["ffmpeg", "-y", "-i", args.stream_url, "-c", "copy", VIDEO_PATH],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def stop_recording():
    global recording_process
    if recording_process:
        recording_process.terminate()
        recording_process = None

@app.route('/record/start', methods=['POST'])
def record_start():
    global recording_process
    if recording_process is None:
        threading.Thread(target=start_recording).start()
        return jsonify({"status": "Recording started"})
    return jsonify({"status": "Already recording"})

@app.route('/record/stop', methods=['POST'])
def record_stop():
    global recording_process
    if recording_process:
        stop_recording()
        return jsonify({"status": "Recording stopped"})
    return jsonify({"status": "Not recording"})

@app.route('/flashback/start', methods=['GET'])
def flashback_start():
    global flashback_process

    if flashback_process is None:
        flashback_process = FlashbackRecorder(args.stream_url, 30)
        # Start buffering in the background
        threading.Thread(target=flashback_process.start_buffering).start()
    
        return jsonify({"status": "Flashback recording started"})
    
    return jsonify({"status": "Already buffering"})

@app.route('/flashback/stop', methods=['GET'])
def flashback_stop():
    global flashback_process
    if flashback_process is not None:
        flashback_process.save_flashback()
        flashback_process = None

        flashback_start()

        return jsonify({"status": "Flashback recording saved"})
    return jsonify({"status": "No current buffer"})

@app.route('/flashback/trigger', methods=["GET"])
def flashback_trigger():
    global flashback_process

    if flashback_process is not None:
        if not flashback_process.is_recording:
          return jsonify({"status": "Flashback recording is being saved"})
        
        return flashback_stop()
    else:
        return jsonify({"status": "Flashback recording not running"})

@app.route('/latest_screenshot', methods=['GET'])
def latest_screenshot():
    return send_file(SCREENSHOT_PATH, mimetype='image/png')

@app.route('/latest_video', methods=['GET'])
def latest_video():
    return send_file(VIDEO_PATH, mimetype='video/mp4')

if __name__ == '__main__':
    app.run(debug=True, port=args.port, host="0.0.0.0")