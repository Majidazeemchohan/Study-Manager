"""Study Manager - Professional Study Management Software (mockup UI)."""
import os
import shutil
import subprocess
import sys
from datetime import datetime, date, timedelta
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont

from database import get_connection, init_db, get_data_dir
from auth import create_user, authenticate, change_password

APP_DIR = os.path.dirname(os.path.abspath(__file__))


def resource_path(*parts):
    """Path to bundled assets.

    Works both when running from source and when packed into a
    PyInstaller .exe (files are extracted to sys._MEIPASS).
    """
    base = getattr(sys, "_MEIPASS", APP_DIR)
    return os.path.join(base, *parts)


ICON_DIR = resource_path("assets", "icons")
IMG_DIR = resource_path("assets", "images")
DATA_DIR = get_data_dir()

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ---- palette (matches design mockup) ----
BG = "#0a1128"
SIDEBAR_BG = "#0d1533"
TOPBAR_BG = "#0d1533"
CARD_BG = "#131b3f"
CARD_BG2 = "#1b2450"
ACCENT = "#2f7bff"
ACCENT_HOVER = "#2560d8"
MUTED = "#8b93b8"
GREEN = "#2ecc71"
ORANGE = "#f59e0b"
RED = "#e74c3c"
TEAL = "#12b5a5"
PURPLE = "#8b5cf6"

CATEGORIES = ["Lectures", "Presentation", "Assignment", "Project", "Notes"]
TASK_TYPES = ["Assignment", "Presentation", "Project"]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

_ICONS = {}


def icon(name, size=20):
    key = (name, size)
    if key not in _ICONS:
        img = Image.open(os.path.join(ICON_DIR, name + ".png"))
        _ICONS[key] = ctk.CTkImage(img, size=(size, size))
    return _ICONS[key]


def banner(name, size):
    img = Image.open(os.path.join(IMG_DIR, name + ".png")).convert("RGB")
    return ctk.CTkImage(img, size=size)


def font(size=13, weight="normal"):
    return ctk.CTkFont(family="Segoe UI", size=size, weight=weight)


def _ui_font(size):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
              "C:/Windows/Fonts/seguisb.ttf",
              "C:/Windows/Fonts/segoeui.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def cover_with_quote():
    """Cover banner with the motivational quote baked in (right aligned)."""
    img = Image.open(os.path.join(IMG_DIR, "cover.png")).convert("RGB")
    d = ImageDraw.Draw(img)
    fnt = _ui_font(30)
    lines = ["Small steps", "every day lead to", "big results"]
    lh = 42
    y0 = (img.height - lh * len(lines)) // 2
    for i, line in enumerate(lines):
        w = d.textlength(line, font=fnt)
        x = img.width - 40 - w
        y = y0 + i * lh
        d.text((x + 2, y + 2), line, font=fnt, fill=(8, 13, 32))
        d.text((x, y), line, font=fnt, fill=(255, 255, 255))
    return img


def goals_with_text():
    """Goals banner with heading text baked in (right side)."""
    img = Image.open(os.path.join(IMG_DIR, "goals.png")).convert("RGB")
    d = ImageDraw.Draw(img)
    f1 = _ui_font(22)
    f2 = _ui_font(46)
    f3 = _ui_font(20)
    x = int(img.width * 0.60)
    y = 52
    d.text((x, y), "Your Goals", font=f1, fill=(139, 147, 184))
    w1 = d.textlength("Your ", font=f2)
    d.text((x, y + 34), "Your ", font=f2, fill=(255, 255, 255))
    d.text((x + w1, y + 34), "Future", font=f2, fill=(47, 123, 255))
    d.text((x, y + 100), "Keep Studying, Keep Growing", font=f3,
           fill=(139, 147, 184))
    return img


