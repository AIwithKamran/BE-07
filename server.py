from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException 

class Task(BaseModel):
    title: str = Field(min_length=1)
    
class TaskUpdate(BaseModel):
    title:str=Field(min_length=1)
    done:bool = False

app = FastAPI()

next_id = 1
tasks = [
    {"id":next_id, 'title' : 'Kamran Khan', 'done' : False}
]

@app.exception_handler(RequestValidationError)
async def validatin_handler(request:Request, exc : RequestValidationError):
    return JSONResponse(status_code=400, content={'error': "Invalid or missing 'title'"})

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

@app.get("/", summary='Server Response')
def server_start():
    return {"name": "Task API", "Version": '1.0', 'endpoints':['/tasks']}

