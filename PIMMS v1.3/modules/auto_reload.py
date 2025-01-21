import sys
import time
from subprocess import Popen

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class ReloadHandler(FileSystemEventHandler):
    def __init__(self, script):
        self.script = script
        self.process = None
        self.restart_process()

    def restart_process(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
        self.process = Popen([sys.executable, self.script])

    def on_modified(self, event):
        if event.src_path.endswith(".py"):
            self.restart_process()


if __name__ == "__main__":
    script = "main.py"  # The script to run
    event_handler = ReloadHandler(script)
    observer = Observer()
    observer.schedule(event_handler, path=".", recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
