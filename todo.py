from pathlib import Path
from textual.app import App, ComposeResult
from textual.color import Lab
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Button, ContentSwitcher, Footer, Header, Input, Label, ListItem, ListView, Select, Tab, Tabs
import os, json

filename = "tasks.json"

class Todo():
    def __init__(self, title: str, description: str, deadline, status: str) -> None:
        self.status = status
        self.title = title
        self.desc =description
        self.deadline = deadline
    
    def to_dict(self, task_id: int):
        return {
            "task_id": task_id,
            "status": self.status,
            "title": self.title,
            "description": self.desc,
            "deadline": str(self.deadline)
        }

def save_todo_to_file(filename: str, todo_item: Todo):
    # check for file existence
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        with open(filename, 'r') as file:
            try:
                todo_list = json.load(file)
                if not isinstance(todo_list, list):
                    todo_list = [todo_list]
            except json.JSONDecodeError:
                todo_list = []
    else:
        todo_list = []
    
    if todo_list:
        next_id = max(item.get("task_id", 0) for item in todo_list) + 1
    else:
        next_id = 1
    todo_list.append(todo_item.to_dict(next_id)) 
    with open(filename, 'w') as file:
        json.dump(todo_list, file, indent=4)


class TaskForm(Widget):
    """ TaskForm takes title description deadline and stores them """
    DEFAULT_CSS = """ 
    TaskForm {
        padding: 1 2;
        border: solid $accent;
        margin: 1;
        height: auto;
    }
    Label {
        margin-top: 1;
        text-style: bold;
    }
    Input, Select {
        margin-bottom: 1;
    }
    Button {
        margin-top: 2;
        width: 100%;
    }
    """
    def compose(self) -> ComposeResult:
        yield Label("Task Title:")
        yield Input(placeholder="Enter short title...", id="task-title")

        yield Label("Description:")
        yield Input(placeholder="Enter detailed description...", id="task-description")

        yield Label("Deadline:")
        yield Input(placeholder="YYYY-MM-DD", id="task-deadline")

        yield Label("Status:")
        status_options = [
            ("Not Started", "not_started"),
            ("In Progress", "in_progress"),
            ("Completed", "completed"),
        ]
        yield Select(
            options=status_options,
            value="not_started",
            allow_blank=False,
            id="task-status",
        )

        yield Button("Create Task", id="submit-task-btn", variant="primary")

class ViewPort(Widget):
    """ A Two pane viewPort that has input fields on the right and all todos on the right"""
    DEFAULT_CSS = """
    ViewPort {
    width: 100%;
    height: 1fr;
    padding: 1 2;
}

#left-side {
    width: 65%;
    height: 1fr;
    padding: 0 1;
    border: round $accent;
}

#right-side {
    width: 35%;
    height: 1fr;
    padding: 0 1;
    border: round $accent;
}

#right-side Label {
    width: 100%;
    height: auto;
}

#task-list {
    height: 1fr;
    margin: 0;
    padding: 0;
}

.task-row {
    width: 100%;
    height: 3;
    padding: 0 1;
    align: left middle;
}

.task-header {
    width: 100%;
    height: 2;
    align: center middle;
}

.task-title {
    width: 1fr;
    height: 3;
    content-align: left middle;
    text-style: bold;
}

.task-deadline {
    width: 12;
    height: 3;
    content-align: right middle;
}

#content-display {
    text-style: bold;
    color: $accent;
}

#btn-form {
    width: auto;
    height: 3;
    layout: horizontal;
    align: right middle;
}

#btn-form Button {
    width: 8;
    height: 3;
    min-width: 8;
    margin-left: 1;
}
    """
    
    def compose(self) -> ComposeResult:
        yield Tabs(
            Tab("Tasks View", id="tab-tasks"),
            Tab("Form View", id="tab-form")
        )
        # the better way is to use contentswitcher and wrapping everything
        with ContentSwitcher(initial="tab-tasks", id="context-switcher"):
            # first panel 
            with Horizontal(id="tab-tasks"):
                with Vertical(id="left-side"):
                    yield Label("Tasks List Panel")
                    yield ListView(id="task-list")
                with Vertical(id="right-side"):
                    yield Label("Task Details Panel", id="content-display")
                    yield Vertical(id="task-details")

            # panel 2
            with Vertical(id="tab-form"):
                yield Label("Add Task Form", id="content-display")
                yield TaskForm()
    
    async def on_list_view_selected(self, event: ListView.Selected):
        task = event.item
        right_side = self.query_one("#task-details", Vertical)
        right_side.remove_children()
        right_side.mount(
            Label(f"Title: {task.title}"),
            Label(f"Description: {task.desc}"),
            Label(f"Status: {task.status}"),
            Label(f"Deadline: {task.deadline}")
        )

    # highlight the tab that was active for now 
    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        if event.tab.id:
            self.query_one(ContentSwitcher).current = event.tab.id
    
    # on_mount means start up we get the tasks 
    def on_mount(self) -> None:
        task_list = self.query_one("#task-list", ListView)
        json_path = Path(filename)

        if json_path.exists():
            try:
                with open(json_path, "r") as file:
                    data = json.load(file)
                    if data:
                        for item in data:
                            task_list.append(TaskItem(
                                    title=item.get("title", "Untitled"),
                                    status=item.get("status", "Not Started"),
                                    deadline=item.get("deadline", "No Deadline"),
                                    desc=item.get("description", "No Description"),
                            ))
                    else:
                        empty_item = ListItem(Label("No tass yet. Add one"))
                        task_list.append(empty_item)
                        self.empty_item = empty_item
            except Exception as e:
                task_list.append(ListItem(Label(f"Error loading JSON: {e}.")))
        else:
            empty_item = ListItem(Label(f"No {filename} file found."), id="empty-item")
            task_list.append(empty_item)

