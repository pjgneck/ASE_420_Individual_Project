import requests
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from tkinter import filedialog, messagebox
from datetime import date
import json

# ---------------- AUTH SCREEN ---------------- #
class AuthScreen:
    def __init__(self):
        self.root = ttk.Window(themename="flatly")
        self.root.title("Login")
        self.root.geometry("400x200")

        ttk.Label(self.root, text="Username:").pack(anchor="w", padx=20, pady=5)
        self.username_var = ttk.StringVar()
        ttk.Entry(self.root, textvariable=self.username_var).pack(fill="x", padx=20)

        ttk.Label(self.root, text="Password:").pack(anchor="w", padx=20, pady=5)
        self.password_var = ttk.StringVar()
        ttk.Entry(self.root, textvariable=self.password_var, show="*").pack(fill="x", padx=20)

        ttk.Button(self.root, text="Login", bootstyle="success", command=self.authenticate).pack(pady=20)
        self.root.mainloop()

    def authenticate(self):
        username = self.username_var.get()
        password = self.password_var.get()
        if not username or not password:
            messagebox.showwarning("Missing Info", "Enter both username and password")
            return

        try:
            resp = requests.post(
                "http://localhost:3030/login",
                json={"username": username, "password": password},
                timeout=5
            )
            data = resp.json()
            if resp.status_code == 200 and data.get("success"):
                token = data.get("token")
                commands = data.get("commands", [])
                devices = data.get("devices", [])
                for widget in self.root.winfo_children():
                    widget.destroy()
                CommandManagerApp(self.root, commands, devices, token, username)
            else:
                messagebox.showerror("Failed", "Invalid username or password")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Server error: {e}")

