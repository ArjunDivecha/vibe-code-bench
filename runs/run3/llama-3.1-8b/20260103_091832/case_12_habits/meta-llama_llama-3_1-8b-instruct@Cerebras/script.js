// Get all habit checkboxes and their corresponding streak counters and completion percentages
const checkboxes = document.querySelectorAll('.habit-checkbox');
const streakCounters = document.querySelectorAll('.streak-counter');
const completionPercentages = document.querySelectorAll('.completion-percentage');

// Function to update habit checkboxes, streak counters, and completion percentages
function updateHabits(habits) {
    checkboxes.forEach((checkbox, index) => {
        const habit = habits[index];
        const checkboxId = checkbox.id;
        const habitName = checkbox.dataset.habit;
        const day = checkbox.dataset.day;

        // Update checkbox state
        if (habits[day - 1][habitName]) {
            document.getElementById(`${checkboxId}-checkbox`).checked = true;
        } else {
            document.getElementById(`${checkboxId}-checkbox`).checked = false;
        }

        // Update streak counter
        const streakCounter = document.getElementById(`${day}-streak-counter`);
        const streak = getStreak(habits, habitName, day);
        streakCounter.textContent = `Streak: ${streak}`;

        // Update completion percentage
        const completionPercentage = document.getElementById(`${day}-completion-percentage`);
        const completedDays = getCompletedDays(habits, habitName, day);
        const totalDays = day;
        const percentage = (completedDays / totalDays) * 100;
        completionPercentage.textContent = `Completion: ${Math.round(percentage)}%`;
    });
}

// Function to get streak
function getStreak(habits, habitName, day) {
    let streak = 0;
    for (let i = day - 1; i >= 0; i--) {
        if (habits[i][habitName]) {
            streak++;
        } else {
            break;
        }
    }
    return streak;
}

// Function to get completed days
function getCompletedDays(habits, habitName, day) {
    let completedDays = 0;
    for (let i = day - 1; i >= 0; i--) {
        if (habits[i][habitName]) {
            completedDays++;
        }
    }
    return completedDays;
}

// Add event listener to add habit form
document.getElementById('add-habit-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const habitName = document.getElementById('habit-name').value;
    addHabit(habitName);
});

// Function to add habit
function addHabit(habitName) {
    const habits = JSON.parse(localStorage.getItem('habits')) || {};
    habits[Date.now()] = habits[Date.now()] || {};
    habits[Date.now()][habitName] = false;
    localStorage.setItem('habits', JSON.stringify(habits));
    updateHabits(habits);
}

// Function to save habit completion
function saveHabitCompletion(habitName, day, completed) {
    const habits = JSON.parse(localStorage.getItem('habits')) || {};
    habits[day] = habits[day] || {};
    habits[day][habitName] = completed;
    localStorage.setItem('habits', JSON.stringify(habits));
    updateHabits(habits);
}

// Add event listener to checkboxes
checkboxes.forEach((checkbox, index) => {
    checkbox.addEventListener('change', (e) => {
        if (e.target.checked) {
            const habitName = checkbox.dataset.habit;
            const day = checkbox.dataset.day;
            saveHabitCompletion(habitName, day, true);
        } else {
            const habitName = checkbox.dataset.habit;
            const day = checkbox.dataset.day;
            saveHabitCompletion(habitName, day, false);
        }
    });
});

// Initialize habits on page load
const habits = JSON.parse(localStorage.getItem('habits')) || {};
updateHabits(habits);
</script>