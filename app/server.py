"""Small database-backed application shared by Docker and the AWS tier."""
import logging
import os
from pathlib import Path

import psycopg
from flask import Flask, jsonify, request

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


@app.get("/")
def index():
    return jsonify(service="Broadcast operations API", notes="/api/notes", readiness="/health/ready")


def connection():
    password = Path(os.environ["DB_PASSWORD_FILE"]).read_text().strip()
    return psycopg.connect(host=os.getenv("DB_HOST", "db"),
                          dbname=os.getenv("DB_NAME", "broadcast"),
                          user=os.getenv("DB_USER", "broadcast"),
                          password=password, connect_timeout=3)


@app.errorhandler(psycopg.Error)
def database_failure(error):
    app.logger.warning("database_unavailable type=%s", type(error).__name__)
    return jsonify(error="Database temporarily unavailable"), 503


@app.get("/health/live")
def live():
    return jsonify(status="alive")


@app.get("/health/ready")
def ready():
    with connection() as conn:
        conn.execute("SELECT 1")
    return jsonify(status="ready")


@app.route("/api/notes", methods=["GET", "POST"])
def notes():
    with connection() as conn:
        # Idempotent bootstrap for this assessment; use migrations for production.
        conn.execute("""CREATE TABLE IF NOT EXISTS notes (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            message VARCHAR(500) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now())""")
        if request.method == "POST":
            body = request.get_json(silent=True)
            message = body.get("message") if isinstance(body, dict) else None
            if not isinstance(message, str) or not 1 <= len(message.strip()) <= 500:
                return jsonify(error="message must contain 1 to 500 characters"), 400
            row = conn.execute("INSERT INTO notes(message) VALUES (%s) RETURNING id, message",
                               (message.strip(),)).fetchone()
            return jsonify(id=row[0], message=row[1]), 201
        rows = conn.execute("SELECT id, message, created_at FROM notes ORDER BY id DESC LIMIT 100").fetchall()
        return jsonify([dict(id=r[0], message=r[1], created_at=r[2].isoformat()) for r in rows])
