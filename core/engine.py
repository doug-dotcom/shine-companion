# core/engine.py
import os
import time
import traceback
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv
from openai import OpenAI


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)).strip())
    except Exception:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)).strip())
    except Exception:
        return default


class CoreEngine:
    """
    Shine Companion CoreEngine
    - Calls OpenAI Chat Completions (openai==2.x)
    - Retries transient failures (including 502/5xx, timeouts, connection errors)
    """

    def __init__(self) -> None:
        load_dotenv()

        self.api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment.")

        # Model (default to mini)
        self.model = (os.getenv("SHINE_MODEL") or "gpt-4o-mini").strip()

        # Optional base URL override (normally NOT needed)
        self.base_url = (os.getenv("OPENAI_BASE_URL") or "").strip() or None

        # Timeouts / retries
        self.timeout_s = _env_float("OPENAI_TIMEOUT_S", 30.0)
        self.max_retries = _env_int("OPENAI_MAX_RETRIES", 6)

        # Create an httpx client with sane timeouts (Railway-friendly)
        timeout = httpx.Timeout(
            connect=self.timeout_s,
            read=self.timeout_s,
            write=self.timeout_s,
            pool=self.timeout_s,
        )
        self._http = httpx.Client(timeout=timeout, follow_redirects=True)

        # Create OpenAI client
        if self.base_url:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, http_client=self._http)
        else:
            self.client = OpenAI(api_key=self.api_key, http_client=self._http)

    def generate_from_messages(self, messages: List[Dict[str, Any]], temperature: float = 0.2) -> str:
        """
        messages example:
          [{"role":"system","content":"..."},{"role":"user","content":"Hello"}]
        Returns assistant text.
        Raises RuntimeError on permanent failure (after retries).
        """

        last_err: Optional[BaseException] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                )
                # OpenAI SDK returns choices[0].message.content
                return (resp.choices[0].message.content or "").strip()

            except Exception as e:
                last_err = e

                # Print full traceback to Railway logs (so we can see the real cause)
                print("==== OPENAI CALL FAILED ====")
                print(f"Attempt {attempt}/{self.max_retries}")
                print(f"Model: {self.model}")
                print(f"Base URL: {self.base_url or 'default'}")
                print(str(e))
                traceback.print_exc()
                print("============================")

                # Exponential backoff with small cap
                # (handles transient 5xx / 502 / timeouts / connection errors)
                sleep_s = min(2 ** (attempt - 1), 10)
                time.sleep(sleep_s)

        raise RuntimeError(f"OpenAI request failed after {self.max_retries} retries: {last_err}")

    def safe_generate(self, messages: List[Dict[str, Any]], temperature: float = 0.2) -> Dict[str, Any]:
        """
        Wrapper that never throws: returns {ok, text} or {ok:false, error, detail}
        """
        try:
            text = self.generate_from_messages(messages, temperature=temperature)
            return {"ok": True, "text": text}
        except Exception as e:
            return {"ok": False, "error": "provider_error", "detail": str(e)}