import sys
import turtle
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, available_timezones
from capture_screenshot import capture_screenshot

# --- Configuration & Colors ---
BG_COLOR = "#F6F3E7"
DIAL_COLOR = "#FFFFFF"
PRIMARY_COLOR = "#1E242B"
ACCENT_BLUE = "#1565C0"
ACCENT_RED = "#D32F2F"
SUBTLE_TEXT = "#555E68"
PANEL_BG = "#FFFFFF"
HIGHLIGHT_BG = "#E3F2FD"
BTN_BG = "#E9EEF4"

VISIBLE_ROWS = 10

FALLBACK_ZONES = [
    ("Addis Ababa (Africa)", timezone(timedelta(hours=3), "EAT")),
    ("Cairo (Africa)", timezone(timedelta(hours=2), "EET")),
    ("Johannesburg (Africa)", timezone(timedelta(hours=2), "SAST")),
    ("Lagos (Africa)", timezone(timedelta(hours=1), "WAT")),
    ("Nairobi (Africa)", timezone(timedelta(hours=3), "EAT")),
    ("New York (America)", timezone(timedelta(hours=-5), "EST")),
    ("Chicago (America)", timezone(timedelta(hours=-6), "CST")),
    ("Denver (America)", timezone(timedelta(hours=-7), "MST")),
    ("Los Angeles (America)", timezone(timedelta(hours=-8), "PST")),
    ("Sao Paulo (America)", timezone(timedelta(hours=-3), "BRT")),
    ("Toronto (America)", timezone(timedelta(hours=-5), "EST")),
    ("Dubai (Asia)", timezone(timedelta(hours=4), "GST")),
    ("Hong Kong (Asia)", timezone(timedelta(hours=8), "HKT")),
    ("Kolkata (Asia)", timezone(timedelta(hours=5, minutes=30), "IST")),
    ("Riyadh (Asia)", timezone(timedelta(hours=3), "AST")),
    ("Seoul (Asia)", timezone(timedelta(hours=9), "KST")),
    ("Shanghai (Asia)", timezone(timedelta(hours=8), "CST")),
    ("Singapore (Asia)", timezone(timedelta(hours=8), "SGT")),
    ("Tokyo (Asia)", timezone(timedelta(hours=9), "JST")),
    ("Sydney (Australia)", timezone(timedelta(hours=11), "AEDT")),
    ("Berlin (Europe)", timezone(timedelta(hours=1), "CET")),
    ("Istanbul (Europe)", timezone(timedelta(hours=3), "TRT")),
    ("London (Europe)", timezone(timedelta(hours=0), "GMT")),
    ("Madrid (Europe)", timezone(timedelta(hours=1), "CET")),
    ("Moscow (Europe)", timezone(timedelta(hours=3), "MSK")),
    ("Paris (Europe)", timezone(timedelta(hours=1), "CET")),
    ("Rome (Europe)", timezone(timedelta(hours=1), "CET")),
    ("Auckland (Pacific)", timezone(timedelta(hours=13), "NZDT")),
]


def load_all_timezones():
    """Fetch every IANA time zone if tzdata is available, otherwise use built-in cities."""
    zones = [("Local Time", None)]
    valid_keys = sorted(
        tz for tz in available_timezones()
        if "/" in tz and not tz.startswith(("Etc/", "SystemV/", "posix/", "right/"))
    )
    if valid_keys:
        for key in valid_keys:
            region, city = key.split("/", 1)
            display_name = f"{city.replace('_', ' ')} ({region})"
            zones.append((display_name, ZoneInfo(key)))
    else:
        zones.extend(FALLBACK_ZONES)
    return zones


TIMEZONES = load_all_timezones()

state = {
    "paused": False,
    "tz_index": 0,
    "radius": 200,
    "last_size": (0, 0),
    "frozen_dt": None,
    "picker_open": False,
    "search_query": "",
    "filtered_indices": list(range(len(TIMEZONES))),
    "selected_row": 0,
    "scroll_offset": 0,
    "buttons": [],
}


def setup_screen():
    screen = turtle.Screen()
    screen.title("Functional Analog Clock")
    screen.setup(width=680, height=760)
    screen.bgcolor(BG_COLOR)
    screen.tracer(0)
    screen.getcanvas().focus_force()
    return screen


