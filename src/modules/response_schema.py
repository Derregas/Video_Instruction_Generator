from typing import List
from pydantic import BaseModel, Field

class Step(BaseModel):
    title: str = Field(
        description="Краткое название шага"
    )
    description: str = Field(
        description="Подробное описание шага",
        min_length=300
    )
    start_time: float = Field(
        description="Время начала шага"
    )
    end_time: float = Field(
        description="Время конца шага" 
    )
    best_image_id: str = Field(
           description="Путь к изображению из наиболее подходящего шага"
    )

class Instruction(BaseModel):
    name: str = Field(
        description="Краткое название всей инструкции"
    )
    key_words: List[str] = Field(
        description="Ключевые слова из инструкции"
    )
    description: str = Field(
        description="Назначение инструкции. Не более 3х предложений",
        max_length=500
    )
    steps: List[Step]