# Flyrank - Internship: Task API

Simple Task API built with FastAPI for creating, reading, updating and deleting tasks.

## Features
- Minimal in-memory Task store
- Endpoints: list tasks, add task, get/update/delete by id, health check

## Requirements
- Python 3.10+ recommended
- See dependency list: [requirmenets.txt](requirmenets.txt)

## Setup
1. Create and activate a virtual environment (Windows PowerShell):

```powershell
python -m venv venv
& venv\Scripts\Activate.ps1
```

2. Install dependencies:

```bash
pip install -r requirmenets.txt
```

## Run
Start the server using Uvicorn (module `server:app`):

```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

The app file is [server.py](server.py). Default API root is `/` and the tasks resource is `/tasks`.

## Endpoints (examples)
- GET / => server metadata
- GET /health => {"status": "ok"}
- GET /tasks => list all tasks
- POST /tasks => add a task
  - Body: {"title": "Task title"}
  - Returns: 201 and the created task
- GET /tasks/{id} => get a task
- PUT /tasks/{id} => update a task
  - Body: {"title": "New title", "done": true}
- DELETE /tasks/{id} => remove a task (204)

Validation: creating/updating tasks requires a non-empty `title`.

## Development notes
- Data is stored in memory in `tasks` inside [server.py](server.py). Restarting the server resets data.
- For production, swap the in-memory store for a persistent database and adjust CORS/security as needed.

## License
This repository does not include a license file. Add one if you plan to publish or share publicly.

## Contact
If you need changes or additional docs, open an issue or contact the project maintainer.
