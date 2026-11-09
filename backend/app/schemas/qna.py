"""Pydantic schemas for grounded question answering."""

from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    """User question submitted to the grounded review chat."""

    question: str = Field(min_length=3, max_length=2000, description="Question about the paper or review findings.")


class AnswerResponse(BaseModel):
    """Grounded answer citing review findings and paper text."""

    question: str
    answer: str
