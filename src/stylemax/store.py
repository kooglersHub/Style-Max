import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from threading import RLock
from uuid import uuid4

from fastapi import HTTPException


def now():
    return datetime.now(timezone.utc).isoformat()


def owner_key(session):
    return hashlib.sha256(session.encode()).hexdigest()


class Store:
    def __init__(self, directory):
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / "stylemax.sqlite3"
        self.lock = RLock()
        with self.connection() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, owner TEXT NOT NULL, body TEXT NOT NULL)"
            )
            db.execute("CREATE INDEX IF NOT EXISTS project_owner ON projects(owner)")

    @contextmanager
    def connection(self):
        with self.lock, sqlite3.connect(self.path, timeout=15) as connection:
            yield connection

    def create(self, owner, brief):
        project = dict(id=uuid4().hex, created_at=now(), updated_at=now(), **brief)
        project.update(
            photos=[],
            looks=[],
            selected=[],
            sizes=None,
            garments=[],
            offers=[],
            sources=[],
            search_links=[],
            preview=None,
            job=None,
            error=None,
        )
        with self.connection() as db:
            db.execute(
                "INSERT INTO projects VALUES (?, ?, ?)", (project["id"], owner, json.dumps(project))
            )
        return project

    def get(self, project_id, owner=None):
        with self.connection() as db:
            row = db.execute(
                "SELECT owner, body FROM projects WHERE id = ?", (project_id,)
            ).fetchone()
        if not row or (owner is not None and row[0] != owner):
            raise HTTPException(404, "Project not found")
        return json.loads(row[1])

    def update(self, project_id, change):
        with self.connection() as db:
            row = db.execute("SELECT body FROM projects WHERE id = ?", (project_id,)).fetchone()
            if not row:
                return None  # Deleting a project also prevents late jobs from recreating it.
            project = json.loads(row[0])
            change(project)
            project["updated_at"] = now()
            db.execute(
                "UPDATE projects SET body = ? WHERE id = ?", (json.dumps(project), project_id)
            )
            return project

    def list(self, owner):
        with self.connection() as db:
            return [
                json.loads(row[0])
                for row in db.execute(
                    "SELECT body FROM projects WHERE owner = ? ORDER BY rowid DESC", (owner,)
                )
            ]

    def delete(self, project_id, owner):
        self.get(project_id, owner)
        with self.connection() as db:
            db.execute("DELETE FROM projects WHERE id = ? AND owner = ?", (project_id, owner))

    def recover(self):
        with self.connection() as db:
            rows = db.execute("SELECT id, body FROM projects").fetchall()
        for project_id, body in rows:
            project = json.loads(body)
            if project.get("job") and project["job"]["status"] in ("queued", "running"):

                def interrupt(value):
                    value["job"]["status"] = "failed"
                    value["error"] = "The server restarted. Retry to continue this project."
                    for look in value["looks"]:
                        if look["status"] in ("running", "queued"):
                            look["status"] = "failed"

                self.update(project_id, interrupt)
