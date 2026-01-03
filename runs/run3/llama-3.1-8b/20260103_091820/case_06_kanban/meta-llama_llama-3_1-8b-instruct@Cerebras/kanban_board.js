// Get elements
const todoColumn = document.getElementById('todo-column');
const inProgressColumn = document.getElementById('in-progress-column');
const doneColumn = document.getElementById('done-column');
const todoColumnContent = document.getElementById('todo-column-content');
const inProgressColumnContent = document.getElementById('in-progress-column-content');
const doneColumnContent = document.getElementById('done-column-content');
const addCardButton = document.querySelector('.todo button');

// Load data from localStorage
const storedData = localStorage.getItem('kanban_board_data');
if (storedData) {
    const data = JSON.parse(storedData);
    data.cards.forEach(card => {
        const cardElement = document.createElement('div');
        cardElement.classList.add('card');
        if (card.priority === 'red') {
            cardElement.classList.add('red');
        } else if (card.priority === 'yellow') {
            cardElement.classList.add('yellow');
        } else if (card.priority === 'green') {
            cardElement.classList.add('green');
        }
        cardElement.textContent = card.title;
        cardElement.draggable = true;
        cardElement.addEventListener('dragstart', startDrag);
        cardElement.addEventListener('drop', dropCard);
        cardElement.addEventListener('click', clickCard);
        document.querySelector(`#${card.column}-column-content`).appendChild(cardElement);
    });
}

// Add event listeners
todoColumn.addEventListener('dragover', allowDrop);
inProgressColumn.addEventListener('dragover', allowDrop);
doneColumn.addEventListener('dragover', allowDrop);
todoColumnContent.addEventListener('dragover', allowDrop);
inProgressColumnContent.addEventListener('dragover', allowDrop);
doneColumnContent.addEventListener('dragover', allowDrop);

// Functions
function addCard(column) {
    const cardElement = document.createElement('div');
    cardElement.classList.add('card');
    cardElement.textContent = 'New Card';
    cardElement.draggable = true;
    cardElement.addEventListener('dragstart', startDrag);
    cardElement.addEventListener('drop', dropCard);
    cardElement.addEventListener('click', clickCard);
    document.querySelector(`#${column}-column-content`).appendChild(cardElement);
    const input = prompt('Enter card title:');
    cardElement.textContent = input;
    cardElement.style.background = getPriorityColor(input);
    const data = {
        card: cardElement.textContent,
        priority: getPriority(input),
        column: column
    };
    const storedData = localStorage.getItem('kanban_board_data');
    if (storedData) {
        const jsonData = JSON.parse(storedData);
        jsonData.cards.push(data);
        localStorage.setItem('kanban_board_data', JSON.stringify(jsonData));
    } else {
        const jsonData = { cards: [data] };
        localStorage.setItem('kanban_board_data', JSON.stringify(jsonData));
    }
}

function clickCard(e) {
    const card = e.target;
    const input = prompt('Enter new title:');
    card.textContent = input;
    card.style.background = getPriorityColor(input);
}

function getPriorityColor(input) {
    if (input.includes('urgent')) {
        return 'red';
    } else if (input.includes('high')) {
        return 'yellow';
    } else {
        return 'green';
    }
}

function getPriority(input) {
    if (input.includes('urgent')) {
        return 'red';
    } else if (input.includes('high')) {
        return 'yellow';
    } else {
        return 'green';
    }
}

function allowDrop(e) {
    e.preventDefault();
}

function startDrag(e) {
    e.dataTransfer.setData('text', e.target.textContent);
    e.dataTransfer.setData('column', e.target.parentNode.id);
}

function dropCard(e) {
    e.preventDefault();
    const card = e.dataTransfer.getData('text');
    const columnId = e.target.parentNode.id;
    const data = {
        card: card,
        priority: getPriority(card),
        column: columnId
    };
    const storedData = localStorage.getItem('kanban_board_data');
    if (storedData) {
        const jsonData = JSON.parse(storedData);
        jsonData.cards.forEach((c, i) => {
            if (c.card === card && c.column === 'todo-column') {
                jsonData.cards.splice(i, 1);
            }
        });
        jsonData.cards.push(data);
        localStorage.setItem('kanban_board_data', JSON.stringify(jsonData));
    } else {
        const jsonData = { cards: [data] };
        localStorage.setItem('kanban_board_data', JSON.stringify(jsonData));
    }
    document.querySelector(`#${columnId}-column-content`).appendChild(e.target);
}

// Add event listener to add card button
addCardButton.addEventListener('click', () => addCard('todo'));