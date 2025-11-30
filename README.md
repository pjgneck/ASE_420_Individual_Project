# Command Grimoire

A streamlined solution for managing SSH commands, devices, and departmental access within IT environments.

---

## 🔧 Problem

   System administrators often rely on numerous commands across multiple devices, making it difficult to track, organize, and share them efficiently. Without a centralized system, users may waste time searching for the correct command or risk executing outdated or incorrect information.

---

## 💡 Solution

   Command Grimoire is a Python Tkinter-based application designed to manage SSH commands, devices, and departments with built‑in user authentication. It is ideal for IT teams, help desks, and network administrators who need a structured and secure command repository.

---

## ✨ Features

   ## User Authentication
   - Secure login with hashed passwords
   - Department‑based access control

   ## Commands Tab
   - View and organize terminal commands
   - Search and filter by command, description, ID, or last‑used date
   - Copy commands directly to clipboard

   ## Devices Tab
   - Track servers, routers, switches, and other hardware
   - Search and filter device information easily

---

## Usage
   - Run run_py.bat
   - Log in with valid credentials.
   - Navigate between Commands, and Devices tabs
   - Use search and filtering tools to quickly locate commands or devices.
   - Managers can add departments, create users, and assign roles.

---

## 🔒 Security Notes
   - All passwords must be hashed in users_auth.json.
   - Users only have access to data within their assigned department.
   - Copying a command automatically updates the last_used field.

---

## 🤝 Contributing
   - Fork the repository
   - Create a new branch for your feature or bugfix
   - Make changes
   - Submit a pull request