def circle_avatar(path, size=120, ring=5, ring_color=(47, 123, 255)):
    """Circular avatar with colored ring; falls back to default icon."""
    if path and os.path.exists(path):
        im = Image.open(path).convert("RGB").resize((size, size), Image.LANCZOS)
    else:
        bg = Image.new("RGBA", (size, size), (27, 36, 80, 255))
        ic = Image.open(os.path.join(ICON_DIR, "profile.png")).convert("RGBA")
        ic = ic.resize((size // 2, size // 2), Image.LANCZOS)
        bg.paste(ic, ((size - ic.width) // 2, (size - ic.height) // 2), ic)
        im = bg.convert("RGB")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size, size], fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    ring_im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(ring_im).ellipse([ring // 2, ring // 2, size - ring // 2 - 1,
                                     size - ring // 2 - 1],
                                    outline=ring_color + (255,), width=ring)
    return Image.alpha_composite(out, ring_im)


def user_data_dir(user_id):
    d = os.path.join(DATA_DIR, f"user_{user_id}")
    os.makedirs(d, exist_ok=True)
    return d


def open_file(path):
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.run(["open", path])
        else:
            subprocess.run(["xdg-open", path])
    except Exception as e:
        messagebox.showerror("Error", f"Could not open file:\n{e}")


def parse_due(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date() if s else None
    except ValueError:
        return None


# =====================================================================
#  LOGIN
# =====================================================================
class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("StudyManager - Login")
        self.geometry("480x660")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self.user_id = None
        init_db()
        self._build()

    def _build(self):
        card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=22, width=370, height=540)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=38, pady=28)

        brand = ctk.CTkFrame(inner, fg_color="transparent")
        brand.pack(pady=(4, 4))
        ctk.CTkLabel(brand, text="", image=icon("logo", 40)).pack(side="left", padx=(0, 10))
        t = ctk.CTkFrame(brand, fg_color="transparent")
        t.pack(side="left", anchor="w")
        row = ctk.CTkFrame(t, fg_color="transparent")
        row.pack(anchor="w")
        ctk.CTkLabel(row, text="Study", font=font(24, "bold")).pack(side="left")
        ctk.CTkLabel(row, text="Manager", font=font(24, "bold"),
                     text_color=ACCENT).pack(side="left")
        ctk.CTkLabel(t, text="Learn  •  Plan  •  Achieve", font=font(11),
                     text_color=MUTED).pack(anchor="w")

        ctk.CTkLabel(inner, text="Welcome back",
                     font=font(17, "bold")).pack(pady=(18, 4))
        ctk.CTkLabel(inner, text="Apne account me login karo",
                     font=font(13), text_color=MUTED).pack(pady=(0, 20))

        self.username = ctk.CTkEntry(inner, placeholder_text="Username", height=46,
                                     font=font(14), corner_radius=12, fg_color=CARD_BG2,
                                     border_width=0)
        self.username.pack(fill="x", pady=(0, 12))
        self.password = ctk.CTkEntry(inner, placeholder_text="Password", show="•",
                                     height=46, font=font(14), corner_radius=12,
                                     fg_color=CARD_BG2, border_width=0)
        self.password.pack(fill="x", pady=(0, 8))

        self.error = ctk.CTkLabel(inner, text="", font=font(12), text_color=RED)
        self.error.pack(pady=(0, 6))

        ctk.CTkButton(inner, text="Login", height=46, corner_radius=12,
                      font=font(15, "bold"), fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=self._do_login).pack(fill="x", pady=(0, 10))
        ctk.CTkButton(inner, text="Create Account", height=46, corner_radius=12,
                      font=font(14), fg_color="transparent", border_width=1,
                      border_color="#2a3568", command=self._do_register).pack(fill="x")

        self.bind("<Return>", lambda e: self._do_login())
        self.username.focus()

    def _do_login(self):
        u, p = self.username.get().strip(), self.password.get()
        if not u or not p:
            self.error.configure(text="Username aur password likho.")
            return
        uid = authenticate(u, p)
        if uid:
            self.user_id = uid
            self.destroy()
        else:
            self.error.configure(text="Ghalat username ya password.")

    def _do_register(self):
        u, p = self.username.get().strip(), self.password.get()
        if not u or not p:
            self.error.configure(text="Pehle username aur password likho.")
            return
        try:
            create_user(u, p)
            self.error.configure(text="Account ban gaya! Ab Login dabao.", text_color=GREEN)
        except ValueError:
            self.error.configure(text="Ye username pehle se hai.", text_color=RED)

# =====================================================================
#  MAIN WINDOW (top bar + sidebar + content)
# =====================================================================
NAV_ITEMS = [
    ("Home", "home", "home"),
    ("My Courses", "courses", "courses"),
    ("Study Plan", "timetable", "timetable"),
    ("Assignments", "tasks", "tasks"),
    ("Notes", "notes", "file"),
    ("Performance", "performance", "chart"),
    ("Profile", "profile", "profile"),
    ("Settings", "settings", "gear"),
]


class MainWindow(ctk.CTk):
    def __init__(self, user_id):
        super().__init__()
        self.title("StudyManager")
        self.geometry("1180x720")
        self.minsize(1000, 620)
        self.configure(fg_color=BG)
        self.user_id = user_id

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.nav_buttons = {}
        self.pages = {}
        self.current = None
        self.current_key = None

        self._build_topbar()
        self._build_sidebar()

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=1, column=1, sticky="nsew", padx=20, pady=16)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.pages = {
            "home": HomePage(self.content, self),
            "courses": CoursesPage(self.content, self),
            "timetable": TimetablePage(self.content, self),
            "tasks": TasksPage(self.content, self),
            "notes": NotesPage(self.content, self),
            "performance": PerformancePage(self.content, self),
            "profile": ProfilePage(self.content, self),
            "settings": SettingsPage(self.content, self),
        }
        self.show_page("home")

    # ---------- top bar ----------
    def _build_topbar(self):
        bar = ctk.CTkFrame(self, fg_color=TOPBAR_BG, corner_radius=0, height=64)
        bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        bar.grid_propagate(False)

        brand = ctk.CTkFrame(bar, fg_color="transparent")
        brand.pack(side="left", padx=20)
        ctk.CTkLabel(brand, text="", image=icon("logo", 38)).pack(side="left", padx=(0, 10))
        t = ctk.CTkFrame(brand, fg_color="transparent")
        t.pack(side="left", anchor="w")
        row = ctk.CTkFrame(t, fg_color="transparent")
        row.pack(anchor="w")
        ctk.CTkLabel(row, text="Study", font=font(19, "bold")).pack(side="left")
        ctk.CTkLabel(row, text="Manager", font=font(19, "bold"),
                     text_color=ACCENT).pack(side="left")
        ctk.CTkLabel(t, text="Learn  •  Plan  •  Achieve", font=font(10),
                     text_color=MUTED).pack(anchor="w")

        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.pack(side="right", padx=20)
        ctk.CTkButton(right, text="", image=icon("bell", 20), width=40, height=40,
                      corner_radius=20, fg_color=CARD_BG, hover_color=CARD_BG2,
                      command=self._notifications).pack(side="left", padx=(0, 12))

        chip = ctk.CTkFrame(right, fg_color=CARD_BG, corner_radius=20)
        chip.pack(side="left")
        self.chip_avatar = ctk.CTkLabel(chip, text="")
        self.chip_avatar.pack(side="left", padx=(6, 8), pady=6)
        self.chip_name = ctk.CTkLabel(chip, text="", font=font(13, "bold"))
        self.chip_name.pack(side="left")
        ctk.CTkLabel(chip, text=" ⌄", font=font(13), text_color=MUTED).pack(
            side="left", padx=(4, 12))
        self._refresh_chip()

    def _refresh_chip(self):
        conn = get_connection()
        user = conn.execute("SELECT username FROM users WHERE id=?",
                            (self.user_id,)).fetchone()
        prof = conn.execute("SELECT name, photo_path FROM profiles WHERE user_id=?",
                            (self.user_id,)).fetchone()
        conn.close()
        name = (prof["name"] if prof and prof["name"] else
                (user["username"] if user else "User"))
        self.chip_name.configure(text=name)
        photo = prof["photo_path"] if prof else None
        self.chip_avatar.configure(
            image=ctk.CTkImage(circle_avatar(photo, 34, 0), size=(34, 34)))
        self._chip_photo = photo

    def _notifications(self):
        win = ctk.CTkToplevel(self)
        win.title("Notifications")
        win.geometry("380x420")
        win.transient(self)
        win.grab_set()
        ctk.CTkLabel(win, text="Notifications", font=font(17, "bold")).pack(
            anchor="w", padx=20, pady=(16, 8))
        body = ctk.CTkScrollableFrame(win, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        today = date.today()
        conn = get_connection()
        rows = conn.execute("""SELECT type, title, due_date FROM tasks
                               WHERE user_id=? AND status='pending' AND due_date IS NOT NULL
                               ORDER BY due_date""", (self.user_id,)).fetchall()
        conn.close()
        shown = 0
        for r in rows:
            d = parse_due(r["due_date"])
            if not d or d > today + timedelta(days=3):
                continue
            shown += 1
            urgent = d < today
            row = ctk.CTkFrame(body, fg_color=CARD_BG, corner_radius=10)
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text="●", text_color=RED if urgent else ORANGE,
                         font=font(16)).pack(side="left", padx=(12, 6), pady=10)
            tx = ctk.CTkFrame(row, fg_color="transparent")
            tx.pack(side="left", fill="x", expand=True, pady=8)
            ctk.CTkLabel(tx, text=r["title"], font=font(13, "bold"),
                         anchor="w").pack(anchor="w")
            ctk.CTkLabel(tx, text=("OVERDUE • " if urgent else "Due ") + str(d),
                         font=font(11), text_color=RED if urgent else ORANGE,
                         anchor="w").pack(anchor="w")
        if not shown:
            ctk.CTkLabel(body, text="Sab theek hai — koi urgent deadline nahi.",
                         text_color=MUTED, font=font(13)).pack(pady=20)

    # ---------- sidebar ----------
    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, fg_color=SIDEBAR_BG, corner_radius=0, width=210)
        sb.grid(row=1, column=0, sticky="nsew")
        sb.grid_propagate(False)
        holder = ctk.CTkFrame(sb, fg_color="transparent")
        holder.pack(fill="x", padx=12, pady=16)
        for label, key, ic in NAV_ITEMS:
            b = ctk.CTkButton(
                holder, text="  " + label, image=icon(ic, 20), anchor="w",
                height=46, corner_radius=12, font=font(14),
                fg_color="transparent", hover_color="#1a2450",
                text_color="#c9cede", command=lambda k=key: self.show_page(k))
            b.pack(fill="x", pady=3)
            self.nav_buttons[key] = b
        ctk.CTkFrame(sb, fg_color="transparent").pack(fill="both", expand=True)
        ctk.CTkButton(sb, text="  Logout", image=icon("logout", 18), anchor="w",
                      height=42, corner_radius=12, font=font(13),
                      fg_color="transparent", hover_color="#3a2030",
                      text_color="#e08a9b",
                      command=self._logout).pack(fill="x", padx=12, pady=16)

    def show_page(self, key):
        if self.current:
            self.current.grid_forget()
            self.nav_buttons[self.current_key].configure(fg_color="transparent")
        self.current_key = key
        self.current = self.pages[key]
        self.current.grid(row=0, column=0, sticky="nsew")
        self.nav_buttons[key].configure(fg_color=ACCENT)
        if hasattr(self.current, "refresh"):
            self.current.refresh()
        if key == "profile":
            self._refresh_chip()

    def _logout(self):
        self.destroy()
        main()


# =====================================================================
#  HOME (dashboard)
# =====================================================================
class HomePage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.user_id = app.user_id
        self._build()
        self.refresh()

    def _build(self):
        ctk.CTkLabel(self, text="Home", font=font(24, "bold")).pack(anchor="w")
        ctk.CTkLabel(self, text=date.today().strftime("%A, %d %B %Y"),
                     font=font(13), text_color=MUTED).pack(anchor="w", pady=(0, 14))

        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.pack(fill="x", pady=(0, 14))
        self.stat_vals = {}
        for label, color in [("Pending", ORANGE), ("Overdue", RED),
                             ("Due this week", ACCENT), ("Done", GREEN)]:
            box = ctk.CTkFrame(cards, fg_color=CARD_BG, corner_radius=16,
                               width=175, height=100)
            box.pack(side="left", padx=(0, 12))
            box.pack_propagate(False)
            ctk.CTkLabel(box, text=label, font=font(12), text_color=MUTED).pack(
                anchor="w", padx=16, pady=(14, 0))
            v = ctk.CTkLabel(box, text="0", font=font(32, "bold"), text_color=color)
            v.pack(anchor="w", padx=16)
            self.stat_vals[label] = v

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(top, text="Upcoming deadlines",
                     font=font(16, "bold")).pack(side="left")
        ctk.CTkButton(top, text="Go to Assignments", width=150, height=32,
                      corner_radius=10, fg_color=CARD_BG2, hover_color=ACCENT,
                      font=font(12),
                      command=lambda: self.app.show_page("tasks")).pack(side="right")

        self.lst = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.lst.pack(fill="both", expand=True)

    def refresh(self):
        for w in self.lst.winfo_children():
            w.destroy()
        conn = get_connection()
        rows = conn.execute("""SELECT t.id, t.type, t.title, t.due_date, t.status,
                                      c.name AS course
                               FROM tasks t LEFT JOIN courses c ON t.course_id=c.id
                               WHERE t.user_id=?""", (self.user_id,)).fetchall()
        conn.close()
        today = date.today()
        pending = overdue = due_week = done = 0
        items = []
        for r in rows:
            d = parse_due(r["due_date"])
            if r["status"] == "done":
                done += 1
                items.append(((2, d or date.max), r, GREEN, "Done"))
            else:
                pending += 1
                if d and d < today:
                    overdue += 1
                    items.append(((0, d), r, RED, f"OVERDUE • {d}"))
                elif d and d <= today + timedelta(days=7):
                    due_week += 1
                    items.append(((1, d), r, ORANGE, f"Due {d}"))
                else:
                    items.append(((1, d or date.max), r, MUTED,
                                  f"Due {d}" if d else "No due date"))
        items.sort(key=lambda x: x[0])
        for _, r, color, tag in items[:12]:
            row = ctk.CTkFrame(self.lst, fg_color=CARD_BG, corner_radius=12)
            row.pack(fill="x", pady=5)
            ctk.CTkLabel(row, text="●", font=font(18), text_color=color).pack(
                side="left", padx=(14, 8), pady=12)
            tx = ctk.CTkFrame(row, fg_color="transparent")
            tx.pack(side="left", fill="x", expand=True, pady=10)
            ctk.CTkLabel(tx, text=r["title"], font=font(14, "bold"),
                         anchor="w").pack(anchor="w")
            ctk.CTkLabel(tx, text=f'{r["type"]} • {r["course"] or "No course"}',
                         font=font(12), text_color=MUTED, anchor="w").pack(anchor="w")
            ctk.CTkLabel(row, text=tag, font=font(12, "bold"),
                         text_color=color).pack(side="right", padx=14)
        if not items:
            ctk.CTkLabel(self.lst, text="Koi task nahi — Assignments se add karo.",
                         text_color=MUTED, font=font(13)).pack(pady=20)
        self.stat_vals["Pending"].configure(text=str(pending))
        self.stat_vals["Overdue"].configure(text=str(overdue))
        self.stat_vals["Due this week"].configure(text=str(due_week))
        self.stat_vals["Done"].configure(text=str(done))

# =====================================================================
#  COURSES
# =====================================================================
class CoursesPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.user_id = app.user_id
        self.sel_course = None
        self.category = CATEGORIES[0]
        self._build()
        self.refresh()

    def _build(self):
        ctk.CTkLabel(self, text="My Courses", font=font(24, "bold")).pack(anchor="w")
        ctk.CTkLabel(self, text="Courses aur un ki files manage karo",
                     font=font(13), text_color=MUTED).pack(anchor="w", pady=(0, 14))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(body, fg_color=CARD_BG, corner_radius=16, width=250)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left.grid_propagate(False)
        ctk.CTkLabel(left, text="Courses", font=font(15, "bold")).pack(
            anchor="w", padx=16, pady=(16, 8))
        self.clist = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self.clist.pack(fill="both", expand=True, padx=8)
        brow = ctk.CTkFrame(left, fg_color="transparent")
        brow.pack(fill="x", padx=12, pady=12)
        ctk.CTkButton(brow, text="", image=icon("plus", 16), width=44, height=36,
                      corner_radius=10, fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=self._add_course).pack(side="left", padx=(0, 8))
        ctk.CTkButton(brow, text="", image=icon("trash", 16), width=44, height=36,
                      corner_radius=10, fg_color=CARD_BG2, hover_color=RED,
                      command=self._remove_course).pack(side="left")

        right = ctk.CTkFrame(body, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(2, weight=1)

        self.chead = ctk.CTkLabel(right, text="", font=font(17, "bold"))
        self.chead.grid(row=0, column=0, sticky="w", pady=(0, 8))

        tools = ctk.CTkFrame(right, fg_color="transparent")
        tools.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        self.seg = ctk.CTkSegmentedButton(tools, values=CATEGORIES,
                                          selected_color=ACCENT,
                                          selected_hover_color=ACCENT_HOVER,
                                          command=self._set_cat)
        self.seg.set(self.category)
        self.seg.pack(side="left")
        ctk.CTkButton(tools, text="  Upload", image=icon("upload", 16), height=36,
                      corner_radius=10, fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      font=font(13, "bold"), command=self._upload).pack(side="right")

        self.flist = ctk.CTkScrollableFrame(right, fg_color=CARD_BG, corner_radius=16)
        self.flist.grid(row=2, column=0, sticky="nsew")

    def _set_cat(self, v):
        self.category = v
        self._refresh_files()

    def _courses(self):
        conn = get_connection()
        rows = conn.execute("SELECT id, name FROM courses WHERE user_id=? ORDER BY name",
                            (self.user_id,)).fetchall()
        conn.close()
        return [(r["id"], r["name"]) for r in rows]

    def refresh(self):
        for w in self.clist.winfo_children():
            w.destroy()
        courses = self._courses()
        if self.sel_course not in [c[0] for c in courses]:
            self.sel_course = courses[0][0] if courses else None
        for cid, name in courses:
            b = ctk.CTkButton(self.clist, text=name, anchor="w", height=42,
                              corner_radius=10, font=font(13),
                              fg_color=ACCENT if cid == self.sel_course else "transparent",
                              hover_color="#1a2450",
                              command=lambda c=cid: self._select(c))
            b.pack(fill="x", pady=3)
        self._refresh_head()
        self._refresh_files()

    def _select(self, cid):
        self.sel_course = cid
        self.refresh()

    def _refresh_head(self):
        if self.sel_course:
            conn = get_connection()
            r = conn.execute("SELECT name FROM courses WHERE id=?",
                             (self.sel_course,)).fetchone()
            conn.close()
            self.chead.configure(text=r["name"] if r else "")
        else:
            self.chead.configure(text="Koi course select karo")

    def _refresh_files(self):
        for w in self.flist.winfo_children():
            w.destroy()
        if not self.sel_course:
            return
        conn = get_connection()
        rows = conn.execute("""SELECT id, file_name, file_path FROM course_files
                               WHERE course_id=? AND category=? ORDER BY uploaded_at DESC""",
                            (self.sel_course, self.category)).fetchall()
        conn.close()
        for r in rows:
            row = ctk.CTkFrame(self.flist, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=5)
            ctk.CTkLabel(row, text="", image=icon("file", 20)).pack(
                side="left", padx=(4, 10))
            ctk.CTkLabel(row, text=r["file_name"], font=font(13)).pack(
                side="left", fill="x", expand=True)
            ctk.CTkButton(row, text="Open", width=66, height=30, corner_radius=8,
                          fg_color=CARD_BG2, hover_color=ACCENT, font=font(12),
                          command=lambda p=r["file_path"]: open_file(p)).pack(
                side="right", padx=3)
            ctk.CTkButton(row, text="", image=icon("trash", 14), width=36, height=30,
                          corner_radius=8, fg_color="transparent", hover_color=RED,
                          command=lambda i=r["id"], p=r["file_path"]:
                          self._del_file(i, p)).pack(side="right", padx=3)
        if not rows:
            ctk.CTkLabel(self.flist, text="Is folder me koi file nahi.",
                         text_color=MUTED, font=font(12)).pack(pady=18)

    def _add_course(self):
        win = ctk.CTkToplevel(self)
        win.title("Add Course")
        win.geometry("340x260")
        win.resizable(False, False)
        win.transient(self.winfo_toplevel())
        win.grab_set()
        frm = ctk.CTkFrame(win, fg_color="transparent")
        frm.pack(fill="both", expand=True, padx=24, pady=20)
        ctk.CTkLabel(frm, text="New Course", font=font(17, "bold")).pack(
            anchor="w", pady=(0, 10))
        ctk.CTkLabel(frm, text="Course name", font=font(12), text_color=MUTED).pack(anchor="w")
        n_e = ctk.CTkEntry(frm, placeholder_text="e.g. Data Structures")
        n_e.pack(fill="x", pady=(2, 10))
        ctk.CTkLabel(frm, text="Course code (optional)", font=font(12),
                     text_color=MUTED).pack(anchor="w")
        c_e = ctk.CTkEntry(frm, placeholder_text="e.g. CS201")
        c_e.pack(fill="x", pady=(2, 0))

        def save():
            if not n_e.get().strip():
                return
            conn = get_connection()
            cur = conn.execute(
                "INSERT INTO courses (user_id, name, code, created_at) VALUES (?,?,?,?)",
                (self.user_id, n_e.get().strip(), c_e.get().strip(),
                 datetime.now().isoformat()))
            self.sel_course = cur.lastrowid
            conn.commit(); conn.close()
            win.destroy()
            self.refresh()
        ctk.CTkButton(frm, text="Add", fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      height=40, corner_radius=10, font=font(14, "bold"),
                      command=save).pack(fill="x", pady=(18, 0))

    def _remove_course(self):
        if not self.sel_course:
            return
        if messagebox.askyesno("Confirm", "Ye course aur is ki sari files delete ho jayengi."):
            conn = get_connection()
            conn.execute("DELETE FROM courses WHERE id=?", (self.sel_course,))
            conn.commit(); conn.close()
            self.sel_course = None
            self.refresh()

    def _upload(self):
        if not self.sel_course:
            messagebox.showwarning("No course", "Pehle koi course select karo.")
            return
        paths = filedialog.askopenfilenames(title="Choose files")
        if not paths:
            return
        dest_dir = os.path.join(user_data_dir(self.user_id),
                                f"course_{self.sel_course}", self.category)
        os.makedirs(dest_dir, exist_ok=True)
        conn = get_connection()
        for p in paths:
            fname = os.path.basename(p)
            dest = os.path.join(dest_dir, fname)
            base, ext = os.path.splitext(fname)
            i = 1
            while os.path.exists(dest):
                dest = os.path.join(dest_dir, f"{base}_{i}{ext}")
                i += 1
            shutil.copy2(p, dest)
            conn.execute("""INSERT INTO course_files (course_id, category, file_name, file_path, uploaded_at)
                            VALUES (?,?,?,?,?)""",
                         (self.sel_course, self.category, os.path.basename(dest), dest,
                          datetime.now().isoformat()))
        conn.commit(); conn.close()
        self._refresh_files()

    def _del_file(self, fid, fpath):
        if messagebox.askyesno("Confirm", "Delete this file?"):
            try:
                os.remove(fpath)
            except OSError:
                pass
            conn = get_connection()
            conn.execute("DELETE FROM course_files WHERE id=?", (fid,))
            conn.commit(); conn.close()
            self._refresh_files()


# =====================================================================
#  ASSIGNMENTS (tasks)
# =====================================================================
class TasksPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.user_id = app.user_id
        self.filter = "All"
        self._build()
        self.refresh()

    def _build(self):
        ctk.CTkLabel(self, text="Assignments", font=font(24, "bold")).pack(anchor="w")
        ctk.CTkLabel(self, text="Assignments • Presentations • Projects",
                     font=font(13), text_color=MUTED).pack(anchor="w", pady=(0, 14))
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", pady=(0, 10))
        ctk.CTkButton(bar, text="  New", image=icon("plus", 16), height=38,
                      corner_radius=10, fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      font=font(13, "bold"), command=self._add_dialog).pack(side="left")
        self.fcombo = ctk.CTkComboBox(bar, values=["All", "Assignment", "Presentation",
                                                   "Project", "pending", "done"],
                                      width=150, height=38, corner_radius=10,
                                      command=lambda v: self._set_filter(v))
        self.fcombo.set("All")
        self.fcombo.pack(side="right")
        self.lst = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.lst.pack(fill="both", expand=True)

    def _set_filter(self, v):
        self.filter = v
        self.refresh()

    def _rows(self):
        q = """SELECT t.id, t.type, t.title, t.due_date, t.status, c.name AS course
               FROM tasks t LEFT JOIN courses c ON t.course_id=c.id
               WHERE t.user_id=?"""
        p = [self.user_id]
        f = self.filter
        if f in ("Assignment", "Presentation", "Project"):
            q += " AND t.type=?"; p.append(f)
        elif f in ("pending", "done"):
            q += " AND t.status=?"; p.append(f)
        q += " ORDER BY t.due_date"
        conn = get_connection()
        rows = conn.execute(q, p).fetchall()
        conn.close()
        return rows

    def refresh(self):
        for w in self.lst.winfo_children():
            w.destroy()
        for r in self._rows():
            self._row(r)
        if not self.lst.winfo_children():
            ctk.CTkLabel(self.lst, text="Koi task nahi.", text_color=MUTED,
                         font=font(13)).pack(pady=20)

    def _pill(self, parent, text, color):
        return ctk.CTkLabel(parent, text=text, font=font(11, "bold"),
                            fg_color=color, text_color="white",
                            corner_radius=8, padx=10, pady=3)

    def _row(self, r):
        card = ctk.CTkFrame(self.lst, fg_color=CARD_BG, corner_radius=14)
        card.pack(fill="x", pady=5)
        left = ctk.CTkFrame(card, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True, padx=14, pady=10)
        top = ctk.CTkFrame(left, fg_color="transparent")
        top.pack(fill="x")
        self._pill(top, r["type"], ACCENT).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(top, text=r["title"], font=font(14, "bold")).pack(side="left")
        ctk.CTkLabel(left, text=f'{r["course"] or "No course"} • Due: {r["due_date"] or "-"}',
                     font=font(12), text_color=MUTED).pack(anchor="w", pady=(4, 0))
        acts = ctk.CTkFrame(card, fg_color="transparent")
        acts.pack(side="right", padx=12)
        st = r["status"]
        self._pill(acts, "Done" if st == "done" else "Pending",
                   GREEN if st == "done" else ORANGE).pack(side="left", padx=(0, 8))
        tid = r["id"]
        if st != "done":
            ctk.CTkButton(acts, text="", image=icon("check", 16), width=36, height=32,
                          corner_radius=8, fg_color=CARD_BG2, hover_color=GREEN,
                          command=lambda: self._mark_done(tid)).pack(side="left", padx=2)
            ctk.CTkButton(acts, text="", image=icon("upload", 16), width=36, height=32,
                          corner_radius=8, fg_color=CARD_BG2, hover_color=ACCENT,
                          command=lambda: self._upload_done(tid)).pack(side="left", padx=2)
        ctk.CTkButton(acts, text="", image=icon("trash", 16), width=36, height=32,
                      corner_radius=8, fg_color=CARD_BG2, hover_color=RED,
                      command=lambda: self._delete(tid)).pack(side="left", padx=2)

    def _mark_done(self, tid):
        conn = get_connection()
        conn.execute("UPDATE tasks SET status='done', completed_at=? WHERE id=?",
                     (datetime.now().isoformat(), tid))
        conn.commit(); conn.close()
        self.refresh()

    def _courses(self):
        conn = get_connection()
        rows = conn.execute("SELECT id, name FROM courses WHERE user_id=? ORDER BY name",
                            (self.user_id,)).fetchall()
        conn.close()
        return [(r["id"], r["name"]) for r in rows]

    def _pick_course(self):
        courses = self._courses()
        if not courses:
            messagebox.showwarning("No courses", "Pehle My Courses me koi course add karo.")
            return None
        win = ctk.CTkToplevel(self)
        win.title("Course select karo")
        win.geometry("340x190")
        win.resizable(False, False)
        win.transient(self.winfo_toplevel())
        win.grab_set()
        ctk.CTkLabel(win, text="Ye task kis course ka hai?",
                     font=font(14, "bold")).pack(padx=20, pady=(20, 10))
        var = ctk.StringVar(value=courses[0][1])
        ctk.CTkComboBox(win, variable=var, values=[n for _, n in courses],
                        state="readonly", width=280).pack(padx=20)
        out = {"id": None}
        def ok():
            for cid, n in courses:
                if n == var.get():
                    out["id"] = cid
            win.destroy()
        ctk.CTkButton(win, text="OK", fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=ok).pack(pady=18)
        win.wait_window()
        return out["id"]

    def _upload_done(self, tid):
        conn = get_connection()
        task = conn.execute("SELECT * FROM tasks WHERE id=?", (tid,)).fetchone()
        conn.close()
        if task is None:
            return
        course_id = task["course_id"]
        if course_id is None:
            course_id = self._pick_course()
            if course_id is None:
                return
            conn = get_connection()
            conn.execute("UPDATE tasks SET course_id=? WHERE id=?", (course_id, tid))
            conn.commit(); conn.close()
        p = filedialog.askopenfilename(title="Choose file to upload")
        if not p:
            return
        dest_dir = os.path.join(user_data_dir(self.user_id), "task_uploads")
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, f"task_{tid}_" + os.path.basename(p))
        shutil.copy2(p, dest)
        category = task["type"]
        course_dir = os.path.join(user_data_dir(self.user_id), f"course_{course_id}", category)
        os.makedirs(course_dir, exist_ok=True)
        fname = os.path.basename(p)
        cdest = os.path.join(course_dir, fname)
        base, ext = os.path.splitext(fname)
        i = 1
        while os.path.exists(cdest):
            cdest = os.path.join(course_dir, f"{base}_{i}{ext}")
            i += 1
        shutil.copy2(p, cdest)
        conn = get_connection()
        conn.execute("""INSERT INTO course_files (course_id, category, file_name, file_path, uploaded_at)
                        VALUES (?,?,?,?,?)""",
                     (course_id, category, os.path.basename(cdest), cdest,
                      datetime.now().isoformat()))
        conn.execute("UPDATE tasks SET status='done', file_path=?, completed_at=? WHERE id=?",
                     (dest, datetime.now().isoformat(), tid))
        conn.commit(); conn.close()
        self.refresh()
        messagebox.showinfo("Done", "File upload ho gayi, task done, aur course ke folder me bhi save ho gayi.")

    def _delete(self, tid):
        if messagebox.askyesno("Confirm", "Delete this task?"):
            conn = get_connection()
            conn.execute("DELETE FROM tasks WHERE id=?", (tid,))
            conn.commit(); conn.close()
            self.refresh()

    def _add_dialog(self):
        win = ctk.CTkToplevel(self)
        win.title("New Task")
        win.geometry("400x540")
        win.resizable(False, False)
        win.transient(self.winfo_toplevel())
        win.grab_set()
        frm = ctk.CTkFrame(win, fg_color="transparent")
        frm.pack(fill="both", expand=True, padx=24, pady=20)
        ctk.CTkLabel(frm, text="New Task", font=font(18, "bold")).pack(
            anchor="w", pady=(0, 12))

        def labeled(label):
            ctk.CTkLabel(frm, text=label, font=font(12), text_color=MUTED).pack(
                anchor="w", pady=(8, 2))
        labeled("Type")
        t_var = ctk.StringVar(value="Assignment")
        ctk.CTkComboBox(frm, variable=t_var, values=TASK_TYPES, state="readonly").pack(fill="x")
        labeled("Title")
        title_e = ctk.CTkEntry(frm, placeholder_text="e.g. Lab report 3")
        title_e.pack(fill="x")
        labeled("Course")
        courses = self._courses()
        c_var = ctk.StringVar(value="No course")
        ctk.CTkComboBox(frm, variable=c_var,
                        values=["No course"] + [n for _, n in courses],
                        state="readonly").pack(fill="x")
        labeled("Due Date (YYYY-MM-DD)")
        due_e = ctk.CTkEntry(frm, placeholder_text="2026-10-20")
        due_e.pack(fill="x")
        labeled("Description")
        desc_e = ctk.CTkEntry(frm, placeholder_text="Optional")
        desc_e.pack(fill="x")

        def save():
            title = title_e.get().strip()
            if not title:
                messagebox.showwarning("Input needed", "Title zaroori hai.", parent=win)
                return
            cid = None
            if c_var.get() != "No course":
                for i, n in courses:
                    if n == c_var.get():
                        cid = i
            if due_e.get().strip() and not parse_due(due_e.get().strip()):
                messagebox.showwarning("Input needed", "Date YYYY-MM-DD me likho.", parent=win)
                return
            conn = get_connection()
            conn.execute("""INSERT INTO tasks (user_id, course_id, type, title, description,
                            due_date, status, created_at)
                            VALUES (?,?,?,?,?,?, 'pending', ?)""",
                         (self.user_id, cid, t_var.get(), title, desc_e.get().strip(),
                          due_e.get().strip() or None, datetime.now().isoformat()))
            conn.commit(); conn.close()
            win.destroy()
            self.refresh()
        ctk.CTkButton(frm, text="Save Task", fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      height=42, corner_radius=10, font=font(14, "bold"),
                      command=save).pack(fill="x", pady=(20, 0))


# =====================================================================
#  STUDY PLAN (timetable)
# =====================================================================
class TimetablePage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.user_id = app.user_id
        self.sel = None
        self._build()
        self.refresh()

    def _build(self):
        ctk.CTkLabel(self, text="Study Plan", font=font(24, "bold")).pack(anchor="w")
        ctk.CTkLabel(self, text="Hafte ka class schedule",
                     font=font(13), text_color=MUTED).pack(anchor="w", pady=(0, 14))
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", pady=(0, 10))
        ctk.CTkButton(bar, text="  Add Class", image=icon("plus", 16), height=38,
                      corner_radius=10, fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      font=font(13, "bold"), command=self._add).pack(side="left")
        ctk.CTkButton(bar, text="  Remove", image=icon("trash", 16), height=38,
                      corner_radius=10, fg_color=CARD_BG2, hover_color=RED,
                      font=font(13), command=self._remove).pack(side="left", padx=(8, 0))
        self.lst = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.lst.pack(fill="both", expand=True)

    def _rows(self):
        conn = get_connection()
        rows = conn.execute("SELECT * FROM timetable WHERE user_id=?",
                            (self.user_id,)).fetchall()
        conn.close()
        order = {d: i for i, d in enumerate(DAYS)}
        return sorted(rows, key=lambda r: (order.get(r["day"], 99), r["start_time"]))

    def refresh(self):
        self.sel = None
        for w in self.lst.winfo_children():
            w.destroy()
        last_day = None
        for r in self._rows():
            if r["day"] != last_day:
                last_day = r["day"]
                ctk.CTkLabel(self.lst, text=last_day, font=font(15, "bold"),
                             text_color=ACCENT).pack(anchor="w", pady=(10, 4), padx=4)
            card = ctk.CTkFrame(self.lst, fg_color=CARD_BG, corner_radius=12)
            card.pack(fill="x", pady=4)
            ctk.CTkLabel(card, text=f'{r["start_time"]} – {r["end_time"]}',
                         font=font(12, "bold"), fg_color=ACCENT, text_color="white",
                         corner_radius=8, padx=10, pady=5).pack(side="left", padx=12, pady=10)
            ctk.CTkLabel(card, text=r["subject"], font=font(14, "bold")).pack(
                side="left", padx=(4, 10))
            if r["room"]:
                ctk.CTkLabel(card, text=f'Room {r["room"]}', font=font(12),
                             text_color=MUTED).pack(side="right", padx=14)
            for w in (card,) + tuple(card.winfo_children()):
                w.bind("<Button-1>", lambda e, i=r["id"]: setattr(self, "sel", i))
        if not self.lst.winfo_children():
            ctk.CTkLabel(self.lst, text="Koi class nahi — Add Class se shuru karo.",
                         text_color=MUTED, font=font(13)).pack(pady=20)

    def _add(self):
        win = ctk.CTkToplevel(self)
        win.title("Add Class")
        win.geometry("360x480")
        win.resizable(False, False)
        win.transient(self.winfo_toplevel())
        win.grab_set()
        frm = ctk.CTkFrame(win, fg_color="transparent")
        frm.pack(fill="both", expand=True, padx=24, pady=20)
        ctk.CTkLabel(frm, text="New Class", font=font(17, "bold")).pack(
            anchor="w", pady=(0, 8))

        def labeled(t):
            ctk.CTkLabel(frm, text=t, font=font(12), text_color=MUTED).pack(
                anchor="w", pady=(8, 2))
        labeled("Day")
        d_var = ctk.StringVar(value=DAYS[0])
        ctk.CTkComboBox(frm, variable=d_var, values=DAYS, state="readonly").pack(fill="x")
        labeled("Start Time (HH:MM)")
        s_e = ctk.CTkEntry(frm, placeholder_text="09:00")
        s_e.pack(fill="x")
        labeled("End Time (HH:MM)")
        e_e = ctk.CTkEntry(frm, placeholder_text="10:30")
        e_e.pack(fill="x")
        labeled("Subject")
        sub_e = ctk.CTkEntry(frm, placeholder_text="e.g. Data Structures")
        sub_e.pack(fill="x")
        labeled("Room (optional)")
        r_e = ctk.CTkEntry(frm, placeholder_text="e.g. R-101")
        r_e.pack(fill="x")

        def save():
            if not sub_e.get().strip() or not s_e.get().strip() or not e_e.get().strip():
                messagebox.showwarning("Input needed", "Day, time aur subject zaroori hain.",
                                       parent=win)
                return
            conn = get_connection()
            conn.execute("""INSERT INTO timetable (user_id, day, start_time, end_time, subject, room)
                            VALUES (?,?,?,?,?,?)""",
                         (self.user_id, d_var.get(), s_e.get().strip(), e_e.get().strip(),
                          sub_e.get().strip(), r_e.get().strip() or None))
            conn.commit(); conn.close()
            win.destroy()
            self.refresh()
        ctk.CTkButton(frm, text="Save", fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      height=42, corner_radius=10, font=font(14, "bold"),
                      command=save).pack(fill="x", pady=(18, 0))

    def _remove(self):
        if not self.sel:
            messagebox.showwarning("No selection", "Pehle koi class select karo.")
            return
        if messagebox.askyesno("Confirm", "Remove this class?"):
            conn = get_connection()
            conn.execute("DELETE FROM timetable WHERE id=?", (self.sel,))
            conn.commit(); conn.close()
            self.refresh()


# =====================================================================
#  NOTES (all notes files across courses)
# =====================================================================
class NotesPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.user_id = app.user_id
        self._build()
        self.refresh()

    def _build(self):
        ctk.CTkLabel(self, text="Notes", font=font(24, "bold")).pack(anchor="w")
        ctk.CTkLabel(self, text="Sab courses ke notes ek jagah",
                     font=font(13), text_color=MUTED).pack(anchor="w", pady=(0, 14))
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", pady=(0, 12))
        self.q = ctk.CTkEntry(bar, placeholder_text="Notes dhoondo…",
                              height=42, corner_radius=12, font=font(13))
        self.q.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.q.bind("<Return>", lambda e: self.refresh())
        ctk.CTkButton(bar, text="  Search", image=icon("search", 16), height=42,
                      corner_radius=12, fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      font=font(13, "bold"), command=self.refresh).pack(side="right")
        self.lst = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.lst.pack(fill="both", expand=True)

    def refresh(self):
        for w in self.lst.winfo_children():
            w.destroy()
        q = self.q.get().strip() if hasattr(self, "q") else ""
        sql = """SELECT cf.file_name, cf.file_path, c.name AS course
                 FROM course_files cf JOIN courses c ON cf.course_id=c.id
                 WHERE c.user_id=? AND cf.category='Notes'"""
        params = [self.user_id]
        if q:
            sql += " AND cf.file_name LIKE ?"
            params.append(f"%{q}%")
        sql += " ORDER BY c.name, cf.file_name"
        conn = get_connection()
        rows = conn.execute(sql, params).fetchall()
        conn.close()
        for r in rows:
            row = ctk.CTkFrame(self.lst, fg_color=CARD_BG, corner_radius=12)
            row.pack(fill="x", pady=5)
            ctk.CTkLabel(row, text="", image=icon("file", 22)).pack(
                side="left", padx=(14, 10), pady=10)
            tx = ctk.CTkFrame(row, fg_color="transparent")
            tx.pack(side="left", fill="x", expand=True, pady=8)
            ctk.CTkLabel(tx, text=r["file_name"], font=font(13, "bold"),
                         anchor="w").pack(anchor="w")
            ctk.CTkLabel(tx, text=r["course"], font=font(12), text_color=MUTED,
                         anchor="w").pack(anchor="w")
            ctk.CTkButton(row, text="Open", width=70, height=32, corner_radius=8,
                          fg_color=CARD_BG2, hover_color=ACCENT, font=font(12),
                          command=lambda p=r["file_path"]: open_file(p)).pack(
                side="right", padx=12)
        if not rows:
            ctk.CTkLabel(self.lst, text="Koi notes nahi mile.",
                         text_color=MUTED, font=font(13)).pack(pady=20)

# =====================================================================
#  PERFORMANCE
# =====================================================================
class PerformancePage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.user_id = app.user_id
        self._build()
        self.refresh()

    def _build(self):
        ctk.CTkLabel(self, text="Performance", font=font(24, "bold")).pack(anchor="w")
        ctk.CTkLabel(self, text="Tumhari progress ek nazar me",
                     font=font(13), text_color=MUTED).pack(anchor="w", pady=(0, 14))
        self.cards = ctk.CTkFrame(self, fg_color="transparent")
        self.cards.pack(fill="x", pady=(0, 14))
        self.bytype = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=16)
        self.bytype.pack(fill="x", pady=(0, 12))

    def _stat(self, parent, label, value, color):
        box = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=16, width=175, height=100)
        box.pack(side="left", padx=(0, 12))
        box.pack_propagate(False)
        ctk.CTkLabel(box, text=label, font=font(12), text_color=MUTED).pack(
            anchor="w", padx=16, pady=(14, 0))
        ctk.CTkLabel(box, text=str(value), font=font(30, "bold"),
                     text_color=color).pack(anchor="w", padx=16)
        return box

    def refresh(self):
        for w in self.cards.winfo_children():
            w.destroy()
        for w in self.bytype.winfo_children():
            w.destroy()
        conn = get_connection()
        total = conn.execute("SELECT COUNT(*) c FROM tasks WHERE user_id=?",
                             (self.user_id,)).fetchone()["c"]
        done = conn.execute("SELECT COUNT(*) c FROM tasks WHERE user_id=? AND status='done'",
                            (self.user_id,)).fetchone()["c"]
        files = conn.execute("""SELECT COUNT(*) c FROM course_files cf
                                JOIN courses c2 ON cf.course_id=c2.id
                                WHERE c2.user_id=?""", (self.user_id,)).fetchone()["c"]
        courses = conn.execute("SELECT COUNT(*) c FROM courses WHERE user_id=?",
                               (self.user_id,)).fetchone()["c"]
        conn.close()
        pct = round(done / total * 100) if total else 0
        self._stat(self.cards, "Completion", f"{pct}%", ACCENT)
        self._stat(self.cards, "Tasks Done", f"{done}/{total}", GREEN)
        self._stat(self.cards, "Files", files, ORANGE)
        self._stat(self.cards, "Courses", courses, PURPLE)

        ctk.CTkLabel(self.bytype, text="Completion by type", font=font(15, "bold")).pack(
            anchor="w", padx=18, pady=(14, 6))
        conn = get_connection()
        for t in TASK_TYPES:
            tot = conn.execute("SELECT COUNT(*) c FROM tasks WHERE user_id=? AND type=?",
                               (self.user_id, t)).fetchone()["c"]
            dn = conn.execute("SELECT COUNT(*) c FROM tasks WHERE user_id=? AND type=? AND status='done'",
                              (self.user_id, t)).fetchone()["c"]
            row = ctk.CTkFrame(self.bytype, fg_color="transparent")
            row.pack(fill="x", padx=18, pady=6)
            ctk.CTkLabel(row, text=t, font=font(13), width=110).pack(side="left")
            bar = ctk.CTkProgressBar(row, height=12, corner_radius=6,
                                     progress_color=ACCENT, fg_color=CARD_BG2)
            bar.pack(side="left", fill="x", expand=True, padx=10)
            bar.set(dn / tot if tot else 0)
            ctk.CTkLabel(row, text=f"{dn}/{tot}", font=font(12),
                         text_color=MUTED, width=60).pack(side="left")
        conn.close()
        ctk.CTkFrame(self.bytype, fg_color="transparent", height=8).pack()


