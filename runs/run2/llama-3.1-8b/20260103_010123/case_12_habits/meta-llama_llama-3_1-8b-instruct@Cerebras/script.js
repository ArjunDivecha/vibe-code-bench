// Add habit to localStorage
function addHabit() {
    const habit = document.getElementById('habit').value.trim();
    if (habit) {
        const habits = JSON.parse(localStorage.getItem('habits')) || [];
        habits.push({ name: habit, completed: [] });
        localStorage.setItem('habits', JSON.stringify(habits));
        document.getElementById('habit').value = '';
        renderHabits();
    }
}

// Render habits
function renderHabits() {
    const habitsElement = document.getElementById('habits');
    habitsElement.innerHTML = '';
    const habits = JSON.parse(localStorage.getItem('habits')) || [];
    habits.forEach((habit, index) => {
        const habitElement = document.createElement('div');
        habitElement.classList.add('habit');
        habitElement.innerHTML = `
            <input type="checkbox" class="habit-checkbox" data-habit-index="${index}">
            <span class="habit-name">${habit.name}</span>
            <span class="streak">Streak: ${getStreak(habit)}</span>
            <span class="completion">Completion: ${(habit.completed.length / 30) * 100}</span>
        `;
        habitsElement.appendChild(habitElement);
    });
    habits.forEach((habit, index) => {
        const habitElement = document.getElementById(`habit-${index}`);
        if (habitElement) {
            habitElement.addEventListener('click', () => {
                const completed = habit.completed.includes(date.today());
                if (completed) {
                    habit.completed = habit.completed.filter((date) => date !== date.today());
                } else {
                    habit.completed.push(date.today());
                }
                habit.streak = getStreak(habit);
                habit.completion = (habit.completed.length / 30) * 100;
                localStorage.setItem('habits', JSON.stringify(habits));
                renderCalendar();
                renderHabits();
            });
        }
    });
}

// Render calendar
function renderCalendar() {
    const calendarElement = document.getElementById('calendar');
    calendarElement.innerHTML = '';
    for (let day = 0; day < 30; day++) {
        const dayElement = document.createElement('div');
        dayElement.classList.add('day');
        dayElement.innerHTML = day;
        calendarElement.appendChild(dayElement);
    }
    const habits = JSON.parse(localStorage.getItem('habits')) || [];
    habits.forEach((habit, index) => {
        const habitElement = document.getElementById(`habit-${index}`);
        if (habitElement) {
            habitElement.addEventListener('click', () => {
                const completed = habit.completed.includes(date.today());
                if (completed) {
                    habit.completed = habit.completed.filter((date) => date !== date.today());
                } else {
                    habit.completed.push(date.today());
                }
                habit.streak = getStreak(habit);
                habit.completion = (habit.completed.length / 30) * 100;
                localStorage.setItem('habits', JSON.stringify(habits));
                renderCalendar();
                renderHabits();
            });
        }
    });
}

// Function to get streak
function getStreak(habit) {
    const today = date.today();
    const completedDates = habit.completed.filter((date) => date <= today);
    const streak = completedDates.length;
    return streak;
}

// Function to get today's date
function date() {
    const today = new Date();
    const year = today.getFullYear();
    const month = today.getMonth() + 1;
    const day = today.getDate();
    return `${year}-${month}-${day}`;
}

// Render habits and calendar
renderHabits();
renderCalendar();

// Add event listener to add habit button
document.getElementById('add-habit').addEventListener('click', addHabit);
</script>