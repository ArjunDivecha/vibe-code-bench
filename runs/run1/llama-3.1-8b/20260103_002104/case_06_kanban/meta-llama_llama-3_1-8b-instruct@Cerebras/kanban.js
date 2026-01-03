const board = document.getElementById('board');
const cards = {
	toDo: [],
	inProgress: [],
	done: []
};

// Get saved cards from localStorage
const savedCards = localStorage.getItem('cards');
if (savedCards) {
	cards = JSON.parse(savedCards);
}

// Render cards
function renderCards() {
	document.getElementById('to-do-cards').innerHTML = '';
	document.getElementById('in-progress-cards').innerHTML = '';
	document.getElementById('done-cards').innerHTML = '';
	cards.toDo.forEach((card, index) => {
		const cardElement = document.createElement('div');
		cardElement.classList.add('card');
		cardElement.draggable = true;
		cardElement.addEventListener('dragstart', (e) => {
			e.dataTransfer.setData('text', index);
		});
		cardElement.addEventListener('dragover', (e) => {
			e.preventDefault();
		});
		cardElement.addEventListener('drop', (e) => {
			const columnIndex = e.target.parentNode.children.length - 1;
			const newColumn = columnIndex === 0 ? 'toDo' : columnIndex === 1 ? 'inProgress' : 'done';
			const oldColumn = e.dataTransfer.getData('text');
			cards[toDoIndex].splice(cards[toDoIndex].indexOf(cards[toDo[oldColumn]]), 1);
			cards[newColumn].push(cards[toDo[oldColumn]]);
			renderCards();
		});
		const cardPriorityElement = document.createElement('span');
		cardPriorityElement.classList.add('card-priority');
		if (card.priority === 'red') {
			cardPriorityElement.classList.add('card-red');
		} else if (card.priority === 'yellow') {
			cardPriorityElement.classList.add('card-yellow');
		} else if (card.priority === 'green') {
			cardPriorityElement.classList.add('card-green');
		}
		cardPriorityElement.textContent = card.priority;
		const cardTitleElement = document.createElement('h2');
		cardTitleElement.classList.add('card-title');
		cardTitleElement.textContent = card.title;
		cardElement.appendChild(cardPriorityElement);
		cardElement.appendChild(cardTitleElement);
		document.getElementById('to-do-cards').appendChild(cardElement);
	});
	cards.inProgress.forEach((card, index) => {
		const cardElement = document.createElement('div');
		cardElement.classList.add('card');
		cardElement.draggable = true;
		cardElement.addEventListener('dragstart', (e) => {
			e.dataTransfer.setData('text', index);
		});
		cardElement.addEventListener('dragover', (e) => {
			e.preventDefault();
		});
		cardElement.addEventListener('drop', (e) => {
			const columnIndex = e.target.parentNode.children.length - 1;
			const newColumn = columnIndex === 0 ? 'toDo' : columnIndex === 1 ? 'inProgress' : 'done';
			const oldColumn = e.dataTransfer.getData('text');
			cards[toDoIndex].splice(cards[toDoIndex].indexOf(cards[toDo[oldColumn]]), 1);
			cards[newColumn].push(cards[toDo[oldColumn]]);
			renderCards();
		});
		const cardPriorityElement = document.createElement('span');
		cardPriorityElement.classList.add('card-priority');
		if (card.priority === 'red') {
			cardPriorityElement.classList.add('card-red');
		} else if (card.priority === 'yellow') {
			cardPriorityElement.classList.add('card-yellow');
		} else if (card.priority === 'green') {
			cardPriorityElement.classList.add('card-green');
		}
		cardPriorityElement.textContent = card.priority;
		const cardTitleElement = document.createElement('h2');
		cardTitleElement.classList.add('card-title');
		cardTitleElement.textContent = card.title;
		cardElement.appendChild(cardPriorityElement);
		cardElement.appendChild(cardTitleElement);
		document.getElementById('in-progress-cards').appendChild(cardElement);
	});
	cards.done.forEach((card, index) => {
		const cardElement = document.createElement('div');
		cardElement.classList.add('card');
		cardElement.draggable = true;
		cardElement.addEventListener('dragstart', (e) => {
			e.dataTransfer.setData('text', index);
		});
		cardElement.addEventListener('dragover', (e) => {
			e.preventDefault();
		});
		cardElement.addEventListener('drop', (e) => {
			const columnIndex = e.target.parentNode.children.length - 1;
			const newColumn = columnIndex === 0 ? 'toDo' : columnIndex === 1 ? 'inProgress' : 'done';
			const oldColumn = e.dataTransfer.getData('text');
			cards[toDoIndex].splice(cards[toDoIndex].indexOf(cards[toDo[oldColumn]]), 1);
			cards[newColumn].push(cards[toDo[oldColumn]]);
			renderCards();
		});
		const cardPriorityElement = document.createElement('span');
		cardPriorityElement.classList.add('card-priority');
		if (card.priority === 'red') {
			cardPriorityElement.classList.add('card-red');
		} else if (card.priority === 'yellow') {
			cardPriorityElement.classList.add('card-yellow');
		} else if (card.priority === 'green') {
			cardPriorityElement.classList.add('card-green');
		}
		cardPriorityElement.textContent = card.priority;
		const cardTitleElement = document.createElement('h2');
		cardTitleElement.classList.add('card-title');
		cardTitleElement.textContent = card.title;
		cardElement.appendChild(cardPriorityElement);
		cardElement.appendChild(cardTitleElement);
		document.getElementById('done-cards').appendChild(cardElement);
	});
}

// Add event listeners
document.getElementById('add-card-button').addEventListener('click', () => {
	const cardTitle = document.getElementById('card-title-input').value;
	const priority = prompt('Enter card priority (red, yellow, green)');
	const newCard = { title: cardTitle, priority: priority };
	if (priority === null) return;
	cards.toDo.push(newCard);
	renderCards();
	document.getElementById('card-title-input').value = '';
	localStorage.setItem('cards', JSON.stringify(cards));
});

// Render cards
renderCards();

// Drag and drop event listeners
document.querySelectorAll('.card').forEach((card) => {
	card.addEventListener('dragover', (e) => {
		e.preventDefault();
	});
});

document.querySelectorAll('.column').forEach((column) => {
	column.addEventListener('dragover', (e) => {
		e.preventDefault();
	});
});

document.querySelectorAll('.card').forEach((card) => {
	card.addEventListener('dragstart', (e) => {
		e.dataTransfer.setData('text', card.dataset.index);
	});
});

document.querySelectorAll('.column').forEach((column) => {
	column.addEventListener('drop', (e) => {
		const columnIndex = e.target.children.length - 1;
		const newColumn = columnIndex === 0 ? 'toDo' : columnIndex === 1 ? 'inProgress' : 'done';
		const oldColumn = e.dataTransfer.getData('text');
		cards[toDoIndex].splice(cards[toDoIndex].indexOf(cards[toDo[oldColumn]]), 1);
		cards[newColumn].push(cards[toDo[oldColumn]]);
		renderCards();
	});
});