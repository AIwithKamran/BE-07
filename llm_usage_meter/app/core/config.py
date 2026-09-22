import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL")


plans = {
    "free" : {
        "monthly_tokens" : 100000,
        "api_calls" : 1000,
    },
    "pro" : {
        "monthly_tokens" : 1000000,
        "api_calls" : 10000
    }
}

INPUT_TOKEN_PRICE = 199
CACHED_INPUT_TOKEN_PRICE = 100
OUTPUT_TOKEN_PRICE = 399
REASONING_TOKEN_PRICE = 500