class Buttons(Widget):
    DEFAULT_CSS = """
        Buttons {
            width: auto;
            height: 3;
        }
    """
    def compose(self) -> ComposeResult:
        with Horizontal(id="btn-form"):
            yield Button("Edit", id="edit-tasks-btn")
            yield Button("Delete", id="delete-btn", variant="error")
        
    
# Represent a single row of lists 
class TaskItem(ListItem):
    def __init__(self, title: str, status: str, deadline: str, desc: str) -> None:
        super().__init__()
        self.title = title
        self.status = status
        self.deadline = deadline
        self.desc = desc 

    def compose(self) -> ComposeResult:
        status_icon = ""
        if self.status == "completed":
            status_icon = "✅"
        elif self.status == "in_progress":
            status_icon = "⏳"
        elif self.status == "not_started":
            status_icon = "❌"

        with Horizontal(classes="task-row"):
            yield Label(f"{status_icon} [bold]{self.title}[/bold]", classes="task-title")
            yield Label(f"{self.deadline}", classes="task-deadline")
            yield Buttons()


class Tasky(App):
    """ A textual app to manage my todos"""
    
    BINDINGS = [("d", "toggle_dark", "Toggle Dark Mode")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield ViewPort()
        yield Footer()
    
    # lets handle the inputs when the button is pressed 
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit-task-btn":
            title = self.query_one("#task-title", Input).value
            description = self.query_one("#task-description", Input).value
            deadline = self.query_one("#task-deadline", Input).value
            status = self.query_one("#task-status", Select).value
            
            # create a new todo and append it to the file 
            todo = Todo(title, description, deadline, str(status))
            save_todo_to_file(filename, todo)

            # trigger a banner
            self.notify(
                message=f"Task '{title}' saved successfully",
                title="Success",
                severity="information",
                timeout=3.0
            )

            self.query_one('#task-title', Input).value = ""
            self.query_one('#task-description', Input).value = ""
            self.query_one('#task-deadline', Input).value = ""

            # right after submittion move the control to the tabs 
            switcher = self.query_one("#context-switcher", ContentSwitcher)
            task_list = self.query_one("#task-list", ListView)
           
            task_list.append(
                TaskItem(
                    title=todo.title,
                    status=todo.status,
                    desc=todo.desc,
                    deadline=todo.deadline
                )
            )
            
            if self.query("#empty-item"):
                self.query_one("#empty-item").remove()
            switcher.current = "tab-tasks"
            switcher.focus()

    def action_toggle_dark(self) -> None:
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )


if __name__ == "__main__":
    app = Tasky()
    app.run()