def create_pen():
    pen = turtle.Turtle()
    pen.hideturtle()
    pen.speed(0)
    pen.penup()
    return pen


def clock_to_turtle_heading(clock_angle_deg):
    """Convert clockwise 12-o'clock-zero angles into standard turtle headings."""
    return (90.0 - clock_angle_deg) % 360.0


def draw_rect(pen, x, y, width, height, fill_color, border_color=None, border_width=1):
    """Draw a filled rectangle centered at (x, y) using pure turtle commands."""
    left = x - width / 2
    top = y + height / 2
    pen.goto(left, top)
    pen.setheading(0)
    pen.color(border_color or fill_color, fill_color)
    pen.pensize(border_width)
    pen.pendown()
    pen.begin_fill()
    for _ in range(2):
        pen.forward(width)
        pen.right(90)
        pen.forward(height)
        pen.right(90)
    pen.end_fill()
    pen.penup()


def draw_button(pen, x, y, width, height, text, action_id, bg=BTN_BG, fg=PRIMARY_COLOR, border=SUBTLE_TEXT):
    """Draw a clickable button on the canvas and register its bounding box."""
    draw_rect(pen, x, y, width, height, bg, border, 1)
    pen.color(fg)
    pen.goto(x, y - 6)
    pen.write(text, align="center", font=("Arial", 10, "bold"))
    state["buttons"].append((x, y, width, height, action_id))


def draw_face(pen, radius):
    """Draw the static circular dial, 60 tick marks, and hour numbers 1-12."""
    pen.clear()
    pen.goto(0, -radius)
    pen.setheading(0)
    pen.color(PRIMARY_COLOR, DIAL_COLOR)
    pen.pensize(max(3, int(radius * 0.018)))
    pen.pendown()
    pen.begin_fill()
    pen.circle(radius)
    pen.end_fill()
    pen.penup()

    for tick in range(60):
        heading = clock_to_turtle_heading(tick * 6)
        pen.goto(0, 0)
        pen.setheading(heading)

        if tick % 15 == 0:
            tick_len, pen_size, color = radius * 0.09, 3, ACCENT_RED
        elif tick % 5 == 0:
            tick_len, pen_size, color = radius * 0.07, 2, PRIMARY_COLOR
        else:
            tick_len, pen_size, color = radius * 0.04, 1, SUBTLE_TEXT

        pen.forward(radius - tick_len - (radius * 0.03))
        pen.color(color)
        pen.pensize(pen_size)
        pen.pendown()
        pen.forward(tick_len)
        pen.penup()

    number_radius = radius * 0.78
    font_size = max(12, int(radius * 0.075))
    pen.color(PRIMARY_COLOR)

    for hour in range(1, 13):
        heading = clock_to_turtle_heading(hour * 30)
        pen.goto(0, 0)
        pen.setheading(heading)
        pen.forward(number_radius)
        pen.sety(pen.ycor() - font_size * 0.65)
        pen.write(str(hour), align="center", font=("Arial", font_size, "bold"))


def draw_hand(pen, clock_angle_deg, length, tail_length, width, color):
    """Draw a single clock hand with counterweight tail rotating around (0, 0)."""
    heading = clock_to_turtle_heading(clock_angle_deg)
    pen.goto(0, 0)
    pen.setheading(heading + 180)
    pen.forward(tail_length)
    pen.setheading(heading)
    pen.color(color)
    pen.pensize(width)
    pen.pendown()
    pen.forward(tail_length + length)
    pen.penup()


def draw_center_cap(pen, radius):
    """Draw the center pin over the base of all three hands."""
    cap_r = max(5, int(radius * 0.03))
    pen.goto(0, -cap_r)
    pen.setheading(0)
    pen.color(PRIMARY_COLOR, ACCENT_RED)
    pen.pensize(2)
    pen.pendown()
    pen.begin_fill()
    pen.circle(cap_r)
    pen.end_fill()
    pen.penup()


