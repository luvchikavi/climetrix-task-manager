import json
import os
from datetime import datetime
from typing import Optional
import uuid
import shutil
import streamlit as st

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "tasks.json")
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "backups")

def get_default_data():
    return {
        "partners": [
            {"name": "Avi", "email": "aviluv@oporto-carbon.com"},
            {"name": "Sivan", "email": "SivanLa@bdo.co.il"},
            {"name": "Lihi", "email": "LihieI@bdo.co.il"}
        ],
        "tasks": [],
        "clients": [],
        "categories": ["Development", "Marketing", "Operations", "Finance", "Legal", "General"]
    }

def load_data():
    # Use session state to cache data during the session
    if "app_data" in st.session_state:
        return st.session_state.app_data

    # Try to load from file
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                st.session_state.app_data = data
                return data
        except (json.JSONDecodeError, FileNotFoundError):
            pass

    # Return default data
    data = get_default_data()
    st.session_state.app_data = data
    return data

def save_data(data):
    # Always update session state
    st.session_state.app_data = data

    # Try to save to file (works locally, may fail on cloud)
    try:
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    except Exception:
        pass  # On read-only filesystem, data stays in session state

def backup_data():
    if not os.path.exists(DATA_FILE):
        return
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"tasks_backup_{timestamp}.json")
    shutil.copy2(DATA_FILE, backup_file)
    # Keep only last 10 backups
    backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith('.json')])
    for old_backup in backups[:-10]:
        os.remove(os.path.join(BACKUP_DIR, old_backup))

def create_task(title: str, description: str = "", assignee: str = "",
                priority: str = "Medium", due_date: Optional[str] = None,
                category: str = "General", links: list = None,
                meeting_summary: str = "", client: str = "") -> dict:
    return {
        "id": str(uuid.uuid4()),
        "title": title,
        "description": description,
        "assignee": assignee,
        "priority": priority,
        "status": "To Do",
        "due_date": due_date,
        "category": category,
        "links": links or [],
        "meeting_summary": meeting_summary,
        "client": client,
        "comments": [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

def add_task(task: dict):
    data = load_data()
    data["tasks"].append(task)
    backup_data()
    save_data(data)
    return task

def update_task(task_id: str, updates: dict):
    data = load_data()
    for i, task in enumerate(data["tasks"]):
        if task["id"] == task_id:
            data["tasks"][i].update(updates)
            data["tasks"][i]["updated_at"] = datetime.now().isoformat()
            break
    backup_data()
    save_data(data)

def delete_task(task_id: str):
    data = load_data()
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    backup_data()
    save_data(data)

def get_task(task_id: str) -> Optional[dict]:
    data = load_data()
    for task in data["tasks"]:
        if task["id"] == task_id:
            return task
    return None

def add_comment(task_id: str, comment: str, author: str):
    data = load_data()
    for task in data["tasks"]:
        if task["id"] == task_id:
            task["comments"].append({
                "id": str(uuid.uuid4()),
                "text": comment,
                "author": author,
                "created_at": datetime.now().isoformat()
            })
            task["updated_at"] = datetime.now().isoformat()
            break
    save_data(data)

def update_partners(partners: list):
    data = load_data()
    data["partners"] = partners
    save_data(data)

def get_partner_names(data):
    """Extract partner names from partner objects"""
    return [p["name"] if isinstance(p, dict) else p for p in data.get("partners", [])]

def get_partner_email(data, name):
    """Get email for a partner by name"""
    for p in data.get("partners", []):
        if isinstance(p, dict) and p.get("name") == name:
            return p.get("email", "")
    return ""

# Client functions
def create_client(name: str, contact_name: str = "", contact_email: str = "",
                  phone: str = "", notes: str = "", status: str = "Lead") -> dict:
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "contact_name": contact_name,
        "contact_email": contact_email,
        "phone": phone,
        "notes": notes,
        "status": status,  # Lead, Contacted, Meeting, Proposal, Negotiation, Won, Lost
        "meetings": [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

def add_client(client: dict):
    data = load_data()
    data["clients"].append(client)
    save_data(data)
    return client

def update_client(client_id: str, updates: dict):
    data = load_data()
    for i, client in enumerate(data["clients"]):
        if client["id"] == client_id:
            data["clients"][i].update(updates)
            data["clients"][i]["updated_at"] = datetime.now().isoformat()
            break
    save_data(data)

def delete_client(client_id: str):
    data = load_data()
    data["clients"] = [c for c in data["clients"] if c["id"] != client_id]
    save_data(data)

def get_client(client_id: str) -> Optional[dict]:
    data = load_data()
    for client in data["clients"]:
        if client["id"] == client_id:
            return client
    return None

def add_meeting_to_client(client_id: str, summary: str, date: str, next_steps: str = ""):
    data = load_data()
    for client in data["clients"]:
        if client["id"] == client_id:
            client["meetings"].append({
                "id": str(uuid.uuid4()),
                "summary": summary,
                "date": date,
                "next_steps": next_steps,
                "created_at": datetime.now().isoformat()
            })
            client["updated_at"] = datetime.now().isoformat()
            break
    save_data(data)

def get_client_names(data):
    """Extract client names"""
    return [c["name"] for c in data.get("clients", [])]
