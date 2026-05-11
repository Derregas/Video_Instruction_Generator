# src/domain/exceptions.py

class TaskRepositoryError(Exception):
    """Базовая ошибка репозитория"""
    pass

class TaskNotFoundError(TaskRepositoryError):
    """Задача не найдена"""
    pass

class TaskAlreadyExistsError(TaskRepositoryError):
    """Задача с таким ID уже существует"""
    pass

class DatabaseError(TaskRepositoryError):
    """Ошибка работы с БД"""
    pass

class InvalidTaskStateError(TaskRepositoryError):
    """Ошибка явного укзания из-за неверного статуса"""
    pass