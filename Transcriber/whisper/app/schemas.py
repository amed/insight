from typing import Literal
from pydantic import BaseModel


class WordItem(BaseModel):
    start: float
    end: float
    word: str


class SegmentItem(BaseModel):
    start: float
    end: float
    text: str
    words: list[WordItem] = []


class TranscribeResponse(BaseModel):
    model: str
    task: Literal["transcribe", "translate"]
    language: str
    language_probability: float
    duration: float
    text: str
    segments: list[SegmentItem]


class ErrorResponse(BaseModel):
    error: dict
