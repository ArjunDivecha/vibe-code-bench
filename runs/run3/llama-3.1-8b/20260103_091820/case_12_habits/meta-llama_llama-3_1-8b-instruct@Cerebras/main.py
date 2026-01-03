import os
import json

def get_habits():
    habits = os.getenv('HABITS', '{}')
    return json.loads(habits)

def save_habits(habits):
    os.environ['HABITS'] = json.dumps(habits)

def get_dates():
    dates = os.getenv('DATES', '[]')
    return json.loads(dates)

def save_dates(dates):
    os.environ['DATES'] = json.dumps(dates)

def get_streak(completed, habits, index):
    streak = 0
    for i in range(index - 1, -1, -1):
        habit = habits[i]
        checkbox = habit.children[1]
        if not checkbox.checked:
            break
        streak += 1
    return streak

def get_completion_percentage(completed):
    return completed * 100

def update_stats():
    habits_div = document.getElementById('habits')
    habits = habits_div.children
    for i in range(len(habits)):
        habit = habits[i]
        checkbox = habit.children[1]
        completed = checkbox.checked
        streak = get_streak(completed, habits, i)
        completion_percentage = get_completion_percentage(completed)
        habit.children[0].textContent = f"{habit.children[0].textContent} (Streak: {streak}, Completion: {completion_percentage}%)"

def main():
    habits = get_habits()
    dates = get_dates()
    render_habits(habits)
    render_calendar(dates)
    update_stats()

if __name__ == "__main__":
    main()