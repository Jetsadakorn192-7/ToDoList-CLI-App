#!/usr/bin/env python3
"""
todo.py — CLI Todo App
Usage: python3 todo.py <command> [options]
"""

import json
from datetime import datetime, date
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich import box
from rich.text import Text
from rich.panel import Panel

console = Console()

# Store data file in the same directory as this script
DATA_FILE = Path(__file__).parent / "todo_data.json"
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

# Color mapping for each priority level
PRIORITY_COLOR = {"high": "red", "medium": "yellow", "low": "green"}

# Symbol mapping for each priority level
PRIORITY_SYMBOL = {"high": "▲", "medium": "●", "low": "▽"}


# ─── Data helpers ────────────────────────────────────────────────────────────

def load_tasks() -> list[dict]:
    """Load all tasks from the JSON file.
    Returns an empty list if the file does not exist yet.
    """
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_tasks(tasks: list[dict]) -> None:
    """Persist the task list to the JSON file."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)


def next_id(tasks: list[dict]) -> int:
    """Return the next available task ID.
    Always increments from the current maximum, so IDs never repeat
    even after deletions.
    """
    return max((t["id"] for t in tasks), default=0) + 1


def parse_date(value: str) -> str:
    """Parse a date string and return it in YYYY-MM-DD format.
    Accepts both YYYY-MM-DD and DD/MM/YYYY input formats.
    Raises click.BadParameter if the format is unrecognised.
    """
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise click.BadParameter(f"รูปแบบวันที่ไม่ถูกต้อง: '{value}'\nใช้รูปแบบ YYYY-MM-DD หรือ DD/MM/YYYY")


def deadline_status(deadline_str: str | None) -> tuple[str, str]:
    """Return a (label, rich_color) tuple describing a task's deadline status.

    Possible states:
      - No deadline   → empty label
      - Overdue       → red warning with days overdue
      - Due today     → yellow alert
      - Due in ≤3 days → yellow countdown
      - Due later     → cyan date display
    """
    if not deadline_str:
        return "", "dim"

    today = date.today()
    dl = date.fromisoformat(deadline_str)
    diff = (dl - today).days

    if diff < 0:
        return f"! เกินกำหนด {abs(diff)}วัน", "bold red"
    elif diff == 0:
        return "◷ วันนี้!", "bold yellow"
    elif diff <= 3:
        return f"◷ อีก {diff}วัน", "yellow"
    else:
        return f"◷ {deadline_str}", "cyan"


# ─── Display helpers ──────────────────────────────────────────────────────────

def build_table(tasks: list[dict]) -> Table:
    """Build and return a Rich Table from a list of task dicts.
    Completed tasks are rendered with dim + strikethrough styling.
    """
    table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        border_style="bright_black",
        expand=True,
    )
    table.add_column("ID", justify="center", width=4)
    table.add_column("สถานะ", justify="center", width=6)
    table.add_column("งาน", min_width=20)
    table.add_column("Priority", justify="center", width=10)
    table.add_column("Deadline", width=18)
    table.add_column("สร้างเมื่อ", width=12)

    for t in tasks:
        done = t.get("done", False)

        # Status symbol: checkmark if done, circle if pending
        status = "✓" if done else "○"

        # Apply strikethrough style to completed task titles
        task_text = Text(t["title"])
        if done:
            task_text.stylize("dim strike")

        # Priority symbol + color; dim when task is done
        pri = t.get("priority", "medium")
        pri_text = Text(f"{PRIORITY_SYMBOL[pri]} {pri}", style=PRIORITY_COLOR[pri])
        if done:
            pri_text.stylize("dim")

        # Deadline label with urgency color; dim when task is done
        dl_label, dl_color = deadline_status(t.get("deadline"))
        dl_text = Text(dl_label, style=dl_color if not done else "dim")

        # Show only the date portion of the ISO timestamp
        created = t.get("created_at", "")[:10]

        table.add_row(
            str(t["id"]),
            status,
            task_text,
            pri_text,
            dl_text,
            Text(created, style="dim"),
        )
    return table


# ─── CLI commands ─────────────────────────────────────────────────────────────

@click.group()
def cli():
    """Todo CLI — จัดการงานของคุณจาก terminal"""


@cli.command("now")
def cmd_now():
    """Display the current date and time in Thai Buddhist Era format."""
    now = datetime.now()

    thai_days   = ["จันทร์","อังคาร","พุธ","พฤหัสบดี","ศุกร์","เสาร์","อาทิตย์"]
    thai_months = ["","มกราคม","กุมภาพันธ์","มีนาคม","เมษายน","พฤษภาคม","มิถุนายน",
                   "กรกฎาคม","สิงหาคม","กันยายน","ตุลาคม","พฤศจิกายน","ธันวาคม"]

    day_name   = thai_days[now.weekday()]
    month_name = thai_months[now.month]
    be_year    = now.year + 543          # Convert CE to Buddhist Era
    time_str   = now.strftime("%H:%M:%S")
    date_str   = f"วัน{day_name}ที่ {now.day} {month_name} พ.ศ. {be_year}"

    console.print(Panel(
        f"[bold white]◷ {time_str}[/bold white]\n[cyan]{date_str}[/cyan]",
        title="[bold yellow]วันและเวลาปัจจุบัน[/bold yellow]",
        border_style="yellow",
        expand=False,
    ))


@cli.command("add")
@click.argument("title")
@click.option("-p", "--priority", type=click.Choice(["high","medium","low"]),
              default="medium", show_default=True, help="ระดับความสำคัญ")
@click.option("-d", "--deadline", default=None,
              help="กำหนดเส้นตาย เช่น 2026-12-31 หรือ 31/12/2026")
def cmd_add(title, priority, deadline):
    """Add a new task.

    Example: todo add "ทำรายงาน" -p high -d 2026-12-31
    """
    tasks = load_tasks()

    # Parse deadline only when provided
    dl = parse_date(deadline) if deadline else None

    task = {
        "id":         next_id(tasks),
        "title":      title,
        "priority":   priority,
        "deadline":   dl,
        "done":       False,
        "created_at": datetime.now().isoformat(),
    }

    tasks.append(task)
    save_tasks(tasks)

    pri_color = PRIORITY_COLOR[priority]
    console.print(
        f"[green]+ เพิ่มงาน[/green] [bold]#{task['id']}[/bold] '{title}' "
        f"([{pri_color}]{priority}[/{pri_color}])"
        + (f" ครบกำหนด [cyan]{dl}[/cyan]" if dl else "")
    )


@cli.command("list")
@click.option("--all", "show_all", is_flag=True, help="แสดงทั้งหมดรวม task ที่เสร็จแล้ว")
@click.option("-p", "--priority", type=click.Choice(["high","medium","low"]),
              default=None, help="filter ตาม priority")
@click.option("--overdue", is_flag=True, help="แสดงเฉพาะ task ที่เกินกำหนด")
def cmd_list(show_all, priority, overdue):
    """List tasks with optional filters.

    By default shows only pending tasks.
    Use --all to include completed ones.
    """
    tasks = load_tasks()

    if not tasks:
        console.print("[dim]ยังไม่มีงาน — ลองใช้ [bold]todo add \"งานของคุณ\"[/bold][/dim]")
        return

    # Start with all tasks then narrow down by active filters
    filtered = tasks

    if not show_all:
        filtered = [t for t in filtered if not t.get("done")]

    if priority:
        filtered = [t for t in filtered if t.get("priority") == priority]

    if overdue:
        today = date.today().isoformat()
        filtered = [
            t for t in filtered
            if t.get("deadline") and t["deadline"] < today and not t.get("done")
        ]

    if not filtered:
        console.print("[dim]ไม่มีงานที่ตรงเงื่อนไข[/dim]")
        return

    # Summary counts across the full unfiltered task list
    pending = sum(1 for t in tasks if not t.get("done"))
    done    = sum(1 for t in tasks if t.get("done"))

    console.print(
        f"\n[bold]Todo List[/bold]  [dim]|[/dim]  "
        f"รอทำ [bold yellow]{pending}[/bold yellow]  "
        f"เสร็จแล้ว [bold green]{done}[/bold green]\n"
    )
    console.print(build_table(filtered))


@cli.command("done")
@click.argument("task_id", type=int)
def cmd_done(task_id):
    """Mark a task as completed.

    Example: todo done 3
    """
    tasks = load_tasks()

    for t in tasks:
        if t["id"] == task_id:
            t["done"] = True
            save_tasks(tasks)
            console.print(f"[green]✓ เสร็จแล้ว:[/green] [bold strike dim]{t['title']}[/bold strike dim]")
            return

    console.print(f"[red]ไม่พบ task #{task_id}[/red]")


@cli.command("undone")
@click.argument("task_id", type=int)
def cmd_undone(task_id):
    """Reopen a completed task.

    Example: todo undone 3
    """
    tasks = load_tasks()

    for t in tasks:
        if t["id"] == task_id:
            t["done"] = False
            save_tasks(tasks)
            console.print(f"[yellow]↩ เปิดใหม่:[/yellow] [bold]{t['title']}[/bold]")
            return

    console.print(f"[red]ไม่พบ task #{task_id}[/red]")


@cli.command("edit")
@click.argument("task_id", type=int)
@click.option("-t", "--title",    default=None, help="ชื่องานใหม่")
@click.option("-p", "--priority", type=click.Choice(["high","medium","low"]),
              default=None, help="priority ใหม่")
@click.option("-d", "--deadline", default=None, help="deadline ใหม่ (ใช้ 'none' เพื่อลบ)")
def cmd_edit(task_id, title, priority, deadline):
    """Edit one or more fields of an existing task.
    Only the options you pass will be updated; others remain unchanged.

    Example: todo edit 2 -t "ชื่อใหม่" -p high
    """
    tasks = load_tasks()

    for t in tasks:
        if t["id"] == task_id:
            # Update only the fields that were explicitly provided
            if title:
                t["title"] = title
            if priority:
                t["priority"] = priority
            if deadline is not None:
                # Allow 'none' as a keyword to remove an existing deadline
                t["deadline"] = None if deadline.lower() == "none" else parse_date(deadline)

            save_tasks(tasks)
            console.print(f"[green]~ แก้ไขแล้ว:[/green] task [bold]#{task_id}[/bold]")
            return

    console.print(f"[red]ไม่พบ task #{task_id}[/red]")


@cli.command("delete")
@click.argument("task_id", type=int)
@click.confirmation_option(prompt="ยืนยันการลบ?")
def cmd_delete(task_id):
    """Permanently delete a task (asks for confirmation).

    Example: todo delete 3
    """
    tasks = load_tasks()
    new_tasks = [t for t in tasks if t["id"] != task_id]

    if len(new_tasks) == len(tasks):
        # No task was removed — ID did not exist
        console.print(f"[red]ไม่พบ task #{task_id}[/red]")
        return

    save_tasks(new_tasks)
    console.print(f"[red]× ลบ task #{task_id} แล้ว[/red]")


@cli.command("search")
@click.argument("keyword")
def cmd_search(keyword):
    """Search tasks by keyword (case-insensitive).

    Example: todo search รายงาน
    """
    tasks = load_tasks()

    # Case-insensitive substring match on task title
    results = [t for t in tasks if keyword.lower() in t["title"].lower()]

    if not results:
        console.print(f"[dim]ไม่พบงานที่มีคำว่า '{keyword}'[/dim]")
        return

    console.print(f"\n[bold]⌕ ผลการค้นหา[/bold] '[cyan]{keyword}[/cyan]' — พบ {len(results)} รายการ\n")
    console.print(build_table(results))


@cli.command("clear")
@click.confirmation_option(prompt="ลบ task ที่เสร็จแล้วทั้งหมด?")
def cmd_clear():
    """Remove all completed tasks (asks for confirmation)."""
    tasks = load_tasks()
    new_tasks = [t for t in tasks if not t.get("done")]
    removed = len(tasks) - len(new_tasks)
    save_tasks(new_tasks)
    console.print(f"[green]× ลบ {removed} task ที่เสร็จแล้วออกแล้ว[/green]")


@cli.command("help")
def cmd_help():
    """Show all commands with usage examples."""
    console.print()
    console.print(Panel(
        "[bold white]Todo CLI[/bold white]  [dim]—[/dim]  จัดการงานของคุณจาก terminal",
        border_style="cyan",
        expand=False,
    ))
    console.print()

    # Each section: (heading, color, [(command, description), ...])
    sections = [
        (
            "◷  วันและเวลา", "cyan",
            [
                ("todo now",  "แสดงวันเวลาปัจจุบัน (พ.ศ.)"),
            ]
        ),
        (
            "+  เพิ่มงาน", "green",
            [
                ('todo add "ซื้อของ"',                      "เพิ่มงานทั่วไป (priority: medium)"),
                ('todo add "ส่งรายงาน" -p high',            "เพิ่มงานด่วน"),
                ('todo add "ประชุม" -d 2026-06-01',          "เพิ่มงานพร้อม deadline"),
                ('todo add "deploy" -p high -d 31/05/2026', "ด่วน + deadline (รองรับ DD/MM/YYYY)"),
            ]
        ),
        (
            "≡  ดูรายการ", "yellow",
            [
                ("todo list",           "แสดงงานที่ยังค้างอยู่"),
                ("todo list --all",     "แสดงทั้งหมดรวมที่เสร็จแล้ว"),
                ("todo list -p high",   "filter เฉพาะงานด่วน"),
                ("todo list --overdue", "แสดงงานที่เกินกำหนดแล้ว"),
            ]
        ),
        (
            "✓  อัปเดตสถานะ", "green",
            [
                ("todo done 3",   "ทำเครื่องหมายงาน #3 ว่าเสร็จแล้ว"),
                ("todo undone 3", "เปิดงาน #3 กลับมาทำใหม่"),
            ]
        ),
        (
            "~  แก้ไขงาน", "blue",
            [
                ('todo edit 2 -t "ชื่อใหม่"',    "เปลี่ยนชื่องาน"),
                ("todo edit 2 -p low",            "เปลี่ยน priority"),
                ("todo edit 2 -d 2026-12-31",     "เปลี่ยน deadline"),
                ("todo edit 2 -d none",           "ลบ deadline ออก"),
                ('todo edit 2 -t "ใหม่" -p high', "เปลี่ยนหลายอย่างพร้อมกัน"),
            ]
        ),
        (
            "⌕  ค้นหา", "magenta",
            [
                ("todo search รายงาน", "ค้นหา task ที่มีคำว่า 'รายงาน'"),
                ("todo search deploy", "ค้นหาด้วยภาษาอังกฤษ"),
            ]
        ),
        (
            "×  ลบ", "red",
            [
                ("todo delete 3", "ลบงาน #3 (จะถามยืนยันก่อน)"),
                ("todo clear",    "ลบทุก task ที่เสร็จแล้วออก"),
            ]
        ),
    ]

    for title, color, rows in sections:
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2), expand=False)
        table.add_column("คำสั่ง", style=f"bold {color}", min_width=42)
        table.add_column("คำอธิบาย", style="dim")

        for cmd, desc in rows:
            table.add_row(cmd, desc)

        console.print(f"  [bold]{title}[/bold]")
        console.print(table)

    console.print("  [dim]─────────────────────────────────────────────────────[/dim]")
    console.print(f"  [dim]ข้อมูลเก็บที่:[/dim] [cyan]{DATA_FILE}[/cyan]")
    console.print(f"  [dim]ทางลัด: เพิ่ม [/dim][bold]alias todo=\"python3 ~/todo.py\"[/bold][dim] ใน ~/.zshrc[/dim]")
    console.print()


if __name__ == "__main__":
    cli()
