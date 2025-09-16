import tkinter as tk
from tkinter import ttk, messagebox
from user_auth import add_user, authenticate, get_user
from command_manager import CommandManager

def show_auth():
    auth_root = tk.Tk()
    auth_root.title("User Authentication")
    auth_root.geometry("450x400")  # Taller window

    notebook = ttk.Notebook(auth_root)
    notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # --------------------- LOGIN TAB --------------------- #
    login_tab = tk.Frame(notebook)
    notebook.add(login_tab, text="Login")

    tk.Label(login_tab, text="Username:").pack(pady=10)
    login_username = tk.Entry(login_tab, width=30)
    login_username.pack(pady=5)

    tk.Label(login_tab, text="Password:").pack(pady=10)
    login_password = tk.Entry(login_tab, show="*", width=30)
    login_password.pack(pady=5)

    def try_login():
        username = login_username.get().strip()
        password = login_password.get()
        if authenticate(username, password):
            user = get_user(username)
            auth_root.destroy()
            main_root = tk.Tk()
            app = CommandManager(main_root, user)
            main_root.mainloop()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

    tk.Button(login_tab, text="Login", width=15, command=try_login).pack(pady=15)

    # --------------------- SIGNUP TAB --------------------- #
    signup_tab = tk.Frame(notebook)
    notebook.add(signup_tab, text="Sign Up")

    tk.Label(signup_tab, text="Username:").pack(pady=8)
    signup_username = tk.Entry(signup_tab, width=30)
    signup_username.pack(pady=5)

    tk.Label(signup_tab, text="Password:").pack(pady=8)
    signup_password = tk.Entry(signup_tab, show="*", width=30)
    signup_password.pack(pady=5)

    tk.Label(signup_tab, text="Confirm Password:").pack(pady=8)
    signup_confirm = tk.Entry(signup_tab, show="*", width=30)
    signup_confirm.pack(pady=5)

    tk.Label(signup_tab, text="Department:").pack(pady=8)
    signup_dept = tk.Entry(signup_tab, width=30)
    signup_dept.pack(pady=5)
    signup_dept.insert(0, "Help Desk")

    def try_signup():
        username = signup_username.get().strip()
        password = signup_password.get()
        confirm = signup_confirm.get()
        department = signup_dept.get().strip()

        if not username or not password or not department:
            messagebox.showerror("Error", "All fields are required.")
            return
        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match.")
            return
        if add_user(username, password, department):
            messagebox.showinfo("Success", "Account created! You can now log in.")
            notebook.select(0)  # Switch to login tab
        else:
            messagebox.showerror("Error", "Username already exists.")

    tk.Button(signup_tab, text="Sign Up", width=15, command=try_signup).pack(pady=15)

    auth_root.mainloop()
