import flet as ft
import webbrowser
import threading
import time
import random
import math

# --- Distraction & Categories ---
DISTRACTION_LIST = ["youtube", "tiktok", "netflix", "discord"]
CATEGORY_KEYWORDS = {
    "Productivity": ["google", "docs.google", "wikipedia", "notion"],
    "Entertainment": ["youtube", "tiktok", "netflix"],
    "Social Media": ["discord", "twitter", "facebook"]
}

# --- Modern Palette ---
BG_COLOR = ft.Colors.GREY_50
CARD_BG_COLOR = ft.Colors.WHITE
TEXT_COLOR = ft.Colors.BLACK87
SUBTEXT_COLOR = ft.Colors.BLACK54
BUTTON_PRIMARY = ft.Colors.INDIGO_300
BUTTON_SECONDARY = ft.Colors.GREEN_300
BUTTON_DANGER = ft.Colors.RED_300
NOTE_COLORS = {
    "general": ft.Colors.GREY_100,
    "work": ft.Colors.INDIGO_100,
    "study": ft.Colors.GREEN_100,
    "personal": ft.Colors.PINK_100,
    "entertainment": ft.Colors.ORANGE_100
}

# --- AI Tip Generator ---
def local_ai_tip(tasks):
    if not tasks:
        return "💡 Add a few tasks to get started!"
    top_task = sorted(tasks, key=lambda x: x["priority"], reverse=True)[0]
    tips = [
        f"Focus on '{top_task['title']}' first — it’s your most important task!",
        f"Break '{top_task['title']}' into smaller steps to reduce pressure.",
        "Take a 5-minute break — then jump back into focus.",
        "Stay consistent and reward your progress!",
        f"Try completing '{top_task['title']}' in the next 25 minutes!"
    ]
    return "💡 " + random.choice(tips)

# --- Helpers ---
def get_category(url):
    url_lower = url.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for k in keywords:
            if k in url_lower:
                return cat
    return "Other"

def is_distracted(url):
    url_lower = url.lower()
    return any(d in url_lower for d in DISTRACTION_LIST)

def summarize_note(note_text):
    words = note_text.split()
    if len(words) <= 20:
        return note_text
    return " ".join(words[:20]) + "..."

def summarize_all_notes(notes):
    if not notes:
        return "💡 No notes yet."
    summary_by_tag = {}
    for note in notes:
        for tag in note["tags"]:
            summary_by_tag.setdefault(tag, []).append(note["summary"])
    return "\n".join([f"#{tag}: {' | '.join(sums)}" for tag, sums in summary_by_tag.items()])

def get_tag_color(note):
    if note["tags"]:
        return NOTE_COLORS.get(note["tags"][0].lower(), NOTE_COLORS["general"])
    return NOTE_COLORS["general"]

