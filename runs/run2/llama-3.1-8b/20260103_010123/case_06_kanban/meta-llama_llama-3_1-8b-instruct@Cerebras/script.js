const cards = JSON.parse(localStorage.getItem('cards')) || [];
const todoColumn = document.getElementById('to-do-column');
const inProgressColumn = document.getElementById('in-progress-column');
const doneColumn = document.getElementById('done-column');
const toDoColumnCards = document.getElementById('to-do-column-cards');
const inProgressColumnCards = document.getElementById('in-progress-column-cards');
const doneColumnCards = document.getElementById('done-column-cards');
const addCardForm = document.getElementById('add-card-form');
const cardTitleInput = document.getElementById('card-title-input');
const cardPrioritySelect = document.getElementById('card-priority-select');
const addCardButton = document.getElementById('add-card-button');

// Function to render cards
function renderCards() {
    toDoColumnCards.innerHTML = '';
    inProgressColumnCards.innerHTML = '';
    doneColumnCards.innerHTML = '';
    cards.forEach((card, index) => {
        const column = document.getElementById(`${card.column}`);
        const cardElement = document.createElement('div');
        cardElement.classList.add('card');
        cardElement.style.width = '90%';
        cardElement.style.height = '100px';
        cardElement.style.marginBottom = '20px';
        cardElement.style.background = getPriorityColor(card.priority);
        cardElement.innerHTML = `
            <input type="checkbox" id="${card.id}" ${card.completed ? 'checked' : ''}>
            <label for="${card.id}">${card.title}</label>
            <button class="edit-button" onclick="editCard(${index})">Edit</button>
            <button class="delete-button" onclick="deleteCard(${index})">Delete</button>
        `;
        column.appendChild(cardElement);
        cardElement.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('text', index);
        });
    });
}

// Function to get priority color
function getPriorityColor(priority) {
    switch (priority) {
        case 'low':
            return '#00ff00';
        case 'medium':
            return '#ffff00';
        case 'high':
            return '#ff0000';
        default:
            return '#f0f0f0';
    }
}

// Function to add new card
function addCard() {
    const title = cardTitleInput.value.trim();
    const priority = cardPrioritySelect.value;
    if (title) {
        const newCard = {
            id: cards.length,
            title,
            priority,
            column: cardPrioritySelect.value === 'low' ? 'to-do-column' : cardPrioritySelect.value === 'medium' ? 'in-progress-column' : 'done-column',
            completed: false
        };
        cards.push(newCard);
        localStorage.setItem('cards', JSON.stringify(cards));
        renderCards();
        cardTitleInput.value = '';
    }
}

// Function to edit card
function editCard(index) {
    const card = cards[index];
    const editForm = document.createElement('form');
    editForm.innerHTML = `
        <input type="text" value="${card.title}" class="edit-input">
        <select>
            <option value="low" ${card.priority === 'low' ? 'selected' : ''}>Low</option>
            <option value="medium" ${card.priority === 'medium' ? 'selected' : ''}>Medium</option>
            <option value="high" ${card.priority === 'high' ? 'selected' : ''}>High</option>
        </select>
    `;
    cardElement = document.getElementById(`${card.column}`);
    cardElement.innerHTML = '';
    cardElement.appendChild(editForm);
    const saveButton = document.createElement('button');
    saveButton.textContent = 'Save';
    saveButton.onclick = () => {
        card.title = editForm.querySelector('.edit-input').value.trim();
        card.priority = editForm.querySelector('select').value;
        localStorage.setItem('cards', JSON.stringify(cards));
        renderCards();
        cardElement.innerHTML = '';
        cardElement.appendChild(cardElement.querySelector('input'));
        cardElement.appendChild(cardElement.querySelector('label'));
        cardElement.appendChild(cardElement.querySelector('.edit-button'));
        cardElement.appendChild(cardElement.querySelector('.delete-button'));
    };
    cardElement.appendChild(saveButton);
}

// Function to delete card
function deleteCard(index) {
    cards.splice(index, 1);
    localStorage.setItem('cards', JSON.stringify(cards));
    renderCards();
}

// Event listeners
addCardButton.addEventListener('click', addCard);
toDoColumnCards.addEventListener('dragover', (e) => {
    e.preventDefault();
});
toDoColumnCards.addEventListener('drop', (e) => {
    e.preventDefault();
    const index = e.dataTransfer.getData('text');
    const card = cards[index];
    card.column = 'in-progress-column';
    localStorage.setItem('cards', JSON.stringify(cards));
    renderCards();
});
inProgressColumnCards.addEventListener('dragover', (e) => {
    e.preventDefault();
});
inProgressColumnCards.addEventListener('drop', (e) => {
    e.preventDefault();
    const index = e.dataTransfer.getData('text');
    const card = cards[index];
    card.column = 'done-column';
    localStorage.setItem('cards', JSON.stringify(cards));
    renderCards();
});
doneColumnCards.addEventListener('dragover', (e) => {
    e.preventDefault();
});
doneColumnCards.addEventListener('drop', (e) => {
    e.preventDefault();
    const index = e.dataTransfer.getData('text');
    const card = cards[index];
    card.column = 'to-do-column';
    localStorage.setItem('cards', JSON.stringify(cards));
    renderCards();
});

// Initial render
renderCards();