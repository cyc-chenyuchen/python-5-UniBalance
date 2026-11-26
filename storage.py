import hashlib
import json
import os
import threading
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MENU_FILE = DATA_DIR / "menu.json"
RECORDS_FILE = DATA_DIR / "records.json"
MAX_RECORDS = 20
_record_lock = threading.Lock()


def load_menu():
    try:
        with MENU_FILE.open("r", encoding="utf-8") as file:
            menu = json.load(file)
    except FileNotFoundError:
        raise ValueError("找不到 data/menu.json；請確認遊戲設定檔案存在。")
    except json.JSONDecodeError as error:
        raise ValueError(f"data/menu.json 格式錯誤：{error}") from error

    if not isinstance(menu, dict):
        raise ValueError("data/menu.json 格式錯誤：根節點必須為物件。")
    labels = menu.get("metric_labels")
    initial = menu.get("initial_metrics")
    required = {"budget_remaining", "problem_improvement", "satisfaction", "fairness"}
    if not isinstance(labels, dict) or not isinstance(initial, dict):
        raise ValueError("data/menu.json 格式錯誤：缺少指標名稱或初始值。")
    if set(labels) != required or set(initial) != required:
        raise ValueError("data/menu.json 格式錯誤：指標欄位不完整。")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in initial.values()):
        raise ValueError("data/menu.json 格式錯誤：初始值必須為整數。")
    return menu


def load_records():
    if not RECORDS_FILE.exists():
        RECORDS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with RECORDS_FILE.open("w", encoding="utf-8") as file:
            json.dump([], file, ensure_ascii=False)
        return []
    try:
        with RECORDS_FILE.open("r", encoding="utf-8") as file:
            records = json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(f"data/records.json 格式錯誤：{error}") from error
    if not isinstance(records, list):
        raise ValueError("data/records.json 格式錯誤：根節點必須為陣列。")
    return records[-MAX_RECORDS:]


def save_record(record):
    with _record_lock:
        records = load_records()
        record_ids = {item.get("record_id") for item in records if isinstance(item, dict)}
        if record.get("record_id") not in record_ids:
            records.append(record)
            records = records[-MAX_RECORDS:]
            with RECORDS_FILE.open("w", encoding="utf-8") as file:
                json.dump(records, file, ensure_ascii=False, indent=2)


def record_archive_key(record):
    record_id = record.get("record_id") if isinstance(record, dict) else None
    if isinstance(record_id, str) and record_id:
        return f"id:{record_id}"
    serialized = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    fingerprint = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return f"legacy:{fingerprint}"


def delete_record(archive_key):
    with _record_lock:
        records = load_records()
        record_index = next(
            (
                index for index, record in enumerate(records)
                if record_archive_key(record) == archive_key
            ),
            None,
        )
        if record_index is None:
            return False
        records.pop(record_index)
        with RECORDS_FILE.open("w", encoding="utf-8") as file:
            json.dump(records, file, ensure_ascii=False, indent=2)
        return True


def clear_records():
    with _record_lock:
        records = load_records()
        with RECORDS_FILE.open("w", encoding="utf-8") as file:
            json.dump([], file, ensure_ascii=False, indent=2)
        return len(records)
