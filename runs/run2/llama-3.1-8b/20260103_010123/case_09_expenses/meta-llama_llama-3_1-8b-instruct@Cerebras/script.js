const expenses = JSON.parse(localStorage.getItem('expenses')) || [];
const categories = ['Food', 'Transport', 'Entertainment', 'Bills', 'Shopping', 'Other'];

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('form');
    const list = document.getElementById('list');
    const stats = document.getElementById('stats');
    const chart = document.getElementById('chart');
    const submitButton = document.getElementById('submit');
    const categorySelect = document.getElementById('category');

    submitButton.addEventListener('click', (e) => {
        e.preventDefault();
        const amount = document.getElementById('amount').value;
        const category = document.getElementById('category').value;
        const description = document.getElementById('description').value;
        const date = document.getElementById('date').value;

        if (amount && category && description && date) {
            const expense = {
                amount,
                category,
                description,
                date
            };

            expenses.push(expense);
            localStorage.setItem('expenses', JSON.stringify(expenses));

            updateList();
            updateStats();
            updateChart();
            categorySelect.value = '';
            document.getElementById('amount').value = '';
            document.getElementById('description').value = '';
            document.getElementById('date').value = '';
        }
    });

    categorySelect.addEventListener('change', () => {
        const selectedCategory = categorySelect.value;
        const filteredExpenses = expenses.filter((expense) => expense.category === selectedCategory);
        list.innerHTML = filteredExpenses.map((expense) => {
            return `<li>Amount: ${expense.amount}, Category: ${expense.category}, Description: ${expense.description}, Date: ${expense.date}</li>`;
        }).join('');
    });

    document.getElementById('date').addEventListener('change', () => {
        const startDate = document.getElementById('date').value;
        const endDate = document.getElementById('date').value;
        const filteredExpenses = expenses.filter((expense) => new Date(expense.date) >= new Date(startDate) && new Date(expense.date) <= new Date(endDate));
        list.innerHTML = filteredExpenses.map((expense) => {
            return `<li>Amount: ${expense.amount}, Category: ${expense.category}, Description: ${expense.description}, Date: ${expense.date}</li>`;
        }).join('');
    });

    function updateList() {
        list.innerHTML = expenses.map((expense) => {
            return `<li>Amount: ${expense.amount}, Category: ${expense.category}, Description: ${expense.description}, Date: ${expense.date}</li>`;
        }).join('');
    }

    function updateStats() {
        const totalSpending = expenses.reduce((acc, expense) => acc + parseFloat(expense.amount), 0);
        document.getElementById('total-spending').textContent = totalSpending;
        const breakdown = expenses.reduce((acc, expense) => {
            if (!acc[expense.category]) {
                acc[expense.category] = 0;
            }
            acc[expense.category] += parseFloat(expense.amount);
            return acc;
        }, {});
        const breakdownList = Object.keys(breakdown).map((category) => {
            return `<li>Category: ${category}, Amount: ${breakdown[category]}</li>`;
        }).join('');
        document.getElementById('category-breakdown').innerHTML = breakdownList;
    }

    function updateChart() {
        const breakdown = expenses.reduce((acc, expense) => {
            if (!acc[expense.category]) {
                acc[expense.category] = 0;
            }
            acc[expense.category] += parseFloat(expense.amount);
            return acc;
        }, {});
        const pieChart = `
            <svg width="100%" height="100%">
                <g transform="translate(50,50)">
                    <rect x="0" y="0" width="100" height="${Math.min(100, 100 * Object.values(breakdown).reduce((acc, val) => acc + val, 0) / Object.values(breakdown).reduce((acc, val) => acc + val, 0) * 0.8)}" fill="blue" />
                </g>
            </svg>
        `;
        chart.innerHTML = pieChart;
    }

    updateList();
    updateStats();
});
</script>