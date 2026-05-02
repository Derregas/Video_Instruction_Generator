# src/models.py

import os
import json
import sqlite3
from enum import Enum
from datetime import datetime

class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskManager:
    def __init__(self, db_path="tasks.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path) if os.path.dirname(self.db_path) else '.', exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    video_filename TEXT,
                    document_names TEXT,
                    result TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)
            ''')
            conn.commit()
    
    def create_task(self, task_id, video_filename, document_names=None):
        doc_names_json = None
        if document_names:
            import json
            doc_names_json = json.dumps(document_names)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'INSERT INTO tasks (id, status, video_filename, document_names) VALUES (?, ?, ?, ?)',
                (task_id, TaskStatus.PENDING.value, video_filename, doc_names_json)
            )
            conn.commit()
    
    def update_task(self, task_id, status=None, result=None, error_message=None):
        updates = []
        params = []
        if status:
            updates.append("status = ?")
            params.append(status)
        if result:
            updates.append("result = ?")
            params.append(result)
        if error_message:
            updates.append("error_message = ?")
            params.append(error_message)
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(task_id)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f'UPDATE tasks SET {", ".join(updates)} WHERE id = ?',
                params
            )
            conn.commit()

    def get_task(self, task_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
            if not row:
                return None
            task = dict(row)
            # Распарсиваем JSON-строки в объекты Python
            if task.get('document_names'):
                try:
                    task['document_names'] = json.loads(task['document_names'])
                except json.JSONDecodeError:
                    task['document_names'] = []
            else:
                task['document_names'] = []
                
            return task
        
    def get_all_tasks(self, limit=50):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                'SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?',
                (limit,)
            ).fetchall()
            return [dict(r) for r in rows]