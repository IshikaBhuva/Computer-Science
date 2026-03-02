import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime

# --- Constants & Styling ---
FILE_NAME = "pro_tasks_data.json"
COLORS = {
    "bg": "#f8fafc",
    "card": "#ffffff",
    "primary": "#2563eb",
    "secondary": "#64748b",
    "success": "#059669",
    "warning": "#d97706",
    "danger": "#dc2626",
    "border": "#e2e8f0",
    "status_completed": "#dcfce7", # Green highlight
    "status_progress": "#dbeafe",  # Blue highlight
    "status_pending": "#ffffff"    # White/Default
}

class ProTodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Automated To-Do List Prioritiser")
        self.root.geometry("1200x800")
        self.root.configure(bg=COLORS["bg"])
        
        self.tasks = []
        self.editing_id = None
        self.load_data()
        
        self.setup_styles()
        self.setup_ui()
        self.refresh_ui()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        # Configure Treeview
        style.configure("Treeview", 
                        background=COLORS["card"], 
                        foreground="#1e293b",
                        rowheight=35,
                        fieldbackground=COLORS["card"],
                        bordercolor=COLORS["border"],
                        borderwidth=1)
        style.map("Treeview", background=[('selected', '#cbd5e1')], foreground=[('selected', '#1e293b')])
        style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"), background="#f1f5f9")

    def setup_ui(self):
        # Main Layout Container
        self.main_container = tk.Frame(self.root, bg=COLORS["bg"], padx=30, pady=20)
        self.main_container.pack(expand=True, fill="both")

        # --- Header & Stats Dashboard ---
        self.header_frame = tk.Frame(self.main_container, bg=COLORS["bg"])
        self.header_frame.pack(fill="x", pady=(0, 20))

        title_label = tk.Label(self.header_frame, text="Task Prioritiser", font=("Helvetica", 24, "bold"), bg=COLORS["bg"], fg="#1e293b")
        title_label.pack(side="left")

        # Stats Counters
        self.stats_frame = tk.Frame(self.header_frame, bg=COLORS["bg"])
        self.stats_frame.pack(side="right")

        self.lbl_total = self.create_stat_box(self.stats_frame, "TASKS", "0", COLORS["secondary"])
        self.lbl_avg = self.create_stat_box(self.stats_frame, "AVG SCORE", "0", COLORS["primary"])
        self.lbl_success = self.create_stat_box(self.stats_frame, "SUCCESS", "0%", COLORS["success"])

        # --- Content Area (Split Panes) ---
        content_frame = tk.Frame(self.main_container, bg=COLORS["bg"])
        content_frame.pack(expand=True, fill="both")

        # Left Column: Input Form
        input_col = tk.Frame(content_frame, bg=COLORS["card"], padx=20, pady=20, highlightthickness=1, highlightbackground=COLORS["border"])
        input_col.place(relx=0, rely=0, relwidth=0.30, relheight=0.95)

        tk.Label(input_col, text="Task Details", font=("Helvetica", 14, "bold"), bg=COLORS["card"]).pack(anchor="w", pady=(0, 15))

        tk.Label(input_col, text="Description", bg=COLORS["card"], fg=COLORS["secondary"]).pack(anchor="w")
        self.ent_name = ttk.Entry(input_col)
        self.ent_name.pack(fill="x", pady=(0, 15))
        self.ent_name.bind("<Return>", lambda e: self.add_task())

        tk.Label(input_col, text="Category", bg=COLORS["card"], fg=COLORS["secondary"]).pack(anchor="w")
        self.cmb_cat = ttk.Combobox(input_col, values=["Work", "Personal", "Urgent", "Learning"], state="readonly")
        self.cmb_cat.set("Work")
        self.cmb_cat.pack(fill="x", pady=(0, 15))

        tk.Label(input_col, text="Importance (1-10)", bg=COLORS["card"], fg=COLORS["secondary"]).pack(anchor="w")
        self.scale_imp = tk.Scale(input_col, from_=1, to=10, orient="horizontal", bg=COLORS["card"], highlightthickness=0)
        self.scale_imp.set(5)
        self.scale_imp.pack(fill="x", pady=(0, 15))

        grid_params = tk.Frame(input_col, bg=COLORS["card"])
        grid_params.pack(fill="x")

        tk.Label(grid_params, text="Due (Days)", bg=COLORS["card"], fg=COLORS["secondary"]).grid(row=0, column=0, sticky="w")
        self.ent_days = ttk.Entry(grid_params, width=10)
        self.ent_days.insert(0, "1")
        self.ent_days.grid(row=1, column=0, pady=(0, 15), padx=(0, 5))

        tk.Label(grid_params, text="Effort (Hrs)", bg=COLORS["card"], fg=COLORS["secondary"]).grid(row=0, column=1, sticky="w")
        self.ent_dur = ttk.Entry(grid_params, width=10)
        self.ent_dur.insert(0, "1")
        self.ent_dur.grid(row=1, column=1, pady=(0, 15))

        self.btn_add = tk.Button(input_col, text="Add to Schedule", command=self.add_task, 
                           bg=COLORS["primary"], fg="white", font=("Helvetica", 11, "bold"), 
                           relief="flat", pady=10, cursor="hand2")
        self.btn_add.pack(fill="x", pady=10)

        # Info Box (Interactive Tip)
        self.info_box = tk.Frame(input_col, bg="#f1f5f9", padx=10, pady=10, highlightthickness=1, highlightbackground=COLORS["border"])
        self.info_box.pack(fill="x", pady=(20, 0))
        self.lbl_tip_head = tk.Label(self.info_box, text="PRO TIP", font=("Helvetica", 8, "bold"), bg="#f1f5f9", fg=COLORS["secondary"])
        self.lbl_tip_head.pack(anchor="w")
        self.lbl_tip = tk.Label(self.info_box, text="Double-click a task to edit its details.", font=("Helvetica", 9), bg="#f1f5f9", fg="#475569", wraplength=200, justify="left")
        self.lbl_tip.pack(anchor="w", pady=(5, 0))

        # Right Column: List & Actions
        list_col = tk.Frame(content_frame, bg=COLORS["bg"])
        list_col.place(relx=0.32, rely=0, relwidth=0.68, relheight=1.0)

        # Search Bar
        search_frame = tk.Frame(list_col, bg=COLORS["card"], padx=10, pady=10, highlightthickness=1, highlightbackground=COLORS["border"])
        search_frame.pack(fill="x", pady=(0, 15), padx=(20, 0))
        
        tk.Label(search_frame, text="🔍", bg=COLORS["card"]).pack(side="left")
        self.ent_search = ttk.Entry(search_frame)
        self.ent_search.pack(side="left", fill="x", expand=True, padx=10)
        self.ent_search.bind("<KeyRelease>", lambda e: self.refresh_list())

        # Treeview
        tree_container = tk.Frame(list_col, bg=COLORS["bg"])
        tree_container.pack(expand=True, fill="both", padx=(20, 0))

        columns = ("score", "status", "name", "cat", "deadline", "created")
        self.tree = ttk.Treeview(tree_container, columns=columns, show="headings")
        self.tree.heading("score", text="Score")
        self.tree.heading("status", text="Status")
        self.tree.heading("name", text="Task Name")
        self.tree.heading("cat", text="Category")
        self.tree.heading("deadline", text="Due")
        self.tree.heading("created", text="Created At")

        self.tree.column("score", width=60, anchor="center")
        self.tree.column("status", width=100, anchor="center")
        self.tree.column("name", width=220)
        self.tree.column("cat", width=100)
        self.tree.column("deadline", width=60, anchor="center")
        self.tree.column("created", width=140, anchor="center")
        
        self.tree.pack(side="left", expand=True, fill="both")
        self.tree.bind("<Double-1>", lambda e: self.load_task_to_edit())
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.update_tip())

        scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Action Buttons Footer
        footer_btn_frame = tk.Frame(list_col, bg=COLORS["bg"], pady=15)
        footer_btn_frame.pack(fill="x", padx=(20, 0))

        tk.Button(footer_btn_frame, text="Change Status", command=self.toggle_status, bg="#f1f5f9", relief="flat", padx=15).pack(side="left", padx=5)
        tk.Button(footer_btn_frame, text="Delete Task", command=self.delete_task, bg="#fee2e2", fg=COLORS["danger"], relief="flat", padx=15).pack(side="left", padx=5)
        tk.Button(footer_btn_frame, text="Clear All", command=self.clear_all, bg=COLORS["bg"], fg=COLORS["secondary"], relief="flat").pack(side="right")

    def create_stat_box(self, parent, title, value, color):
        box = tk.Frame(parent, bg=COLORS["card"], padx=15, pady=10, highlightthickness=1, highlightbackground=COLORS["border"])
        box.pack(side="left", padx=5)
        val_lbl = tk.Label(box, text=value, font=("Helvetica", 14, "bold"), fg=color, bg=COLORS["card"])
        val_lbl.pack()
        tk.Label(box, text=title, font=("Helvetica", 7, "bold"), fg=COLORS["secondary"], bg=COLORS["card"]).pack()
        return val_lbl

    def calculate_score(self, importance, days, duration):
        urgency = 10 / (max(float(days), 0.1))
        imp_factor = float(importance) * 2
        effort_factor = float(duration) * 0.5
        return round((urgency + imp_factor) - effort_factor, 1)

    def add_task(self):
        name = self.ent_name.get().strip()
        if not name:
            messagebox.showwarning("Input Error", "Please enter a task description.")
            return
        
        try:
            days = float(self.ent_days.get())
            dur = float(self.ent_dur.get())
            imp = self.scale_imp.get()
            score = self.calculate_score(imp, days, dur)
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            if self.editing_id:
                # Update existing
                for t in self.tasks:
                    if t['id'] == self.editing_id:
                        t.update({"name": name, "cat": self.cmb_cat.get(), "imp": imp, "days": days, "dur": dur, "score": score})
                        break
                self.editing_id = None
                self.btn_add.config(text="Add to Schedule", bg=COLORS["primary"])
            else:
                # Create new
                task = {
                    "id": datetime.now().timestamp(),
                    "name": name,
                    "cat": self.cmb_cat.get(),
                    "imp": imp,
                    "days": days,
                    "dur": dur,
                    "score": score,
                    "status": "Pending",
                    "created_at": now_str
                }
                self.tasks.append(task)

            self.save_data()
            self.refresh_ui()
            self.clear_form()
        except ValueError:
            messagebox.showerror("Error", "Invalid numbers for days or duration.")

    def clear_form(self):
        self.ent_name.delete(0, tk.END)
        self.ent_days.delete(0, tk.END)
        self.ent_days.insert(0, "1")
        self.ent_dur.delete(0, tk.END)
        self.ent_dur.insert(0, "1")
        self.scale_imp.set(5)
        self.editing_id = None
        self.btn_add.config(text="Add to Schedule", bg=COLORS["primary"])

    def load_task_to_edit(self):
        selected = self.tree.selection()
        if not selected: return
        
        task_id = float(self.tree.item(selected[0])['tags'][0])
        task = next((t for t in self.tasks if t['id'] == task_id), None)
        
        if task:
            self.clear_form()
            self.ent_name.insert(0, task['name'])
            self.cmb_cat.set(task['cat'])
            self.scale_imp.set(task['imp'])
            self.ent_days.delete(0, tk.END)
            self.ent_days.insert(0, str(task['days']))
            self.ent_dur.delete(0, tk.END)
            self.ent_dur.insert(0, str(task['dur']))
            
            self.editing_id = task['id']
            self.btn_add.config(text="Update Task", bg=COLORS["warning"])

    def update_tip(self):
        selected = self.tree.selection()
        if not selected:
            self.lbl_tip.config(text="Select a task to see management tips.")
            return
            
        task_id = float(self.tree.item(selected[0])['tags'][0])
        task = next((t for t in self.tasks if t['id'] == task_id), None)
        
        if task:
            if task['status'] == "Completed":
                tip = "Great job! This task is archived. Focus on your next priority."
            elif task['score'] > 15:
                tip = "High Priority: Do this first. It has a high impact and short deadline."
            elif task['days'] < 2:
                tip = "Urgent: Deadline is very close. Consider delegating other tasks."
            else:
                tip = "Quick Win: You can finish this quickly to build momentum."
            self.lbl_tip.config(text=tip)

    def toggle_status(self):
        selected = self.tree.selection()
        if not selected: return
        
        task_id = self.tree.item(selected[0])['tags'][0]
        states = ["Pending", "In Progress", "Completed"]
        
        for t in self.tasks:
            if str(t['id']) == str(task_id):
                current_idx = states.index(t['status'])
                t['status'] = states[(current_idx + 1) % len(states)]
                break
        
        self.save_data()
        self.refresh_ui()

    def delete_task(self):
        selected = self.tree.selection()
        if not selected: return
        
        task_id = self.tree.item(selected[0])['tags'][0]
        self.tasks = [t for t in self.tasks if str(t['id']) != str(task_id)]
        self.save_data()
        self.refresh_ui()

    def clear_all(self):
        if messagebox.askyesno("Confirm", "Clear all tasks?"):
            self.tasks = []
            self.save_data()
            self.refresh_ui()

    def refresh_ui(self):
        self.refresh_list()
        self.update_stats()

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        query = self.ent_search.get().lower()
        # Sort logic: In Progress first, then Pending by score, Completed at bottom
        def sort_key(x):
            status_order = {"In Progress": 0, "Pending": 1, "Completed": 2}
            return (status_order.get(x['status'], 1), -x['score'])
            
        sorted_tasks = sorted(self.tasks, key=sort_key)
        
        for t in sorted_tasks:
            if query in t['name'].lower() or query in t['cat'].lower():
                # Determine tag based on Status (requested change)
                if t['status'] == "Completed":
                    tag = "st_completed"
                elif t['status'] == "In Progress":
                    tag = "st_progress"
                else:
                    tag = "st_pending"
                
                created_at = t.get('created_at', 'N/A')
                
                self.tree.insert("", "end", values=(
                    t['score'], t['status'], t['name'], t['cat'], f"{t['days']}d", created_at
                ), tags=(str(t['id']), tag))
        
        # Configure Row Status Colors (requested change)
        self.tree.tag_configure("st_completed", background=COLORS["status_completed"], foreground="#15803d")
        self.tree.tag_configure("st_progress", background=COLORS["status_progress"])
        self.tree.tag_configure("st_pending", background=COLORS["status_pending"])

    def update_stats(self):
        total = len(self.tasks)
        avg = round(sum(t['score'] for t in self.tasks) / total, 1) if total > 0 else 0
        completed = len([t for t in self.tasks if t['status'] == "Completed"])
        percent = round((completed / total) * 100) if total > 0 else 0
        
        self.lbl_total.config(text=str(total))
        self.lbl_avg.config(text=str(avg))
        self.lbl_success.config(text=f"{percent}%")

    def save_data(self):
        try:
            with open(FILE_NAME, "w") as f:
                json.dump(self.tasks, f)
        except Exception as e:
            print(f"Error saving: {e}")

    def load_data(self):
        if os.path.exists(FILE_NAME):
            try:
                with open(FILE_NAME, "r") as f:
                    self.tasks = json.load(f)
            except: 
                self.tasks = []

if __name__ == "__main__":
    root = tk.Tk()
    app = ProTodoApp(root)
    root.mainloop()