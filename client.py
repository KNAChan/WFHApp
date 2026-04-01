import tkinter as tk
from tkinter import messagebox
import threading
import time
import requests
import socketio
from pynput import mouse, keyboard

# ---------------- CONFIG ----------------
SERVER_URL = "http://192.168.100.174:5000"
SIO = socketio.Client()

USER = None
last_activity_time = time.time()
USERS_STATUS = {}

# Status colors
STATUS_COLORS = {
    "active": "#2ecc71",
    "busy": "#e74c3c",
    "away": "#f39c12",
    "offline": "#95a5a6"
}

IDLE_THRESHOLD = 10  # change to 600 for 10 min


# ---------------- APP ----------------
class WFHApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("WFH Status App")
        self.geometry("420x500")
        self.configure(bg="#1e1e2f")

        self.current_status = "offline"
        self.checked_in = False
        self.in_call = False
        self.idle_thread_running = False

        self.user_labels = {}

        self.create_login()

    # ---------------- LOGIN ----------------
    def create_login(self):
        self.clear()

        frame = tk.Frame(self, bg="#1e1e2f")
        frame.pack(expand=True)

        tk.Label(frame, text="WFH Login", font=("Segoe UI", 16, "bold"),
                 bg="#1e1e2f", fg="white").pack(pady=20)

        self.username = tk.Entry(frame, font=("Segoe UI", 12))
        self.username.pack(pady=5)

        self.password = tk.Entry(frame, show="*", font=("Segoe UI", 12))
        self.password.pack(pady=5)

        tk.Button(frame, text="Login", width=15, command=self.login).pack(pady=15)

    def login(self):
        global USER
        try:
            res = requests.post(f"{SERVER_URL}/login", json={
                "username": self.username.get(),
                "password": self.password.get()
            })

            if res.status_code == 200:
                USER = res.json()
                self.current_status = "offline"
                self.create_main()
                self.start_tracking()
            else:
                messagebox.showerror("Error", "Login failed")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ---------------- MAIN UI ----------------
    def create_main(self):
        self.clear()

        main = tk.Frame(self, bg="#1e1e2f")
        main.pack(fill="both", expand=True)

        tk.Label(main, text=f"Welcome {USER['name']}",
                 font=("Segoe UI", 14, "bold"),
                 bg="#1e1e2f", fg="white").pack(pady=10)

        # Status display
        self.status_label = tk.Label(
            main,
            text="OFFLINE",
            font=("Segoe UI", 12, "bold"),
            bg=STATUS_COLORS["offline"],
            fg="white",
            width=20,
            height=2
        )
        self.status_label.pack(pady=10)

        # Buttons
        btn_frame = tk.Frame(main, bg="#1e1e2f")
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Check In", width=12, command=self.check_in).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Check Out", width=12, command=self.check_out).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Call", width=12, command=self.toggle_call).grid(row=1, column=0, pady=5)
        tk.Button(btn_frame, text="Logout", width=12, command=self.logout).grid(row=1, column=1, pady=5)

        # Users list
        tk.Label(main, text="Team Status",
                 font=("Segoe UI", 12, "bold"),
                 bg="#1e1e2f", fg="white").pack(pady=10)

        self.users_frame = tk.Frame(main, bg="#2b2b3c")
        self.users_frame.pack(fill="both", expand=True, padx=10, pady=5)

    def clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    # ---------------- BUTTONS ----------------
    def check_in(self):
        self.checked_in = True
        self.update_status("active")

    def check_out(self):
        self.checked_in = False
        self.in_call = False
        self.update_status("offline")

    def toggle_call(self):
        if not self.checked_in:
            messagebox.showinfo("Info", "Check in first!")
            return

        self.in_call = not self.in_call
        self.update_status("busy" if self.in_call else "active")

    def logout(self):
        if self.checked_in:
            messagebox.showwarning("Warning", "Please check out first!")
            return

        self.in_call = False
        self.update_status("offline")

        global USER
        USER = None

        if SIO.connected:
            SIO.disconnect()

        self.create_login()

    # ---------------- STATUS ----------------
    def update_status(self, status):
        self.current_status = status

        self.status_label.config(
            text=status.upper(),
            bg=STATUS_COLORS.get(status, "gray")
        )

        if USER:
            try:
                SIO.emit("update_status", {
                    "user_id": USER["id"],
                    "status": status,
                    "checked_in": self.checked_in,
                    "in_call": self.in_call
                })
            except:
                pass

    # ---------------- USERS UI ----------------
    def update_users_ui(self):
        for user in USERS_STATUS:
            uid = user["id"]
            name = user["name"]
            status = user["status"]

            color = STATUS_COLORS.get(status, "gray")

            if uid not in self.user_labels:
                row = tk.Frame(self.users_frame, bg="#2b2b3c")
                row.pack(fill="x", pady=2)

                canvas = tk.Canvas(row, width=15, height=15,
                                   bg="#2b2b3c", highlightthickness=0)
                canvas.pack(side="left", padx=5)

                label = tk.Label(row,
                                 text=f"{name} - {status}",
                                 bg="#2b2b3c",
                                 fg="white",
                                 font=("Segoe UI", 10))
                label.pack(side="left")

                self.user_labels[uid] = (canvas, label)

            canvas, label = self.user_labels[uid]
            canvas.delete("all")
            canvas.create_oval(2, 2, 13, 13, fill=color)
            label.config(text=f"{name} - {status}")

    # ---------------- ACTIVITY ----------------
    def start_tracking(self):
        self.start_listeners()
        if not self.idle_thread_running:
            self.idle_thread_running = True
            threading.Thread(target=self.track_status, daemon=True).start()

    def start_listeners(self):
        def on_activity(*args):
            global last_activity_time
            last_activity_time = time.time()

        mouse.Listener(on_move=on_activity, on_click=on_activity).start()
        keyboard.Listener(on_press=on_activity).start()

    def is_idle(self):
        return (time.time() - last_activity_time) > IDLE_THRESHOLD

    def is_online(self):
        try:
            requests.get("https://www.google.com", timeout=3)
            return True
        except:
            return False

    def track_status(self):
        while True:
            time.sleep(1)

            if not self.checked_in:
                continue

            if not self.is_online():
                if self.current_status != "offline":
                    self.update_status("offline")
                continue

            if self.in_call:
                continue

            if self.is_idle():
                if self.current_status != "away":
                    self.update_status("away")
            else:
                if self.current_status != "active":
                    self.update_status("active")


# ---------------- SOCKET ----------------
@SIO.event
def connect():
    print("Connected")

@SIO.event
def disconnect():
    print("Disconnected")

@SIO.on("status_update")
def status_update(data):
    global USERS_STATUS
    USERS_STATUS = data
    try:
        app.after(0, app.update_users_ui)
    except:
        pass


# ---------------- RUN ----------------
if __name__ == "__main__":
    try:
        SIO.connect(SERVER_URL)
    except Exception as e:
        print("Socket error:", e)

    app = WFHApp()
    app.mainloop()