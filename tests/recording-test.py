import ffmpeg
import argparse

parser = argparse.ArgumentParser(description='recording-test')
parser.add_argument("stream_url", type=str, help='recording URL')
parser.add_argument("--output", type=str, default="output.mp4", help='recording URL')
args = parser.parse_args()

try:
    # Start recording the stream
    (
        ffmpeg
        .input(args.stream_url)
        .output(args.output, vcodec='copy', acodec='copy')  # Use 'copy' to avoid re-encoding
        .run()
    )
    print("Recording complete.")
except ffmpeg.Error as e:
    print("An error occurred:", e.stderr.decode())