# ---------------- COMMAND MANAGER APP ---------------- #
class CommandManagerApp:
    def __init__(self, root, commands, devices, token, username):
        self.root = root
        self.token = token
        self.commands = commands
        self.devices = devices
        self.username = username

        self.root.title(f"Command Manager - {username}")
        self.root.geometry("1150x700")

        # ---------------- STYLING ---------------- #
        self.style = ttk.Style("flatly")
        self.style.configure("Custom.Treeview",
            rowheight=28,
        )
        self.style.configure("Custom.Treeview.Heading",
            font=("Segoe UI", 10, "bold"),
            borderwidth=1,
            relief="solid"
        )
        self.style.map("Custom.Treeview", background=[("selected", "#3399FF")])

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.create_commands_tab()
        self.create_devices_tab()

    # ---------------- COMMANDS TAB ---------------- #
    def create_commands_tab(self):
        self.tab_commands = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_commands, text="Commands")

        search_frame = ttk.Frame(self.tab_commands)
        search_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(search_frame, text="Search:").pack(side="left", padx=5)
        self.cmd_search_var = ttk.StringVar()
        ttk.Entry(search_frame, textvariable=self.cmd_search_var, width=25).pack(side="left", padx=5)
        ttk.Label(search_frame, text="Filter by:").pack(side="left", padx=5)
        self.cmd_filter_var = ttk.StringVar(value="command")
        ttk.OptionMenu(search_frame, self.cmd_filter_var, "command", "command", "description", "last_used").pack(side="left")
        self.cmd_search_var.trace("w", lambda n, i, m: self.refresh_commands_table())

        btn_frame = ttk.Frame(self.tab_commands)
        btn_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(btn_frame, text="Add Command", bootstyle="success-outline", command=self.open_add_command_window).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Remove Command", bootstyle="danger-outline", command=self.remove_command).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Refresh", bootstyle="info-outline", command=self.refresh_commands_table).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Import JSON", bootstyle="secondary-outline", command=self.import_commands).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Export JSON", bootstyle="secondary-outline", command=self.export_commands).pack(side="left", padx=5)

        table_frame = ttk.Frame(self.tab_commands)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.cmd_tree = ttk.Treeview(table_frame, show="headings", style="Custom.Treeview")
        self.cmd_tree.pack(fill="both", expand=True)
        self.cmd_tree.bind("<Double-1>", self.copy_command)

        self.refresh_commands_table()

    def refresh_commands_table(self):
        search = self.cmd_search_var.get().lower()
        col = self.cmd_filter_var.get() or "command"
        for item in self.cmd_tree.get_children():
            self.cmd_tree.delete(item)
        filtered = [c for c in self.commands if search in str(c.get(col, "")).lower()]
        columns = ["command", "description", "last_used"]
        self.cmd_tree["columns"] = columns
        for c in columns:
            width = 300 if c == "command" else 150
            self.cmd_tree.heading(c, text=c.capitalize(), anchor="center")
            self.cmd_tree.column(c, width=width, anchor="w")
        for i, c in enumerate(filtered):
            tag = "odd" if i % 2 == 0 else "even"
            self.cmd_tree.insert("", "end", values=[c.get("command",""), c.get("description",""), c.get("last_used","")], tags=(tag,))
        self.cmd_tree.tag_configure("odd", background="#f9f9f9")
        self.cmd_tree.tag_configure("even", background="#ffffff")

    def open_add_command_window(self):
        win = ttk.Toplevel(self.root)
        win.title("Add Command")
        win.geometry("400x200")
        entries = {}
        for f in ["command","description"]:
            ttk.Label(win, text=f.capitalize()+":").pack(anchor="w", pady=3, padx=10)
            entries[f] = ttk.Entry(win,width=35)
            entries[f].pack(fill="x", pady=2, padx=10)

        def save_cmd():
            new_cmd = {
                "command": entries["command"].get(),
                "description": entries["description"].get(),
                "last_used": str(date.today())
            }
            self.commands.append(new_cmd)
            self.refresh_commands_table()
            win.destroy()
            Messagebox.show_info("Success","Command added!")

        ttk.Button(win, text="Save Command", bootstyle="success", command=save_cmd).pack(pady=10)

    def copy_command(self,event):
        row = self.cmd_tree.focus()
        if not row: return
        cmd = self.cmd_tree.item(row)["values"][0]
        self.root.clipboard_clear()
        self.root.clipboard_append(cmd)
        self.root.update()
        Messagebox.show_info("Copied",f"Command copied:\n{cmd}")

    def import_commands(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files","*.json")])
        if not file_path: return
        with open(file_path,"r") as f:
            data = json.load(f)
        for c in data:
            c["last_used"] = str(date.today())
            self.commands.append(c)
        self.refresh_commands_table()
        Messagebox.show_info("Imported", f"{len(data)} commands imported!")

    def export_commands(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files","*.json")])
        if not file_path: return
        with open(file_path,"w") as f:
            json.dump(self.commands,f,indent=4)
        Messagebox.show_info("Exported", f"{len(self.commands)} commands exported!")

    def remove_command(self):
        row = self.cmd_tree.focus()
        if not row:
            Messagebox.showwarning("No selection", "Select a command to remove")
            return
        values = self.cmd_tree.item(row)["values"]
        cmd_name = values[0]
        # Confirm deletion
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to remove '{cmd_name}'?"):
            self.commands = [c for c in self.commands if c.get("command") != cmd_name]
            self.refresh_commands_table()
            Messagebox.show_info("Removed", f"Command '{cmd_name}' removed")


    # ---------------- DEVICES TAB ---------------- #
    def create_devices_tab(self):
        self.tab_devices = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_devices, text="Devices")

        search_frame = ttk.Frame(self.tab_devices)
        search_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(search_frame, text="Search:").pack(side="left", padx=5)
        self.dev_search_var = ttk.StringVar()
        ttk.Entry(search_frame,textvariable=self.dev_search_var,width=25).pack(side="left", padx=5)
        ttk.Label(search_frame,text="Filter by:").pack(side="left", padx=5)
        self.dev_filter_var = ttk.StringVar(value="device")
        ttk.OptionMenu(search_frame,self.dev_filter_var,"device","device","ip").pack(side="left")
        self.dev_search_var.trace("w", lambda n,i,m:self.refresh_devices_table())

        btn_frame = ttk.Frame(self.tab_devices)
        btn_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(btn_frame,text="Add Device", bootstyle="success-outline", command=self.open_add_device_window).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Remove Device", bootstyle="danger-outline", command=self.remove_device).pack(side="left", padx=5)
        ttk.Button(btn_frame,text="Refresh", bootstyle="info-outline", command=self.refresh_devices_table).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Import JSON", bootstyle="secondary-outline", command=self.import_devices).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Export JSON", bootstyle="secondary-outline", command=self.export_devices).pack(side="left", padx=5)

        table_frame = ttk.Frame(self.tab_devices)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.dev_tree = ttk.Treeview(table_frame, show="headings", style="Custom.Treeview")
        self.dev_tree.pack(fill="both", expand=True)
        self.dev_tree.bind("<Double-1>", self.copy_device_ip)
        self.refresh_devices_table()

    def import_devices(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files","*.json")])
        if not file_path: return
        with open(file_path,"r") as f:
            data = json.load(f)
        self.devices.extend(data)
        self.refresh_devices_table()
        Messagebox.show_info("Imported", f"{len(data)} devices imported!")

    def export_devices(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files","*.json")])
        if not file_path: return
        with open(file_path,"w") as f:
            json.dump(self.devices,f,indent=4)
        Messagebox.show_info("Exported", f"{len(self.devices)} devices exported!")

    def refresh_devices_table(self):
        search = self.dev_search_var.get().lower()
        col = self.dev_filter_var.get() or "device"
        for item in self.dev_tree.get_children():
            self.dev_tree.delete(item)
        filtered = [d for d in self.devices if search in str(d.get(col,"")).lower()]
        columns = ["device","ip"]
        self.dev_tree["columns"]=columns
        for c in columns:
            width=250 if c=="device" else 150
            self.dev_tree.heading(c,text=c.capitalize(), anchor="center")
            self.dev_tree.column(c,width=width,anchor="w")
        for i, d in enumerate(filtered):
            tag = "odd" if i % 2 == 0 else "even"
            self.dev_tree.insert("", "end", values=[d.get("device",""), d.get("ip","")], tags=(tag,))
        self.dev_tree.tag_configure("odd", background="#f9f9f9")
        self.dev_tree.tag_configure("even", background="#ffffff")

    def open_add_device_window(self):
        win = ttk.Toplevel(self.root)
        win.title("Add Device")
        win.geometry("400x200")
        entries={}
        for f in ["device","ip"]:
            ttk.Label(win,text=f.capitalize()+":").pack(anchor="w", pady=3, padx=10)
            entries[f]=ttk.Entry(win,width=35)
            entries[f].pack(fill="x", pady=2, padx=10)

        def save_dev():
            new_dev={"device":entries["device"].get(),"ip":entries["ip"].get()}
            self.devices.append(new_dev)
            self.refresh_devices_table()
            win.destroy()
            Messagebox.show_info("Success","Device added!")

        ttk.Button(win,text="Save Device", bootstyle="success",command=save_dev).pack(pady=10)

    def copy_device_ip(self,event):
        row = self.dev_tree.focus()
        if not row: return
        ip = self.dev_tree.item(row)["values"][1]
        self.root.clipboard_clear()
        self.root.clipboard_append(ip)
        self.root.update()
        Messagebox.show_info("Copied", f"IP copied:\n{ip}")

    def remove_device(self):
        row = self.dev_tree.focus()
        if not row:
            Messagebox.showwarning("No selection", "Select a device to remove")
            return
        values = self.dev_tree.item(row)["values"]
        device_name = values[0]
        # Confirm deletion
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to remove '{device_name}'?"):
            self.devices = [d for d in self.devices if d.get("device") != device_name]
            self.refresh_devices_table()
            Messagebox.show_info("Removed", f"Device '{device_name}' removed")


# ---------------- START APP ---------------- #
if __name__=="__main__":
    AuthScreen()
