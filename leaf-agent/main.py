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
STATE_FILE = os.getenv('STATE_FILE', './leaf_state.json')

os.makedirs(WATCH_DIR, exist_ok=True)

class FileMonitor(FileSystemEventHandler):
    def __init__(self):
        self.uploaded_files = self.load_state()
        self.process_existing_files()
    
    def load_state(self):
        """加载已上传文件的状态"""
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_state(self):
        """保存已上传文件的状态"""
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(self.uploaded_files, f)
        except Exception as e:
            print(f'⚠️ 无法保存状态: {e}')
    
    def get_file_hash(self, filepath):
        hash_obj = hashlib.sha256()
        try:
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            print(f'⚠️ 无法计算哈希: {filepath}, {e}')
            return None
    
    def upload_file(self, filepath, is_edit=False):
        if not os.path.isfile(filepath):
            return
        
        try:
            file_hash = self.get_file_hash(filepath)
            if not file_hash:
                return
            
            relative_path = os.path.relpath(filepath, WATCH_DIR)
            file_key = f'/{DEVICE_NAME}/{relative_path}'
            
            # 检查文件是否已经上传过且哈希未变
            if file_key in self.uploaded_files and self.uploaded_files[file_key] == file_hash:
                print(f'⏭️ 文件未变化，跳过: {relative_path}')
                return
            
            # 判断是否为编辑
            if file_key in self.uploaded_files:
                is_edit = True
                print(f'📝 检测到文件修改: {relative_path}')
            
            print(f'准备上传: {relative_path}')
            
            with open(filepath, 'rb') as f:
                files = {'file': (os.path.basename(filepath), f)}
                data = {
                    'zone': ZONE,
                    'path': file_key,
                    'source_device': DEVICE_NAME,
                    'is_edit': str(is_edit).lower()
                }
                headers = {}
                if DEVICE_TOKEN:
                    headers['Authorization'] = f'Bearer {DEVICE_TOKEN}'
                
                # 添加重试机制
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        response = requests.post(
                            f'{HUB_URL}/api/files/upload',
                            files=files,
                            data=data,
                            headers=headers,
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            print(f'✅ 上传成功: {relative_path}')
                            self.uploaded_files[file_key] = file_hash
                            self.save_state()
                            break
                        else:
                            print(f'❌ 上传失败 (尝试 {attempt + 1}/{max_retries}): {response.status_code} {response.text}')
                    except requests.exceptions.RequestException as e:
                        print(f'⚠️ 网络错误 (尝试 {attempt + 1}/{max_retries}): {e}')
                    
                    if attempt < max_retries - 1:
                        time.sleep(2)
        except Exception as e:
            print(f'❌ 错误: {str(e)}')
    
    def process_existing_files(self):
        print('📂 扫描现有文件...')
        for root, dirs, files in os.walk(WATCH_DIR):
            for file in files:
                filepath = os.path.join(root, file)
                self.upload_file(filepath)
    
    def on_created(self, event):
        if not event.is_directory:
            time.sleep(1)  # 等待文件写入完成
            self.upload_file(event.src_path)
    
    def on_modified(self, event):
        if not event.is_directory:
            time.sleep(1)  # 等待文件写入完成
            self.upload_file(event.src_path, is_edit=True)

def main():
    print(f'🔬 LabVault Leaf Agent 启动')
    print(f'监控目录: {WATCH_DIR}')
    print(f'Hub URL: {HUB_URL}')
    print(f'设备名称: {DEVICE_NAME}')
    print(f'目标区域: {ZONE}')
    print(f'状态文件: {STATE_FILE}')
    print('-' * 50)
    
    # 检查监控目录权限
    if not os.access(WATCH_DIR, os.R_OK):
        print(f'❌ 无法读取监控目录: {WATCH_DIR}')
        return
    
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
