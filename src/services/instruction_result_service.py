# src/services/instruction_result_service.py

import logging
import uuid
from typing import List, Optional
from datetime import datetime
from src.domain.entities import Instruction, InstructionStep, Keywords, ResourceRegistry
from src.domain.repositories import (
    IInstructionRepository, IInstructionStepRepository,
    IKeywordsRepository, IResourceRegistryRepository
)
from src.domain.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class InstructionResultService:
    """
    Сервис для управления результатами обработки инструкций.
    
    Предоставляет методы для:
    - Создания инструкций с шагами
    - Управления ключевыми словами
    - Регистрации ресурсов
    """
    
    def __init__(self, 
                 instruction_repo: IInstructionRepository,
                 step_repo: IInstructionStepRepository,
                 keywords_repo: IKeywordsRepository,
                 resource_repo: IResourceRegistryRepository):
        self.instruction_repo = instruction_repo
        self.step_repo = step_repo
        self.keywords_repo = keywords_repo
        self.resource_repo = resource_repo
    
    def create_instruction(self, 
                          task_id: str,
                          title: str,
                          description: str) -> Instruction:
        """Создать новую инструкцию для задачи"""
        try:
            instruction = Instruction(
                id=str(uuid.uuid4()),
                task_id=task_id,
                title=title,
                description=description,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.instruction_repo.create_instruction(instruction)
            logger.info(f"Инструкция создана: {instruction.id} для задачи {task_id}")
            return instruction
        except DatabaseError as e:
            logger.error(f"Ошибка при создании инструкции: {e}")
            raise
    
    def add_instruction_step(self,
                            instruction_id: str,
                            step_order: int,
                            title: str,
                            text: str,
                            time_start: Optional[float] = None,
                            time_end: Optional[float] = None,
                            image_id: Optional[str] = None) -> InstructionStep:
        """Добавить шаг к инструкции"""
        try:
            step = InstructionStep(
                id=str(uuid.uuid4()),
                instruction_id=instruction_id,
                step_order=step_order,
                title=title,
                text=text,
                time_start=time_start,
                time_end=time_end,
                image_id=image_id,
                created_at=datetime.utcnow()
            )
            self.step_repo.create_step(step)
            logger.info(f"Шаг {step_order} добавлен к инструкции {instruction_id}")
            return step
        except DatabaseError as e:
            logger.error(f"Ошибка при добавлении шага: {e}")
            raise
    
    def get_instruction_with_steps(self, instruction_id: str) -> Optional[dict]:
        """Получить инструкцию со всеми её шагами"""
        try:
            instruction = self.instruction_repo.get_instruction_by_id(instruction_id)
            if not instruction:
                return None
            
            steps = self.step_repo.get_steps_by_instruction_id(instruction_id)
            keywords = self.keywords_repo.get_keywords_by_instruction(instruction_id)
            
            return {
                'instruction': instruction,
                'steps': steps,
                'keywords': keywords
            }
        except DatabaseError as e:
            logger.error(f"Ошибка при получении инструкции {instruction_id}: {e}")
            raise
    
    def get_instruction_by_task_id(self, task_id: str) -> Optional[dict]:
        """Получить инструкцию для задачи"""
        try:
            instruction = self.instruction_repo.get_instruction_by_task_id(task_id)
            if not instruction:
                return None
            
            steps = self.step_repo.get_steps_by_instruction_id(instruction.id)
            keywords = self.keywords_repo.get_keywords_by_instruction(instruction.id)
            resources = self.resource_repo.get_resources_by_instruction(instruction.id)
            
            return {
                'instruction': instruction,
                'steps': steps,
                'keywords': keywords,
                'resources': resources
            }
        except DatabaseError as e:
            logger.error(f"Ошибка при получении инструкции для задачи {task_id}: {e}")
            raise
    
    def set_keywords(self, instruction_id: str, keywords_list: List[str]) -> Keywords:
        """Установить ключевые слова для инструкции"""
        try:
            # Проверяем, существуют ли уже ключевые слова
            existing = self.keywords_repo.get_keywords_by_instruction(instruction_id)
            
            keywords = Keywords(
                id=existing.id if existing else str(uuid.uuid4()),
                instruction_id=instruction_id,
                keywords_list=keywords_list,
                created_at=existing.created_at if existing else datetime.utcnow()
            )
            
            if existing:
                self.keywords_repo.update_keywords(keywords)
                logger.info(f"Ключевые слова обновлены для инструкции {instruction_id}")
            else:
                self.keywords_repo.create_keywords(keywords)
                logger.info(f"Ключевые слова созданы для инструкции {instruction_id}")
            
            return keywords
        except DatabaseError as e:
            logger.error(f"Ошибка при установке ключевых слов: {e}")
            raise
    
    def register_resource(self,
                         filename: str,
                         filepath: str,
                         resource_type: str,
                         instruction_id: Optional[str] = None) -> ResourceRegistry:
        """Зарегистрировать ресурс (файл)"""
        try:
            resource = ResourceRegistry(
                id=str(uuid.uuid4()),
                filename=filename,
                filepath=filepath,
                resource_type=resource_type,
                instruction_id=instruction_id,
                created_at=datetime.utcnow()
            )
            self.resource_repo.create_resource(resource)
            logger.info(f"Ресурс зарегистрирован: {resource.id} ({filename})")
            return resource
        except DatabaseError as e:
            logger.error(f"Ошибка при регистрации ресурса: {e}")
            raise
    
    def get_all_instructions(self, limit: int = 50, offset: int = 0) -> List[Instruction]:
        """Получить все инструкции"""
        try:
            return self.instruction_repo.get_all_instructions(limit=limit, offset=offset)
        except DatabaseError as e:
            logger.error(f"Ошибка при получении инструкций: {e}")
            raise
    
    def delete_instruction(self, instruction_id: str) -> None:
        """Удалить инструкцию (каскадно удалит шаги, ключевые слова и ресурсы)"""
        try:
            self.instruction_repo.delete_instruction(instruction_id)
            logger.info(f"Инструкция удалена: {instruction_id}")
        except DatabaseError as e:
            logger.error(f"Ошибка при удалении инструкции: {e}")
            raise

    def update_instruction_full(self, instruction_id: str, data: dict) -> None:
        """
        Полное обновление инструкции: заголовок, описание, ключевые слова и шаги.
        data: {
            'title': str,
            'description': str,
            'keywords': List[str],
            'steps': [
                {'id': str, 'title': str, 'text': str, 'time_start': float, 'time_end': float, 'image_id': str},
                ...
            ]
        }
        """
        try:
            # 1. Обновляем основную информацию
            instruction = self.instruction_repo.get_instruction_by_id(instruction_id)
            if not instruction:
                raise DatabaseError(f"Инструкция {instruction_id} не найдена")
            
            instruction.title = data.get('title', instruction.title)
            instruction.description = data.get('description', instruction.description)
            instruction.updated_at = datetime.utcnow()
            self.instruction_repo.update_instruction(instruction)
            
            # 2. Обновляем ключевые слова
            if 'keywords' in data:
                self.set_keywords(instruction_id, data['keywords'])
            
            # 3. Обновляем шаги
            if 'steps' in data:
                # Самый простой и надежный способ при изменении порядка/количества:
                # Удаляем все старые шаги и создаем новые с правильным порядком
                # (В реальном проекте лучше делать merge, но для данной задачи это допустимо)
                
                # Сначала получаем все текущие шаги, чтобы удалить их
                current_steps = self.step_repo.get_steps_by_instruction_id(instruction_id)
                for s in current_steps:
                    self.step_repo.delete_step(s.id)
                
                # Создаем шаги заново в указанном порядке
                for i, step_data in enumerate(data['steps'], 1):
                    self.add_instruction_step(
                        instruction_id=instruction_id,
                        step_order=i,
                        title=step_data['title'],
                        text=step_data['text'],
                        time_start=step_data.get('time_start'),
                        time_end=step_data.get('time_end'),
                        image_id=step_data.get('image_id')
                    )
            
            logger.info(f"Инструкция {instruction_id} полностью обновлена")
        except Exception as e:
            logger.error(f"Ошибка при полном обновлении инструкции {instruction_id}: {e}")
            raise DatabaseError(f"Не удалось обновить инструкцию: {e}")
