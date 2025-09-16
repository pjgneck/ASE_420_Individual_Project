# SSH Command Manager

## Problem

   System administrators often rely on a variety of commands across multiple devices, which can become difficult to track and share efficiently, Without an organized solution, users may waste time searching for the correct commands or risk errors when executing them.

---

## Solution

   A Python Tkinter application to manage SSH commands, devices, and departments with user authentication.  
   Designed for IT teams, help desks, and network administrators.

---

## Features

   ### User Authentication
   - Secure login system with hashed passwords
   - Department-based access

   ### Commands Tab
   - View SSH commands
   - Search and filter by command, description, ID, last used
   - Copy commands to clipboard

   ### Devices Tab
   - Track servers, routers, switches, and other devices
   - Search and filter options

   ### Manage Tab (Managers only)
   - Add departments, users, managers, and team leads

---


## Requirements

- Python 3.x
- `tkinter` (usually included with Python)
- Optional JSON files pre-created in `data/` folder:
  - `users_auth.json`
  - `departments.json`
- Install Tkinter if needed:
```bash
pip install tk
```
---

## Default Access

To quickly start the application, a placeholder user can be used:
   - Username: admin
   - Password: password123 (hash this before storing!)
   - Department: Help Desk
Allows immediate access without creating a new user.

---

## Usage
   - Run run_py.bat
   - Log in with valid credentials
   - Navigate Commands, Devices, and Manage tabs
   - Use search/filter to find commands or devices quickly
   - Managers can add departments, users, and assign roles

---

## Security Notes
   - Passwords must be hashed in users_auth.json
   - Users only access their department data
   - Copying a command updates the last_used field automatically

---

## Contributing
   - Fork the repository
   - Create a new branch for your feature or bugfix
   - Make changes
   - Submit a pull request