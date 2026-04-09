import socketio
import threading
import customtkinter as ctk
import sys
import os
import json
import time
import base64
from io import BytesIO
import winsound
from tkinter import filedialog, Menu
from PIL import Image
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
        
        self.sio = socketio.Client()
        self.running = False
        self.gui_done = False
        self.token = None
        self.username = None
        self.last_typed = 0
        self.typing_timer = None
        self.latest_online_users = []
        self.active_group_id = 'global'
        self.user_groups = []
        self.all_groups = []
        
        self.messages_ui = {} # Map msg_id to a dict of UI widgets 
        
        self.sio.on('connect', self.on_connect)
        self.sio.on('disconnect', self.on_disconnect)
        self.sio.on('auth_success', self.on_auth_success)
        self.sio.on('auth_error', self.on_auth_error)
        self.sio.on('sys_msg', self.on_sys_msg)
        self.sio.on('online_users', self.on_online_users)
        self.sio.on('typing', self.on_typing)
        self.sio.on('history', self.on_history)
        self.sio.on('new_message', self.on_new_message)
        self.sio.on('message_edited', self.on_message_edited)
        self.sio.on('message_deleted', self.on_message_deleted)
        self.sio.on('message_read', self.on_message_read)
        self.sio.on('user_groups', self.on_user_groups)
        self.sio.on('all_groups', self.on_all_groups)
        
        # Setup Main Window
        self.win.title("Mesynk Plus")
        self.win.geometry("900x700") 
        self.win.minsize(700, 500)
        
        self.win.grid_rowconfigure(0, weight=1)
        self.win.grid_columnconfigure(0, weight=1)
        
        # Build Sleek Login Frame
        self.build_login_ui()
        self.win.protocol("WM_DELETE_WINDOW", self.stop)
        self.win.lift()

    def on_connect(self):
        print("Connected to Socket.IO Server")
        
    def on_disconnect(self):
        print("Disconnected from server")
        if self.gui_done:
            self.win.after(0, lambda: self.show_toast("DISCONNECTED FROM SERVER"))
        self.win.after(0, self.reset_login_ui)

    def on_auth_success(self, data):
        message = data.get("message", "")
        if "token" in data:
            self.token = data.get("token")
            self.username = data.get("username")
            self.user_groups = data.get("groups", [])
            self.active_group_id = 'global'
            self.win.after(0, self.build_chat_interface)
            self.sio.emit('explore_groups')
        else:
            self.win.after(0, lambda m=message: self.error_label.configure(text=m, text_color="#4CAF50"))
            self.win.after(0, self.reset_login_ui)

    def on_auth_error(self, data):
        msg = data.get("message")
        self.win.after(0, lambda err=msg: self.error_label.configure(text=err, text_color="#FF6B6B"))
        self.win.after(0, self.reset_login_ui)

    def on_sys_msg(self, data):
        if self.gui_done:
            msg = data.get("message")
            self.win.after(0, lambda m=msg: self.show_toast(m))

    def on_online_users(self, data):
        users = data.get("users", [])
        self.latest_online_users = users
        if self.gui_done:
            self.win.after(0, lambda u=users: self.update_online_users(u))

    def on_user_groups(self, data):
        self.user_groups = data.get("groups", [])
        if self.gui_done:
            self.win.after(0, self.update_groups_list)

    def on_all_groups(self, data):
        self.all_groups = data.get("groups", [])
        if self.gui_done:
            self.win.after(0, self.update_explore_list)

    def on_typing(self, data):
        if self.gui_done:
            if data.get("group_id", "global") == self.active_group_id:
                user = data.get("username")
                self.win.after(0, lambda u=user: self.show_typing(u))

    def on_history(self, data):
        if self.gui_done:
            group_id = data.get("group_id", "global")
            if group_id == self.active_group_id:
                self.win.after(0, self._render_history, data.get("messages", []))

    def _render_history(self, messages):
        for widget in self.msg_list_frame.winfo_children():
            widget.destroy()
        self.messages_ui.clear()
        for msg in messages:
            self.render_message(msg)

    def on_new_message(self, data):
        if self.gui_done:
            group_id = data.get("group_id", "global")
            if group_id != self.active_group_id:
                if data.get('username') != self.username:
                    try: winsound.MessageBeep(winsound.MB_ICONASTERISK)
                    except: pass
                return
                
            if data.get('username') != self.username:
                try: winsound.MessageBeep(winsound.MB_ICONASTERISK)
                except: pass
            self.win.after(0, lambda m=data: self.render_message(m))

    def on_message_edited(self, data):
        if self.gui_done:
            if data.get("group_id", "global") == self.active_group_id:
                self.win.after(0, lambda d=data: self._update_msg_text(d['id'], d['text']))

    def on_message_deleted(self, data):
        if self.gui_done:
            if data.get("group_id", "global") == self.active_group_id:
                self.win.after(0, lambda id=data['id']: self._mark_msg_deleted(id))

    def on_message_read(self, data):
        if self.gui_done:
            if data.get("group_id", "global") == self.active_group_id:
                self.win.after(0, lambda id=data['id']: self._update_msg_read(id))

    def _update_msg_text(self, msg_id, new_text):
        if msg_id in self.messages_ui:
            ui = self.messages_ui[msg_id]
            ui['text_label'].configure(text=new_text + " (edited)")

    def _mark_msg_deleted(self, msg_id):
        if msg_id in self.messages_ui:
            ui = self.messages_ui[msg_id]
            ui['text_label'].configure(text="🚫 This message was deleted", text_color="#7A7A7A")
            if 'image_label' in ui:
                ui['image_label'].destroy()
            if 'edit_btn' in ui:
                 ui['edit_btn'].destroy()
            if 'del_btn' in ui:
                 ui['del_btn'].destroy()

    def _update_msg_read(self, msg_id):
        if msg_id in self.messages_ui:
            ui = self.messages_ui[msg_id]
            if 'status_label' in ui:
                ui['status_label'].configure(text="✔✔", text_color="#3B8EDB")

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
        self.password_entry.bind('<Return>', lambda event: self.start_auth("login"))
        
        button_frame = ctk.CTkFrame(self.login_frame, fg_color="transparent")
        button_frame.grid(row=3, column=0, pady=10)
        
        self.login_btn = ctk.CTkButton(button_frame, text="Login", width=135, height=50, font=("Inter", 15, "bold"), command=lambda: self.start_auth("login"))
        self.login_btn.grid(row=0, column=0, padx=5)

        self.register_btn = ctk.CTkButton(button_frame, text="Register", width=135, height=50, font=("Inter", 15, "bold"), fg_color="#4CAF50", hover_color="#45a049", command=lambda: self.start_auth("register"))
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
            if not self.sio.connected:
                self.sio.connect(f"http://{self.host}:{self.port}")
            self.running = True
            
            self.sio.emit(action, {"username": username, "password": password})
        except Exception as e:
            self.error_label.configure(text=f"Connection Error: Is server running?", text_color="#FF6B6B")
            self.reset_login_ui()

    def reset_login_ui(self):
        if hasattr(self, 'login_btn') and self.login_btn.winfo_exists():
            self.login_btn.configure(state="normal")
            self.register_btn.configure(state="normal")
            self.username_entry.configure(state="normal")
            self.password_entry.configure(state="normal")
        try:
            if self.sio.connected:
                self.sio.disconnect()
            self.running = False
        except:
            pass

    def build_chat_interface(self):
        if hasattr(self, 'login_frame') and self.login_frame.winfo_exists():
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

        # Replaced Textbox with ScrollableFrame
        self.msg_list_frame = ctk.CTkScrollableFrame(chat_frame, corner_radius=15, fg_color="#1E1E24")
        self.msg_list_frame.grid(row=0, column=0, columnspan=2, pady=(0, 5), sticky="nsew")

        # Typing Indicator
        self.typing_label = ctk.CTkLabel(chat_frame, text="", text_color="#AAAAAA", font=("Inter", 12, "italic"), height=20)
        self.typing_label.grid(row=1, column=0, sticky="w", padx=10)

        # Input Area
        input_frame = ctk.CTkFrame(chat_frame, fg_color="transparent")
        input_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
        input_frame.grid_columnconfigure(2, weight=1)

        self.attach_btn = ctk.CTkButton(input_frame, text="📎", width=40, height=50, corner_radius=10, font=("Inter", 20), fg_color="#4F4F4F", command=self.open_file_picker)
        self.attach_btn.grid(row=0, column=0, padx=(0, 5))

        self.emoji_btn = ctk.CTkButton(input_frame, text="😊", width=40, height=50, corner_radius=10, font=("Inter", 20), fg_color="#4F4F4F", command=self.open_emoji_picker)
        self.emoji_btn.grid(row=0, column=1, padx=(0, 10))

        self.input_area = ctk.CTkEntry(input_frame, placeholder_text="Type a message...", corner_radius=20, height=50, font=("Inter", 15))
        self.input_area.grid(row=0, column=2, padx=(0, 10), sticky="ew")
        self.input_area.bind('<Return>', lambda event: self.write())
        self.input_area.bind('<KeyRelease>', self.on_key_release)

        self.send_button = ctk.CTkButton(input_frame, text="Send", command=self.write, width=90, height=50, corner_radius=20, font=("Inter", 15, "bold"))
        self.send_button.grid(row=0, column=3, sticky="e")
        
        # Sidebar for Chat Management
        sidebar = ctk.CTkFrame(self.win, fg_color="#1E1E24", corner_radius=15, width=250)
        sidebar.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        sidebar.grid_rowconfigure(0, weight=1)
        sidebar.grid_columnconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(sidebar, corner_radius=15)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        self.tabview.add("Groups")
        self.tabview.add("Explore")
        self.tabview.add("Online")
        
        # Groups Tab
        self.tabview.tab("Groups").grid_rowconfigure(0, weight=0)
        self.tabview.tab("Groups").grid_rowconfigure(1, weight=1)
        self.tabview.tab("Groups").grid_columnconfigure(0, weight=1)
        
        create_grp_btn = ctk.CTkButton(self.tabview.tab("Groups"), text="+ Create Group", command=self.prompt_create_group, height=30)
        create_grp_btn.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        self.groups_list_frame = ctk.CTkScrollableFrame(self.tabview.tab("Groups"), fg_color="transparent")
        self.groups_list_frame.grid(row=1, column=0, sticky="nsew")
        
        # Explore Tab
        self.tabview.tab("Explore").grid_rowconfigure(0, weight=1)
        self.tabview.tab("Explore").grid_columnconfigure(0, weight=1)
        self.explore_list_frame = ctk.CTkScrollableFrame(self.tabview.tab("Explore"), fg_color="transparent")
        self.explore_list_frame.grid(row=0, column=0, sticky="nsew")
        
        # Online Tab
        self.tabview.tab("Online").grid_rowconfigure(0, weight=1)
        self.tabview.tab("Online").grid_columnconfigure(0, weight=1)
        self.online_users_list = ctk.CTkScrollableFrame(self.tabview.tab("Online"), fg_color="transparent")
        self.online_users_list.grid(row=0, column=0, sticky="nsew")
        self.online_users_labels = []

        self.gui_done = True
        self.input_area.focus()
        
        if hasattr(self, 'user_groups') and self.user_groups:
            self.update_groups_list()
        if hasattr(self, 'all_groups') and self.all_groups:
            self.update_explore_list()
        if hasattr(self, 'latest_online_users') and self.latest_online_users:
            self.update_online_users(self.latest_online_users)

    def render_message(self, msg):
        msg_id = msg['id']
        username = msg['username']
        text = msg['text']
        ts = msg['timestamp']
        is_edited = msg.get('is_edited', False)
        deleted = msg.get('deleted', False)
        msg_type = msg.get('msg_type', 'text')
        file_data = msg.get('file_data')
        read_by = msg.get('read_by', [])
        
        is_mine = (username == self.username)
        align = "e" if is_mine else "w"
        color = "#2b5278" if is_mine else "#3A3A3C"
        
        container = ctk.CTkFrame(self.msg_list_frame, fg_color="transparent")
        container.pack(fill="x", padx=10, pady=5)
        
        bubble = ctk.CTkFrame(container, fg_color=color, corner_radius=15)
        bubble.pack(side="right" if is_mine else "left", padx=5, pady=2, ipadx=10, ipady=5)
        
        # Metadata (Username & Time)
        meta_text = ts if is_mine else f"{username} • {ts}"
        meta_label = ctk.CTkLabel(bubble, text=meta_text, text_color="#AAAAAA", font=("Inter", 10))
        meta_label.pack(anchor="w" if not is_mine else "e", padx=5)

        ui_elements = {}

        if deleted:
            text_label = ctk.CTkLabel(bubble, text="🚫 This message was deleted", text_color="#7A7A7A", font=("Inter", 14, "italic"), wraplength=400, justify="left")
            text_label.pack(anchor="w", padx=5, pady=(2, 0))
            ui_elements['text_label'] = text_label
        else:
            if msg_type == 'image' and file_data:
                try:
                    img_bytes = base64.b64decode(file_data)
                    img = Image.open(BytesIO(img_bytes))
                    img.thumbnail((300, 300))
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
                    img_label = ctk.CTkLabel(bubble, image=ctk_img, text="")
                    img_label.pack(padx=5, pady=5)
                    ui_elements['image_label'] = img_label
                except Exception as e:
                    print(f"Error reading image logic: {e}")
            
            main_text = text + (" (edited)" if is_edited else "")
            text_label = ctk.CTkLabel(bubble, text=main_text, font=("Inter", 14), wraplength=400, justify="left" if not is_mine else "right")
            text_label.pack(anchor="w" if not is_mine else "e", padx=5, pady=2)
            ui_elements['text_label'] = text_label

            # Read Receipts
            if is_mine:
                # "✔✔" logic
                read_str = "✔✔" if len(read_by) > 0 else "✔"
                status_color = "#3B8EDB" if len(read_by) > 0 else "#AAAAAA"
                status_label = ctk.CTkLabel(bubble, text=read_str, font=("Inter", 10), text_color=status_color)
                status_label.pack(anchor="e", padx=5)
                ui_elements['status_label'] = status_label
            else:
                # Mark as read if not ours
                if self.username not in read_by:
                    self.sio.emit('mark_read', {'id': msg_id})

            # Edit/Delete Buttons
            if is_mine:
                actions_frame = ctk.CTkFrame(bubble, fg_color="transparent")
                actions_frame.pack(anchor="e", padx=5, pady=(2,0))
                
                edit_btn = ctk.CTkButton(actions_frame, text="Edit", width=30, height=20, font=("Inter", 10), fg_color="#4F4F4F", command=lambda id=msg_id: self.prompt_edit_message(id))
                edit_btn.pack(side="left", padx=2)
                
                del_btn = ctk.CTkButton(actions_frame, text="Delete", width=40, height=20, font=("Inter", 10), fg_color="#FF4C4C", hover_color="#E03A3A", command=lambda id=msg_id: self.sio.emit('delete_message', {'id': id}))
                del_btn.pack(side="left", padx=2)
                
                ui_elements['edit_btn'] = edit_btn
                ui_elements['del_btn'] = del_btn

        self.messages_ui[msg_id] = ui_elements
        
        # Scroll to bottom
        self.msg_list_frame.update_idletasks()
        try:
            self.msg_list_frame._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass
        
        # Setup typing clearing
        if not is_mine:
            self.typing_label.configure(text="")

    def prompt_edit_message(self, msg_id):
        dialog = ctk.CTkInputDialog(text="Type new message:", title="Edit Message")
        self.win.update_idletasks()
        new_text = dialog.get_input()
        if new_text:
            self.sio.emit('edit_message', {'id': msg_id, 'text': new_text, 'group_id': self.active_group_id})

    def open_file_picker(self):
        filepath = filedialog.askopenfilename(title="Select an Image", filetypes=(("Image files", "*.png *.jpg *.jpeg *.gif"), ("All files", "*.*")))
        if filepath:
            try:
                with open(filepath, "rb") as image_file:
                    encoded = base64.b64encode(image_file.read()).decode('utf-8')
                    # Emit it
                    self.sio.emit('send_message', {'text': f"Shared an image: {os.path.basename(filepath)}", 'msg_type': 'image', 'file_data': encoded, 'group_id': self.active_group_id})
            except Exception as e:
                self.show_toast(f"Failed to load image: {e}")

    def open_emoji_picker(self):
        picker = ctk.CTkToplevel(self.win)
        picker.title("Emoji")
        picker.geometry("280x200")
        picker.attributes("-topmost", True)
        
        emojis = ["😀","😂","😍","😎","😢","😡","👍","👎","🔥","❤️","🎉","🤔","👌","🙌","✨"]
        
        frame = ctk.CTkFrame(picker, fg_color="transparent")
        frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        for i, emp in enumerate(emojis):
            r, c = divmod(i, 5)
            btn = ctk.CTkButton(frame, text=emp, width=40, height=40, font=("Inter", 20), fg_color="transparent", command=lambda e=emp: self.insert_emoji(e, picker))
            btn.grid(row=r, column=c, padx=2, pady=2)

    def insert_emoji(self, emoji, window):
        self.input_area.insert("end", emoji)
        window.destroy()
        self.input_area.focus()

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

    def on_key_release(self, event):
        if not self.gui_done: return
        if event.keysym == 'Return': return
        
        current_time = time.time()
        if current_time - self.last_typed > 1.5:
            self.sio.emit('typing', {'group_id': self.active_group_id})
            self.last_typed = current_time

    def write(self):
        if not self.gui_done: return
        
        text = self.input_area.get()
        if text.strip():
            self.sio.emit('send_message', {'text': text.strip(), 'msg_type': 'text', 'group_id': self.active_group_id})
            self.input_area.delete(0, 'end')

    def prompt_create_group(self):
        dialog = ctk.CTkInputDialog(text="Enter group name:", title="Create Group")
        self.win.update_idletasks()
        name = dialog.get_input()
        if name and name.strip():
            self.sio.emit('create_group', {'name': name.strip()})

    def switch_group(self, group_id, group_name):
        self.active_group_id = group_id
        self.win.title(f"Mesynk - Logged in as: {self.username} | {group_name}")
        self.sio.emit('fetch_history', {'group_id': group_id})

    def update_groups_list(self):
        for w in self.groups_list_frame.winfo_children():
            w.destroy()
        # Ensure 'global' is always logically prominent if present
        for g in self.user_groups:
            btn = ctk.CTkButton(self.groups_list_frame, text=g['name'], anchor="w", fg_color="#2b5278" if self.active_group_id == g['id'] else "transparent", text_color="white" if self.active_group_id == g['id'] else "#3B8EDB", hover_color="#2b5278", command=lambda gid=g['id'], gname=g['name']: self.switch_group(gid, gname))
            btn.pack(fill="x", pady=2)

    def update_explore_list(self):
        for w in self.explore_list_frame.winfo_children():
            w.destroy()
        my_group_ids = [g['id'] for g in self.user_groups]
        for g in self.all_groups:
            if g['id'] not in my_group_ids:
                btn = ctk.CTkButton(self.explore_list_frame, text=f"Join {g['name']}", anchor="w", fg_color="transparent", text_color="#4CAF50", hover_color="#45a049", command=lambda gid=g['id']: self.sio.emit('join_group', {'group_id': gid}))
                btn.pack(fill="x", pady=2)

    def stop(self):
        self.running = False
        try:
            if self.sio.connected:
                self.sio.disconnect()
        except:
            pass
        self.win.destroy()
        sys.exit(0)

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    app = ctk.CTk()
    client = ChatClientGUI(app)
    app.mainloop()
