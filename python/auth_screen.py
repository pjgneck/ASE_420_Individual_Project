
import requests
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
# Assuming CommandManagerApp is in command_manager_app.py based on previous steps
from command_manager import CommandManagerApp 

API_BASE_URL = "http://localhost:3030"

# ---------------- AUTH SCREEN ---------------- #
class AuthScreen:
    """Handles the user login/signup screen and authentication with the server."""
    
    def __init__(self):
        # Initialize the main Tkinter window
        self.root = ttk.Window(themename="flatly")
        self.root.title("Login / Sign Up")
        self.root.geometry("400x250") # Increased size to fit the new button

        self.username_var = ttk.StringVar()
        self.password_var = ttk.StringVar()

        # Create UI elements
        ttk.Label(self.root, text="Username:").pack(anchor="w", padx=20, pady=5)
        ttk.Entry(self.root, textvariable=self.username_var).pack(fill="x", padx=20)

        ttk.Label(self.root, text="Password:").pack(anchor="w", padx=20, pady=5)
        ttk.Entry(self.root, textvariable=self.password_var, show="*").pack(fill="x", padx=20)
        
        # Frame for holding both login and signup buttons
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=20)

        ttk.Button(btn_frame, text="Login", bootstyle="success", command=self.authenticate).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Sign Up", bootstyle="info-outline", command=self.sign_up).pack(side="left", padx=10)
        
        self.root.mainloop()

    def _validate_input(self, action="Login"):
        """Helper to validate username and password presence."""
        username = self.username_var.get()
        password = self.password_var.get()
        
        if not username or not password:
            messagebox.showwarning("Missing Info", f"Enter both username and password for {action}")
            return None, None
        return username, password

    def authenticate(self):
        """Attempts to authenticate the user against the server."""
        username, password = self._validate_input("Login")
        if not username: return
        
        try:
            resp = requests.post(
                f"{API_BASE_URL}/login",
                json={"username": username, "password": password},
                timeout=5
            )
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    self._transition_to_app(data, username)
                    return
                else:
                    messagebox.showerror("Login Failed", "Invalid username or password")
            else:
                 messagebox.showerror("Login Failed", f"Authentication failed with status code {resp.status_code}")
                 
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Server error or connection failed: {e}")

    def sign_up(self):
        """Attempts to register a new user against the server."""
        username, password = self._validate_input("Sign Up")
        if not username: return

        try:
            resp = requests.post(
                f"{API_BASE_URL}/signup",
                json={"username": username, "password": password},
                timeout=5
            )

            data = resp.json()
            if resp.status_code == 201 and data.get("success"):
                messagebox.showinfo("Success", "Registration successful! You are now logged in.")
                self._transition_to_app(data, username)
            elif resp.status_code == 409:
                messagebox.showwarning("Registration Failed", "Username already taken.")
            elif data.get("message"):
                messagebox.showerror("Registration Failed", data["message"])
            else:
                messagebox.showerror("Registration Failed", f"Registration failed with status code {resp.status_code}")

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Server error or connection failed: {e}")

    def _transition_to_app(self, data, username):
        """Helper to clear the screen and launch the main application."""
        token = data.get("token")
        commands = data.get("commands", [])
        devices = data.get("devices", [])
        
        # Clear the current screen widgets
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Transition to the main application
        CommandManagerApp(self.root, commands, devices, token, username)