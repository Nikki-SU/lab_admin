import os
import time
import hashlib
import json
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests
from dotenv import load_dotenv

load_dotenv()

HUB_URL = os.getenv('HUB_URL', 'http://localhost:8000')
DEVICE_TOKEN = os.getenv('DEVICE_TOKEN', '')
WATCH_DIR = os.getenv('WATCH_DIR', './watch')
DEVICE_NAME = os.getenv('DEVICE_NAME', 'Leaf-Device')
ZONE = os.getenv('ZONE', 'DATA')  # DATA or COLLABORATION

os.makedirs(WATCH_DIR, exist_ok=True)

class FileMonitor(FileSystemEventHandler):
    def __init__(self):
        self.uploaded_files = set()
        self.process_existing_files()
    
    def process_existing_files(self):
        for root, dirs, files in os.walk(WATCH_DIR):
            for file in files:
                filepath = os.path.join(root, file)
                self.upload_file(filepath)
    
    def get_file_hash(self, filepath):
        hash_obj = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    
    def upload_file(self, filepath):
        if not os.path.isfile(filepath):
            return
        
        try:
            file_hash = self.get_file_hash(filepath)
            relative_path = os.path.relpath(filepath, WATCH_DIR)
            
            print(f'准备上传: {relative_path}')
            
            with open(filepath, 'rb') as f:
                files = {'file': (os.path.basename(filepath), f)}
                data = {
                    'zone': ZONE,
                    'path': f'/{DEVICE_NAME}/{relative_path}',
                }
                headers = {}
                if DEVICE_TOKEN:
                    headers['Authorization'] = f'Bearer {DEVICE_TOKEN}'
                
                response = requests.post(
                    f'{HUB_URL}/files/upload',
                    files=files,
                    data=data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    print(f'✅ 上传成功: {relative_path}')
                    self.uploaded_files.add(file_hash)
                else:
                    print(f'❌ 上传失败: {response.text}')
        except Exception as e:
            print(f'❌ 错误: {str(e)}')
    
    def on_created(self, event):
        if not event.is_directory:
            time.sleep(1)
            self.upload_file(event.src_path)
    
    def on_modified(self, event):
        if not event.is_directory:
            time.sleep(1)
            self.upload_file(event.src_path)

def main():
    print(f'🔬 LabVault Leaf Agent 启动')
    print(f'监控目录: {WATCH_DIR}')
    print(f'Hub URL: {HUB_URL}')
    print(f'设备名称: {DEVICE_NAME}')
    print(f'目标区域: {ZONE}')
    print('-' * 50)
    
    event_handler = FileMonitor()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('\n停止监控...')
        observer.stop()
    observer.join()

if __name__ == '__main__':
    main()
