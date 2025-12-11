from ..tools.extraction_tools import ImageOCR, PDFParser, AudioTranscriber, YouTubeTool # Corrected relative import
from ..tools.llm_task_tools import LLM_IntentRouter, LLM_TaskTools                     # Corrected relative import
from .models import AgentResponse, IntentPlan                                           # Corrected relative import (local to core)
from fastapi import UploadFile
from typing import List, Optional
import re 

class AgentOrchestrator:
    def __init__(self):
        self.log: List[str] = []

    def _log(self, message: str):
        """Internal logging utility for Explainability."""
        self.log.append(f"[{len(self.log) + 1}] {message}")

    async def run(self, query: str, file: Optional[UploadFile]) -> AgentResponse:
        self.log = []
        extracted_text = query.strip()
        final_result = ""
        ocr_confidence = None
        
        self._log(f"Received query: '{query[:50]}...'")

        # --- STEP 1: Input Handling and Extraction ---
        if file:
            file_type = file.filename.split('.')[-1].lower()
            self._log(f"Processing uploaded file: {file.filename} (Type: {file_type})")
            
            try:
                if file_type in ['jpg', 'png']:
                    # NOTE: Replace mock with actual Pytesseract code
                    extracted_text, ocr_confidence = await ImageOCR.extract(file)
                elif file_type == 'pdf':
                    # NOTE: Replace mock with actual pdfplumber code
                    extracted_text = await PDFParser.extract(file)
                elif file_type in ['mp3', 'wav', 'm4a']:
                    # NOTE: Replace mock with actual Whisper code
                    extracted_text = await AudioTranscriber.transcribe(file)
                else:
                    self._log("Unsupported file type. Treating as Text-Only.")
                
                if extracted_text:
                    self._log(f"Content extracted: {extracted_text[:50]}...")
                
            except Exception as e:
                self._log(f"Error during extraction: {e}. Stopping execution.")
                return AgentResponse(status="Error", extracted_text="", result=f"Extraction failed: {e}", log=self.log)

        full_context = extracted_text + " " + query.strip()

        # --- STEP 2: Intent Understanding and Follow-Up Check (Autonomy & Planning) ---
        intent_plan: IntentPlan = LLM_IntentRouter.get_intent(full_context)
        self._log(f"Identified intent: {intent_plan.intent} (Clear: {intent_plan.is_clear})")

        # Check for YouTube URL regardless of LLM intent for direct tool use
        url_match = re.search(r'(?:youtube\.com/\S*(?:v=|/e/)|youtu\.be/)\S*', full_context)
        if url_match:
            intent_plan.intent = "YOUTUBE_FETCH"
            intent_plan.is_clear = True
            
        # MANDATORY FOLLOW-UP QUESTION RULE
        if intent_plan.is_clear == False or intent_plan.intent == "AMBIGUOUS":
            follow_up_q = LLM_TaskTools.generate_follow_up(full_context)
            self._log("Intent ambiguous. Returning follow-up question.")
            return AgentResponse(
                status="Awaiting Clarity", 
                extracted_text=extracted_text, 
                result=follow_up_q, 
                log=self.log
            )

        # --- STEP 3: Task Execution ---
        self._log(f"Executing task: {intent_plan.intent}")
        try:
            if intent_plan.intent == "YOUTUBE_FETCH":
                url = url_match.group(0) if url_match else query 
                final_result = YouTubeTool.fetch_transcript(url)
            elif intent_plan.intent == "SUMMARIZE":
                final_result = LLM_TaskTools.summarize(extracted_text, intent_plan.detected_constraints)
            elif intent_plan.intent == "SENTIMENT":
                final_result = LLM_TaskTools.sentiment(extracted_text)
            elif intent_plan.intent == "CODE_EXPLAIN":
                final_result = LLM_TaskTools.code_explain(extracted_text)
            elif intent_plan.intent == "CONVERSATIONAL":
                final_result = LLM_TaskTools.conversational(query)
            elif intent_plan.intent == "EXTRACTION_ONLY":
                confidence_str = f" (OCR Confidence: {ocr_confidence})" if ocr_confidence is not None else ""
                final_result = f"Extracted Text: {extracted_text}{confidence_str}"
            else:
                final_result = f"Unknown Intent: {intent_plan.intent}. Please clarify."
        
        except Exception as e:
            self._log(f"Error during task execution: {e}")
            final_result = f"Task Execution Failed: {e}"

        self._log("Execution complete. Formatting final output.")
        
        return AgentResponse(
            status="Complete", 
            extracted_text=extracted_text, 
            result=final_result, 
            log=self.log
        )