import os
from werkzeug.datastructures import FileStorage

def docs_size(docs: list[FileStorage]) -> int:
    total_size = 0
    for doc in docs:
        doc.seek(0, os.SEEK_END)    # Перемещаем указатель в конец файла
        size = doc.tell()           # Получаем позицию указателя в байтах - размер файла
        doc.seek(0)                 # возвращаем указатель в начало
        total_size += size
    return total_size

def docs_save(docs: list[FileStorage], request_temp_dir: str) -> list[str]:
    document_paths = []
    for doc in docs:
        doc_path = os.path.join(request_temp_dir, f"doc_{doc.filename}")
        doc.save(doc_path)
        document_paths.append(doc_path)
    return document_paths