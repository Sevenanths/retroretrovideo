import subprocess
import threading
import time
import os
import ffmpeg


class FlashbackRecorder:
    def __init__(self, stream_url, buffer_duration=30, output_file="flashback.mp4"):
        self.stream_url = stream_url
        self.buffer_duration = buffer_duration
        self.output_file = output_file
        self.recording_process = None
        self.is_recording = False

    def start_buffering(self):
        """Starts the circular buffer process."""
        if self.recording_process:
            return  # Buffering already running

        self.recording_process = subprocess.Popen(
            [
                "ffmpeg",
                "-y",
                "-i", self.stream_url,
                "-f", "segment",
                "-segment_time", str(self.buffer_duration),
                "-segment_format", "mp4",
                "-segment_list", "catfile.ffcat",
                "-segment_wrap", "2",
                "-reset_timestamps", "1",
                "segment%d.mp4"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.is_recording = True

    def save_flashback(self):
        self.stop_buffering()

        time.sleep(1)

        # Concat recorded files
        ffmpeg.input('catfile.ffcat', format='concat') \
            .output('combined.mp4', c='copy', map=0, y=None) \
            .run()

        ffmpeg.input('combined.mp4', sseof=-self.buffer_duration) \
            .output(self.output_file, y=None) \
            .run()

        os.remove("catfile.ffcat")
        os.remove("segment0.mp4")
        os.remove("segment1.mp4")
        os.remove("combined.mp4")

        print(f"Saved flashback to {self.output_file}")

    def stop_buffering(self):
        """Stops the circular buffer process."""
        if self.recording_process:
            self.recording_process.terminate()
            self.recording_process = None
            self.is_recording = False
            print("Stopped buffering.")
