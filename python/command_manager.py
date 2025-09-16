import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import date

# ---------------- FILE PATHS ---------------- #
DATA_DIR = os.path.join("..", "data")
USER_FILE = os.path.join(DATA_DIR, "users_auth.json")
DEPT_FILE = os.path.join(DATA_DIR, "departments.json")

# ---------------- COMMAND MANAGER CLASS ---------------- #
class CommandManager:
    def __init__(self, root, user):
        self.root = root
        self.user = user
        self.root.title(f"SSH Command Manager - Logged in as {user['username']}")
        self.root.geometry("1050x650")
        self.root.configure(bg="#e8ebf0")

        self.load_users()
        self.load_departments()
        self.set_user_department()
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.create_commands_tab()
        self.create_devices_tab()
        self.create_manage_tab()

    # ---------------- LOAD/REFRESH DATA ---------------- #
    def load_users(self):
        try:
            with open(USER_FILE, "r", encoding="utf-8") as f:
                self.users_data = json.load(f)
        except:
            self.users_data = []

    def save_users_data(self):
        with open(USER_FILE, "w", encoding="utf-8") as f:
            json.dump(self.users_data, f, indent=4)

    def load_departments(self):
        try:
            with open(DEPT_FILE, "r", encoding="utf-8") as f:
                self.departments_data = json.load(f)
        except:
            self.departments_data = []

    def save_departments_data(self):
        with open(DEPT_FILE, "w", encoding="utf-8") as f:
            json.dump(self.departments_data, f, indent=4)

    def set_user_department(self):
        # Set user's department data
        self.user_dept_data = next((d for d in self.departments_data if d["department"] == self.user["department"]), None)

    # ---------------- COMMANDS TAB ---------------- #
    def create_commands_tab(self):
        self.tab_commands = tk.Frame(self.notebook, bg="#f0f0f5")
        self.notebook.add(self.tab_commands, text="Commands")

        # Search/filter
        search_frame = tk.Frame(self.tab_commands, bg="#f0f0f5")
        search_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(search_frame, text="Search:", bg="#f0f0f5").pack(side=tk.LEFT)
        self.cmd_search_var = tk.StringVar()
        tk.Entry(search_frame, textvariable=self.cmd_search_var, width=25).pack(side=tk.LEFT, padx=5)
        tk.Label(search_frame, text="Filter by:", bg="#f0f0f5").pack(side=tk.LEFT, padx=5)
        self.cmd_filter_var = tk.StringVar()
        ttk.OptionMenu(search_frame, self.cmd_filter_var, "command", "command", "description", "id", "last_used").pack(side=tk.LEFT)
        self.cmd_search_var.trace("w", lambda n,i,m:self.filter_commands())

        # Buttons
        btn_frame = tk.Frame(self.tab_commands, bg="#f0f0f5")
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(btn_frame, text="Add Command", command=self.open_add_command_window).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_commands_table).pack(side=tk.LEFT, padx=5)

        # Treeview
        self.cmd_tree = ttk.Treeview(self.tab_commands)
        self.cmd_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        vsb = ttk.Scrollbar(self.tab_commands, orient="vertical", command=self.cmd_tree.yview)
        vsb.pack(side="right", fill="y")
        self.cmd_tree.configure(yscrollcommand=vsb.set)
        hsb = ttk.Scrollbar(self.tab_commands, orient="horizontal", command=self.cmd_tree.xview)
        hsb.pack(side="bottom", fill="x")
        self.cmd_tree.configure(xscrollcommand=hsb.set)
        self.cmd_tree.bind("<Button-1>", self.on_command_click)

        self.refresh_commands_table()

    def refresh_commands_table(self):
        self.all_commands = self.user_dept_data.get("commands", []) if self.user_dept_data else []
        self.filter_commands()

    def filter_commands(self):
        search = self.cmd_search_var.get().lower()
        col = self.cmd_filter_var.get()
        for item in self.cmd_tree.get_children():
            self.cmd_tree.delete(item)
        filtered = [c for c in self.all_commands if search in str(c.get(col, "")).lower()]
        if filtered:
            columns = ["id", "command", "description", "last_used"]
            self.cmd_tree["columns"] = columns
            self.cmd_tree["show"] = "headings"
            for c in columns:
                width = 300 if c=="command" else 150
                self.cmd_tree.heading(c, text=c, anchor="w")
                self.cmd_tree.column(c, width=width, anchor="w")
            for c in filtered:
                values = [c.get(col,"") for col in columns]
                self.cmd_tree.insert("", tk.END, values=values)
        else:
            self.cmd_tree["columns"] = []
            self.cmd_tree["show"] = ""

    def on_command_click(self, event):
        region = self.cmd_tree.identify("region", event.x, event.y)
        if region != "cell": return
        row_id = self.cmd_tree.identify_row(event.y)
        col_id = self.cmd_tree.identify_column(event.x)
        if not row_id or not col_id: return
        col_index = int(col_id.replace("#",""))-1
        col_name = self.cmd_tree["columns"][col_index]
        if col_name=="command":
            item = self.cmd_tree.item(row_id)
            command = item["values"][col_index]
            self.root.clipboard_clear()
            self.root.clipboard_append(command)
            self.root.update()
            messagebox.showinfo("Copied", f"Command copied:\n{command}")
            # Update last_used
            for c in self.all_commands:
                if str(c["id"])==str(item["values"][0]):
                    c["last_used"] = str(date.today())
            self.save_departments_data()
            self.refresh_commands_table()

    def open_add_command_window(self):
        win = tk.Toplevel(self.root)
        win.title("Add Command")
        win.geometry("400x250")
        fields = ["id","command","description"]
        entries = {}
        for i,f in enumerate(fields):
            tk.Label(win,text=f).grid(row=i,column=0,padx=10,pady=5,sticky="w")
            entries[f] = tk.Entry(win,width=35)
            entries[f].grid(row=i,column=1,padx=10,pady=5)
        def save_cmd():
            new_c = {f:entries[f].get() for f in fields}
            new_c["last_used"] = str(date.today())
            self.user_dept_data.setdefault("commands",[]).append(new_c)
            self.save_departments_data()
            self.refresh_commands_table()
            win.destroy()
        ttk.Button(win,text="Save",command=save_cmd).grid(row=len(fields),column=0,columnspan=2,pady=10)

    # ---------------- DEVICES TAB ---------------- #
    def create_devices_tab(self):
        self.tab_devices = tk.Frame(self.notebook, bg="#f0f0f5")
        self.notebook.add(self.tab_devices, text="Devices")

        search_frame = tk.Frame(self.tab_devices,bg="#f0f0f5")
        search_frame.pack(fill=tk.X,padx=10,pady=5)
        tk.Label(search_frame,text="Search:",bg="#f0f0f5").pack(side=tk.LEFT)
        self.dev_search_var = tk.StringVar()
        tk.Entry(search_frame,textvariable=self.dev_search_var,width=25).pack(side=tk.LEFT,padx=5)
        tk.Label(search_frame,text="Filter by:",bg="#f0f0f5").pack(side=tk.LEFT,padx=5)
        self.dev_filter_var = tk.StringVar()
        ttk.OptionMenu(search_frame,self.dev_filter_var,"device","device","id","ip","username").pack(side=tk.LEFT)
        self.dev_search_var.trace("w",lambda n,i,m:self.filter_devices())

        btn_frame = tk.Frame(self.tab_devices,bg="#f0f0f5")
        btn_frame.pack(fill=tk.X,padx=10,pady=5)
        ttk.Button(btn_frame,text="Add Device",command=self.open_add_device_window).pack(side=tk.LEFT,padx=5)
        ttk.Button(btn_frame,text="Refresh",command=self.refresh_devices_table).pack(side=tk.LEFT,padx=5)

        self.dev_tree = ttk.Treeview(self.tab_devices)
        self.dev_tree.pack(fill=tk.BOTH,expand=True,padx=10,pady=5)
        vsb = ttk.Scrollbar(self.tab_devices,orient="vertical",command=self.dev_tree.yview)
        vsb.pack(side="right",fill="y")
        self.dev_tree.configure(yscrollcommand=vsb.set)
        hsb = ttk.Scrollbar(self.tab_devices,orient="horizontal",command=self.dev_tree.xview)
        hsb.pack(side="bottom",fill="x")
        self.dev_tree.configure(xscrollcommand=hsb.set)
        self.refresh_devices_table()

    def refresh_devices_table(self):
        self.all_devices = self.user_dept_data.get("devices", []) if self.user_dept_data else []
        self.filter_devices()

    def filter_devices(self):
        search = self.dev_search_var.get().lower()
        col = self.dev_filter_var.get()
        for item in self.dev_tree.get_children():
            self.dev_tree.delete(item)
        filtered = [d for d in self.all_devices if search in str(d.get(col,"")).lower()]
        if filtered:
            columns = ["id","device","ip","username"]
            self.dev_tree["columns"] = columns
            self.dev_tree["show"] = "headings"
            for c in columns:
                width = 250 if c=="device" else 150
                self.dev_tree.heading(c,text=c)
                self.dev_tree.column(c,width=width)
            for d in filtered:
                self.dev_tree.insert("",tk.END,values=[d.get(col,"") for col in columns])
        else:
            self.dev_tree["columns"]=[]
            self.dev_tree["show"]=""

    def open_add_device_window(self):
        win = tk.Toplevel(self.root)
        win.title("Add Device")
        win.geometry("400x200")
        fields = ["id","device","ip","username"]
        entries={}
        for i,f in enumerate(fields):
            tk.Label(win,text=f).grid(row=i,column=0,padx=10,pady=5,sticky="w")
            entries[f] = tk.Entry(win,width=35)
            entries[f].grid(row=i,column=1,padx=10,pady=5)
        def save_dev():
            new_d = {f:entries[f].get() for f in fields}
            self.user_dept_data.setdefault("devices",[]).append(new_d)
            self.save_departments_data()
            self.refresh_devices_table()
            win.destroy()
        ttk.Button(win,text="Save",command=save_dev).grid(row=len(fields),column=0,columnspan=2,pady=10)

    # ---------------- MANAGE TAB ---------------- #
    def create_manage_tab(self):
        self.tab_manage = tk.Frame(self.notebook,bg="#f0f0f5")
        self.notebook.add(self.tab_manage,text="Manage")

        self.refresh_manage_tab()

    def refresh_manage_tab(self):
        # Clear tab
        for widget in self.tab_manage.winfo_children():
            widget.destroy()

        # Load departments and users
        dept_names = [d["department"] for d in self.departments_data]
        usernames = [u["username"] for u in self.users_data]

        # Add Department
        dept_frame = tk.LabelFrame(self.tab_manage,text="Add Department",padx=10,pady=10,bg="#f0f0f5")
        dept_frame.pack(fill=tk.X,padx=15,pady=10)
        tk.Label(dept_frame,text="Department Name:",bg="#f0f0f5").grid(row=0,column=0,padx=5,pady=5)
        self.new_dept_var = tk.StringVar()
        tk.Entry(dept_frame,textvariable=self.new_dept_var,width=30).grid(row=0,column=1,padx=5,pady=5)
        tk.Label(dept_frame,text="Managers (comma-separated):",bg="#f0f0f5").grid(row=1,column=0,padx=5,pady=5)
        self.new_mgr_var = tk.StringVar()
        tk.Entry(dept_frame,textvariable=self.new_mgr_var,width=30).grid(row=1,column=1,padx=5,pady=5)
        tk.Label(dept_frame,text="Team Leads (comma-separated):",bg="#f0f0f5").grid(row=2,column=0,padx=5,pady=5)
        self.new_tl_var = tk.StringVar()
        tk.Entry(dept_frame,textvariable=self.new_tl_var,width=30).grid(row=2,column=1,padx=5,pady=5)
        ttk.Button(dept_frame,text="Add Department",command=self.add_department).grid(row=3,column=0,columnspan=2,pady=10)

        # Add User
        user_frame = tk.LabelFrame(self.tab_manage,text="Add User",padx=10,pady=10,bg="#f0f0f5")
        user_frame.pack(fill=tk.X,padx=15,pady=10)
        tk.Label(user_frame,text="Username:",bg="#f0f0f5").grid(row=0,column=0,padx=5,pady=5)
        self.new_user_var = tk.StringVar()
        tk.Entry(user_frame,textvariable=self.new_user_var,width=20).grid(row=0,column=1,padx=5,pady=5)
        tk.Label(user_frame,text="Department:",bg="#f0f0f5").grid(row=0,column=2,padx=5,pady=5)
        self.user_dept_var = tk.StringVar()
        self.user_dept_var.set(dept_names[0] if dept_names else "")
        ttk.OptionMenu(user_frame,self.user_dept_var,self.user_dept_var.get(),*dept_names).grid(row=0,column=3,padx=5,pady=5)
        ttk.Button(user_frame,text="Add User",command=self.add_user).grid(row=0,column=4,padx=5,pady=5)

        # Assign Managers
        mgr_frame = tk.LabelFrame(self.tab_manage,text="Assign Managers",padx=10,pady=10,bg="#f0f0f5")
        mgr_frame.pack(fill=tk.X,padx=15,pady=10)
        tk.Label(mgr_frame,text="Department:",bg="#f0f0f5").grid(row=0,column=0,padx=5,pady=5)
        self.mgr_dept_var = tk.StringVar()
        self.mgr_dept_var.set(dept_names[0] if dept_names else "")
        ttk.OptionMenu(mgr_frame,self.mgr_dept_var,self.mgr_dept_var.get(),*dept_names).grid(row=0,column=1,padx=5,pady=5)
        tk.Label(mgr_frame,text="Username:",bg="#f0f0f5").grid(row=0,column=2,padx=5,pady=5)
        self.mgr_user_var = tk.StringVar()
        self.mgr_user_var.set(usernames[0] if usernames else "")
        ttk.OptionMenu(mgr_frame,self.mgr_user_var,self.mgr_user_var.get(),*usernames).grid(row=0,column=3,padx=5,pady=5)
        ttk.Button(mgr_frame,text="Add Manager",command=self.add_manager_to_dept).grid(row=0,column=4,padx=5,pady=5)

        # Assign Team Leads
        tl_frame = tk.LabelFrame(self.tab_manage,text="Assign Team Leads",padx=10,pady=10,bg="#f0f0f5")
        tl_frame.pack(fill=tk.X,padx=15,pady=10)
        tk.Label(tl_frame,text="Department:",bg="#f0f0f5").grid(row=0,column=0,padx=5,pady=5)
        self.tl_dept_var = tk.StringVar()
        self.tl_dept_var.set(dept_names[0] if dept_names else "")
        ttk.OptionMenu(tl_frame,self.tl_dept_var,self.tl_dept_var.get(),*dept_names).grid(row=0,column=1,padx=5,pady=5)
        tk.Label(tl_frame,text="Username:",bg="#f0f0f5").grid(row=0,column=2,padx=5,pady=5)
        self.tl_user_var = tk.StringVar()
        self.tl_user_var.set(usernames[0] if usernames else "")
        ttk.OptionMenu(tl_frame,self.tl_user_var,self.tl_user_var.get(),*usernames).grid(row=0,column=3,padx=5,pady=5)
        ttk.Button(tl_frame,text="Add Team Lead",command=self.add_teamlead_to_dept).grid(row=0,column=4,padx=5,pady=5)

    # ----------------- ADD/UPDATE ---------------- #
    def add_department(self):
        dept_name = self.new_dept_var.get().strip()
        managers = [m.strip() for m in self.new_mgr_var.get().split(",") if m.strip()]
        teamleads = [t.strip() for t in self.new_tl_var.get().split(",") if t.strip()]
        if not dept_name or not managers or not teamleads:
            messagebox.showerror("Error","Department, Managers, and Team Leads required")
            return
        if any(d["department"]==dept_name for d in self.departments_data):
            messagebox.showinfo("Info","Department already exists")
            return
        new_dept = {"department":dept_name,"managers":managers,"teamleads":teamleads,"commands":[],"devices":[]}
        self.departments_data.append(new_dept)
        self.save_departments_data()
        messagebox.showinfo("Success",f"Department '{dept_name}' added")
        self.refresh_manage_tab()
        self.load_departments()
        self.set_user_department()

    def add_user(self):
        username = self.new_user_var.get().strip()
        dept_name = self.user_dept_var.get()
        if not username or not dept_name:
            messagebox.showerror("Error","Username and Department required")
            return
        self.users_data.append({"username":username,"department":dept_name,"password":""})
        self.save_users_data()
        messagebox.showinfo("Success",f"User '{username}' added to {dept_name}")
        self.refresh_manage_tab()

    def add_manager_to_dept(self):
        dept_name = self.mgr_dept_var.get()
        username = self.mgr_user_var.get()
        for d in self.departments_data:
            if d["department"]==dept_name and username not in d["managers"]:
                d["managers"].append(username)
        self.save_departments_data()
        messagebox.showinfo("Success",f"'{username}' added as manager to {dept_name}")
        self.refresh_manage_tab()

    def add_teamlead_to_dept(self):
        dept_name = self.tl_dept_var.get()
        username = self.tl_user_var.get()
        for d in self.departments_data:
            if d["department"]==dept_name and username not in d["teamleads"]:
                d["teamleads"].append(username)
        self.save_departments_data()
        messagebox.showinfo("Success",f"'{username}' added as team lead to {dept_name}")
        self.refresh_manage_tab()


# ----------------- LOGIN ----------------- #
def login_screen():
    login_root = tk.Tk()
    login_root.title("Login")
    login_root.geometry("400x200")
    login_root.configure(bg="#e8ebf0")

    tk.Label(login_root,text="Username:",bg="#e8ebf0").pack(pady=10)
    username_var = tk.StringVar()
    tk.Entry(login_root,textvariable=username_var,width=30).pack()

    tk.Label(login_root,text="Password:",bg="#e8ebf0").pack(pady=10)
    password_var = tk.StringVar()
    tk.Entry(login_root,textvariable=password_var,width=30,show="*").pack()

    def attempt_login():
        try:
            with open(USER_FILE,"r",encoding="utf-8") as f:
                users = json.load(f)
        except:
            users=[]
        user = next((u for u in users if u["username"]==username_var.get() and u["password"]==password_var.get()),None)
        if user:
            login_root.destroy()
            root = tk.Tk()
            CommandManager(root,user)
            root.mainloop()
        else:
            messagebox.showerror("Error","Invalid username/password")

    ttk.Button(login_root,text="Login",command=attempt_login).pack(pady=20)
    login_root.mainloop()


# ----------------- START APP ----------------- #
if __name__=="__main__":
    login_screen()
