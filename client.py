import socket
import threading
import customtkinter as ctk
import sys

class ChatClientGUI:
    def __init__(self, app, host='127.0.0.1', port=55555):
        self.win = app
        self.host = host
        self.port = port
        
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = False
        self.gui_done = False
        
        # Setup Main Window
        self.win.title("Chat Application")
        self.win.geometry("500x600")
        
        # Configure initial grid
        self.win.grid_rowconfigure(0, weight=1)
        self.win.grid_columnconfigure(0, weight=1)
        
        # Create Login Frame
        self.login_frame = ctk.CTkFrame(self.win)
        self.login_frame.grid(row=0, column=0, sticky="nsew")
        self.login_frame.grid_rowconfigure((0, 1, 2, 3), weight=1)
        self.login_frame.grid_columnconfigure(0, weight=1)
        
        self.nickname_label = ctk.CTkLabel(self.login_frame, text="Join Chat", font=("Inter", 24, "bold"))
        self.nickname_label.grid(row=0, column=0, pady=(100, 10))
        
        self.nickname_entry = ctk.CTkEntry(self.login_frame, placeholder_text="Enter Nickname...", width=250, height=45, font=("Inter", 14))
        self.nickname_entry.grid(row=1, column=0, pady=10)
        self.nickname_entry.bind('<Return>', lambda event: self.connect_server())
        
        self.login_btn = ctk.CTkButton(self.login_frame, text="Join", width=250, height=45, font=("Inter", 14, "bold"), command=self.connect_server)
        self.login_btn.grid(row=2, column=0, pady=10)
        
        self.error_label = ctk.CTkLabel(self.login_frame, text="", text_color="#FF6B6B", font=("Inter", 12))
        self.error_label.grid(row=3, column=0, pady=(10, 100))
        
        self.win.protocol("WM_DELETE_WINDOW", self.stop)
        
        # Force the UI to show immediately without grabbing focus incorrectly
        self.win.lift()

    def connect_server(self):
        self.nickname = self.nickname_entry.get().strip()
        if not self.nickname:
            self.error_label.configure(text="Nickname is required.")
            return
            
        self.error_label.configure(text="Connecting...", text_color="#FCA311")
        self.win.update_idletasks() # Force UI refresh
            
        try:
            self.client.connect((self.host, self.port))
            # Success! Build Chat Interface
            self.build_chat_interface()
            
            self.running = True
            # Start the receiving messages thread
            receive_thread = threading.Thread(target=self.receive, daemon=True)
            receive_thread.start()
        except ConnectionRefusedError:
            self.error_label.configure(text="Connection Refused! Is server.py running?", text_color="#FF6B6B")
            # Reset the socket so a user can try again safely
            self.client.close()
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except Exception as e:
            self.error_label.configure(text=f"Error: {e}", text_color="#FF6B6B")

    def build_chat_interface(self):
        # Destroy the login screen
        self.login_frame.destroy()
        
        self.win.title(f"Chat Application - {self.nickname}")
        
        # Reconfigure grid for chat screen
        self.win.grid_rowconfigure(0, weight=1)
        self.win.grid_columnconfigure(0, weight=1)
        self.win.grid_columnconfigure(1, weight=0)

        self.text_area = ctk.CTkTextbox(self.win, state="disabled", wrap="word", corner_radius=10, font=("Inter", 13))
        self.text_area.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="nsew")

        self.input_area = ctk.CTkEntry(self.win, placeholder_text="Type a message...", corner_radius=10, height=45, font=("Inter", 14))
        self.input_area.grid(row=1, column=0, padx=(20, 10), pady=(10, 20), sticky="ew")

        # Unbind previous return key for login and rebind to send message
        self.win.bind('<Return>', lambda event: self.write())

        self.send_button = ctk.CTkButton(self.win, text="Send", command=self.write, width=80, height=45, corner_radius=10, font=("Inter", 14, "bold"))
        self.send_button.grid(row=1, column=1, padx=(0, 20), pady=(10, 20), sticky="e")
        
        self.gui_done = True
        
        # Focus on input area immediately to start typing
        self.input_area.focus()

    # Receive messages from the server
    def receive(self):
        while self.running:
            try:
                message = self.client.recv(1024).decode('utf-8')

                if message == 'NICK':
                    self.client.send(self.nickname.encode('utf-8'))
                else:
                    if self.gui_done:
                        self.text_area.configure(state="normal")
                        self.text_area.insert('end', message + '\n')
                        self.text_area.yview('end')
                        self.text_area.configure(state="disabled")
            except Exception as e:
                # Connection closed
                self.client.close()
                break

    # Send messages to the server
    def write(self):
        if not self.gui_done: return
        
        text = self.input_area.get()
        if text.strip():
            message = f'{self.nickname}: {text}'
            try:
                self.client.send(message.encode('utf-8'))
                self.input_area.delete(0, 'end')
            except:
                pass

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
