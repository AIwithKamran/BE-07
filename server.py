import sqlite3
from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException 


DB_FILE = 'tasks.db'

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        done BOOLEAN NOT NULL DEFAULT 0
                     )
                """)
    
    cur.execute("SELECT COUNT(*) FROM tasks")
    count = cur.fetchone()[0]
    if count == 0:
        example_task = {
            ("Buy groceries", 0),
            ("Finish assignment", 0),
            ("Walk the dog", 1),
        }
        
        cur.executemany('INSERT INTO tasks (title, done) VALUES (?, ?)',
                        example_task)
        
    conn.commit()
    conn.close()
        
init_db()



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

@app.get("/tasks", summary="List all tasks")
def read_tasks():
    return tasks

@app.get("/health")
def health():
    return {'status':'ok'}

@app.post('/tasks', status_code=201, summary='Adding Task')
def add_task(task:Task):
    global next_id
    new_task = {'id':next_id, 'title': task.title, 'done':False}
    tasks.append(new_task)
    next_id += 1
    return new_task

@app.get('/tasks/{task_id}', summary="Get One Task Data")
def read_one(task_id:int):
    for t in tasks:
        if t['id'] == task_id:
            return t
    raise HTTPException(status_code=404, detail="Task not found")

@app.put('/tasks/{task_id}', summary="Update Task Data")
def update_task(task_id:int, updated_task:TaskUpdate):
    for t in tasks:
        if t['id'] == task_id:
            t['title'] =  updated_task.title
            t['done'] = updated_task.done
            return t
    raise HTTPException(status_code=404, detail="Task not Found")

@app.delete("/tasks/{task_id}", summary="Delete Task")
def del_task(task_id:int):
    for t in tasks:
        if t['id'] == task_id:
            tasks.remove(t)
            return Response(status_code=204)
    raise HTTPException(status_code=404, detail="Task not found.")