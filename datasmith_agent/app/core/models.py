from pydantic import BaseModel, Field
from typing import List, Optional, Any

# --- Intent Models ---
class IntentPlan(BaseModel):
    """Structured output for the LLM Intent Router."""
    intent: str = Field(..., description="One of: SUMMARIZE, SENTIMENT, CODE_EXPLAIN, YOUTUBE_FETCH, CONVERSATIONAL, EXTRACTION_ONLY, AMBIGUOUS")
    detected_constraints: List[str] = Field(default_factory=list, description="List of format constraints (e.g., '3_bullets', '5_sentences', 'bug_detection', 'time_complexity')")
    is_clear: bool = Field(..., description="True if the user's request is clear and actionable, False if a follow-up is needed.")

# --- Task Output Models ---
class SummarizationOutput(BaseModel):
    """Output structure for the Summarization Task."""
    one_line_summary: str
    three_bullets: List[str]
    five_sentence_summary: str

class SentimentOutput(BaseModel):
    """Output structure for the Sentiment Analysis Task."""
    label: str = Field(..., description="Positive, Negative, or Neutral.")
    confidence: str = Field(..., description="LLM's confidence level (e.g., '95%', 'High').")
    justification: str = Field(..., description="One-line justification for the label.")

class CodeAnalysis(BaseModel):
    """Output structure for Code Explanation Task."""
    explanation: str
    bug_detection: str
    time_complexity: str

class AgentResponse(BaseModel):
    """Final response returned to the UI."""
    status: str
    extracted_text: str
    result: str
    log: List[str]