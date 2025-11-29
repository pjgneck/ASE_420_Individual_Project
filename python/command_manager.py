import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from tkinter import filedialog, messagebox # Use standard messagebox for error/warnings
from datetime import date
import json
import requests # Added for API calls

API_BASE_URL = "http://localhost:3030"

# ---------------- COMMAND MANAGER APP ---------------- #
class CommandManagerApp:
    """The main application interface for managing commands and devices."""

    def __init__(self, root, commands, devices, token, username):
        self.root = root
        self.token = token
        self.commands = commands
        self.devices = devices
        self.username = username

        self.root.title(f"Command Manager - {username}")
        self.root.geometry("1150x700")

        self._setup_treeview_style()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.create_commands_tab()
        self.create_devices_tab()

    def _setup_treeview_style(self):
        """Configures the custom styling for the Treeviews."""
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
        # Removed self.style.tag_configure calls here to fix the AttributeError

    def _fetch_data(self, endpoint, success_message="Data refreshed."):
        """Helper function to fetch data from the API."""
        try:
            resp = requests.get(
                f"{API_BASE_URL}{endpoint}",
                params={"token": self.token},
                timeout=5
            )
            resp.raise_for_status() # Raise exception for bad status codes (4xx or 5xx)
            data = resp.json()
            if data.get("success"):
                return data
            else:
                # FIXED: Use tkinter messagebox for error dialogs
                messagebox.showerror("API Error", data.get("message", "Failed to fetch data."))
                return None
        except requests.exceptions.RequestException as e:
            # FIXED: Use tkinter messagebox for connection error dialogs
            messagebox.showerror("Connection Error", f"Failed to connect to server: {e}")
            return None

    def _send_data(self, endpoint, data, success_message="Operation successful."):
        """Helper function to send data to the API (POST/DELETE/PUT)."""
        method = "POST"
        if endpoint.endswith('/remove'):
            method = "DELETE"
        elif endpoint.endswith('/update'):
             method = "PUT"
        
        # 1. Payload includes token (for req.body.token check on backend)
        payload = {"token": self.token, **data}
        
        # 2. Query params also include token (for req.query.token check on backend, safer for DELETE/PUT)
        query_params = {"token": self.token} 

        try:
            resp = requests.request(
                method,
                f"{API_BASE_URL}{endpoint}",
                json=payload,
                params=query_params, # Send token via query parameter as a reliable backup
                timeout=5
            )
            resp.raise_for_status()
            response_data = resp.json()
            if response_data.get("success"):
                # Use ttkbootstrap Messagebox for success/info messages
                Messagebox.show_info("Success", success_message) 
                return True
            else:
                # FIXED: Use tkinter messagebox for error dialogs
                messagebox.showerror("API Error", response_data.get("message", "Operation failed."))
                return False
        except requests.exceptions.RequestException as e:
            # FIXED: Use tkinter messagebox for connection error dialogs
            messagebox.showerror("Connection Error", f"Failed to connect to server: {e}")
            return False
    
    # ---------------- COMMANDS TAB ---------------- #

    def create_commands_tab(self):
        """Sets up the UI for the Commands tab."""
        self.tab_commands = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_commands, text="Commands")

        # Search/Filter Frame
        search_frame = ttk.Frame(self.tab_commands)
        search_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(search_frame, text="Search:").pack(side="left", padx=5)
        self.cmd_search_var = ttk.StringVar()
        ttk.Entry(search_frame, textvariable=self.cmd_search_var, width=25).pack(side="left", padx=5)
        
        ttk.Label(search_frame, text="Filter by:").pack(side="left", padx=5)
        self.cmd_filter_var = ttk.StringVar(value="command")
        filter_options = ["command", "description", "last_used"] 
        ttk.OptionMenu(search_frame, self.cmd_filter_var, "command", *filter_options).pack(side="left")
        
        self.cmd_search_var.trace_add("write", lambda n, i, m: self.refresh_commands_table())

        # Button Frame
        btn_frame = ttk.Frame(self.tab_commands)
        btn_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(btn_frame, text="Add Command", bootstyle="success-outline", command=self.open_add_command_window).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Remove Command", bootstyle="danger-outline", command=self.remove_command).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Refresh", bootstyle="info-outline", command=self.refresh_commands_table).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Import JSON", bootstyle="secondary-outline", command=self.import_commands).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Export JSON", bootstyle="secondary-outline", command=self.export_commands).pack(side="left", padx=5)

        # Table Frame and Treeview
        table_frame = ttk.Frame(self.tab_commands)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.cmd_tree = ttk.Treeview(table_frame, show="headings", style="Custom.Treeview")
        self.cmd_tree.pack(fill="both", expand=True)
        self.cmd_tree.bind("<Double-1>", self.copy_command)
        
        # Configure tags on the Treeview widget itself (Fix for AttributeError)
        self.cmd_tree.tag_configure("odd", background="#f9f9f9")
        self.cmd_tree.tag_configure("even", background="#ffffff")
        
        self.refresh_commands_table()
    
    def refresh_commands_table(self):
        """Fetches commands from the API, filters, and repopulates the Treeview."""
        
        api_data = self._fetch_data("/commands", "Commands list fetched.")
        if api_data:
            self.commands = api_data.get("commands", [])
        else:
            # Keep existing list if API fails
            self.commands = self.commands or [] 

        search = self.cmd_search_var.get().lower()
        col = self.cmd_filter_var.get() or "command"
        
        # Clear existing entries
        for item in self.cmd_tree.get_children():
            self.cmd_tree.delete(item)
            
        filtered = [c for c in self.commands if search in str(c.get(col, "")).lower()]
        
        columns = ["id", "command", "description", "last_used"] # Include ID for removal
        self.cmd_tree["columns"] = columns
        
        # Setup columns and headings
        self.cmd_tree.heading("id", text="ID", anchor="center")
        self.cmd_tree.column("id", width=50, anchor="w")
        for c in columns[1:]:
            width = 300 if c == "command" else 150
            self.cmd_tree.heading(c, text=c.capitalize(), anchor="center")
            self.cmd_tree.column(c, width=width, anchor="w")
            
        # Insert data with alternating tags
        for i, c in enumerate(filtered):
            tag = "odd" if i % 2 == 0 else "even"
            self.cmd_tree.insert("", "end", 
                                 values=[c.get("id", ""), c.get("command", ""), c.get("description", ""), c.get("last_used", "")], 
                                 tags=(tag,))

    def open_add_command_window(self):
        """Opens a top-level window to add a new command."""
        win = ttk.Toplevel(self.root)
        win.title("Add Command")
        win.geometry("400x200")
        
        entries = {}
        for f in ["command", "description"]:
            ttk.Label(win, text=f.capitalize() + ":").pack(anchor="w", pady=3, padx=10)
            entries[f] = ttk.Entry(win, width=35)
            entries[f].pack(fill="x", pady=2, padx=10)

        def save_cmd():
            """Saves the new command via API and updates the table."""
            cmd_text = entries["command"].get()
            desc_text = entries["description"].get()
            
            if not cmd_text:
                # FIXED: Use tkinter messagebox.showwarning
                messagebox.showwarning("Missing Info", "Command text is required.")
                return

            data = {
                "command": cmd_text,
                "description": desc_text,
            }
            
            if self._send_data("/commands/add", data, "Command added successfully."):
                win.destroy()
                self.refresh_commands_table()

        ttk.Button(win, text="Save Command", bootstyle="success", command=save_cmd).pack(pady=10)

    def copy_command(self, event):
        """Copies the selected command text to the clipboard."""
        row = self.cmd_tree.focus()
        if not row: return
        
        # Command is the second element (index 1) in the values list, after ID (index 0)
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
            # FIXED: Use tkinter messagebox.showerror
            messagebox.showerror("Error", f"Failed to read/parse JSON file: {e}")
            return
            
        # Only keep 'command' and 'description' fields for upload
        commands_to_import = [{"command": c.get("command"), "description": c.get("description", "")}
                              for c in data if c.get("command")]

        if not commands_to_import:
            # FIXED: Use tkinter messagebox.showwarning
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
                # Use self.commands (last fetched data) for export
                json.dump(self.commands, f, indent=4) 
            Messagebox.show_info("Exported", f"{len(self.commands)} commands exported!")
        except Exception as e:
            # FIXED: Use tkinter messagebox.showerror
            messagebox.showerror("Error", f"Failed to export commands: {e}")

    def remove_command(self):
        """Removes the selected command via API."""
        row = self.cmd_tree.focus()
        if not row:
            # FIXED: Use tkinter messagebox.showwarning
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
        self.tab_devices = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_devices, text="Devices")

        # Search/Filter Frame
        search_frame = ttk.Frame(self.tab_devices)
        search_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(search_frame, text="Search:").pack(side="left", padx=5)
        self.dev_search_var = ttk.StringVar()
        ttk.Entry(search_frame, textvariable=self.dev_search_var, width=25).pack(side="left", padx=5)
        
        ttk.Label(search_frame, text="Filter by:").pack(side="left", padx=5)
        self.dev_filter_var = ttk.StringVar(value="device")
        filter_options = ["device", "ip"] 
        ttk.OptionMenu(search_frame, self.dev_filter_var, "device", *filter_options).pack(side="left")
        
        self.dev_search_var.trace_add("write", lambda n, i, m: self.refresh_devices_table())

        # Button Frame
        btn_frame = ttk.Frame(self.tab_devices)
        btn_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(btn_frame, text="Add Device", bootstyle="success-outline", command=self.open_add_device_window).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Remove Device", bootstyle="danger-outline", command=self.remove_device).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Refresh", bootstyle="info-outline", command=self.refresh_devices_table).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Import JSON", bootstyle="secondary-outline", command=self.import_devices).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Export JSON", bootstyle="secondary-outline", command=self.export_devices).pack(side="left", padx=5)

        # Table Frame and Treeview
        table_frame = ttk.Frame(self.tab_devices)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.dev_tree = ttk.Treeview(table_frame, show="headings", style="Custom.Treeview")
        self.dev_tree.pack(fill="both", expand=True)
        self.dev_tree.bind("<Double-1>", self.copy_device_ip)
        
        # Configure tags on the Treeview widget itself (Fix for AttributeError)
        self.dev_tree.tag_configure("odd", background="#f9f9f9")
        self.dev_tree.tag_configure("even", background="#ffffff")
        
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
        self.dev_tree.column("id", width=50, anchor="w")
        for c in columns[1:]:
            width = 250 if c == "device" else 150
            self.dev_tree.heading(c, text=c.capitalize(), anchor="center")
            self.dev_tree.column(c, width=width, anchor="w")
            
        for i, d in enumerate(filtered):
            tag = "odd" if i % 2 == 0 else "even"
            self.dev_tree.insert("", "end", 
                                 values=[d.get("id", ""), d.get("device", ""), d.get("ip", "")], 
                                 tags=(tag,))

    def open_add_device_window(self):
        """Opens a top-level window to add a new device."""
        win = ttk.Toplevel(self.root)
        win.title("Add Device")
        win.geometry("400x200")
        
        entries = {}
        for f in ["device", "ip"]:
            ttk.Label(win, text=f.capitalize() + ":").pack(anchor="w", pady=3, padx=10)
            entries[f] = ttk.Entry(win, width=35)
            entries[f].pack(fill="x", pady=2, padx=10)

        def save_dev():
            """Saves the new device via API and updates the table."""
            dev_name = entries["device"].get()
            ip_addr = entries["ip"].get()
            
            if not dev_name or not ip_addr:
                # FIXED: Use tkinter messagebox.showwarning
                messagebox.showwarning("Missing Info", "Device name and IP are required.")
                return

            data = {"device": dev_name, "ip": ip_addr}
            
            if self._send_data("/devices/add", data, "Device added successfully."):
                win.destroy()
                self.refresh_devices_table()

        ttk.Button(win, text="Save Device", bootstyle="success", command=save_dev).pack(pady=10)

    def copy_device_ip(self, event):
        """Copies the selected device's IP address to the clipboard."""
        row = self.dev_tree.focus()
        if not row: return
        
        # IP is the third element (index 2) in the values list, after ID and Device Name
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
            # FIXED: Use tkinter messagebox.showerror
            messagebox.showerror("Error", f"Failed to read/parse JSON file: {e}")
            return
            
        devices_to_import = [{"device": d.get("device"), "ip": d.get("ip")}
                             for d in data if d.get("device") and d.get("ip")]

        if not devices_to_import:
            # FIXED: Use tkinter messagebox.showwarning
            messagebox.showwarning("Import Failed", "No valid devices found in the file.")
            return

        api_data = {"devices": devices_to_import}
        
        # NOTE: Your server only has a single POST /devices/add. For bulk import, 
        # the server API would ideally have a bulk import endpoint (e.g., /devices/import). 
        # Sticking with the existing logic for now until an API change is requested.
        
        # For simplicity, we just refresh the table and show the message based on local data.
        # This part should be updated if you implement a bulk /devices/import API endpoint.
        
        Messagebox.show_info("Import Note", "Please implement a bulk import API endpoint for devices.")


    def export_devices(self):
        """Opens a dialog to export all locally held devices to a JSON file."""
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not file_path: return
        
        try:
            with open(file_path, "w") as f:
                json.dump(self.devices, f, indent=4)
            Messagebox.show_info("Exported", f"{len(self.devices)} devices exported!")
        except Exception as e:
            # FIXED: Use tkinter messagebox.showerror
            messagebox.showerror("Error", f"Failed to export devices: {e}")
            
    def remove_device(self):
        """Removes the selected device via API."""
        row = self.dev_tree.focus()
        if not row:
            # FIXED: Use tkinter messagebox.showwarning
            messagebox.showwarning("No selection", "Select a device to remove")
            return
            
        values = self.dev_tree.item(row)["values"]
        dev_id = values[0]
        dev_name = values[1]
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to remove '{dev_name}' (ID: {dev_id})?"):
            data = {"id": dev_id}
            
            if self._send_data("/devices/remove", data, f"Device '{dev_name}' removed."):
                self.refresh_devices_table()