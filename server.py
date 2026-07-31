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
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks")
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/health")
def health():
    return {'status':'ok'}

@app.post('/tasks', status_code=201, summary='Adding Task')
def add_task(task:Task):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", (task.title, False))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return {"id" : new_id, "title": task.title, "done":False}


@app.get('/tasks/{task_id}', summary="Get One Task Data")
def read_one(task_id:int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks where id = ?", (task_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return dict(row)
    raise HTTPException(status_code=404, detail="Task not found")

@app.put('/tasks/{task_id}', summary="Update Task Data")
def update_task(task_id:int, updated_task:TaskUpdate):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks where id = ?", (task_id,))
    row = cur.fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found.")
    cur.execute("UPDATE tasks SET title = ?, done = ? WHERE id = ?",
                (updated_task.title, updated_task.done, task_id))
    conn.commit()
    conn.close()
    
    return {"id": task_id, "title": updated_task.title, "done": updated_task.done}

@app.delete("/tasks/{task_id}", summary="Delete Task")
def del_task(task_id:int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE id = ?", (task_id, ))
    row = cur.fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Task Not Found")
    
    cur.execute("DELETE FROM tasks WHERE id = ?", (task_id, ))
    conn.commit()
    conn.close()
    
    return Response(status_code=204)