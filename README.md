# Study Manager

Professional study management software for PC (Windows/Linux/Mac).

## Features

- **Login / Multiple users** — software asks for username + password on open; each user has their own data.
- **Profile** — name, department, semester, section, registration number, profile photo.
- **Courses** — add/remove courses at will. Each course has folders:
  Lectures, Presentation, Assignment, Project, Notes — upload any files (PDF, Word, PPT, etc.).
- **Task Tracker** — assignments, presentations, projects with pending/done status, due dates.
  Uploading a file for a task asks for the course and auto-saves a copy into that course's folder.
- **Dashboard** — pending/overdue/due-this-week/done stats; deadlines sorted with overdue on top, overdue red.
- **Timetable** — weekly class schedule (day, time, subject, room).
- **Profile** — cover banner, photo, info cards (Registration No, Department, Degree, Semester, Section, University).
- **Notes** — all course notes in one place with search.
- **Performance** — completion stats and progress by task type.
- **Settings** — change password, open data folder, logout.

## Run (source code)

Requires Python 3.10+.

```bash
cd study-manager
pip install customtkinter pillow
python app.py        # Windows
python3 app.py       # Linux / Mac
```

Tip (Windows): `pythonw app.py` se chalao taake kali console window na khule.

## Build Windows .exe (proper app)

1. `build.bat` par double-click karo (2-5 minute lagega).
2. `dist\StudyManager.exe` ban jayegi — double-click se chalao, koi console nahi khulegi.

## Make installer (setup + desktop shortcut)

1. Pehle `build.bat` se exe banao.
2. Inno Setup install karo: https://jrsoftware.org/isinfo.php
3. `installer.iss` ko Inno Setup me kholo aur **Compile** (F9) dabao.
4. `Output\StudyManagerSetup.exe` mil jayegi — ye proper installer hai:
   install location, Start Menu entry aur **Desktop shortcut** ke sath.

## Data

All data is stored locally in `study_manager.db` (SQLite) and the `data/` folder.
Each user's files live under `data/user_<id>/`.
