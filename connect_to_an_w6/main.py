import os
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from enum import Enum
from dotenv import load_dotenv
from openai import OpenAI
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ValidationError

app = FastAPI()

load_dotenv()

PROMPT_VERSION  = "triage-v1"
SYSTEM_PROMPT = Path(f'prompts/{PROMPT_VERSION}.md').read_text()
MODEL_NAME = "meta-llama/llama-3.2-1b-instruct"

Path('logs').mkdir(exist_ok=True)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1/",
    api_key=os.getenv("OPENROUTER_API_KEY")    
)

class TriageInput(BaseModel):
    text : str = Field(..., min_length=1, max_length=2000)

class Category(str, Enum):
    billing = 'billing'
    bug = 'bug'
    feature = "feature"
    account = "account"
    other = "other"
    
class Urgency(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"

class TriageOutput(BaseModel):
    category : Category
    urgency : Urgency
    confidence : float = Field(..., ge=0.0, le=1.0)
    reason : str


def extract_json(raw_text: str) -> str:
    """Strip markdown code fences and grab the {...} object if there's noise around it."""
    text = raw_text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else text


def call_model(user_text: str, extra_messages: list | None = None) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}]
    if extra_messages:
        messages.extend(extra_messages)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=0.2,
        messages=messages,
    )
    return response.choices[0].message.content


def quarantine(input_text: str, raw_output: str, error: str):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt_version": PROMPT_VERSION,
        "input": input_text,
        "raw_output": raw_output,
        "error": error,
    }
    with open("logs/quarantine.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")    
    
@app.post("/triage", response_model=TriageOutput)
def triage(payload : TriageInput):
    if os.getenv("LLM_STUB") == "1":
        return TriageOutput(
            category=Category.other,
            urgency=Urgency.low,
            confidence=0.42,
            reason="Stub reason, no model called."
        )
        
    raw_1 = call_model(payload.text)
    try:
        parsed_1 = json.loads(extract_json(raw_1))
        return TriageOutput.model_validate(parsed_1)
    except (json.JSONDecodeError, ValidationError) as e:
        first_error = str(e)

    # --- Repair attempt (exactly once) ---
    repair_messages = [
        {"role": "assistant", "content": raw_1},
        {"role": "user", "content": (
            f"Your previous answer was rejected for this reason: {first_error}\n"
            "Return only corrected JSON matching the schema. No explanation, no markdown fences."
        )},
    ]
    raw_2 = call_model(payload.text, extra_messages=repair_messages)
    try:
        parsed_2 = json.loads(extract_json(raw_2))
        return TriageOutput.model_validate(parsed_2)
    except (json.JSONDecodeError, ValidationError) as e:
        quarantine(payload.text, raw_2, str(e))
        raise HTTPException(
            status_code=422,
            detail="Model could not produce a valid triage response after one repair attempt."
        )