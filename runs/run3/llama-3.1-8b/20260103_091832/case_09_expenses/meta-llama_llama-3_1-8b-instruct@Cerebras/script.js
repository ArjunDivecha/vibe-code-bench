const expenses = JSON.parse(localStorage.getItem('expenses')) || [];

const categoryFilter = document.getElementById('category-filter');
const startDateInput = document.getElementById('start-date');
const endDateInput = document.getElementById('end-date');
const applyFilterButton = document.getElementById('apply-filter');
const expenseList = document.getElementById('expense-ul');

categoryFilter.addEventListener('change', filterByCategory);
applyFilterButton.addEventListener('click', filterByDateRange);

function filterByCategory() {
    const selectedCategory = categoryFilter.value;
    const filteredExpenses = expenses.filter(expense => expense.category === selectedCategory);
    renderExpenses(filteredExpenses);
}

function filterByDateRange() {
    const startDate = new Date(startDateInput.value);
    const endDate = new Date(endDateInput.value);
    const filteredExpenses = expenses.filter(expense => {
        const expenseDate = new Date(expense.date);
        return expenseDate >= startDate && expenseDate <= endDate;
    });
    renderExpenses(filteredExpenses);
}

function renderExpenses(expenses) {
    expenseList.innerHTML = '';
    expenses.forEach(expense => {
        const li = document.createElement('li');
        li.textContent = `${expense.date}: ${expense.description} - ${expense.category} ($${expense.amount})`;
        expenseList.appendChild(li);
    });
}

document.getElementById('expense-form').addEventListener('submit', addExpense);
function addExpense(e) {
    e.preventDefault();
    const amount = document.getElementById('amount').value;
    const category = document.getElementById('category').value;
    const description = document.getElementById('description').value;
    const date = document.getElementById('date').value;
    const newExpense = {
        amount: parseFloat(amount),
        category,
        description,
        date,
    };
    expenses.push(newExpense);
    localStorage.setItem('expenses', JSON.stringify(expenses));
    renderExpenses(expenses);
    document.getElementById('amount').value = '';
    document.getElementById('category').value = '';
    document.getElementById('description').value = '';
    document.getElementById('date').value = '';
}

function getTotalSpending() {
    return expenses.reduce((acc, expense) => acc + expense.amount, 0);
}

const totalSpending = document.getElementById('total-spending');
const chart = document.getElementById('chart');

totalSpending.textContent = `Total Spending: $${getTotalSpending()}`;

const categories = expenses.reduce((acc, expense) => {
    acc[expense.category] = (acc[expense.category] || 0) + expense.amount;
    return acc;
}, {});

const pieChartData = Object.keys(categories).map(category => ({
    label: category,
    value: categories[category],
}));

const ctx = document.createElement('canvas').getContext('2d');
ctx.canvas.width = 400;
ctx.canvas.height = 400;
chart.appendChild(ctx.canvas);

const pieChart = new Chart(ctx, {
    type: 'pie',
    data: {
        labels: pieChartData.map(data => data.label),
        datasets: [{
            data: pieChartData.map(data => data.value),
            backgroundColor: pieChartData.map(data => `#${Math.floor(Math.random() * 16777215).toString(16).padStart(6, '0')}`),
        }],
    },
    options: {
        title: {
            display: true,
            text: 'Breakdown by Category',
        },
    },
});
</script>