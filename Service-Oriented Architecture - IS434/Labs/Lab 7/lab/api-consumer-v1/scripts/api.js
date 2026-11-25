const API_URL = 'http://localhost:5000/api/todos';

export function fetchTodos() {
    return fetch(API_URL).then(res => res.json());
}

export function addTodo(task) {
    return fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task }),
    });
}

export function deleteTodo(id) {
    return fetch(`${API_URL}/${id}`, {
        method: 'DELETE'
    });
}
