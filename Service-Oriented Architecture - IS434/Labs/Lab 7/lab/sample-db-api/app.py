from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app, origins=["http://127.0.0.1:5500"])
DATABASE = "todo.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/api/todos", methods=["GET"])
def get_tasks():
    conn = get_db_connection()
    tasks = conn.execute("SELECT * FROM tasks").fetchall()
    conn.close()
    tasks_list = [{"id": task["id"], "task": task["task"]} for task in tasks]
    return jsonify(tasks_list)


@app.route("/api/todos", methods=["POST"])
def add_task():
    task = request.json.get("task")
    if task:
        conn = get_db_connection()
        conn.execute("INSERT INTO tasks (task) VALUES (?)", (task,))
        conn.commit()
        conn.close()
        return jsonify({"message": "Task added"}), 201
    return jsonify({"error": "No task provided"}), 400


@app.route("/api/todos/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Task deleted"}), 200


if __name__ == "__main__":
    app.run(debug=True)