# =====================================================================
#  PROFILE (matches design mockup)
# =====================================================================
class ProfilePage(ctk.CTkFrame):
    FIELDS = [
        ("Registration No", "registration_number", "profile", "#2f7bff"),
        ("Department", "department", "bank", "#12b5a5"),
        ("Degree", "degree", "logo", "#8b5cf6"),
        ("Semester", "semester", "timetable", "#f59e0b"),
        ("Section", "section", "courses", "#2f7bff"),
        ("University Name", "university", "bank", "#2f7bff"),
    ]

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.user_id = app.user_id
        self.photo_path = None
        self._cover_img = ctk.CTkImage(cover_with_quote(), size=(880, 190))
        self._goals_img = ctk.CTkImage(goals_with_text(), size=(880, 170))
        self._build()
        self.refresh()

    def _build(self):
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        # ---- cover ----
        ctk.CTkLabel(self.scroll, text="", image=self._cover_img).pack(fill="x")

        # ---- avatar + name row ----
        head = ctk.CTkFrame(self.scroll, fg_color="transparent")
        head.pack(fill="x", padx=24, pady=(14, 6))
        av_wrap = ctk.CTkFrame(head, fg_color="transparent", width=140, height=140)
        av_wrap.pack(side="left", padx=(0, 18))
        av_wrap.pack_propagate(False)
        self.avatar = ctk.CTkLabel(av_wrap, text="")
        self.avatar.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkButton(av_wrap, text="", image=icon("camera", 16), width=38, height=38,
                      corner_radius=19, fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=self._photo).place(relx=0.88, rely=0.88, anchor="center")

        tx = ctk.CTkFrame(head, fg_color="transparent")
        tx.pack(side="left", anchor="w")
        self.pname = ctk.CTkLabel(tx, text="", font=font(26, "bold"))
        self.pname.pack(anchor="w")
        sub = ctk.CTkFrame(tx, fg_color="transparent")
        sub.pack(anchor="w", pady=(6, 0))
        ctk.CTkLabel(sub, text="", image=icon("profile", 16)).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(sub, text="Student", font=font(13), text_color=MUTED).pack(side="left")
        ctk.CTkLabel(sub, text="Active", font=font(12, "bold"), text_color="white",
                     fg_color=ACCENT, corner_radius=10, padx=14, pady=4).pack(
            side="left", padx=(14, 0))

        ctk.CTkButton(head, text="Edit Profile", height=38, corner_radius=10,
                      fg_color=CARD_BG2, hover_color=ACCENT, font=font(13, "bold"),
                      command=self._edit_dialog).pack(side="right", anchor="s")

        # ---- info cards ----
        self.cards_holder = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.cards_holder.pack(fill="x", padx=16, pady=10)
        self.card_vals = {}

        # ---- goals banner ----
        ctk.CTkLabel(self.scroll, text="", image=self._goals_img).pack(
            fill="x", padx=16, pady=(6, 16))

    def _info_card(self, parent, row, col, label, key, ic, color, full=False):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=16)
        card.grid(row=row, column=col, columnspan=2 if full else 1,
                  sticky="ew", padx=8, pady=8)
        chip = ctk.CTkLabel(card, text="", image=icon(ic, 22), fg_color=color,
                            corner_radius=12, width=52, height=52)
        chip.pack(side="left", padx=14, pady=14)
        tx = ctk.CTkFrame(card, fg_color="transparent")
        tx.pack(side="left", fill="x", expand=True, pady=10)
        ctk.CTkLabel(tx, text=label + ":", font=font(12), text_color=MUTED,
                     anchor="w").pack(anchor="w")
        v = ctk.CTkLabel(tx, text="—", font=font(15, "bold"), anchor="w")
        v.pack(anchor="w")
        self.card_vals[key] = v

    def refresh(self):
        for w in self.cards_holder.winfo_children():
            w.destroy()
        self.card_vals = {}
        self.cards_holder.grid_columnconfigure((0, 1), weight=1)
        conn = get_connection()
        prof = conn.execute("SELECT * FROM profiles WHERE user_id=?",
                            (self.user_id,)).fetchone()
        user = conn.execute("SELECT username FROM users WHERE id=?",
                            (self.user_id,)).fetchone()
        conn.close()
        prof = dict(prof) if prof else {}
        name = prof.get("name") or (user["username"] if user else "User")
        self.pname.configure(text=name)
        photo = prof.get("photo_path")
        self.photo_path = photo
        self.avatar.configure(
            image=ctk.CTkImage(circle_avatar(photo, 128), size=(128, 128)))

        fields = self.FIELDS
        for i, (label, key, ic, color) in enumerate(fields):
            full = (i == len(fields) - 1)  # university spans full width
            self._info_card(self.cards_holder, i // 2, (i % 2), label, key, ic,
                            color, full=full)
            val = prof.get(key) or "—"
            self.card_vals[key].configure(text=val)
        self._prof = prof

    def _photo(self):
        p = filedialog.askopenfilename(title="Choose profile photo",
                                       filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.bmp")])
        if p:
            dest = os.path.join(user_data_dir(self.user_id),
                                "profile_photo" + os.path.splitext(p)[1])
            shutil.copy2(p, dest)
            conn = get_connection()
            conn.execute("UPDATE profiles SET photo_path=? WHERE user_id=?",
                         (dest, self.user_id))
            conn.commit(); conn.close()
            self.refresh()
            self.app._refresh_chip()

    def _edit_dialog(self):
        prof = getattr(self, "_prof", {})
        win = ctk.CTkToplevel(self)
        win.title("Edit Profile")
        win.geometry("440x560")
        win.resizable(False, False)
        win.transient(self.winfo_toplevel())
        win.grab_set()
        frm = ctk.CTkScrollableFrame(win, fg_color="transparent")
        frm.pack(fill="both", expand=True, padx=20, pady=16)
        ctk.CTkLabel(frm, text="Edit Profile", font=font(17, "bold")).pack(
            anchor="w", pady=(0, 8))
        entries = {}
        labels = [("Full Name", "name"), ("Registration No", "registration_number"),
                  ("Department", "department"), ("Degree", "degree"),
                  ("Semester", "semester"), ("Section", "section"),
                  ("University Name", "university")]
        for lab, key in labels:
            ctk.CTkLabel(frm, text=lab, font=font(12), text_color=MUTED).pack(
                anchor="w", pady=(8, 2))
            e = ctk.CTkEntry(frm, height=38, corner_radius=10, font=font(13))
            e.insert(0, prof.get(key) or "")
            e.pack(fill="x")
            entries[key] = e

        def save():
            conn = get_connection()
            conn.execute("""UPDATE profiles SET name=?, registration_number=?, department=?,
                            degree=?, semester=?, section=?, university=? WHERE user_id=?""",
                         (entries["name"].get().strip(),
                          entries["registration_number"].get().strip(),
                          entries["department"].get().strip(),
                          entries["degree"].get().strip(),
                          entries["semester"].get().strip(),
                          entries["section"].get().strip(),
                          entries["university"].get().strip(),
                          self.user_id))
            conn.commit(); conn.close()
            win.destroy()
            self.refresh()
            self.app._refresh_chip()
            messagebox.showinfo("Saved", "Profile update ho gayi.")
        ctk.CTkButton(frm, text="Save", fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      height=42, corner_radius=10, font=font(14, "bold"),
                      command=save).pack(fill="x", pady=(18, 0))


# =====================================================================
#  SETTINGS
# =====================================================================
class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.user_id = app.user_id
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Settings", font=font(24, "bold")).pack(anchor="w")
        ctk.CTkLabel(self, text="Account aur app settings",
                     font=font(13), text_color=MUTED).pack(anchor="w", pady=(0, 14))

        card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=16)
        card.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(card, text="Change Password", font=font(15, "bold")).pack(
            anchor="w", padx=18, pady=(14, 4))
        self.cur = ctk.CTkEntry(card, placeholder_text="Current password", show="•",
                                height=40, corner_radius=10)
        self.cur.pack(fill="x", padx=18, pady=4)
        self.new = ctk.CTkEntry(card, placeholder_text="New password", show="•",
                                height=40, corner_radius=10)
        self.new.pack(fill="x", padx=18, pady=4)
        self.cfm = ctk.CTkEntry(card, placeholder_text="Confirm new password", show="•",
                                height=40, corner_radius=10)
        self.cfm.pack(fill="x", padx=18, pady=4)
        ctk.CTkButton(card, text="Update Password", fg_color=ACCENT,
                      hover_color=ACCENT_HOVER, height=40, corner_radius=10,
                      font=font(13, "bold"), command=self._change_pw).pack(
            anchor="w", padx=18, pady=(8, 16))

        card2 = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=16)
        card2.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(card2, text="Data", font=font(15, "bold")).pack(
            anchor="w", padx=18, pady=(14, 4))
        ctk.CTkButton(card2, text="Open Data Folder", height=38, corner_radius=10,
                      fg_color=CARD_BG2, hover_color=ACCENT, font=font(13),
                      command=lambda: open_file(user_data_dir(self.user_id))).pack(
            anchor="w", padx=18, pady=(4, 16))

        ctk.CTkLabel(self, text="StudyManager v6", font=font(12),
                     text_color=MUTED).pack(anchor="w", pady=(4, 0))
        ctk.CTkButton(self, text="  Logout", image=icon("logout", 16), height=42,
                      corner_radius=10, fg_color="transparent", border_width=1,
                      border_color=RED, text_color=RED, hover_color="#3a2030",
                      font=font(13, "bold"), command=self.app._logout).pack(
            anchor="w", pady=10)

    def refresh(self):
        pass

    def _change_pw(self):
        from auth import authenticate as auth_check
        conn = get_connection()
        user = conn.execute("SELECT username FROM users WHERE id=?",
                            (self.user_id,)).fetchone()
        conn.close()
        if not auth_check(user["username"], self.cur.get()):
            messagebox.showerror("Error", "Current password ghalat hai.")
            return
        if not self.new.get() or self.new.get() != self.cfm.get():
            messagebox.showerror("Error", "Naya password match nahi kar raha.")
            return
        change_password(self.user_id, self.new.get())
        self.cur.delete(0, "end"); self.new.delete(0, "end"); self.cfm.delete(0, "end")
        messagebox.showinfo("Done", "Password change ho gaya.")


def main():
    init_db()
    missing = [n for n in ("logo", "home", "courses", "timetable", "tasks", "file",
                           "chart", "profile", "gear", "bell", "logout", "plus",
                           "upload", "trash", "camera", "bank")
               if not os.path.exists(os.path.join(ICON_DIR, n + ".png"))]
    if missing:
        messagebox.showerror("Missing icons",
                             "assets/icons me ye nahi mile: " + ", ".join(missing))
        return
    for b in ("cover", "goals"):
        if not os.path.exists(os.path.join(IMG_DIR, b + ".png")):
            messagebox.showerror("Missing images",
                                 "assets/images me %s.png nahi mili." % b)
            return
    login = LoginWindow()
    login.mainloop()
    if login.user_id:
        app = MainWindow(login.user_id)
        app.mainloop()


if __name__ == "__main__":
    main()
