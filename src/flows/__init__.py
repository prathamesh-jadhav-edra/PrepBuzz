"""Flows module - Contains all processing flows."""

from .question_flow import QuestionSelectionFlow
from .reasoning_flow import ReasoningExtractionFlow
from .llm_flow import LLMProcessingFlow
from .video_flow import VideoGenerationFlow

# Import flows to register them
from . import question_flow
from . import reasoning_flow
from . import llm_flow
from . import video_flow

__all__ = [
    "QuestionSelectionFlow",
    "ReasoningExtractionFlow",
    "LLMProcessingFlow",
    "VideoGenerationFlow",
]
