import sqlite3
import os
from datetime import datetime

DB_PATH = r"D:\ChatgptDATAB\chatgpt_team.sqlite"

def save_chat_request(role, content, function_call_json="", metadata_json=""):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO chats (timestamp, role, content, function_call_json, metadata_json) VALUES (?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), role, content, function_call_json, metadata_json)
        )

def save_file_upload(filename, filetype, mimetype, content, chat_id=None, extra_json=""):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO files (timestamp, filename, filetype, mimetype, content, chat_id, extra_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), filename, filetype, mimetype, content, chat_id, extra_json)
        )

def save_raw_request(endpoint, raw_body, headers_json):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO raw_requests (timestamp, endpoint, body, headers_json) VALUES (?, ?, ?, ?)",
            (datetime.now().isoformat(), endpoint, raw_body, headers_json)
        )

def init_db():
    """Create all DB tables at app startup. Call this ONCE, not per-insert."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS chats ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "timestamp TEXT NOT NULL,"
            "role TEXT NOT NULL,"
            "content TEXT,"
            "function_call_json TEXT,"
            "metadata_json TEXT)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS files ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "timestamp TEXT NOT NULL,"
            "filename TEXT NOT NULL,"
            "filetype TEXT,"
            "mimetype TEXT,"
            "content BLOB,"
            "chat_id INTEGER,"
            "extra_json TEXT)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS raw_requests ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "timestamp TEXT NOT NULL,"
            "endpoint TEXT,"
            "body BLOB,"
            "headers_json TEXT)"
        )
