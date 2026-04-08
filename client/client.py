import socket
import threading
import customtkinter as ctk
import sys
import os
import json
import time
from dotenv import load_dotenv

# Load explicitly handled .env variables
load_dotenv()
DEFAULT_HOST = os.getenv('HOST', '127.0.0.1')
DEFAULT_PORT = int(os.getenv('PORT', 55555))

class ChatClientGUI:
    def __init__(self, app, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.win = app
        self.host = host
        self.port = port
        
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = False
        self.gui_done = False
        self.token = None
        self.username = None
        self.last_typed = 0
        self.typing_timer = None
        self.latest_online_users = []
        
        # Setup Main Window
        self.win.title("Mesynk Plus")
        self.win.geometry("800x600") 
        self.win.minsize(600, 500)
        
        self.win.grid_rowconfigure(0, weight=1)
        self.win.grid_columnconfigure(0, weight=1)
        
        # Build Sleek Login Frame
        self.build_login_ui()
        self.win.protocol("WM_DELETE_WINDOW", self.stop)
        self.win.lift()

    def build_login_ui(self):
        if hasattr(self, 'login_frame') and self.login_frame.winfo_exists():
            self.login_frame.destroy()
            
        self.login_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        self.login_frame.grid(row=0, column=0, sticky="nsew")
        self.login_frame.grid_rowconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.login_frame.grid_columnconfigure(0, weight=1)
        
        self.brand_label = ctk.CTkLabel(self.login_frame, text="Mesynk", font=("Outfit", 36, "bold"), text_color="#3B8EDB")
        self.brand_label.grid(row=0, column=0, pady=(50, 20))
        
        self.username_entry = ctk.CTkEntry(self.login_frame, placeholder_text="Username", width=280, height=50, font=("Inter", 15))
        self.username_entry.grid(row=1, column=0, pady=10)
        
        self.password_entry = ctk.CTkEntry(self.login_frame, placeholder_text="Password", width=280, height=50, font=("Inter", 15), show="*")
        self.password_entry.grid(row=2, column=0, pady=10)
        self.password_entry.bind('<Return>', lambda event: self.start_auth("LOGIN"))
        
        button_frame = ctk.CTkFrame(self.login_frame, fg_color="transparent")
        button_frame.grid(row=3, column=0, pady=10)
        
        self.login_btn = ctk.CTkButton(button_frame, text="Login", width=135, height=50, font=("Inter", 15, "bold"), command=lambda: self.start_auth("LOGIN"))
        self.login_btn.grid(row=0, column=0, padx=5)

        self.register_btn = ctk.CTkButton(button_frame, text="Register", width=135, height=50, font=("Inter", 15, "bold"), fg_color="#4CAF50", hover_color="#45a049", command=lambda: self.start_auth("REGISTER"))
        self.register_btn.grid(row=0, column=1, padx=5)
        
        self.error_label = ctk.CTkLabel(self.login_frame, text="", text_color="#FF6B6B", font=("Inter", 13))
        self.error_label.grid(row=4, column=0, pady=(10, 50))

    def start_auth(self, action):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            self.error_label.configure(text="Username and Password are required.", text_color="#FF6B6B")
            return
            
        self.login_btn.configure(state="disabled")
        self.register_btn.configure(state="disabled")
        self.username_entry.configure(state="disabled")
        self.password_entry.configure(state="disabled")
        self.error_label.configure(text="Connecting...", text_color="#FCA311")
        self.win.update_idletasks()
            
        try:
            # Reconnect if previous connection dropped
            try:
                self.client.send(b'')
            except:
                self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client.connect((self.host, self.port))
            
            if not self.running:
                self.running = True
                threading.Thread(target=self.receive, daemon=True).start()
            
            self.send_json({"type": action, "username": username, "password": password})
            
        except ConnectionRefusedError:
            self.error_label.configure(text="Connection Refused! Is server running?", text_color="#FF6B6B")
            self.reset_login_ui()
        except Exception as e:
            self.error_label.configure(text=f"Error: {e}", text_color="#FF6B6B")
            self.reset_login_ui()

    def reset_login_ui(self):
        if hasattr(self, 'login_btn') and self.login_btn.winfo_exists():
            self.login_btn.configure(state="normal")
            self.register_btn.configure(state="normal")
            self.username_entry.configure(state="normal")
            self.password_entry.configure(state="normal")
        try:
            self.client.close()
            self.running = False
        except:
            pass

    def send_json(self, data):
        try:
            self.client.send((json.dumps(data) + '\n').encode('utf-8'))
        except Exception as e:
            print(f"Send Error: {e}")

    def build_chat_interface(self):
        self.login_frame.destroy()
        self.win.title(f"Mesynk - Logged in as: {self.username}")
        
        self.win.grid_rowconfigure(0, weight=1)
        self.win.grid_columnconfigure(0, weight=3) # Chat area
        self.win.grid_columnconfigure(1, weight=1) # Sidebar
        
        # Main Chat Area
        chat_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        chat_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        chat_frame.grid_rowconfigure(0, weight=1)
        chat_frame.grid_rowconfigure(1, weight=0)
        chat_frame.grid_rowconfigure(2, weight=0)
        chat_frame.grid_columnconfigure(0, weight=1)

        self.text_area = ctk.CTkTextbox(chat_frame, state="disabled", wrap="word", corner_radius=15, font=("Inter", 14), fg_color="#1E1E24")
        self.text_area.grid(row=0, column=0, columnspan=2, pady=(0, 5), sticky="nsew")

        # Typing Indicator
        self.typing_label = ctk.CTkLabel(chat_frame, text="", text_color="#AAAAAA", font=("Inter", 12, "italic"), height=20)
        self.typing_label.grid(row=1, column=0, sticky="w", padx=10)

        # Input Area
        input_frame = ctk.CTkFrame(chat_frame, fg_color="transparent")
        input_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)

        self.input_area = ctk.CTkEntry(input_frame, placeholder_text="Type a message...", corner_radius=20, height=50, font=("Inter", 15))
        self.input_area.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.input_area.bind('<Return>', lambda event: self.write())
        self.input_area.bind('<KeyRelease>', self.on_key_release)

        self.send_button = ctk.CTkButton(input_frame, text="Send", command=self.write, width=90, height=50, corner_radius=20, font=("Inter", 15, "bold"))
        self.send_button.grid(row=0, column=1, sticky="e")
        
        # Sidebar for Online Users
        sidebar = ctk.CTkFrame(self.win, fg_color="#1E1E24", corner_radius=15)
        sidebar.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        sidebar.grid_rowconfigure(1, weight=1)
        sidebar.grid_columnconfigure(0, weight=1)

        self.sidebar_title = ctk.CTkLabel(sidebar, text="Online Users", font=("Inter", 16, "bold"), text_color="#3B8EDB")
        self.sidebar_title.grid(row=0, column=0, pady=15, sticky="n")

        self.online_users_list = ctk.CTkScrollableFrame(sidebar, fg_color="transparent")
        self.online_users_list.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.online_users_labels = []

        self.gui_done = True
        self.input_area.focus()
        
        if hasattr(self, 'latest_online_users') and self.latest_online_users:
            self.update_online_users(self.latest_online_users)

    def update_online_users(self, users):
        if not self.gui_done: return
        for bg in self.online_users_labels:
            bg.destroy()
        self.online_users_labels.clear()

        for user in users:
            color = "#D4AF37" if user == self.username else "#E0E0E0"
            lbl = ctk.CTkLabel(self.online_users_list, text=f"• {user}", font=("Inter", 14), text_color=color, anchor="w")
            lbl.pack(fill="x", padx=10, pady=2)
            self.online_users_labels.append(lbl)
            
        self.online_users_list.update_idletasks()

    def show_typing(self, username):
        if not self.gui_done: return
        if username == self.username: return
        
        self.typing_label.configure(text=f"{username} is typing...")
        if self.typing_timer is not None:
            self.win.after_cancel(self.typing_timer)
        self.typing_timer = self.win.after(2000, lambda: self.typing_label.configure(text=""))

    def show_toast(self, message):
        toast = ctk.CTkLabel(self.win, text=message, fg_color="#3B8EDB", text_color="white", corner_radius=10, font=("Inter", 12, "bold"), padx=15, pady=8)
        toast.place(relx=0.5, rely=0.05, anchor="n")
        self.win.after(3000, toast.destroy)

    def receive(self):
        buffer = ""
        while self.running:
            try:
                data = self.client.recv(1024)
                if not data: break
                
                buffer += data.decode('utf-8')
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    if not line: continue
                    
                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    msg_type = payload.get("type")

                    if msg_type == "AUTH_SUCCESS":
                        message = payload.get("message", "")
                        if payload.get("token"):
                            self.token = payload.get("token")
                            self.username = payload.get("username")
                            self.win.after(0, self.build_chat_interface)
                        else:
                            # Registration success
                            self.win.after(0, lambda m=message: self.error_label.configure(text=m, text_color="#4CAF50"))
                            self.win.after(0, self.reset_login_ui)

                    elif msg_type == "AUTH_ERROR":
                        msg = payload.get("message")
                        self.win.after(0, lambda err=msg: self.error_label.configure(text=err, text_color="#FF6B6B"))
                        self.win.after(0, self.reset_login_ui)

                    elif msg_type == "MSG":
                        if self.gui_done:
                            user = payload.get('username')
                            text = payload.get('text')
                            ts = payload.get('timestamp')
                            formatted_msg = f"[{ts}] {user}: {text}\n\n"
                            
                            def update_text(m=formatted_msg):
                                self.text_area.configure(state="normal")
                                self.text_area.insert('end', m)
                                self.text_area.yview('end')
                                self.text_area.configure(state="disabled")
                            
                            self.win.after(0, update_text)
                            
                            if user != self.username:
                                self.win.after(0, lambda: self.typing_label.configure(text=""))

                    elif msg_type == "SYS_MSG":
                        if self.gui_done:
                            msg = payload.get("message")
                            self.win.after(0, lambda m=msg: self.show_toast(m))

                    elif msg_type == "ONLINE_USERS":
                        users = payload.get("users", [])
                        self.latest_online_users = users
                        if self.gui_done:
                            self.win.after(0, lambda u=users: self.update_online_users(u))

                    elif msg_type == "TYPING":
                        if self.gui_done:
                            user = payload.get("username")
                            self.win.after(0, lambda u=user: self.show_typing(u))

            except Exception as e:
                print(f"Disconnected: {e}")
                if self.gui_done:
                    self.win.after(0, lambda: self.show_toast("DISCONNECTED FROM SERVER"))
                self.win.after(0, self.reset_login_ui)
                break

    def on_key_release(self, event):
        if not self.gui_done: return
        # Don't trigger typing for "Enter" key
        if event.keysym == 'Return': return
        
        current_time = time.time()
        if current_time - self.last_typed > 1.5:
            self.send_json({"type": "TYPING"})
            self.last_typed = current_time

    def write(self):
        if not self.gui_done: return
        
        text = self.input_area.get()
        if text.strip():
            self.send_json({"type": "MSG", "text": text.strip()})
            self.input_area.delete(0, 'end')

    def stop(self):
        self.running = False
        self.win.destroy()
        try:
            self.client.close()
        except:
            pass
        sys.exit(0)

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    app = ctk.CTk()
    client = ChatClientGUI(app)
    app.mainloop()
