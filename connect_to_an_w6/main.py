import os
import json
import re
import time
import random
from datetime import datetime, timezone
from pathlib import Path
from enum import Enum
from dotenv import load_dotenv
from openai import OpenAI, APITimeoutError, RateLimitError, APIStatusError
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ValidationError

load_dotenv()
app = FastAPI()

PROMPT_VERSION = "triage-v1"
PROMPT_PATH = Path(f"prompts/{PROMPT_VERSION}.md")
MODEL_NAME = os.getenv("LLM_MODEL", "meta-llama/llama-3.2-1b-instruct")

Path("logs").mkdir(exist_ok=True)

client = OpenAI(
    base_url=os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1/"),
    api_key=os.getenv("LLM_API_KEY", os.getenv("OPENROUTER_API_KEY", "ollama")),
    timeout=30.0,
    max_retries=0,
)

def get_system_prompt() -> str:
    if not PROMPT_PATH.exists():
        raise RuntimeError(f"Prompt file {PROMPT_PATH} not found.")
    return PROMPT_PATH.read_text(encoding="utf-8")

class TriageInput(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)

class Category(str, Enum):
    billing = "billing"
    bug = "bug"
    feature = "feature"
    account = "account"
    other = "other"

class Urgency(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"

class TriageOutput(BaseModel):
    category: Category
    urgency: Urgency
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str

def extract_json(raw_text: str) -> str:
    text = raw_text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else text

def log_cost(prompt_version: str, model: str, usage, duration_ms: float, repaired: bool):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt_version": prompt_version,
        "model": model,
        "input_tokens": usage.prompt_tokens if usage else None,
        "output_tokens": usage.completion_tokens if usage else None,
        "duration_ms": round(duration_ms, 1),
        "repaired": repaired,
    }
    print("COST_LOG:", json.dumps(entry))

def quarantine(input_text: str, raw_output: str, error: str):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt_version": PROMPT_VERSION,
        "input": input_text,
        "raw_output": raw_output,
        "error": error,
    }
    with open("logs/quarantine.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def call_model_with_retry(messages: list, max_attempts: int = 3):
    last_exception = None
    for attempt in range(max_attempts):
        start = time.monotonic()
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                temperature=0.2,
                messages=messages,
            )
            duration_ms = (time.monotonic() - start) * 1000
            return response, duration_ms
        except APITimeoutError as e:
            last_exception = e
        except RateLimitError as e:
            last_exception = e
        except APIStatusError as e:
            if 500 <= e.status_code < 600:
                last_exception = e
            else:
                raise
        sleep_time = (2 ** attempt) + random.uniform(0, 0.5)
        time.sleep(sleep_time)
    raise last_exception

def call_model(user_text: str, extra_messages: list | None = None):
    messages = [
        {"role": "system", "content": get_system_prompt()},
        {"role": "user", "content": user_text}
    ]
    if extra_messages:
        messages.extend(extra_messages)
    response, duration_ms = call_model_with_retry(messages)
    return response.choices[0].message.content, response.usage, duration_ms

@app.post("/triage", response_model=TriageOutput)
def triage(payload: TriageInput):
    if os.getenv("LLM_ENABLED", "true").lower() == "false":
        return TriageOutput(
            category=Category.other,
            urgency=Urgency.low,
            confidence=0.0,
            reason="LLM disabled via kill switch; returning safe fallback."
        )

    if os.getenv("LLM_STUB") == "1":
        return TriageOutput(
            category=Category.other,
            urgency=Urgency.low,
            confidence=0.42,
            reason="Stub reason, no model called."
        )

    try:
        raw_1, usage_1, duration_1 = call_model(payload.text)
    except APITimeoutError:
        raise HTTPException(status_code=504, detail="Model timed out.")
    except (RateLimitError, APIStatusError) as e:
        raise HTTPException(status_code=502, detail=f"Model provider error: {e}")

    log_cost(PROMPT_VERSION, MODEL_NAME, usage_1, duration_1, repaired=False)

    try:
        parsed_1 = json.loads(extract_json(raw_1))
        return TriageOutput.model_validate(parsed_1)
    except (json.JSONDecodeError, ValidationError) as e:
        first_error = str(e)

    repair_messages = [
        {"role": "assistant", "content": raw_1},
        {"role": "user", "content": (
            f"Your previous answer was rejected for this reason: {first_error}\n"
            "Return only corrected JSON matching the schema. No explanation, no markdown fences."
        )},
    ]
    try:
        raw_2, usage_2, duration_2 = call_model(payload.text, extra_messages=repair_messages)
    except APITimeoutError:
        raise HTTPException(status_code=504, detail="Model timed out during repair.")
    except (RateLimitError, APIStatusError) as e:
        raise HTTPException(status_code=502, detail=f"Model provider error during repair: {e}")

    log_cost(PROMPT_VERSION, MODEL_NAME, usage_2, duration_2, repaired=True)

    try:
        parsed_2 = json.loads(extract_json(raw_2))
        return TriageOutput.model_validate(parsed_2)
    except (json.JSONDecodeError, ValidationError) as e:
        quarantine(payload.text, raw_2, str(e))
        raise HTTPException(
            status_code=422,
            detail="Model could not produce a valid triage response after one repair attempt."
        )