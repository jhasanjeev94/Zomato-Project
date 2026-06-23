import json
import time
from groq import Groq
from backend.config import settings
from backend.models.schemas import RestaurantRecommendation

MAX_RETRIES = 3

class GroqClient:
    def __init__(self):
        self.client = None

    def _init_client(self):
        if self.client is None:
            if not settings.GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY is not set in environment")
            self.client = Groq(api_key=settings.GROQ_API_KEY)

    def get_recommendations(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> dict:
        """Call Groq API with retry logic and parse the response."""
        self._init_client()
        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.7,
                    max_tokens=settings.MAX_TOKENS,
                    response_format={"type": "json_object"},
                )

                content = response.choices[0].message.content
                return self._parse_response(content)

            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    wait = 2 ** attempt  # Exponential backoff
                    time.sleep(wait)
                else:
                    raise RuntimeError(f"Groq API failed after {MAX_RETRIES} retries: {e}")

    def _parse_response(self, content: str) -> dict:
        """Parse LLM response as JSON with regex fallback."""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Fallback: try to extract JSON block from response
            import re
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise ValueError("Could not parse LLM response as JSON")

groq_client = GroqClient()
