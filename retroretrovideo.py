from flask import Flask, render_template, request, redirect, url_for, session, send_file
#from flask_socketio import SocketIO, emit
import os
import json
import argparse
import subprocess
import base64

app = Flask(__name__)
app.secret_key = 'secret_key_for_sessions'
#socketio = SocketIO(app)

SCREENSHOT_PATH = "/tmp/output.png"

#
# Argument parsing
#

parser = argparse.ArgumentParser(description='retroretrovideo - screenshots and retroactive recording for any video source')
parser.add_argument('mode', type=str, help='mode - live or test (test will fake output)')
parser.add_argument('--port', type=int, nargs='?', default="5000", help='Port to run the application on')
args = parser.parse_args()

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

@app.route('/latest_screenshot', methods=['GET'])
def latest_screenshot():
    return send_file(SCREENSHOT_PATH, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True, port=args.port, host="0.0.0.0")