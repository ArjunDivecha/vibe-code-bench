# Debug Session: Fix the Todo App

You've been given a broken Todo application. Your task is to find and fix all the bugs so all tests pass.

## The Broken Code

The following `todo.html` file has **5 bugs** that need to be fixed:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Todo App</title>
    <style>
        body { font-family: Arial; max-width: 500px; margin: 50px auto; }
        .todo-item { display: flex; align-items: center; padding: 10px; border-bottom: 1px solid #eee; }
        .todo-item.completed span { text-decoration: line-through; color: #888; }
        .todo-item button { margin-left: auto; }
        input[type="text"] { width: 100%; padding: 10px; font-size: 16px; }
        .count { color: #666; margin-top: 10px; }
    </style>
</head>
<body>
    <h1>Todo List</h1>
    <input type="text" id="newTodo" placeholder="Add a new todo...">
    <div id="todoList"></div>
    <div class="count">Items: <span id="count">0</span></div>
    
    <script>
        let todos = [];
        
        // BUG 1: Event listener uses wrong event type
        document.getElementById('newTodo').addEventListener('change', function(e) {
            if (e.key === 'Enter' && this.value.trim()) {
                addTodo(this.value.trim());
                this.value = '';
            }
        });
        
        function addTodo(text) {
            // BUG 2: ID generation is not unique
            const todo = { id: todos.length, text: text, completed: false };
            todos.push(todo);
            renderTodos();
            saveTodos();
        }
        
        function toggleTodo(id) {
            const todo = todos.find(t => t.id === id);
            if (todo) {
                // BUG 3: Toggle logic is inverted
                todo.completed = false;
            }
            renderTodos();
            saveTodos();
        }
        
        function deleteTodo(id) {
            // BUG 4: Filter condition is wrong
            todos = todos.filter(t => t.id === id);
            renderTodos();
            saveTodos();
        }
        
        function renderTodos() {
            const list = document.getElementById('todoList');
            list.innerHTML = todos.map(todo => `
                <div class="todo-item ${todo.completed ? 'completed' : ''}">
                    <input type="checkbox" ${todo.completed ? 'checked' : ''} 
                           onclick="toggleTodo(${todo.id})">
                    <span>${todo.text}</span>
                    <button onclick="deleteTodo(${todo.id})">Delete</button>
                </div>
            `).join('');
            
            // BUG 5: Count shows wrong number
            document.getElementById('count').textContent = todos.filter(t => t.completed).length;
        }
        
        function saveTodos() {
            localStorage.setItem('todos', JSON.stringify(todos));
        }
        
        function loadTodos() {
            const saved = localStorage.getItem('todos');
            if (saved) {
                todos = JSON.parse(saved);
                renderTodos();
            }
        }
        
        loadTodos();
    </script>
</body>
</html>
```

## Your Task

1. **Identify all 5 bugs** in the code above
2. **Create a fixed version** of `todo.html` with all bugs corrected
3. **Document the fixes** in a `FIXES.md` file explaining each bug and its solution

## Bug Hints

The 5 bugs are related to:
1. Event handling for adding todos
2. ID generation causing duplicates after delete
3. Toggle completion logic
4. Delete filtering
5. Item count display

## Expected Behavior After Fixes

- Pressing Enter adds a new todo
- Clicking checkbox toggles completed state
- Clicking Delete removes the todo
- Count shows total items (not completed items)
- IDs remain unique even after deleting items

## Deliverables

1. `todo.html` - The fixed version
2. `FIXES.md` - Documentation of each bug and fix

## Evaluation

You'll be scored on:
1. All bugs correctly identified and fixed
2. No new bugs introduced
3. Clear documentation of fixes
4. Clean code formatting
