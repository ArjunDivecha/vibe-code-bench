```javascript
// Get elements
const sidebarLinks = document.querySelectorAll('.sidebar-link');
const contentArea = document.getElementById('content-area');
const newProjectModal = document.getElementById('new-project-modal');
const projectNameInput = document.getElementById('project-name');
const createProjectBtn = document.getElementById('create-project-btn');

// Add event listeners to sidebar links
sidebarLinks.forEach(link => {
    link.addEventListener('click', () => {
        // Swap content
        const currentLink = document.querySelector('.sidebar-link.active');
        currentLink.classList.remove('active');
        link.classList.add('active');

        const currentContent = document.querySelector('.content-area.active');
        currentContent.classList.remove('active');
        contentArea.classList.add('active');
    });
});

// Add event listener to new project button
document.querySelector('.new-project-btn').addEventListener('click', () => {
    // Show modal
    newProjectModal.style.display = 'block';
});

// Add event listener to create project button
createProjectBtn.addEventListener('click', () => {
    // Get project name
    const projectName = projectNameInput.value;

    // Create new project
    const newProject = {
        name: projectName,
        tasks: []
    };

    // Add new project to storage
    const storedProjects = localStorage.getItem('projects');
    if (storedProjects) {
        const existingProjects = JSON.parse(storedProjects);
        existingProjects.push(newProject);
        localStorage.setItem('projects', JSON.stringify(existingProjects));
    } else {
        localStorage.setItem('projects', JSON.stringify([newProject]));
    }

    // Hide modal
    newProjectModal.style.display = 'none';
});

// Add event listener to task list checkboxes
document.querySelectorAll('.task-item input[type="checkbox"]').forEach(checkbox => {
    checkbox.addEventListener('change', () => {
        // Update task list
        const taskList = document.querySelector('.task-list');
        const tasks = JSON.parse(localStorage.getItem('tasks')) || [];
        const taskIndex = tasks.indexOf(checkbox.parentNode);
        if (taskIndex >= 0) {
            tasks.splice(taskIndex, 1);
            localStorage.setItem('tasks', JSON.stringify(tasks));
        }
    });
});
```