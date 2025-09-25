import socket
import threading
import tkinter
from tkinter import simpledialog, scrolledtext

# Client GUI class using tkinter
class ChatClientGUI:
    def __init__(self, nickname, host='127.0.0.1', port=55555):
        self.nickname = nickname  # Store the nickname as an instance variable
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((host, port))

        self.gui_done = False
        self.running = True

        # Start the GUI thread
        gui_thread = threading.Thread(target=self.gui_loop)
        gui_thread.start()

        # Start the receiving messages thread
        receive_thread = threading.Thread(target=self.receive)
        receive_thread.start()

    # GUI Loop that sets up the interface
    def gui_loop(self):
        self.win = tkinter.Tk()
        self.win.configure(bg="lightgray")
        self.win.title(f"Chat Application - {self.nickname}")

        self.chat_label = tkinter.Label(self.win, text="Chat:", bg="lightgray")
        self.chat_label.config(font=("Arial", 12))
        self.chat_label.pack(padx=20, pady=5)

        # Text area to display chat messages
        self.text_area = scrolledtext.ScrolledText(self.win)
        self.text_area.pack(padx=20, pady=5)
        self.text_area.config(state="disabled")  # To make the chat area read-only

        # Label for message input
        self.msg_label = tkinter.Label(self.win, text="Enter your message:", bg="lightgray")
        self.msg_label.config(font=("Arial", 12))
        self.msg_label.pack(padx=20, pady=5)

        # Entry box for typing the message
        self.input_area = tkinter.Entry(self.win, font=("Arial", 12))
        self.input_area.pack(padx=20, pady=5)

        # Send button
        self.send_button = tkinter.Button(self.win, text="Send", command=self.write)
        self.send_button.config(font=("Arial", 12))
        self.send_button.pack(padx=20, pady=5)

        # Gracefully close the window
        self.win.protocol("WM_DELETE_WINDOW", self.stop)

        self.gui_done = True
        self.win.mainloop()

    # Receive messages from the server
    def receive(self):
        while self.running:
            try:
                message = self.client.recv(1024).decode('utf-8')

                if message == 'NICK':
                    self.client.send(self.nickname.encode('utf-8'))
                else:
                    if self.gui_done:
                        self.text_area.config(state="normal")
                        self.text_area.insert('end', message + '\n')
                        self.text_area.yview('end')
                        self.text_area.config(state="disabled")
            except ConnectionAbortedError:
                break
            except:
                print("Error occurred!")
                self.client.close()
                break

    # Send messages to the server
    def write(self):
        message = f'{self.nickname}: {self.input_area.get()}'
        self.client.send(message.encode('utf-8'))
        self.input_area.delete(0, 'end')

    # Stop the client and close the GUI
    def stop(self):
        self.running = False
        self.win.destroy()
        self.client.close()
        exit(0)

# Create a temporary root window to ask for the nickname, then hide it
root = tkinter.Tk()
root.withdraw()  # Hide the root window

# Ask for nickname before starting the GUI
nickname = simpledialog.askstring("Nickname", "Please choose a nickname", parent=root)

# Create the client GUI and pass the nickname
client = ChatClientGUI(nickname)


