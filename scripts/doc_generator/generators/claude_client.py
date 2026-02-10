"""Claude API client - uses urllib (no SDK dependency)"""
import urllib.request
import urllib.error
import json
import time
from config import Config


class ClaudeClient:
    """Client for Claude API using urllib"""

    def __init__(self, api_key):
        """
        Initialize Claude API client

        Args:
            api_key: Anthropic API key
        """
        self.api_key = api_key
        self.model = Config.CLAUDE_MODEL
        self.max_tokens = Config.MAX_TOKENS
        self.temperature = Config.TEMPERATURE
        self.api_url = "https://api.anthropic.com/v1/messages"

    def generate(self, user_prompt, system_prompt=""):
        """
        Generate content using Claude API

        Args:
            user_prompt: User message/prompt
            system_prompt: System prompt (optional)

        Returns:
            str: Generated content

        Raises:
            Exception: If API call fails after retries
        """
        return self._generate_with_retry(user_prompt, system_prompt, retries=3)

    def _generate_with_retry(self, user_prompt, system_prompt, retries=3):
        """Generate with exponential backoff retry"""
        for attempt in range(retries):
            try:
                return self._make_api_call(user_prompt, system_prompt)
            except urllib.error.HTTPError as e:
                if e.code == 429:  # Rate limit
                    if attempt < retries - 1:
                        wait_time = 2 ** attempt
                        print(f"Rate limited. Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                        continue
                raise Exception(f"Claude API HTTP Error {e.code}: {e.reason}")
            except urllib.error.URLError as e:
                raise Exception(f"Claude API URL Error: {e.reason}")
            except Exception as e:
                raise Exception(f"Claude API Error: {str(e)}")

        raise Exception("Max retries exceeded")

    def _make_api_call(self, user_prompt, system_prompt):
        """Make actual API call to Claude"""
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }

        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [{"role": "user", "content": user_prompt}]
        }

        if system_prompt:
            payload["system"] = system_prompt

        # Create request
        req = urllib.request.Request(
            self.api_url,
            data=json.dumps(payload).encode('utf-8'),
            headers=headers,
            method="POST"
        )

        # Make request
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data["content"][0]["text"]
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else "No error details"
            raise Exception(f"Claude API HTTP {e.code}: {error_body}")
