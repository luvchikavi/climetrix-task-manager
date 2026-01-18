import streamlit as st
from streamlit_option_menu import option_menu
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from utils.data_manager import (
    load_data, save_data, create_task, add_task,
    update_task, delete_task, add_comment, update_partners,
    get_partner_names, get_partner_email,
    create_client, add_client, update_client, delete_client,
    get_client, add_meeting_to_client, get_client_names
)
from utils.helpers import (
    get_priority_color, get_status_color, format_date,
    is_overdue, days_until_due, get_due_date_badge
)

# Page config
st.set_page_config(
    page_title="Climaterix Task Manager",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with Climetrix branding (using Streamlit default fonts)
st.markdown("""
<style>
    .logo-container {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 0.5rem;
    }

    .logo-icon {
        width: 40px;
        height: 40px;
        border-radius: 12px;
        background: linear-gradient(to right, #2563eb, #7c3aed);
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }

    .logo-icon svg {
        width: 24px;
        height: 24px;
        fill: white;
    }

    .logo-text {
        font-size: 1.25rem;
        font-weight: 700;
        color: #1f2937;
        letter-spacing: -0.025em;
    }

    .logo-text-accent {
        color: #2563eb;
    }

    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 0.5rem;
    }

    .sub-header {
        font-size: 1rem;
        color: #6b7280;
        margin-bottom: 2rem;
    }

    .task-card {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.8rem;
        border-left: 4px solid;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .task-title {
        font-weight: 600;
        font-size: 1rem;
        margin-bottom: 0.5rem;
    }

    .task-meta {
        font-size: 0.85rem;
        color: #666;
    }

    .priority-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 500;
        color: white;
    }

    .status-column {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        min-height: 400px;
    }

    .column-header {
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e0e0e0;
    }

    .metric-card {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
    }

    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1e40af;
    }

    .metric-label {
        font-size: 0.9rem;
        color: #2563eb;
        margin-top: 0.5rem;
    }

    .overdue {
        border-left-color: #D32F2F !important;
        background: #FFEBEE !important;
    }

    div[data-testid="stExpander"] {
        background: white;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }

    /* Gradient button style matching climetrix.io */
    .stButton > button[kind="primary"] {
        background: linear-gradient(to right, #2563eb, #7c3aed);
        border: none;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.95);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "edit_task_id" not in st.session_state:
    st.session_state.edit_task_id = None
if "show_new_task" not in st.session_state:
    st.session_state.show_new_task = False
if "new_task_client" not in st.session_state:
    st.session_state.new_task_client = None

def render_task_card(task, show_status=True):
    """Render a task card with all details"""
    priority_color = get_priority_color(task["priority"])
    status_color = get_status_color(task["status"])
    due_text, due_color = get_due_date_badge(task.get("due_date"), task["status"])
    is_task_overdue = is_overdue(task.get("due_date")) and task["status"] != "Done"

    card_class = "task-card overdue" if is_task_overdue else "task-card"

    with st.container():
        st.markdown(f"""
        <div class="{card_class}" style="border-left-color: {priority_color};">
            <div class="task-title">{task['title']}</div>
            <div class="task-meta">
                <span class="priority-badge" style="background: {priority_color};">{task['priority']}</span>
                {'<span class="priority-badge" style="background: ' + status_color + '; margin-left: 5px;">' + task['status'] + '</span>' if show_status else ''}
                <span style="margin-left: 10px; color: {due_color};">{due_text}</span>
            </div>
            <div class="task-meta" style="margin-top: 5px;">
                👤 {task.get('assignee', 'Avi')} | 📁 {task.get('category', 'General')}{' | 🏢 ' + task.get('client') if task.get('client') else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Expandable details
        with st.expander("View Details", expanded=False):
            if task.get("description"):
                st.markdown(f"**Description:** {task['description']}")

            if task.get("meeting_summary"):
                st.markdown(f"**Meeting Summary:** {task['meeting_summary']}")

            if task.get("links"):
                st.markdown("**Links:**")
                for link in task["links"]:
                    st.markdown(f"- [{link}]({link})")

            if task.get("comments"):
                st.markdown("**Comments:**")
                for comment in task["comments"]:
                    st.markdown(f"- {comment['text']} _{comment['author']} - {format_date(comment['created_at'])}_")

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Edit", key=f"edit_{task['id']}", use_container_width=True):
                    st.session_state.edit_task_id = task["id"]
                    st.rerun()
            with col2:
                new_status = st.selectbox(
                    "Status",
                    ["To Do", "In Progress", "Done"],
                    index=["To Do", "In Progress", "Done"].index(task["status"]),
                    key=f"status_{task['id']}",
                    label_visibility="collapsed"
                )
                if new_status != task["status"]:
                    update_task(task["id"], {"status": new_status})
                    st.rerun()
            with col3:
                if st.button("Delete", key=f"delete_{task['id']}", type="secondary", use_container_width=True):
                    delete_task(task["id"])
                    st.rerun()

def render_task_form(task=None, default_client=None):
    """Render form for creating/editing a task"""
    data = load_data()
    partner_names = get_partner_names(data)
    client_names = get_client_names(data)
    is_edit = task is not None

    st.subheader("Edit Task" if is_edit else "New Task")

    with st.form(key="task_form"):
        title = st.text_input("Title*", value=task["title"] if task else "")
        description = st.text_area("Description", value=task.get("description", "") if task else "")

        col1, col2 = st.columns(2)
        with col1:
            assignee = st.selectbox(
                "Assignee",
                partner_names,
                index=partner_names.index(task.get("assignee")) if task and task.get("assignee") in partner_names else 0
            )
            priority = st.selectbox(
                "Priority",
                ["High", "Medium", "Low"],
                index=["High", "Medium", "Low"].index(task.get("priority", "Medium")) if task else 1
            )
        with col2:
            category = st.selectbox(
                "Category",
                data["categories"],
                index=data["categories"].index(task.get("category", "General")) if task else 0
            )
            due_date = st.date_input(
                "Due Date",
                value=datetime.fromisoformat(task["due_date"]).date() if task and task.get("due_date") else None
            )

        # Client selection
        client_options = ["No Client"] + client_names
        default_idx = 0
        if default_client and default_client in client_names:
            default_idx = client_options.index(default_client)
        elif task and task.get("client") in client_names:
            default_idx = client_options.index(task.get("client"))
        client = st.selectbox("Client", client_options, index=default_idx)

        meeting_summary = st.text_area(
            "Meeting Summary",
            value=task.get("meeting_summary", "") if task else "",
            help="Add notes from relevant meetings"
        )

        links_input = st.text_area(
            "Links (one per line)",
            value="\n".join(task.get("links", [])) if task else "",
            help="Add relevant links, documents, or resources"
        )

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Save Task", type="primary", use_container_width=True)
        with col2:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

        if cancelled:
            st.session_state.edit_task_id = None
            st.session_state.show_new_task = False
            st.rerun()

        if submitted:
            if not title:
                st.error("Title is required")
            else:
                links = [l.strip() for l in links_input.split("\n") if l.strip()]
                task_data = {
                    "title": title,
                    "description": description,
                    "assignee": assignee,
                    "priority": priority,
                    "category": category,
                    "due_date": due_date.isoformat() if due_date else None,
                    "meeting_summary": meeting_summary,
                    "links": links,
                    "client": client if client != "No Client" else ""
                }

                if is_edit:
                    update_task(task["id"], task_data)
                    st.session_state.edit_task_id = None
                else:
                    new_task = create_task(**task_data)
                    add_task(new_task)
                    st.session_state.show_new_task = False

                st.success("Task saved!")
                st.rerun()

def render_kanban():
    """Render Kanban board view"""
    data = load_data()
    partner_names = get_partner_names(data)
    client_names = get_client_names(data)
    tasks = data["tasks"]

    # Filters
    with st.expander("Filters", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            filter_assignee = st.multiselect("Assignee", partner_names)
        with col2:
            filter_priority = st.multiselect("Priority", ["High", "Medium", "Low"])
        with col3:
            filter_category = st.multiselect("Category", data["categories"])
        with col4:
            filter_client = st.multiselect("Client", client_names)

    # Apply filters
    if filter_assignee:
        tasks = [t for t in tasks if t.get("assignee") in filter_assignee]
    if filter_priority:
        tasks = [t for t in tasks if t.get("priority") in filter_priority]
    if filter_category:
        tasks = [t for t in tasks if t.get("category") in filter_category]
    if filter_client:
        tasks = [t for t in tasks if t.get("client") in filter_client]

    # Kanban columns
    col1, col2, col3 = st.columns(3)

    statuses = ["To Do", "In Progress", "Done"]
    columns = [col1, col2, col3]
    colors = ["#2196F3", "#FF9800", "#4CAF50"]

    for col, status, color in zip(columns, statuses, colors):
        with col:
            status_tasks = [t for t in tasks if t.get("status") == status]
            st.markdown(f"""
            <div class="status-column">
                <div class="column-header" style="color: {color};">
                    {status} <span style="background: {color}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.8rem;">{len(status_tasks)}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Sort by priority and due date
            status_tasks.sort(key=lambda x: (
                {"High": 0, "Medium": 1, "Low": 2}.get(x.get("priority"), 1),
                days_until_due(x.get("due_date"))
            ))

            for task in status_tasks:
                render_task_card(task, show_status=False)

def render_list_view():
    """Render list view with table"""
    data = load_data()
    partner_names = get_partner_names(data)
    client_names = get_client_names(data)
    tasks = data["tasks"]

    if not tasks:
        st.info("No tasks yet. Create your first task!")
        return

    # Filters
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        filter_status = st.multiselect("Status", ["To Do", "In Progress", "Done"])
    with col2:
        filter_assignee = st.multiselect("Assignee", partner_names, key="list_assignee")
    with col3:
        filter_priority = st.multiselect("Priority", ["High", "Medium", "Low"], key="list_priority")
    with col4:
        filter_client = st.multiselect("Client", client_names, key="list_client")
    with col5:
        sort_by = st.selectbox("Sort by", ["Due Date", "Priority", "Created", "Title", "Client"])

    # Apply filters
    filtered = tasks.copy()
    if filter_status:
        filtered = [t for t in filtered if t.get("status") in filter_status]
    if filter_assignee:
        filtered = [t for t in filtered if t.get("assignee") in filter_assignee]
    if filter_priority:
        filtered = [t for t in filtered if t.get("priority") in filter_priority]
    if filter_client:
        filtered = [t for t in filtered if t.get("client") in filter_client]

    # Sort
    if sort_by == "Due Date":
        filtered.sort(key=lambda x: days_until_due(x.get("due_date")))
    elif sort_by == "Priority":
        filtered.sort(key=lambda x: {"High": 0, "Medium": 1, "Low": 2}.get(x.get("priority"), 1))
    elif sort_by == "Created":
        filtered.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    elif sort_by == "Client":
        filtered.sort(key=lambda x: x.get("client", "").lower())
    else:
        filtered.sort(key=lambda x: x.get("title", "").lower())

    st.markdown(f"**Showing {len(filtered)} of {len(tasks)} tasks**")

    for task in filtered:
        render_task_card(task)

def render_dashboard():
    """Render dashboard overview with metrics"""
    data = load_data()
    tasks = data["tasks"]

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    total = len(tasks)
    todo = len([t for t in tasks if t.get("status") == "To Do"])
    in_progress = len([t for t in tasks if t.get("status") == "In Progress"])
    done = len([t for t in tasks if t.get("status") == "Done"])
    overdue = len([t for t in tasks if is_overdue(t.get("due_date")) and t.get("status") != "Done"])

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total}</div>
            <div class="metric-label">Total Tasks</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);">
            <div class="metric-value" style="color: #1565C0;">{todo}</div>
            <div class="metric-label" style="color: #1976D2;">To Do</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);">
            <div class="metric-value" style="color: #E65100;">{in_progress}</div>
            <div class="metric-label" style="color: #F57C00;">In Progress</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);">
            <div class="metric-value" style="color: #065f46;">{done}</div>
            <div class="metric-label" style="color: #059669;">Completed</div>
        </div>
        """, unsafe_allow_html=True)

    if overdue > 0:
        st.warning(f"⚠️ You have {overdue} overdue task(s)!")

    st.markdown("---")

    # Charts
    if tasks:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Tasks by Status")
            status_counts = {"To Do": todo, "In Progress": in_progress, "Done": done}
            fig = px.pie(
                values=list(status_counts.values()),
                names=list(status_counts.keys()),
                color_discrete_sequence=["#2196F3", "#FF9800", "#4CAF50"]
            )
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Tasks by Assignee")
            assignee_counts = {}
            for task in tasks:
                assignee = task.get("assignee") or "Unassigned"
                assignee_counts[assignee] = assignee_counts.get(assignee, 0) + 1

            fig = px.bar(
                x=list(assignee_counts.keys()),
                y=list(assignee_counts.values()),
                color_discrete_sequence=["#2563eb"]
            )
            fig.update_layout(
                xaxis_title="Partner",
                yaxis_title="Tasks",
                margin=dict(t=0, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)

        # Upcoming tasks
        st.subheader("Upcoming Deadlines")
        upcoming = [t for t in tasks if t.get("due_date") and t.get("status") != "Done"]
        upcoming.sort(key=lambda x: x.get("due_date"))

        if upcoming[:5]:
            for task in upcoming[:5]:
                due_text, due_color = get_due_date_badge(task.get("due_date"), task["status"])
                st.markdown(f"- **{task['title']}** - {due_text} ({'👤 ' + task.get('assignee', 'Unassigned')})")
        else:
            st.info("No upcoming deadlines")

def render_clients():
    """Render potential clients page"""
    data = load_data()
    clients = data.get("clients", [])
    tasks = data["tasks"]

    # Add new client section
    with st.expander("➕ Add New Client", expanded=False):
        with st.form("new_client_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input("Company Name*")
                new_contact = st.text_input("Contact Person")
            with col2:
                new_email = st.text_input("Email")
                new_phone = st.text_input("Phone")
            new_notes = st.text_area("Notes")
            new_status = st.selectbox("Status", ["Lead", "Contacted", "Meeting", "Proposal", "Negotiation", "Won", "Lost"])

            if st.form_submit_button("Add Client", type="primary"):
                if new_name:
                    client = create_client(
                        name=new_name,
                        contact_name=new_contact,
                        contact_email=new_email,
                        phone=new_phone,
                        notes=new_notes,
                        status=new_status
                    )
                    add_client(client)
                    st.success(f"Added {new_name}!")
                    st.rerun()
                else:
                    st.error("Company name is required")

    # Filter by status
    status_filter = st.multiselect(
        "Filter by Status",
        ["Lead", "Contacted", "Meeting", "Proposal", "Negotiation", "Won", "Lost"],
        default=["Lead", "Contacted", "Meeting", "Proposal", "Negotiation"]
    )

    filtered_clients = [c for c in clients if c.get("status") in status_filter]

    if not filtered_clients:
        st.info("No clients yet. Add your first potential client above!")
        return

    st.markdown(f"**Showing {len(filtered_clients)} clients**")

    # Display clients
    for client in filtered_clients:
        client_tasks = [t for t in tasks if t.get("client") == client["name"]]
        pending_tasks = len([t for t in client_tasks if t.get("status") != "Done"])

        status_colors = {
            "Lead": "#9E9E9E",
            "Contacted": "#2196F3",
            "Meeting": "#FF9800",
            "Proposal": "#9C27B0",
            "Negotiation": "#FF5722",
            "Won": "#4CAF50",
            "Lost": "#F44336"
        }
        status_color = status_colors.get(client.get("status"), "#9E9E9E")

        st.markdown(f"""
        <div style="background: white; border-radius: 10px; padding: 1rem; margin-bottom: 1rem; border-left: 4px solid {status_color}; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong style="font-size: 1.1rem;">{client['name']}</strong>
                    <span style="background: {status_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; margin-left: 10px;">{client.get('status', 'Lead')}</span>
                </div>
                <div style="color: #666; font-size: 0.85rem;">
                    📋 {len(client_tasks)} tasks ({pending_tasks} pending)
                </div>
            </div>
            <div style="color: #666; font-size: 0.85rem; margin-top: 5px;">
                👤 {client.get('contact_name', 'N/A')} | 📧 {client.get('contact_email', 'N/A')} | 📞 {client.get('phone', 'N/A')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander(f"Manage {client['name']}", expanded=False):
            tab1, tab2, tab3 = st.tabs(["Tasks", "Meetings", "Details"])

            with tab1:
                # Show client tasks
                if client_tasks:
                    for task in client_tasks:
                        render_task_card(task)
                else:
                    st.info("No tasks for this client yet")

                # Quick add task button
                if st.button(f"➕ Add Task for {client['name']}", key=f"add_task_{client['id']}"):
                    st.session_state.show_new_task = True
                    st.session_state.new_task_client = client["name"]
                    st.rerun()

            with tab2:
                # Meeting history
                meetings = client.get("meetings", [])
                if meetings:
                    for meeting in sorted(meetings, key=lambda x: x.get("date", ""), reverse=True):
                        st.markdown(f"""
                        <div style="background: #f5f5f5; padding: 0.8rem; border-radius: 8px; margin-bottom: 0.5rem;">
                            <strong>{format_date(meeting.get('date', ''))}</strong><br>
                            <span style="color: #333;">{meeting.get('summary', '')}</span>
                            {f"<br><em style='color: #666;'>Next steps: {meeting.get('next_steps', '')}</em>" if meeting.get('next_steps') else ''}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No meetings recorded yet")

                # Add meeting form
                st.markdown("**Add Meeting**")
                with st.form(f"meeting_form_{client['id']}"):
                    meeting_date = st.date_input("Date", value=date.today())
                    meeting_summary = st.text_area("Summary")
                    meeting_next = st.text_area("Next Steps")

                    if st.form_submit_button("Save Meeting"):
                        if meeting_summary:
                            add_meeting_to_client(client["id"], meeting_summary, meeting_date.isoformat(), meeting_next)
                            st.success("Meeting saved!")
                            st.rerun()

            with tab3:
                # Edit client details
                with st.form(f"edit_client_{client['id']}"):
                    edit_name = st.text_input("Company Name", value=client.get("name", ""))
                    col1, col2 = st.columns(2)
                    with col1:
                        edit_contact = st.text_input("Contact Person", value=client.get("contact_name", ""))
                        edit_email = st.text_input("Email", value=client.get("contact_email", ""))
                    with col2:
                        edit_phone = st.text_input("Phone", value=client.get("phone", ""))
                        edit_status = st.selectbox(
                            "Status",
                            ["Lead", "Contacted", "Meeting", "Proposal", "Negotiation", "Won", "Lost"],
                            index=["Lead", "Contacted", "Meeting", "Proposal", "Negotiation", "Won", "Lost"].index(client.get("status", "Lead"))
                        )
                    edit_notes = st.text_area("Notes", value=client.get("notes", ""))

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("Save Changes", type="primary"):
                            update_client(client["id"], {
                                "name": edit_name,
                                "contact_name": edit_contact,
                                "contact_email": edit_email,
                                "phone": edit_phone,
                                "status": edit_status,
                                "notes": edit_notes
                            })
                            st.success("Client updated!")
                            st.rerun()
                    with col2:
                        if st.form_submit_button("Delete Client", type="secondary"):
                            delete_client(client["id"])
                            st.rerun()

def render_settings():
    """Render settings page"""
    data = load_data()

    st.subheader("Team Members")

    # Display current team
    for partner in data["partners"]:
        if isinstance(partner, dict):
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem; border-left: 4px solid #2563eb;">
                <strong>{partner['name']}</strong><br>
                <span style="color: #666;">{partner.get('email', '')}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    st.subheader("Add Team Member")
    with st.form("add_partner_form"):
        new_name = st.text_input("Name")
        new_email = st.text_input("Email")

        if st.form_submit_button("Add Member", type="primary"):
            if new_name:
                data["partners"].append({"name": new_name, "email": new_email})
                save_data(data)
                st.success(f"Added {new_name}!")
                st.rerun()

    st.markdown("---")
    st.subheader("Data Export")

    if st.button("Export Tasks to CSV"):
        if data["tasks"]:
            df = pd.DataFrame(data["tasks"])
            csv = df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                "climaterix_tasks.csv",
                "text/csv"
            )
        else:
            st.info("No tasks to export")

# Main app
def main():
    # Sidebar
    with st.sidebar:
        # Climetrix Logo matching climetrix.io design
        st.markdown('''
        <div class="logo-container">
            <div class="logo-icon">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z" fill="white" stroke="white"/>
                    <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12" stroke="white" fill="none"/>
                </svg>
            </div>
            <span class="logo-text">CLIME<span class="logo-text-accent">TRIX</span></span>
        </div>
        ''', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Task Manager</p>', unsafe_allow_html=True)

        selected = option_menu(
            menu_title=None,
            options=["Dashboard", "Kanban Board", "Task List", "Clients", "Settings"],
            icons=["speedometer2", "kanban", "list-task", "building", "gear"],
            default_index=0,
            styles={
                "container": {"padding": "0!important"},
                "icon": {"color": "#2563eb", "font-size": "1rem"},
                "nav-link": {
                    "font-size": "0.9rem",
                    "text-align": "left",
                    "margin": "0px",
                    "padding": "10px 15px",
                },
                "nav-link-selected": {"background-color": "#eff6ff", "color": "#1e40af"},
            }
        )

        st.markdown("---")

        if st.button("➕ New Task", type="primary", use_container_width=True):
            st.session_state.show_new_task = True
            st.session_state.edit_task_id = None

    # Main content
    if st.session_state.show_new_task:
        render_task_form(default_client=st.session_state.new_task_client)
        st.session_state.new_task_client = None
    elif st.session_state.edit_task_id:
        task = None
        data = load_data()
        for t in data["tasks"]:
            if t["id"] == st.session_state.edit_task_id:
                task = t
                break
        if task:
            render_task_form(task)
        else:
            st.session_state.edit_task_id = None
            st.rerun()
    elif selected == "Dashboard":
        st.markdown('<p class="main-header">Dashboard</p>', unsafe_allow_html=True)
        render_dashboard()
    elif selected == "Kanban Board":
        st.markdown('<p class="main-header">Kanban Board</p>', unsafe_allow_html=True)
        render_kanban()
    elif selected == "Task List":
        st.markdown('<p class="main-header">Task List</p>', unsafe_allow_html=True)
        render_list_view()
    elif selected == "Clients":
        st.markdown('<p class="main-header">Potential Clients</p>', unsafe_allow_html=True)
        render_clients()
    elif selected == "Settings":
        st.markdown('<p class="main-header">Settings</p>', unsafe_allow_html=True)
        render_settings()

if __name__ == "__main__":
    main()
