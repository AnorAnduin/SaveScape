import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
import shutil
import dropbox

# Configuration
SAVE_STATE_DIR = "/path/to/pcsx2/sstates"  # Directory where PCSX2 saves states
BACKUP_DIR = "/path/to/save_state_backups"  # Local backup directory
DROPBOX_TOKEN = "your_dropbox_token"  # Your Dropbox API token for cloud sync

# Initialize Dropbox client
dbx = dropbox.Dropbox(DROPBOX_TOKEN)

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
        backup_path = os.path.join(BACKUP_DIR, backup_name)
        
        # Copy the file to the local backup directory
        shutil.copy(file_path, backup_path)
        print(f"Backed up save state to: {backup_path}")

        # Upload to Dropbox
        self.upload_to_dropbox(backup_path, backup_name)

    def upload_to_dropbox(self, local_path, backup_name):
        with open(local_path, "rb") as f:
            dbx.files_upload(f.read(), f"/PCSX2 Backups/{backup_name}")
        print(f"Uploaded {backup_name} to Dropbox.")

if __name__ == "__main__":
    # Ensure the backup directory exists
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
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

