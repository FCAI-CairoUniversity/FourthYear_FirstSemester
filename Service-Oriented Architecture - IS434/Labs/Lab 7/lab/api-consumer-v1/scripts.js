const API_URL = 'http://localhost:5000/api/todos';

// Initial load
fetchTodos();

// Fetch and render TODOs
function fetchTodos() {
    fetch(API_URL)
        .then(res => res.json())
        .then(renderTodos);
}

// Render the list of TODOs
function renderTodos(todos) {
    const list = document.getElementById('todo-list');
    list.innerHTML = '';
    todos.forEach(todo => {
        list.appendChild(createTodoElement(todo));
    });
}

// Create a single TODO list item element
function createTodoElement(todo) {
    const li = document.createElement('li');
    li.textContent = todo.task;

    const deleteBtn = document.createElement('button');
    deleteBtn.textContent = 'Delete';
    deleteBtn.onclick = function () {
        deleteTodo(todo.id);
    };
    li.appendChild(deleteBtn);

    return li;
}

// Send request to delete a TODO
function deleteTodo(id) {
    fetch(`${API_URL}/${id}`, {
        method: 'DELETE'
    })
        .then(fetchTodos);
}

// Handle form submission to add a TODO
document.getElementById('todo-form').onsubmit = handleFormSubmit;

function handleFormSubmit(e) {
    e.preventDefault();
    const task = document.getElementById('todo-task').value;
    addTodo(task);
}

// Send request to add a TODO
function addTodo(task) {
    fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task }),
    })
        .then(() => {
            document.getElementById('todo-task').value = '';
            fetchTodos();
        });
}
