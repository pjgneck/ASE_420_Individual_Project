import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from tkinter import filedialog, messagebox 
from datetime import date
import json
import requests 
from ttkbootstrap.constants import *

API_BASE_URL = "http://localhost:3030"

# ---------------- COMMAND MANAGER APP ---------------- #
class CommandManagerApp:
    """The main application interface for managing commands and devices with persistent storage."""

    def __init__(self, root, commands, devices, token, username):
        self.root = root
        self.token = token
        self.commands = commands
        self.devices = devices
        self.username = username

        self.root.title(f"Command Manager - {username}")
        self.root.geometry("1200x750")

        self._setup_treeview_style()
        # --- UI CHANGE: Apply background color to the root window (Uses the 'darkly' theme's background color) ---
        self.root.configure(background=self.style.colors.bg)

        # Application Header (Optional but nice)
        ttk.Label(self.root, text="Command Management Console", font=("Helvetica", 16, "bold"), bootstyle="primary").pack(pady=(10, 5))

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=10)
        # Note: Frames inside the notebook inherit the theme's default background.

        self.create_commands_tab()
        self.create_devices_tab()

    def _setup_treeview_style(self):
        """Configures the custom styling for the Treeviews."""
        # --- UI CHANGE: Switched theme from 'flatly' to 'darkly' ---
        # Other popular themes include 'cosmo', 'journal', 'superhero'
        self.style = ttk.Style("darkly") 
        self.style.configure("Custom.Treeview",
            rowheight=30, # Slightly taller rows
            font=("Segoe UI", 10)
        )
        self.style.configure("Custom.Treeview.Heading",
            font=("Segoe UI", 11, "bold"),
            background=self.style.colors.light,
            foreground=self.style.colors.dark
        )
        self.style.map("Custom.Treeview", background=[("selected", self.style.colors.primary)])

    # --- API HELPERS ---

    def _fetch_data(self, endpoint, success_message="Data refreshed."):
        """Helper function to fetch data from the API."""
        try:
            resp = requests.get(
                f"{API_BASE_URL}{endpoint}",
                params={"token": self.token},
                timeout=5
            )
            resp.raise_for_status() 
            data = resp.json()
            if data.get("success"):
                return data
            else:
                messagebox.showerror("API Error", data.get("message", "Failed to fetch data."))
                return None
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Connection Error", f"Failed to connect to server: {e}")
            return None

    def _send_data(self, endpoint, data, success_message="Operation successful."):
        """Helper function to send data to the API (POST/DELETE/PUT)."""
        method = "POST"
        if endpoint.endswith('/remove'):
            method = "DELETE"
        elif endpoint.endswith('/update'):
             method = "PUT"
        
        # Payload includes token for req.body.token check
        payload = {"token": self.token, **data}
        # Query params include token as a robust fallback for req.query.token check
        query_params = {"token": self.token} 

        try:
            resp = requests.request(
                method,
                f"{API_BASE_URL}{endpoint}",
                json=payload,
                params=query_params,
                timeout=5
            )
            resp.raise_for_status()
            response_data = resp.json()
            if response_data.get("success"):
                Messagebox.show_info("Success", success_message) 
                return True
            else:
                messagebox.showerror("API Error", response_data.get("message", "Operation failed."))
                return False
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Connection Error", f"Failed to connect to server: {e}")
            return False
    
    # ---------------- COMMANDS TAB ---------------- #

    def create_commands_tab(self):
        """Sets up the UI for the Commands tab."""
        self.tab_commands = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_commands, text="Commands")

        # --- Search/Filter Area (Using Grid for Alignment) ---
        search_frame = ttk.Frame(self.tab_commands, padding=(0, 5))
        search_frame.pack(fill="x")
        
        search_frame.columnconfigure(1, weight=1) # Make the entry field expand

        ttk.Label(search_frame, text="Search Term:", bootstyle="secondary").grid(row=0, column=0, padx=(0, 10), sticky="w")
        self.cmd_search_var = ttk.StringVar()
        ttk.Entry(search_frame, textvariable=self.cmd_search_var, width=30).grid(row=0, column=1, padx=(0, 20), sticky="ew")
        
        ttk.Label(search_frame, text="Filter By:", bootstyle="secondary").grid(row=0, column=2, padx=(0, 10), sticky="w")
        self.cmd_filter_var = ttk.StringVar(value="command")
        filter_options = ["command", "description", "last_used"] 
        ttk.OptionMenu(search_frame, self.cmd_filter_var, "command", *filter_options).grid(row=0, column=3, sticky="ew")
        
        self.cmd_search_var.trace_add("write", lambda n, i, m: self.refresh_commands_table())

        # --- Button Bar ---
        btn_frame = ttk.Frame(self.tab_commands, padding=(0, 10))
        btn_frame.pack(fill="x")
        
        # UI FIX: Used solid colors for main actions (success, danger, info)
        ttk.Button(btn_frame, text="Add Command", bootstyle="success", command=self.open_add_command_window).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Remove Command", bootstyle="danger", command=self.remove_command).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Refresh Data", bootstyle="info", command=self.refresh_commands_table).pack(side="left", padx=(15, 5))
        
        # UI FIX: Used light-outline for export/import for high contrast on dark theme
        ttk.Button(btn_frame, text="Export JSON", bootstyle="light-outline", command=self.export_commands).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Import JSON", bootstyle="light-outline", command=self.import_commands).pack(side="right", padx=5)

        # --- Table Area ---
        table_frame = ttk.Frame(self.tab_commands)
        table_frame.pack(fill="both", expand=True)

        self.cmd_tree = ttk.Treeview(table_frame, show="headings", style="Custom.Treeview")
        self.cmd_tree.pack(fill="both", expand=True)
        self.cmd_tree.bind("<Double-1>", self.copy_command)
        
        # FIX: Configure tags with dark backgrounds and light foreground for contrast
        self.cmd_tree.tag_configure("odd", background="#2a2a2a", foreground="white")
        self.cmd_tree.tag_configure("even", background="#1e1e1e", foreground="white")
        
        self.refresh_commands_table()
    
    def refresh_commands_table(self):
        """Fetches commands from the API, filters, and repopulates the Treeview."""
        
        api_data = self._fetch_data("/commands", "Commands list fetched.")
        if api_data:
            self.commands = api_data.get("commands", [])
        else:
            self.commands = self.commands or [] 

        search = self.cmd_search_var.get().lower()
        col = self.cmd_filter_var.get() or "command"
        
        for item in self.cmd_tree.get_children():
            self.cmd_tree.delete(item)
            
        filtered = [c for c in self.commands if search in str(c.get(col, "")).lower()]
        
        columns = ["id", "command", "description", "last_used"] 
        self.cmd_tree["columns"] = columns
        
        # Setup columns and headings
        self.cmd_tree.heading("id", text="ID", anchor="center")
        self.cmd_tree.column("id", width=50, stretch=NO, anchor="w")
        
        self.cmd_tree.heading("command", text="Command", anchor="center")
        self.cmd_tree.column("command", width=400, stretch=YES, anchor="w")
        
        self.cmd_tree.heading("description", text="Description", anchor="center")
        self.cmd_tree.column("description", width=450, stretch=YES, anchor="w")

        self.cmd_tree.heading("last_used", text="Last Used", anchor="center")
        self.cmd_tree.column("last_used", width=150, stretch=NO, anchor="w")
            
        # Insert data with alternating tags
        for i, c in enumerate(filtered):
            tag = "odd" if i % 2 == 0 else "even"
            self.cmd_tree.insert("", "end", 
                                 values=[c.get("id", ""), c.get("command", ""), c.get("description", ""), c.get("last_used", "")], 
                                 tags=(tag,))

    def open_add_command_window(self):
        """Opens a top-level window to add a new command."""
        win = ttk.Toplevel(self.root)
        win.title("Add New Command")
        win.geometry("450x250")
        win.resizable(False, False)
        
        main_frame = ttk.Frame(win, padding=20)
        main_frame.pack(fill="both", expand=True)

        entries = {}
        for f in ["command", "description"]:
            ttk.Label(main_frame, text=f.capitalize() + ":", font=("Helvetica", 10, "bold")).pack(anchor="w", pady=(5, 0), padx=5)
            entries[f] = ttk.Entry(main_frame, width=40, font=("Helvetica", 11))
            entries[f].pack(fill="x", pady=(0, 10), padx=5)

        def save_cmd():
            """Saves the new command via API and updates the table."""
            cmd_text = entries["command"].get()
            desc_text = entries["description"].get()
            
            if not cmd_text:
                messagebox.showwarning("Missing Info", "Command text is required.")
                return

            data = {
                "command": cmd_text,
                "description": desc_text,
            }
            
            if self._send_data("/commands/add", data, "Command added successfully."):
                win.destroy()
                self.refresh_commands_table()

        ttk.Button(main_frame, text="Save Command", bootstyle="success", command=save_cmd).pack(pady=10, fill="x")

    def copy_command(self, event):
        """Copies the selected command text to the clipboard."""
        row = self.cmd_tree.focus()
        if not row: return
        
        cmd = self.cmd_tree.item(row)["values"][1] 
        self.root.clipboard_clear()
        self.root.clipboard_append(cmd)
        self.root.update()
        Messagebox.show_info("Copied", f"Command copied:\n{cmd}")

    def import_commands(self):
        """Opens a dialog to import commands from a JSON file and sends them to the API."""
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not file_path: return
        
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read/parse JSON file: {e}")
            return
            
        commands_to_import = [{"command": c.get("command"), "description": c.get("description", "")}
                              for c in data if c.get("command")]

        if not commands_to_import:
            messagebox.showwarning("Import Failed", "No valid commands found in the file.")
            return

        api_data = {"commands": commands_to_import}
        
        if self._send_data("/commands/import", api_data, f"{len(commands_to_import)} commands imported successfully."):
            self.refresh_commands_table()

    def export_commands(self):
        """Opens a dialog to export all locally held commands to a JSON file."""
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not file_path: return
        
        try:
            with open(file_path, "w") as f:
                json.dump(self.commands, f, indent=4) 
            Messagebox.show_info("Exported", f"{len(self.commands)} commands exported!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export commands: {e}")

    def remove_command(self):
        """Removes the selected command via API."""
        row = self.cmd_tree.focus()
        if not row:
            messagebox.showwarning("No selection", "Select a command to remove")
            return
            
        values = self.cmd_tree.item(row)["values"]
        cmd_id = values[0]
        cmd_name = values[1]
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to remove '{cmd_name}' (ID: {cmd_id})?"):
            data = {"id": cmd_id}
            
            if self._send_data("/commands/remove", data, f"Command '{cmd_name}' removed."):
                self.refresh_commands_table()

    # ---------------- DEVICES TAB ---------------- #
    
    def create_devices_tab(self):
        """Sets up the UI for the Devices tab."""
        self.tab_devices = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_devices, text="Devices")

        # --- Search/Filter Area (Using Grid for Alignment) ---
        search_frame = ttk.Frame(self.tab_devices, padding=(0, 5))
        search_frame.pack(fill="x")
        
        search_frame.columnconfigure(1, weight=1)

        ttk.Label(search_frame, text="Search Term:", bootstyle="secondary").grid(row=0, column=0, padx=(0, 10), sticky="w")
        self.dev_search_var = ttk.StringVar()
        ttk.Entry(search_frame, textvariable=self.dev_search_var, width=30).grid(row=0, column=1, padx=(0, 20), sticky="ew")
        
        ttk.Label(search_frame, text="Filter By:", bootstyle="secondary").grid(row=0, column=2, padx=(0, 10), sticky="w")
        self.dev_filter_var = ttk.StringVar(value="device")
        filter_options = ["device", "ip"] 
        ttk.OptionMenu(search_frame, self.dev_filter_var, "device", *filter_options).grid(row=0, column=3, sticky="ew")
        
        self.dev_search_var.trace_add("write", lambda n, i, m: self.refresh_devices_table())

        # --- Button Bar ---
        btn_frame = ttk.Frame(self.tab_devices, padding=(0, 10))
        btn_frame.pack(fill="x")
        
        # UI FIX: Changed to solid colors for main actions
        ttk.Button(btn_frame, text="Add Device", bootstyle="success", command=self.open_add_device_window).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Remove Device", bootstyle="danger", command=self.remove_device).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Refresh Data", bootstyle="info", command=self.refresh_devices_table).pack(side="left", padx=(15, 5))
        
        # UI FIX: Changed to light-outline for better visibility on dark theme
        ttk.Button(btn_frame, text="Import JSON", bootstyle="light-outline", command=self.import_devices).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Export JSON", bootstyle="light-outline", command=self.export_devices).pack(side="right", padx=5)


        # --- Table Area ---
        table_frame = ttk.Frame(self.tab_devices)
        table_frame.pack(fill="both", expand=True)
        self.dev_tree = ttk.Treeview(table_frame, show="headings", style="Custom.Treeview")
        self.dev_tree.pack(fill="both", expand=True)
        self.dev_tree.bind("<Double-1>", self.copy_device_ip)
        
        # FIX: Configure tags with dark backgrounds and light foreground for contrast
        self.dev_tree.tag_configure("odd", background="#2a2a2a", foreground="white")
        self.dev_tree.tag_configure("even", background="#1e1e1e", foreground="white")
        
        self.refresh_devices_table()

    def refresh_devices_table(self):
        """Fetches devices from the API, filters, and repopulates the Treeview."""
        
        api_data = self._fetch_data("/devices", "Devices list fetched.")
        if api_data:
            self.devices = api_data.get("devices", [])
        else:
            self.devices = self.devices or []
        
        search = self.dev_search_var.get().lower()
        col = self.dev_filter_var.get() or "device"
        
        for item in self.dev_tree.get_children():
            self.dev_tree.delete(item)
            
        filtered = [d for d in self.devices if search in str(d.get(col, "")).lower()]
        
        columns = ["id", "device", "ip"] # Include ID for removal
        self.dev_tree["columns"] = columns
        
        self.dev_tree.heading("id", text="ID", anchor="center")
        self.dev_tree.column("id", width=50, stretch=NO, anchor="w")
        
        self.dev_tree.heading("device", text="Device", anchor="center")
        self.dev_tree.column("device", width=400, stretch=YES, anchor="w")
        
        self.dev_tree.heading("ip", text="IP Address", anchor="center")
        self.dev_tree.column("ip", width=450, stretch=YES, anchor="w")
            
        for i, d in enumerate(filtered):
            tag = "odd" if i % 2 == 0 else "even"
            self.dev_tree.insert("", "end", 
                                 values=[d.get("id", ""), d.get("device", ""), d.get("ip", "")], 
                                 tags=(tag,))

    def open_add_device_window(self):
        """Opens a top-level window to add a new device."""
        win = ttk.Toplevel(self.root)
        win.title("Add New Device")
        win.geometry("450x250")
        win.resizable(False, False)
        
        main_frame = ttk.Frame(win, padding=20)
        main_frame.pack(fill="both", expand=True)

        entries = {}
        for f in ["device", "ip"]:
            ttk.Label(main_frame, text=f.capitalize() + ":", font=("Helvetica", 10, "bold")).pack(anchor="w", pady=(5, 0), padx=5)
            entries[f] = ttk.Entry(main_frame, width=40, font=("Helvetica", 11))
            entries[f].pack(fill="x", pady=(0, 10), padx=5)

        def save_dev():
            """Saves the new device via API and updates the table."""
            dev_name = entries["device"].get()
            ip_addr = entries["ip"].get()
            
            if not dev_name or not ip_addr:
                messagebox.showwarning("Missing Info", "Device name and IP are required.")
                return

            data = {"device": dev_name, "ip": ip_addr}
            
            if self._send_data("/devices/add", data, "Device added successfully."):
                win.destroy()
                self.refresh_devices_table()

        ttk.Button(main_frame, text="Save Device", bootstyle="success", command=save_dev).pack(pady=10, fill="x")

    def copy_device_ip(self, event):
        """Copies the selected device's IP address to the clipboard."""
        row = self.dev_tree.focus()
        if not row: return
        
        ip = self.dev_tree.item(row)["values"][2] 
        self.root.clipboard_clear()
        self.root.clipboard_append(ip)
        self.root.update()
        Messagebox.show_info("Copied", f"IP copied:\n{ip}")

    def import_devices(self):
        """Opens a dialog to import devices from a JSON file and sends them to the API."""
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not file_path: return
        
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read/parse JSON file: {e}")
            return
            
        devices_to_import = [{"device": d.get("device"), "ip": d.get("ip")}
                             for d in data if d.get("device") and d.get("ip")]

        if not devices_to_import:
            messagebox.showwarning("Import Failed", "No valid devices found in the file.")
            return

        # --- FIX: Iterate and call the single ADD endpoint for each device ---
        success_count = 0
        for device_data in devices_to_import:
            # Note: This is less efficient than a bulk API, but functional
            if self._send_data("/devices/add", device_data, f"Device {device_data['device']} added."):
                success_count += 1
        
        # Only refresh and show summary if any devices were attempted
        if success_count > 0:
            Messagebox.show_info("Import Complete", f"{success_count} device(s) successfully imported.")
            self.refresh_devices_table()
        # --- END FIX ---
            
    def export_devices(self):
        """Opens a dialog to export all locally held devices to a JSON file."""
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not file_path: return
        
        try:
            with open(file_path, "w") as f:
                json.dump(self.devices, f, indent=4)
            Messagebox.show_info("Exported", f"{len(self.devices)} devices exported!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export devices: {e}")
            
    def remove_device(self):
        """Removes the selected device via API."""
        row = self.dev_tree.focus()
        if not row:
            messagebox.showwarning("No selection", "Select a device to remove")
            return
            
        values = self.dev_tree.item(row)["values"]
        dev_id = values[0]
        dev_name = values[1]
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to remove '{dev_name}' (ID: {dev_id})?"):
            data = {"id": dev_id}
            
            if self._send_data("/devices/remove", data, f"Device '{dev_name}' removed."):
                self.refresh_devices_table()