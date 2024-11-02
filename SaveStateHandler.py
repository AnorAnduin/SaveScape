import os
import time
import json
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
import shutil

# Load configuration from JSON file
BASE_DIR = Path(__file__).resolve().parent
with open(BASE_DIR / "config.json", "r") as config_file:
    config = json.load(config_file)

# Set up directories and Dropbox flag
SAVE_STATE_DIR = BASE_DIR / config["SAVE_STATE_DIR"]
BACKUP_DIR = BASE_DIR / config["BACKUP_DIR"]
USE_DROPBOX = config.get("USE_DROPBOX", False)
DROPBOX_TOKEN = config.get("DROPBOX_TOKEN")

# Initialize Dropbox client if USE_DROPBOX is true
dbx = None
if USE_DROPBOX and DROPBOX_TOKEN:
    import dropbox
    dbx = dropbox.Dropbox(DROPBOX_TOKEN)

# Ensure the backup directory exists
os.makedirs(BACKUP_DIR, exist_ok=True)

class SaveStateHandler(FileSystemEventHandler):
    def on_created(self, event):
        # Check if the created file is a save state (.p2s file)
        if event.is_directory:
            return
        if event.src_path.endswith(".p2s"):
            print(f"New save state detected: {event.src_path}")
            self.backup_save_state(event.src_path)

    def backup_save_state(self, file_path):
        # Create a timestamped backup of the save state file
        file_name = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{timestamp}_{file_name}"
        backup_path = BACKUP_DIR / backup_name

        # Copy the file to the local backup directory
        shutil.copy(file_path, backup_path)
        print(f"Backed up save state to: {backup_path}")

        # Upload to Dropbox if USE_DROPBOX is enabled
        if USE_DROPBOX and dbx:
            self.upload_to_dropbox(backup_path, backup_name)

    def upload_to_dropbox(self, local_path, backup_name):
        with open(local_path, "rb") as f:
            dbx.files_upload(f.read(), f"/PCSX2 Backups/{backup_name}")
        print(f"Uploaded {backup_name} to Dropbox.")

if __name__ == "__main__":
    # Set up and start the observer
    event_handler = SaveStateHandler()
    observer = Observer()
    observer.schedule(event_handler, SAVE_STATE_DIR, recursive=False)
    observer.start()
    print("Monitoring save states... Press Ctrl+C to stop.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
