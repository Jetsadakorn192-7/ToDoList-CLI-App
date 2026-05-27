# Project Todolist

CLI Todo App สำหรับจัดการงานประจำวันผ่าน terminal เขียนด้วย Python

---

## Requirements

- Python 3.10+
- pip

---

## Installation

```bash
# 1. Clone repo
git clone https://github.com/Jetsadakorn192-7/Project_Todolist.git
cd Project_Todolist

# 2. ติดตั้ง dependencies
pip install rich click

# 3. ทดสอบรัน
python3 todo.py help
```

**ตั้ง alias (แนะนำ)** — เพิ่มบรรทัดนี้ใน `~/.zshrc` หรือ `~/.bashrc`:

```bash
alias todo="python3 ~/Project/Project_Todolist/todo.py"
```

แล้ว reload:

```bash
source ~/.zshrc
```

---

## Usage

### ดูวันเวลาปัจจุบัน

```bash
todo now
```

### เพิ่มงาน

```bash
todo add "ชื่องาน"
todo add "ส่งรายงาน" -p high
todo add "ประชุมทีม" -d 2026-06-01
todo add "deploy production" -p high -d 31/05/2026
```

| Option | ค่าที่รับได้ | Default |
|---|---|---|
| `-p` / `--priority` | `high`, `medium`, `low` | `medium` |
| `-d` / `--deadline` | `YYYY-MM-DD` หรือ `DD/MM/YYYY` | — |

### ดูรายการ

```bash
todo list                  # งานที่ยังค้างอยู่
todo list --all            # ทั้งหมดรวมที่เสร็จแล้ว
todo list -p high          # filter เฉพาะงานด่วน
todo list --overdue        # งานที่เกินกำหนดแล้ว
```

### อัปเดตสถานะ

```bash
todo done 3                # ทำเครื่องหมายงาน #3 ว่าเสร็จแล้ว
todo undone 3              # เปิดงาน #3 กลับมาทำใหม่
```

### แก้ไขงาน

```bash
todo edit 2 -t "ชื่อใหม่"   # เปลี่ยนชื่องาน
todo edit 2 -p low          # เปลี่ยน priority
todo edit 2 -d 2026-12-31   # เปลี่ยน deadline
todo edit 2 -d none         # ลบ deadline ออก
```

### ค้นหา

```bash
todo search รายงาน
todo search deploy
```

### ลบ

```bash
todo delete 3              # ลบงาน #3 (จะถามยืนยันก่อน)
todo clear                 # ลบทุก task ที่เสร็จแล้วออก
```

### ดูคำสั่งทั้งหมด

```bash
todo help
```

---

## Project Structure

```
Project_Todolist/
├── todo.py            # source code หลัก
├── .gitignore
└── README.md
```

ข้อมูลทั้งหมดเก็บใน `todo_data.json` (สร้างอัตโนมัติ ไม่ถูก track โดย git)

---

## Tech Stack

- [Python 3](https://www.python.org/)
- [Click](https://click.palletsprojects.com/) — CLI framework
- [Rich](https://github.com/Textualize/rich) — terminal UI
