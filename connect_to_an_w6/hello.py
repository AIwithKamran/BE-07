import os
from dotenv import load_dotenv
from openai import OpenAI
from fastapi import FastAPI
from pydantic import BaseModel
app = FastAPI()

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1/",
    api_key=os.getenv("OPENROUTER_API_KEY")    
)

class DataInput(BaseModel):
    data : str

@app.post("/your-thing")
def hello(payload : DataInput):
    response = client.chat.completions.create(
        model="mistralai/mistral-nemo",
        messages=[
        {
            "role": "user",
            "content": payload.data
        }
        ]
    )

    print(response.choices[0].message.content)