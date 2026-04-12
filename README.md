# Mesynk 🚀

A modern, fast, and robust real-time chat application built with Python. Developed over a comprehensive **30-Day Networking Roadmap**, this project evolves from a simple networking experiment into a production-ready communication platform incorporating modern features, containerization, and advanced UI/UX.

## 🌟 Features Achieved
- **WebSockets / Socket.IO Integration**: Transitioned from raw sockets to event-driven Socket.IO handling for resilient asynchronous communication.
- **JWT Authentication & Security**: Complete secure login system featuring password hashing (PBKDF2) alongside JWT for persistent session tracking. Server-side Rate limiting prevents API abuse and DoS.
- **Advanced Chat Capabilities**:
  - Global & Private Group Chats
  - Full Message Management (Edit / Delete)
  - Picture and File Sharing
  - Read Receipts and Real-Time Typing Indicators
  - Message and User Search Capabilities
- **Modern UI / UX**: Beautifully dark-themed graphical interface built dynamically with `customtkinter`. Features fluid connection loading states, avatar uploading, animated toast notifications, and slick integrated tab management.
- **Database Modularity**: Seamless integration with SQLite using robust multi-table schemas covering users, messages, groups, and members.
- **Docker-Ready**: Packaged with a complete `Dockerfile` and `render.yaml` Blueprint for 1-click cloud deployments (see `DEPLOYMENT.md`).

## 🛠️ Architecture & Project Structure
The application is strictly separated into a headless backend `server/` node and an interactive `client/` graphical interface:
```text
├── client/
│   └── client.py        # GUI, Socket.IO client logic, Tab & Event Mapping
├── server/
│   ├── server.py        # Main WSGI Server (Socket.IO + Eventlet) 
│   ├── database.py      # SQLite3 operations, queries, database init
│   └── Dockerfile       # Container definition for the node
├── tests/
│   └── test_database.py # Baseline database unit test suite
├── .env                 # Environment variables configuration
├── requirements.txt     # Python Dependencies array
├── render.yaml          # Render Cloud Blueprint Setup
├── docker-compose.yml   # Containerized local application stack
├── DEPLOYMENT.md        # Deployment and hosting guidelines
└── README.md            # You are here!
```

## ⚙️ Installation & Usage

**1. Install dependencies:**
```bash
pip install -r requirements.txt
```

**2. Configure your environment:**
Review the `.env` file (if provided) and confirm your networking preferences.
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
*(You can launch `client.py` as many times as you want to simulate multiple concurrent users!)*

**5. Running Unit Tests:**
To ensure your core infrastructure remains solid, a test suite has been provided covering database operations. You can trigger tests locally:
```bash
python -m unittest discover tests
```

---

*This application marks the successful milestone of the demanding 30-Day Python Socket/Network Roadmap. It bridges the gap between learning theoretical sockets and implementing scalable, fully-featured desktop/web systems.*
