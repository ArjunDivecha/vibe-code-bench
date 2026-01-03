const sidebar = document.querySelector('.sidebar');
const homeView = document.querySelector('.home-view');
const projectsView = document.querySelector('#projects-view');
const settingsView = document.querySelector('#settings-view');
const newProjectModal = document.querySelector('.new-project-modal');
const newProjectForm = document.querySelector('.new-project-modal form');

let activeView = 'home';

sidebar.addEventListener('click', (e) => {
    if (e.target.tagName === 'A') {
        const link = e.target;
        const view = link.getAttribute('href').slice(1);
        if (view === activeView) return;
        activeView = view;
        homeView.style.display = 'none';
        projectsView.style.display = 'none';
        settingsView.style.display = 'none';
        document.querySelector(`#${view}-view`).style.display = 'block';
    }
});

newProjectForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const projectName = newProjectForm.querySelector('input[type="text"]').value;
    const projectDescription = newProjectForm.querySelector('input[type="text"]').nextElementSibling.value;
    console.log(projectName, projectDescription);
    newProjectModal.style.display = 'none';
});

document.querySelector('.new-project-btn').addEventListener('click', () => {
    newProjectModal.style.display = 'block';
});

// Persist tasks in localStorage
const taskList = document.querySelector('.task-list');
const tasks = localStorage.getItem('tasks');
if (tasks) {
    const tasksArray = JSON.parse(tasks);
    tasksArray.forEach((task) => {
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = task.id;
        const label = document.createElement('label');
        label.for = task.id;
        label.textContent = task.name;
        taskList.appendChild(checkbox);
        taskList.appendChild(label);
    });
}

// Add event listener to checkboxes
taskList.addEventListener('change', (e) => {
    if (e.target.tagName === 'INPUT' && e.target.type === 'checkbox') {
        const taskId = e.target.id;
        const taskName = e.target.nextElementSibling.textContent;
        const tasks = localStorage.getItem('tasks');
        if (tasks) {
            const tasksArray = JSON.parse(tasks);
            const task = tasksArray.find((task) => task.id === taskId);
            if (task) {
                task.completed = e.target.checked;
                localStorage.setItem('tasks', JSON.stringify(tasksArray));
            }
        }
    }
});
</script>