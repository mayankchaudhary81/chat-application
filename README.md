Chat Application (Python + Sockets + Tkinter)

A simple real-time chat application built using Python sockets for networking and Tkinter for the client-side graphical user interface (GUI).
This project demonstrates how multiple clients can connect to a server and exchange messages in a chatroom environment.

🚀 Features

Multi-client chatroom support

Server handles multiple clients using threads

GUI-based client with Tkinter

Real-time message broadcasting

User-friendly interface with scrollable chat area

Custom nickname for each client

🛠️ Technologies Used

Python 3

socket (for networking)

threading (for handling multiple clients)

Tkinter (for GUI client)

📂 Project Structure
├── server.py   # Server-side code to handle client connections
├── client.py   # Client-side GUI application

⚙️ How It Works

Start the server
Run the server script to listen for incoming connections.

python server.py


The server will start on 127.0.0.1:55555.

Start the client(s)
Run the client script. You’ll be prompted to enter a nickname.

python client.py


A chat window will open where you can send and receive messages.

Chat in real-time
Multiple clients can connect to the same server and exchange messages instantly.


✅ Future Improvements

Add file sharing support

Enhance UI design

Add message timestamps

Create a login/registration system


🤝 Contributing

Contributions are welcome! Feel free to fork this repo and submit a pull request with improvements.

Contact
Name: Mayank Chaudhary Email: chaudharymayank8928@gmail.com LinkedIn: www.linkedin.com/in/-mayank-chaudhary