def format_tz_label(name, current_dt):
    """Format the active time zone name alongside its abbreviation and UTC offset."""
    abbr = current_dt.tzname() or "Local"
    offset = current_dt.utcoffset()
    if offset is None:
        return f"{name} ({abbr})"

    total_minutes = int(offset.total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    hours, mins = divmod(abs(total_minutes), 60)
    offset_str = f"UTC{sign}{hours}" if mins == 0 else f"UTC{sign}{hours}:{mins:02d}"
    return f"{name} — {abbr} ({offset_str})"


def draw_ui_labels(pen, current_dt, radius):
    """Draw interactive control buttons, active time zone header, and digital readout."""
    pen.clear()
    state["buttons"] = []

    name, _ = TIMEZONES[state["tz_index"]]
    tz_label = format_tz_label(name, current_dt)
    count_info = f"[{state['tz_index'] + 1}/{len(TIMEZONES)}]"

    bar_y = radius + 68
    draw_button(pen, -195, bar_y, 90, 28, "◀ Prev", "prev_tz")
    draw_button(
        pen,
        -75,
        bar_y,
        125,
        28,
        "▶ Resume" if state["paused"] else "⏸ Pause",
        "toggle_pause",
        bg="#FFEBEE" if state["paused"] else BTN_BG,
        fg=ACCENT_RED if state["paused"] else PRIMARY_COLOR,
        border=ACCENT_RED if state["paused"] else SUBTLE_TEXT,
    )
    draw_button(
        pen,
        65,
        bar_y,
        130,
        28,
        "🔍 Time Zones",
        "open_picker",
        bg=HIGHLIGHT_BG,
        fg=ACCENT_BLUE,
        border=ACCENT_BLUE,
    )
    draw_button(pen, 195, bar_y, 90, 28, "Next ▶", "next_tz")

    pen.color(ACCENT_BLUE)
    pen.goto(0, radius + 28)
    pen.write(f"{tz_label}  {count_info}", align="center", font=("Arial", 12, "bold"))

    pen.color(PRIMARY_COLOR)
    pen.goto(0, -radius - 42)
    pen.write(current_dt.strftime("%I:%M:%S %p"), align="center", font=("Courier", 18, "bold"))

    pen.color(SUBTLE_TEXT)
    pen.goto(0, -radius - 68)
    pen.write(current_dt.strftime("%A, %b %d, %Y"), align="center", font=("Arial", 11, "normal"))


def draw_picker_overlay(pen):
    """Draw the pure-turtle searchable time zone selector overlay."""
    pen.clear()
    if not state["picker_open"]:
        return

    panel_w = 440
    row_h = 30
    header_h = 74
    footer_h = 28
    panel_h = header_h + (VISIBLE_ROWS * row_h) + footer_h
    top_y = panel_h / 2

    draw_rect(pen, 0, 0, panel_w, panel_h, PANEL_BG, PRIMARY_COLOR, 2)

    # Header + Close [X] Button
    draw_rect(pen, 0, top_y - 18, panel_w - 4, 34, PRIMARY_COLOR)
    pen.color("#FFFFFF")
    pen.goto(-panel_w / 2 + 14, top_y - 25)
    pen.write(
        f"Select Time Zone ({len(state['filtered_indices'])} matches)",
        align="left",
        font=("Arial", 11, "bold"),
    )
    draw_button(
        pen,
        panel_w / 2 - 22,
        top_y - 18,
        28,
        24,
        "✕",
        "close_picker",
        bg=ACCENT_RED,
        fg="#FFFFFF",
        border="#FFFFFF",
    )

    # Pure-Turtle Search Input Display + Clear Button
    search_y = top_y - 54
    draw_rect(pen, -18, search_y, panel_w - 60, 28, "#F4F6F8", ACCENT_BLUE, 2)
    pen.goto(-panel_w / 2 + 20, search_y - 7)
    if state["search_query"]:
        pen.color(PRIMARY_COLOR)
        pen.write(f"🔍  {state['search_query']}_", align="left", font=("Arial", 11, "bold"))
        draw_button(pen, panel_w / 2 - 26, search_y, 34, 26, "Clear", "clear_search")
    else:
        pen.color(SUBTLE_TEXT)
        pen.write("🔍  Type to filter or scroll with mouse wheel...", align="left", font=("Arial", 10, "italic"))

    start_y = top_y - header_h - row_h / 2
    filtered = state["filtered_indices"]

    if not filtered:
        pen.color(ACCENT_RED)
        pen.goto(0, 0)
        pen.write("No matching time zones found", align="center", font=("Arial", 11, "bold"))
    else:
        for row in range(VISIBLE_ROWS):
            list_pos = state["scroll_offset"] + row
            if list_pos >= len(filtered):
                break

            tz_idx = filtered[list_pos]
            label, _ = TIMEZONES[tz_idx]
            row_y = start_y - (row * row_h)
            is_selected = list_pos == state["selected_row"]
            is_active = tz_idx == state["tz_index"]

            if is_selected:
                draw_rect(pen, 0, row_y, panel_w - 16, row_h - 2, HIGHLIGHT_BG, ACCENT_BLUE, 1)

            pen.color(ACCENT_BLUE if (is_selected or is_active) else PRIMARY_COLOR)
            pen.goto(-panel_w / 2 + 20, row_y - 7)
            prefix = "✓ " if is_active else "   "
            pen.write(
                f"{prefix}{label}",
                align="left",
                font=("Arial", 10, "bold" if (is_selected or is_active) else "normal"),
            )

    pen.color(SUBTLE_TEXT)
    pen.goto(0, -top_y + 9)
    pen.write(
        "Type to search  •  Click or [Enter] to select  •  Scroll wheel or [↑/↓]  •  [Esc] Close",
        align="center",
        font=("Arial", 9, "normal"),
    )


def update_filter(query):
    """Filter the time zone list based on typed search characters."""
    state["search_query"] = query
    q = query.strip().lower()
    if not q:
        state["filtered_indices"] = list(range(len(TIMEZONES)))
    else:
        state["filtered_indices"] = [
            i for i, (label, _) in enumerate(TIMEZONES) if q in label.lower()
        ]
    state["selected_row"] = 0
    state["scroll_offset"] = 0


def move_selection(delta):
    """Move highlight up or down inside the searchable list."""
    count = len(state["filtered_indices"])
    if count == 0:
        return
    state["selected_row"] = (state["selected_row"] + delta) % count
    if state["selected_row"] < state["scroll_offset"]:
        state["scroll_offset"] = state["selected_row"]
    elif state["selected_row"] >= state["scroll_offset"] + VISIBLE_ROWS:
        state["scroll_offset"] = state["selected_row"] - VISIBLE_ROWS + 1


def confirm_selection():
    """Apply the highlighted time zone and close the picker overlay."""
    if state["filtered_indices"]:
        state["tz_index"] = state["filtered_indices"][state["selected_row"]]
        if state["paused"]:
            state["frozen_dt"] = get_current_time()
    state["picker_open"] = False


def get_current_time():
    """Return the current datetime in the selected time zone."""
    _, tz = TIMEZONES[state["tz_index"]]
    return datetime.now().astimezone() if tz is None else datetime.now(tz)


def main():
    screen = setup_screen()
    face_pen = create_pen()
    hand_pen = create_pen()
    ui_pen = create_pen()
    picker_pen = create_pen()

    def update_clock(force_hands=False):
        """Refresh the clock hands, UI labels, and picker overlay cleanly."""
        w = screen.window_width()
        h = screen.window_height()
        if (w, h) != state["last_size"]:
            state["last_size"] = (w, h)
            state["radius"] = max(140, min(w, h - 210) // 2)
            draw_face(face_pen, state["radius"])
            force_hands = True

        now = state["frozen_dt"] if state["paused"] else get_current_time()
        r = state["radius"]

        if not state["paused"] or force_hands:
            seconds = now.second + now.microsecond / 1_000_000.0
            minutes = now.minute + seconds / 60.0
            hours = (now.hour % 12) + minutes / 60.0

            hand_pen.clear()
            draw_hand(hand_pen, hours * 30.0, r * 0.48, r * 0.08, 6, PRIMARY_COLOR)
            draw_hand(hand_pen, minutes * 6.0, r * 0.66, r * 0.10, 4, ACCENT_BLUE)
            draw_hand(hand_pen, seconds * 6.0, r * 0.71, r * 0.13, 2, ACCENT_RED)
            draw_center_cap(hand_pen, r)

        draw_ui_labels(ui_pen, now, r)
        draw_picker_overlay(picker_pen)
        screen.update()

    def toggle_pause():
        state["paused"] = not state["paused"]
        state["frozen_dt"] = get_current_time() if state["paused"] else None
        update_clock(force_hands=True)

    def cycle_tz(step):
        state["tz_index"] = (state["tz_index"] + step) % len(TIMEZONES)
        if state["paused"]:
            state["frozen_dt"] = get_current_time()
        update_clock(force_hands=True)

    def open_picker():
        state["picker_open"] = True
        update_filter("")
        state["selected_row"] = state["tz_index"]
        state["scroll_offset"] = max(0, state["tz_index"] - VISIBLE_ROWS // 2)
        update_clock(force_hands=True)

    def close_picker():
        state["picker_open"] = False
        update_clock(force_hands=True)

    def handle_action(action_id):
        if action_id == "toggle_pause":
            toggle_pause()
        elif action_id == "prev_tz":
            cycle_tz(-1)
        elif action_id == "next_tz":
            cycle_tz(1)
        elif action_id == "open_picker":
            open_picker()
        elif action_id == "close_picker":
            close_picker()
        elif action_id == "clear_search":
            update_filter("")
            update_clock()

    def handle_keypress(event):
        """Handle keyboard shortcuts and live search typing."""
        key = event.keysym
        char = event.char

        if state["picker_open"]:
            if key == "Escape":
                close_picker()
            elif key in ("Return", "KP_Enter"):
                confirm_selection()
                update_clock(force_hands=True)
            elif key == "Up":
                move_selection(-1)
                update_clock()
            elif key == "Down":
                move_selection(1)
                update_clock()
            elif key == "BackSpace":
                update_filter(state["search_query"][:-1])
                update_clock()
            elif char and (char.isalnum() or char in (" ", "_", "-", "/")):
                update_filter(state["search_query"] + char)
                update_clock()
            return

        if key == "space":
            toggle_pause()
        elif key in ("t", "T", "Right"):
            cycle_tz(1)
        elif key in ("b", "B", "Left"):
            cycle_tz(-1)
        elif key in ("s", "S"):
            open_picker()

    def on_click(x, y):
        """Handle mouse clicks on buttons, picker rows, time zone banner, and clock dial."""
        canvas = screen.getcanvas()
        canvas.focus_force()

        for bx, by, bw, bh, action_id in reversed(state["buttons"]):
            if abs(x - bx) <= bw / 2 and abs(y - by) <= bh / 2:
                handle_action(action_id)
                return

        if state["picker_open"]:
            panel_w = 440
            row_h = 30
            header_h = 74
            footer_h = 28
            panel_h = header_h + (VISIBLE_ROWS * row_h) + footer_h
            top_y = panel_h / 2

            if abs(x) > panel_w / 2 or abs(y) > top_y:
                close_picker()
                return

            start_y = top_y - header_h
            if start_y >= y >= start_y - (VISIBLE_ROWS * row_h):
                clicked_row = int((start_y - y) // row_h)
                list_pos = state["scroll_offset"] + clicked_row
                if list_pos < len(state["filtered_indices"]):
                    state["selected_row"] = list_pos
                    confirm_selection()
                    update_clock(force_hands=True)
            return

        r = state["radius"]
        if r + 15 <= y <= r + 48:
            open_picker()
            return

        if (x ** 2 + y ** 2) <= r ** 2:
            toggle_pause()

    def on_mousewheel(event):
        """Scroll the time zone list with the mouse wheel."""
        if not state["picker_open"]:
            return
        if getattr(event, "num", None) == 4 or getattr(event, "delta", 0) > 0:
            move_selection(-1)
        elif getattr(event, "num", None) == 5 or getattr(event, "delta", 0) < 0:
            move_selection(1)
        update_clock()

    canvas = screen.getcanvas()
    canvas.bind("<Key>", handle_keypress)
    canvas.bind("<MouseWheel>", on_mousewheel)
    canvas.bind("<Button-4>", on_mousewheel)
    canvas.bind("<Button-5>", on_mousewheel)
    screen.onclick(on_click)

    def schedule_tick():
        update_clock()
        screen.ontimer(schedule_tick, 50)

    schedule_tick()
    if sys.platform == "win32":
        screen.ontimer(capture_screenshot, 1000)
    screen.mainloop()


if __name__ == "__main__":
    main()