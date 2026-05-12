# src/services/task_queue.py

import queue
import threading
import logging
from typing import Optional
from src.domain.entities import TaskStatus
from src.domain.repositories import ITaskRepository
from flask_app.task_processor import ITaskProcessor

logger = logging.getLogger(__name__)

class TaskQueue:
    """
    Очередь выполнения задач - выполняет одну задачу за раз.
    """
    
    def __init__(self, task_repository: ITaskRepository, processor: ITaskProcessor):
        self.task_repo = task_repository
        self.processor = processor
        self.queue: queue.Queue = queue.Queue()  # FIFO очередь
        self.is_running = False
        self.worker_thread: Optional[threading.Thread] = None
        self.current_task_id: Optional[str] = None
        self.lock = threading.Lock()  # Для синхронизации
    
    def start(self):
        """Запускает worker поток"""
        if self.is_running:
            logger.warning("TaskQueue уже запущена")
            return
        
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        logger.info("TaskQueue запущена")
    
    def stop(self):
        """Останавливает очередь"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("TaskQueue остановлена")
    
    def enqueue(self, task_id: str) -> bool:
        """
        Добавляет задачу в очередь.
        Возвращает True если успешно, False если задача уже в очереди.
        """
        # Проверяем что задача не добавлена дважды
        if task_id in list(self.queue.queue):
            logger.warning(f"Задача {task_id} уже в очереди")
            return False
        
        if task_id == self.current_task_id:
            logger.warning(f"Задача {task_id} уже выполняется")
            return False
        
        self.queue.put(task_id)
        logger.info(f"Задача {task_id} добавлена в очередь. Размер очереди: {self.queue.qsize()}")
        return True
    
    def get_queue_size(self) -> int:
        """Возвращает размер очереди"""
        return self.queue.qsize()
    
    def get_current_task(self) -> Optional[str]:
        """Возвращает ID текущей выполняемой задачи"""
        with self.lock:
            return self.current_task_id
    
    def _worker(self):
        """Основной worker поток - выполняет задачи последовательно"""
        while self.is_running:
            try:
                # Получаем задачу из очереди с timeout
                # Если очередь пуста, ждёт 5 секунд
                task_id = self.queue.get(timeout=5)
                
                with self.lock:
                    self.current_task_id = task_id
                
                #logger.info(f"[{task_id}] Начало обработки из очереди")
                
                self.processor.process(task_id)
                
            except queue.Empty:
                # Очередь пуста - продолжаем ждать
                continue
            except Exception as e:
                logger.error(f"Ошибка в worker потоке: {e}", exc_info=True)
            finally:
                with self.lock:
                    self.current_task_id = None
    
    def load_pending_tasks(self):
        """
        Загружает все незавершённые задачи при старте сервера.
        Выполняется один раз при инициализации.
        """
        try:
            # Получаем все задачи (без лимита)
            all_tasks = self.task_repo.get_all(limit=1000)
            all_tasks.reverse()
            pending_tasks = [
                task for task in all_tasks 
                if task.status in (TaskStatus.PENDING, TaskStatus.PROCESSING)
            ]
            
            logger.info(f"Найдено {len(pending_tasks)} незавершённых задач")
            
            # Добавляем в очередь (они будут выполнены по очереди)
            for task in pending_tasks:
                self.enqueue(task.id)
                
        except Exception as e:
            logger.error(f"Ошибка при загрузке pending задач: {e}", exc_info=True)