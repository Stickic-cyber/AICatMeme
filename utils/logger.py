import os
import csv
import json
import threading
from core.config import LOG_CSV_FILE

csv_lock = threading.Lock()

def initialize_csv():
    with csv_lock:
        os.makedirs(os.path.dirname(LOG_CSV_FILE), exist_ok=True)
        if not os.path.exists(LOG_CSV_FILE):
            with open(LOG_CSV_FILE, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['timestamp', 'user_ip', 'user_story', 'generated_data', 'user_id', 'video_success', 'upload_success', 'message'])

def log_submission(timestamp, user_ip, user_story, generated_data, user_id, video_success, upload_success, message):
    with csv_lock:
        with open(LOG_CSV_FILE, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, user_ip, user_story, json.dumps(generated_data, ensure_ascii=False), user_id, video_success, upload_success, message])