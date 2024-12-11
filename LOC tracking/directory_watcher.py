import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class DirectoryEventHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            print(f"Directory modified: {event.src_path}")
            self.run_batch_file()

    def on_created(self, event):
        if event.is_directory:
            print(f"Directory created: {event.src_path}")
            self.run_batch_file()

    def run_batch_file(self):
        batch_file_path = r"C:\Users\grego\HTML Projects\CV website project\LOC tracking\run_automated_code_counter.bat"
        print(f"Running batch file: {batch_file_path}")
        subprocess.run([batch_file_path], shell=True)

if __name__ == "__main__":
    path = r"C:\Users\grego\HTML Projects\CV website project"
    event_handler = DirectoryEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    print(f"Watching directory: {path}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()