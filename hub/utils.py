import hashlib
import uuid
import os
import re
from datetime import datetime
from typing import Optional, Tuple
from .models import FileZone, SourceType
from .config import settings


def generate_uuid():
    return str(uuid.uuid4())


def compute_file_hash(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def parse_data_filename(filename: str) -> Optional[dict]:
    pattern = r'^(\d{8})_([a-zA-Z0-9]+)_([^_]+)(?:_(.+))?\.([a-zA-Z0-9]+)$'
    match = re.match(pattern, filename)
    if not match:
        return None
    
    date = match.group(1)
    operator = match.group(2)
    sample = match.group(3)
    experiment_subtype = match.group(5)
    ext = match.group(6)
    
    return {
        'date': date,
        'operator': operator,
        'sample': sample,
        'experiment_subtype': experiment_subtype,
        'extension': ext
    }


def validate_data_filename(filename: str) -> Tuple[bool, Optional[str]]:
    parsed = parse_data_filename(filename)
    if not parsed:
        return False, "文件名不符合命名规范：格式应为 YYYYMMDD_operator_sample[_subtype].ext"
    return True, None


def get_storage_path(zone: FileZone, filename: str, user_id: str, experiment_type: Optional[str] = None) -> str:
    if zone == FileZone.DATA:
        if not experiment_type:
            raise ValueError("数据区文件必须指定 experiment_type")
        date_str = datetime.utcnow().strftime("%Y%m%d")
        path = os.path.join(settings.DATA_ZONE_PATH, user_id, experiment_type, date_str)
    else:
        path = os.path.join(settings.COLLAB_ZONE_PATH, user_id)
    
    os.makedirs(path, exist_ok=True)
    return path


def format_log_timestamp(dt: datetime) -> str:
    return dt.strftime("%Y%m%d_%H%M")


def generate_registration_code() -> str:
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
