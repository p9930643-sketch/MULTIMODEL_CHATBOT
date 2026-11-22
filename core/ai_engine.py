import logging
from typing import List, Optional, Dict, Any
import google.generativeai as genai
from core.config import settings
from core.prompt_templates import EMPATHETIC_COMPANION_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class AIEngine:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip() and self.api_key != "your_gemini_api_key_here")

    def generate_chat_response(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        system_instruction: Optional[str] = None
    ) -> str:
        """
        Generates text response using Gemini with conversation context and empathetic persona.
        """
        if not self.is_configured():
            return (
                "⚠️ **Gemini API Key is not configured.**\n\n"
                "Please add your `GEMINI_API_KEY` to the `.env` file to enable live AI responses. "
                "I am ready to assist you once your key is connected!"
            )

        sys_prompt = system_instruction or EMPATHETIC_COMPANION_SYSTEM_PROMPT

        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=sys_prompt
            )

            # Build Gemini history format
            history_messages = []
            if conversation_history:
                for msg in conversation_history:
                    role = "user" if msg.get("sender") == "user" else "model"
                    history_messages.append({
                        "role": role,
                        "parts": [msg.get("content", "")]
                    })

            chat = model.start_chat(history=history_messages)
            response = chat.send_message(prompt)
            return response.text if response and response.text else "I am here with you, but I couldn't generate a text response right now."
        except Exception as e:
            logger.error("Error generating Gemini chat response: %s", e)
            return f"I encountered an error communicating with the AI service: {str(e)}"

    def generate_multimodal_response(
        self,
        prompt: str,
        media_parts: List[Any],
        system_instruction: Optional[str] = None
    ) -> str:
        """
        Processes text prompt combined with media parts (PIL images, audio file parts, documents).
        """
        if not self.is_configured():
            return (
                "⚠️ **Gemini API Key is not configured.**\n\n"
                "Please add your `GEMINI_API_KEY` to the `.env` file to process multimodal images and audio."
            )

        sys_prompt = system_instruction or EMPATHETIC_COMPANION_SYSTEM_PROMPT

        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=sys_prompt
            )
            content = media_parts + [prompt]
            response = model.generate_content(content)
            return response.text if response and response.text else "I reviewed the content, but couldn't produce a summary."
        except Exception as e:
            logger.error("Error generating Gemini multimodal response: %s", e)
            return f"Error analyzing multimodal content: {str(e)}"

ai_engine = AIEngine()