# --- Main App ---
def main(page: ft.Page):
    page.title = "🧠 FocusFlow - Modern Productivity App"
    page.padding = 20
    page.bgcolor = BG_COLOR
    page.font_family = "Arial"

    # --- State ---
    tasks = []
    focus_running = False
    focus_seconds = 0
    focus_history = []
    current_focus_url = None
    focus_start_time = None
    notes = []
    calc_expression = ""

    # --- UI Components ---
    task_input = ft.TextField(label="New Task", width=300, filled=True, bgcolor=ft.Colors.WHITE)
    priority_dropdown = ft.Dropdown(
        label="Priority",
        options=[ft.dropdown.Option(str(i)) for i in range(1, 6)],
        value="3",
        width=120,
        filled=True,
        bgcolor=ft.Colors.WHITE
    )
    task_list = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=8, height=200)
    focus_label = ft.Text("Focus Timer: 00:00", size=20, weight=ft.FontWeight.BOLD, color=TEXT_COLOR)
    ai_tip_text = ft.Text("💡 AI Tip: Add a few tasks to begin!", size=16, italic=True, color=SUBTEXT_COLOR)

    history_list = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=6, height=200)
    history_summary_text = ft.Text("Focus Summary will appear here.", size=16, italic=True, color=SUBTEXT_COLOR)

    note_input = ft.TextField(label="New Note", multiline=True, width=400, height=100, filled=True, bgcolor=ft.Colors.WHITE)
    tag_input = ft.TextField(label="Tags (comma-separated)", width=400, filled=True, bgcolor=ft.Colors.WHITE)
    note_list = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=8, height=200)
    global_summary_text = ft.Text("Global AI Summary of notes will appear here.", size=16, italic=True, color=SUBTEXT_COLOR)

    calc_output = ft.Text(value="", size=24, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT, color=TEXT_COLOR)

    # --- Priority Color ---
    def get_priority_color(priority):
        colors_map = {1: ft.Colors.AMBER_100, 2: ft.Colors.AMBER_200, 3: ft.Colors.AMBER_300,
                      4: ft.Colors.AMBER_400, 5: ft.Colors.AMBER_600}
        return colors_map.get(priority, ft.Colors.AMBER_200)

    # --- Task Functions ---
    def add_task(e):
        if task_input.value:
            tasks.append({"title": task_input.value, "priority": int(priority_dropdown.value)})
            task_input.value = ""
            refresh_task_list()
            ai_tip_text.value = local_ai_tip(tasks)
            page.update()

    def remove_task(task):
        if task in tasks:
            tasks.remove(task)
        refresh_task_list()
        ai_tip_text.value = local_ai_tip(tasks)
        page.update()

    def refresh_task_list():
        task_list.controls.clear()
        for t in tasks:
            row = ft.Row([
                ft.Checkbox(value=False, on_change=lambda e, t=t: remove_task(t)),
                ft.Text(t["title"], size=16, color=TEXT_COLOR),
                ft.Container(
                    ft.Text(f"Priority {t['priority']}"),
                    padding=5,
                    bgcolor=get_priority_color(t["priority"]),
                    border_radius=0
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            task_list.controls.append(row)
        page.update()

    # --- Focus Timer ---
    def start_focus_timer(e):
        nonlocal focus_running
        if not focus_running:
            focus_running = True
            start_button.text = "⏸ Pause"
            threading.Thread(target=run_focus_timer, daemon=True).start()
        else:
            focus_running = False
            start_button.text = "▶️ Start Focus"
        page.update()

    def run_focus_timer():
        nonlocal focus_seconds, focus_running
        while focus_running:
            time.sleep(1)
            focus_seconds += 1
            mins, secs = divmod(focus_seconds, 60)
            focus_label.value = f"Focus Timer: {mins:02d}:{secs:02d}"
            if focus_seconds % 60 == 0:
                ai_tip_text.value = local_ai_tip(tasks)
            page.update()

    def reset_focus_timer(e):
        nonlocal focus_seconds, focus_running
        focus_running = False
        focus_seconds = 0
        focus_label.value = "Focus Timer: 00:00"
        start_button.text = "▶️ Start Focus"
        page.update()

    # --- Focus Mode ---
    def open_focus_browser(e):
        nonlocal current_focus_url, focus_start_time
        url = focus_url_input.value or "https://www.google.com"
        current_focus_url = url
        focus_start_time = time.time()
        webbrowser.open(url)
        threading.Thread(target=monitor_focus_browser, args=(url,), daemon=True).start()

    def monitor_focus_browser(url):
        nonlocal current_focus_url, focus_start_time
        while focus_running and current_focus_url == url:
            time.sleep(2)
            if is_distracted(url):
                ai_tip_text.value = f"⚠️ Distracted on {url}! Get back to work."
        if focus_start_time:
            elapsed = int(time.time() - focus_start_time)
            focus_history.append({"url": url, "time_spent": elapsed})
            focus_start_time = None
            update_history_summary()

    # --- Focus History ---
    def update_history_summary():
        history_list.controls.clear()
        for entry in focus_history:
            history_list.controls.append(ft.Text(f"{entry['url']} - {entry['time_spent']}s", color=TEXT_COLOR))

        category_times = {}
        for entry in focus_history:
            cat = get_category(entry["url"])
            category_times[cat] = category_times.get(cat, 0) + entry["time_spent"]
        if category_times:
            max_cat = max(category_times, key=category_times.get)
            total_time = sum(category_times.values())
            history_summary_text.value = f"💡 Most of your focus time was spent on {max_cat} ({category_times[max_cat]}s). Total focus time: {total_time}s."
        else:
            history_summary_text.value = "💡 No focus history yet."
        page.update()

    # --- Notes Functions ---
    def add_note(e):
        if note_input.value.strip():
            tags = [t.strip() for t in tag_input.value.split(",") if t.strip()]
            note = {"text": note_input.value.strip(),
                    "summary": summarize_note(note_input.value.strip()),
                    "tags": tags or ["general"]}
            notes.append(note)
            note_input.value = ""
            tag_input.value = ""
            refresh_notes()
            page.update()

    def remove_note(note):
        if note in notes:
            notes.remove(note)
        refresh_notes()
        page.update()

    def refresh_notes():
        note_list.controls.clear()
        for note in notes:
            note_card = ft.Card(
                content=ft.Column([
                    ft.Text(note["text"], size=16, weight=ft.FontWeight.W_500, color=TEXT_COLOR),
                    ft.Text(f"Summary: {note['summary']}", size=14, italic=True, color=SUBTEXT_COLOR),
                    ft.Text(f"Tags: {', '.join(note['tags'])}", size=14, italic=True, color=ft.Colors.INDIGO_400),
                    ft.Row(
                        [ft.ElevatedButton("Delete", on_click=lambda e, n=note: remove_note(n), bgcolor=BUTTON_DANGER)],
                        alignment=ft.MainAxisAlignment.END
                    )
                ], spacing=8),
                elevation=5,
                bgcolor=get_tag_color(note)
            )
            note_list.controls.append(note_card)
        global_summary_text.value = summarize_all_notes(notes)
        page.update()

    # --- Calculator Functions ---
    def calc_button_click(e, value):
        nonlocal calc_expression
        try:
            if value == "C":
                calc_expression = ""
            elif value == "=":
                safe_dict = {"sin": math.sin, "cos": math.cos, "tan": math.tan,
                             "pi": math.pi, "e": math.e}
                calc_expression = str(eval(calc_expression, {"__builtins__": None}, safe_dict))
            else:
                calc_expression += str(value)
        except:
            calc_expression = "Error"
        calc_output.value = calc_expression
        page.update()

    def create_calc_buttons():
        buttons = []
        layout = [
            ["7", "8", "9", "/"],
            ["4", "5", "6", "*"],
            ["1", "2", "3", "-"],
            ["0", ".", "=", "+"],
            ["C", "sin(", "cos(", "tan("]
        ]
        for row in layout:
            btn_row = ft.Row(spacing=5)
            for b in row:
                btn_row.controls.append(ft.ElevatedButton(b, width=60, height=50, on_click=lambda e, val=b: calc_button_click(e, val), bgcolor=BUTTON_PRIMARY, color=TEXT_COLOR))
            buttons.append(btn_row)
        return buttons

    # --- UI ---
    focus_url_input = ft.TextField(label="Focus URL", width=300, value="https://www.google.com", filled=True, bgcolor=ft.Colors.WHITE)
    add_button = ft.ElevatedButton("Add Task", on_click=add_task, icon=ft.Icons.ADD, bgcolor=BUTTON_PRIMARY, color=TEXT_COLOR)
    start_button = ft.ElevatedButton("▶️ Start Focus", on_click=start_focus_timer, bgcolor=BUTTON_SECONDARY, color=TEXT_COLOR)
    reset_button = ft.ElevatedButton("🔄 Reset Timer", on_click=reset_focus_timer, bgcolor=BUTTON_DANGER, color=TEXT_COLOR)
    focus_mode_button = ft.ElevatedButton("🔒 Start Focus Mode", on_click=open_focus_browser, bgcolor=BUTTON_PRIMARY, color=TEXT_COLOR)
    add_note_button = ft.ElevatedButton("Add Note", on_click=add_note, icon=ft.Icons.NOTE_ADD, bgcolor=BUTTON_PRIMARY, color=TEXT_COLOR)

    tabs = ft.Tabs(tabs=[
        ft.Tab(text="Tasks & Timer", content=ft.Column([
            ft.Row([task_input, priority_dropdown, add_button]),
            ft.Text("Your Tasks:", size=18, weight="bold", color=TEXT_COLOR),
            task_list,
            ft.Divider(),
            ft.Row([focus_label, start_button, reset_button], alignment=ft.MainAxisAlignment.SPACE_AROUND),
            ft.Divider(),
            ft.Text("Focus Mode:", size=20, weight="bold", color=TEXT_COLOR),
            ft.Row([focus_url_input, focus_mode_button]),
            ft.Divider(),
            ft.Text("AI Focus Coach", size=20, weight="bold", color=TEXT_COLOR),
            ai_tip_text
        ], spacing=12)),

        ft.Tab(text="Focus History", content=ft.Column([
            ft.Text("Focus History:", size=18, weight="bold", color=TEXT_COLOR),
            history_list,
            ft.Divider(),
            ft.Text("AI Summary:", size=18, weight="bold", color=TEXT_COLOR),
            history_summary_text
        ], spacing=8)),

        ft.Tab(text="Notes", content=ft.Column([
            note_input,
            tag_input,
            add_note_button,
            ft.Divider(),
            note_list,
            ft.Divider(),
            ft.Text("Global AI Summary:", size=18, weight="bold", color=TEXT_COLOR),
            global_summary_text
        ], spacing=8)),

        ft.Tab(text="Calculator", content=ft.Column([
            calc_output,
            *create_calc_buttons()
        ], spacing=5))
    ], expand=True)

    page.add(tabs)

if __name__ == "__main__":
    ft.app(target=main)
