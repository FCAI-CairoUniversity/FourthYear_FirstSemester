import { fetchTodos, addTodo, deleteTodo } from './api.js';

document.addEventListener("DOMContentLoaded", initializeUI);

function initializeUI() {
    loadAndRenderTodos();

    document.getElementById('todo-form').onsubmit = function (e) {
        e.preventDefault();
        const task = document.getElementById('todo-task').value;
        addTodo(task)
            .then(() => {
                document.getElementById('todo-task').value = '';
                loadAndRenderTodos();
            });
    };
}

function loadAndRenderTodos() {
    fetchTodos()
        .then(renderTodos);
}

function renderTodos(todos) {
    const list = document.getElementById('todo-list');
    list.innerHTML = '';
    todos.forEach(todo => {
        list.appendChild(createTodoElement(todo));
    });
}

function createTodoElement(todo) {
    const li = document.createElement('li');
    li.textContent = todo.task;

    const deleteBtn = document.createElement('button');
    deleteBtn.textContent = 'Delete';
    deleteBtn.onclick = function () {
        deleteTodo(todo.id)
            .then(loadAndRenderTodos);
    };
    li.appendChild(deleteBtn);

    return li;
}
