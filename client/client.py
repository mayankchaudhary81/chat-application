import socket
import threading
import customtkinter as ctk
import sys
import os
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
        
        # Setup Main Window
        self.win.title("Mesynk Plus")
        self.win.geometry("600x700") 
        
        self.win.grid_rowconfigure(0, weight=1)
        self.win.grid_columnconfigure(0, weight=1)
        
        # Build Sleek Login Frame
        self.login_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        self.login_frame.grid(row=0, column=0, sticky="nsew")
        self.login_frame.grid_rowconfigure((0, 1, 2, 3), weight=1)
        self.login_frame.grid_columnconfigure(0, weight=1)
        
        # UI Styling (Day 7)
        self.nickname_label = ctk.CTkLabel(self.login_frame, text="Mesynk", font=("Outfit", 36, "bold"), text_color="#3B8EDB")
        self.nickname_label.grid(row=0, column=0, pady=(150, 20))
        
        self.nickname_entry = ctk.CTkEntry(self.login_frame, placeholder_text="Enter Nickname...", width=280, height=50, font=("Inter", 15))
        self.nickname_entry.grid(row=1, column=0, pady=10)
        self.nickname_entry.bind('<Return>', lambda event: self.connect_server())
        
        self.login_btn = ctk.CTkButton(self.login_frame, text="Join Hub", width=280, height=50, font=("Inter", 15, "bold"), command=self.connect_server)
        self.login_btn.grid(row=2, column=0, pady=10)
        
        self.error_label = ctk.CTkLabel(self.login_frame, text="", text_color="#FF6B6B", font=("Inter", 13))
        self.error_label.grid(row=3, column=0, pady=(10, 150))
        
        self.win.protocol("WM_DELETE_WINDOW", self.stop)
        self.win.lift()

    def connect_server(self):
        self.nickname = self.nickname_entry.get().strip()
        if not self.nickname:
            self.error_label.configure(text="Nickname is required.", text_color="#FF6B6B")
            return
            
        # Loading States (Day 5)
        self.login_btn.configure(state="disabled", text="Connecting...", fg_color="#FCA311")
        self.nickname_entry.configure(state="disabled")
        self.error_label.configure(text="")
        self.win.update_idletasks()
            
        try:
            self.client.connect((self.host, self.port))
            # Success!
            self.build_chat_interface()
            self.running = True
            threading.Thread(target=self.receive, daemon=True).start()
        except ConnectionRefusedError:
            self.error_label.configure(text="Connection Refused! Is server.py running?", text_color="#FF6B6B")
            self.reset_login_ui()
        except Exception as e:
            self.error_label.configure(text=f"Error: {e}", text_color="#FF6B6B")
            self.reset_login_ui()

    def reset_login_ui(self):
        self.login_btn.configure(state="normal", text="Join Hub", fg_color=['#3a7ebf', '#1f538d'])
        self.nickname_entry.configure(state="normal")
        self.client.close()
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def build_chat_interface(self):
        self.login_frame.destroy()
        self.win.title(f"Mesynk - Logged in as: {self.nickname}")
        
        self.win.grid_rowconfigure(0, weight=1)
        self.win.grid_columnconfigure(0, weight=1)
        self.win.grid_columnconfigure(1, weight=0)

        # UI Styling (Day 7)
        self.text_area = ctk.CTkTextbox(self.win, state="disabled", wrap="word", corner_radius=15, font=("Inter", 14), fg_color="#1E1E24")
        self.text_area.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="nsew")

        self.input_area = ctk.CTkEntry(self.win, placeholder_text="Type a message...", corner_radius=20, height=50, font=("Inter", 15))
        self.input_area.grid(row=1, column=0, padx=(20, 10), pady=(10, 20), sticky="ew")

        self.win.bind('<Return>', lambda event: self.write())

        self.send_button = ctk.CTkButton(self.win, text="Send ➔", command=self.write, width=90, height=50, corner_radius=20, font=("Inter", 15, "bold"))
        self.send_button.grid(row=1, column=1, padx=(0, 20), pady=(10, 20), sticky="e")
        
        self.gui_done = True
        self.input_area.focus()

    # Toast Notifications (Day 6)
    def show_toast(self, message):
        toast = ctk.CTkLabel(self.win, text=message, fg_color="#3B8EDB", text_color="white", corner_radius=10, font=("Inter", 12, "bold"), padx=15, pady=8)
        toast.place(relx=0.5, rely=0.05, anchor="n")
        self.win.after(3000, toast.destroy)

    def receive(self):
        while self.running:
            try:
                message = self.client.recv(1024).decode('utf-8')
                if not message: break

                if message == 'NICK':
                    self.client.send(self.nickname.encode('utf-8'))
                else:
                    if self.gui_done:
                        # Popup Toast for specific Server Prompts
                        if "joined the chat" in message or "left the chat" in message:
                            self.show_toast(message)

                        self.text_area.configure(state="normal")
                        self.text_area.insert('end', message + '\n\n')
                        self.text_area.yview('end')
                        self.text_area.configure(state="disabled")
            except Exception as e:
                if self.gui_done:
                    self.show_toast("DISCONNECTED FROM SERVER")
                self.client.close()
                break

    def write(self):
        if not self.gui_done: return
        
        text = self.input_area.get()
        if text.strip():
            message = f'{self.nickname}: {text}'
            try:
                self.client.send(message.encode('utf-8'))
                self.input_area.delete(0, 'end')
            except Exception:
                self.show_toast("Failed to send message")

    def stop(self):
        self.running = False
        self.win.destroy()
        try:
            self.client.close()
        except:
            pass
        sys.exit(0)

if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = ctk.CTk()
    client = ChatClientGUI(app)
    app.mainloop()
