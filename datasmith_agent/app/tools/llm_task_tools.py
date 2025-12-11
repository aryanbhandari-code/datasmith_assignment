# TEMPORARY CHECK
import os
print(f"API KEY STATUS: {os.environ.get('OPENROUTER_API_KEY')}")
# If this prints 'None' or an empty string, the key is not loading.

import os
import requests
import json
from ..core.models import IntentPlan, SummarizationOutput, SentimentOutput, CodeAnalysis, BaseModel
from pydantic import ValidationError
from typing import List, Type

# --- Configuration for OpenRouter/DeepSeek ---
MODEL_NAME = "deepseek-ai/deepseek-r1t2-chimera" 
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY")
# Fallback function for when the API key is missing or the API fails
def LLM_MOCK_FALLBACK(prompt: str, schema: Type[BaseModel]) -> dict:
    # (The full mock logic is omitted here for brevity but should be in your file)
    # The logic ensures a structured response even on failure, preventing 500 errors.
    print(f"--- WARNING: Using MOCK FALLBACK for prompt: {prompt[:30]}... ---")
    if schema == IntentPlan:
        if "summarize" in prompt.lower() or "explain" in prompt.lower():
            return IntentPlan(intent="AMBIGUOUS", is_clear=False).model_dump()
        else:
            return IntentPlan(intent="CONVERSATIONAL", is_clear=True).model_dump()
    elif schema == SummarizationOutput:
        return SummarizationOutput(one_line_summary="Mock Summary.", three_bullets=["Mock Point 1"], five_sentence_summary="Mock five sentence summary.").model_dump()
    elif schema == CodeAnalysis:
        return CodeAnalysis(explanation="Mock Explanation.", bug_detection="Mock Bug.", time_complexity="Mock O(n)").model_dump()
    else:
        return {}


def call_llm_structured(prompt: str, schema: Type[BaseModel]) -> dict:
    """Function to call OpenRouter and enforce JSON schema."""
    if not OPENROUTER_KEY:
        return LLM_MOCK_FALLBACK(prompt, schema)

    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://your-domain.com", 
        "X-Title": "DataSmith Agent" 
    }

    system_prompt = (
        f"You are a precise agent. Your response MUST be a JSON object conforming strictly "
        f"to the following Pydantic schema (including all field names): {schema.schema_json()}. Do not include any text outside the JSON."
    )

    data = {
        "model": MODEL_NAME, 
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"}, 
        "temperature": 0.1
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status() 

        json_response_text = response.json()['choices'][0]['message']['content']
        return json.loads(json_response_text)

    except Exception as e:
        print(f"OPENROUTER API ERROR: {e}")
        return LLM_MOCK_FALLBACK(prompt, schema)

# --- LLM Implementations ---

class LLM_IntentRouter:
    @staticmethod
    def get_intent(context: str) -> IntentPlan:
        prompt = f"Determine the single primary intent (SUMMARIZE, CODE_EXPLAIN, SENTIMENT, CONVERSATIONAL, EXTRACTION_ONLY) and if the request is clear. Context: {context}"
        raw_response = call_llm_structured(prompt, IntentPlan) 
        
        try:
            return IntentPlan(**raw_response)
        except (ValidationError, TypeError):
            return IntentPlan(intent="AMBIGUOUS", is_clear=False)


class LLM_TaskTools:
    @staticmethod
    def generate_follow_up(context: str) -> str:
        return "I detected content, but what should I do with it? (e.g., Summarize, Analyze Sentiment, Explain Code)"

    @staticmethod
    def summarize(content: str, constraints: List[str]) -> str:
        prompt = f"Summarize the following content. Output must contain a 1-line summary, 3 bullets, and a 5-sentence summary. Content: {content}"
        mock_output = call_llm_structured(prompt, SummarizationOutput)
        
        summary = f"One-Line Summary: {mock_output.get('one_line_summary', 'N/A')}\n\n"
        summary += "Key Points:\n" + "\n".join([f"* {b}" for b in mock_output.get('three_bullets', [])])
        summary += f"\n\nFive-Sentence Summary:\n{mock_output.get('five_sentence_summary', 'N/A')}"
        return summary

    @staticmethod
    def sentiment(content: str) -> str:
        prompt = f"Perform sentiment analysis on the text. Return the JSON structure with label, confidence (as a percentage), and one-line justification. Text: {content}"
        mock_output = call_llm_structured(prompt, SentimentOutput)
        
        return (
            f"Label: {mock_output.get('label', 'N/A')} "
            f"(Confidence: {mock_output.get('confidence', 'N/A')}) - "
            f"Justification: {mock_output.get('justification', 'N/A')}"
        )

    @staticmethod
    def code_explain(content: str) -> str:
        prompt = (
            f"Analyze the following Python code. Your response MUST be a single JSON object conforming to the CodeAnalysis schema. "
            f"Analyze its function, detect any bugs, and state its time complexity. Code:\n\n```python\n{content}\n```"
        )
        analysis_output = call_llm_structured(prompt, CodeAnalysis) 

        return (
            f"Code Explanation:\n{analysis_output.get('explanation', 'N/A')}\n\n"
            f"Bug Detection:\n{analysis_output.get('bug_detection', 'N/A')}\n\n"
            f"Time Complexity: {analysis_output.get('time_complexity', 'N/A')}"
        )
        
    @staticmethod
    def conversational(query: str) -> str:
        return f"Hello! I am a DataSmith Agent. I can process text, images, PDFs, or audio, and perform tasks like summarization, sentiment analysis, and code explanation based on your goal."