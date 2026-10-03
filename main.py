from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
import sqlite3

# check_same_thread=False: FastAPI runs normal `def` endpoints in worker threads,
# and sqlite3 refuses to share a connection across threads by default.
conn = sqlite3.connect("tasks.db", check_same_thread=False)
conn.row_factory = sqlite3.Row  # rows behave like dicts

conn.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY,
    title TEXT,
    done BOOLEAN
)
""")
conn.commit()

count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
if count == 0:
    seed = ["Learn Encapsulation", "Practice DLD Viva", "Study Ideology Topics"]
    for title in seed:
        conn.execute(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            (title, False)
        )
    conn.commit()


def row_to_dict(row):
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


app = FastAPI(
    title="🚀 Task Manager API",
    version="1.0.0",
    description="""
A simple Task Management API.

## Features

- ✅ Create Tasks
- ✏️ Update Tasks
- ❌ Delete Tasks
- 📋 View Tasks

Built with FastAPI and SQLite.
"""
)


class TaskCreate(BaseModel):
    title: str


class TaskUpdate(BaseModel):
    title: str
    done: bool


@app.get("/", summary="API Information")
def home():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health", summary="Health Check")
def health():
    return {"status": "ok"}


@app.get("/tasks", summary="Get all tasks")
def get_all_tasks():
    rows = conn.execute("SELECT * FROM tasks").fetchall()
    return [row_to_dict(r) for r in rows]


@app.get("/tasks/{task_id}", summary="Get one task")
def get_task(task_id: int):
    row = conn.execute(
        "SELECT * FROM tasks WHERE id = ?", (task_id,)
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    return row_to_dict(row)


@app.post("/tasks", status_code=201, summary="Create new task")
def create_task(task: TaskCreate):
    if task.title.strip() == "":
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    cursor = conn.execute(
        "INSERT INTO tasks (title, done) VALUES (?, ?)",
        (task.title, False)
    )
    conn.commit()

    return {"id": cursor.lastrowid, "title": task.title, "done": False}


@app.put("/tasks/{task_id}", summary="Update task")
def update_task(task_id: int, updated_task: TaskUpdate):
    if updated_task.title.strip() == "":
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    cursor = conn.execute(
        "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
        (updated_task.title, updated_task.done, task_id)
    )
    conn.commit()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    return {"id": task_id, "title": updated_task.title, "done": updated_task.done}


@app.delete("/tasks/{task_id}", status_code=204, summary="Delete task")
def delete_task(task_id: int):
    cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    return Response(status_code=204)