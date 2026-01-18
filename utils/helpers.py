from datetime import datetime, date

def get_priority_color(priority: str) -> str:
    colors = {
        "High": "#D32F2F",
        "Medium": "#FF9800",
        "Low": "#4CAF50"
    }
    return colors.get(priority, "#9E9E9E")

def get_status_color(status: str) -> str:
    colors = {
        "To Do": "#2196F3",
        "In Progress": "#FF9800",
        "Done": "#4CAF50"
    }
    return colors.get(status, "#9E9E9E")

def format_date(date_str: str) -> str:
    if not date_str:
        return "No due date"
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%b %d, %Y")
    except:
        return date_str

def is_overdue(due_date_str: str) -> bool:
    if not due_date_str:
        return False
    try:
        due = datetime.fromisoformat(due_date_str).date()
        return due < date.today()
    except:
        return False

def days_until_due(due_date_str: str) -> int:
    if not due_date_str:
        return 999
    try:
        due = datetime.fromisoformat(due_date_str).date()
        return (due - date.today()).days
    except:
        return 999

def get_due_date_badge(due_date_str: str, status: str) -> tuple:
    """Returns (text, color) for due date badge"""
    if status == "Done":
        return ("Completed", "#4CAF50")
    if not due_date_str:
        return ("No deadline", "#9E9E9E")

    days = days_until_due(due_date_str)
    if days < 0:
        return (f"Overdue by {-days}d", "#D32F2F")
    elif days == 0:
        return ("Due today", "#FF5722")
    elif days <= 3:
        return (f"Due in {days}d", "#FF9800")
    else:
        return (format_date(due_date_str), "#9E9E9E")
