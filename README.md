# Mesynk 🚀

A modern, fast, and secure real-time chat application built with Python. 
This project demonstrates robust network programming (via Sockets), multi-threading, environment configuration, and modern desktop UI design using CustomTkinter.

## 🌟 Features
- **Client-Server Architecture**: Dedicated servers capable of handling asynchronous multi-user communication.
- **Modern UI**: Dark-mode natively styled using `customtkinter`, featuring fluid connection loading states, animated in-app toast notifications, and aesthetic chat interfaces.
- **Robust Error Handling**: Graceful client and server disconnects without crashed sockets or application hangs.
- **Environment Driven Settings**: Hidden system variables (ports and IPs) securely abstracted in `.env` configurations.

## 🛠️ Architecture & Project Structure
The application is strictly separated into the backend `server/` node and the interactive `client/` graphical interface:
```text
├── client/
│   └── client.py      # GUI and Socket Logic for users
├── server/
│   └── server.py      # Socket server, connection handler and broadcaster
├── .env               # Environment configurations
├── requirements.txt   # Dependency list
└── README.md          # Documentation
```

## ⚙️ Installation & Usage

**1. Install dependencies:**
```bash
pip install -r requirements.txt
```

**2. Configure your environment:**
Open the `.env` file and set your networking preferences.
```env
HOST=127.0.0.1
PORT=55555
```

**3. Run the Server:**
Launch the background listener node.
```bash
python server/server.py
```

**4. Start Client Connections:**
Open a new terminal window and launch a UI client.
```bash
python client/client.py
```
*(You can open as many clients as you want to simulate multiple users!)*

---

*This project was heavily refactored over a comprehensive 7-day sprint targeting file restructuring, environment safety, UI polish, and error resilience to mirror modern enterprise standards.*
