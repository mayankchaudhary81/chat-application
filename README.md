# Chat Application (Python + Sockets + CustomTkinter)

A fast, real-time chat application built using Python sockets for networking and **CustomTkinter** for a modern, dark-mode-native graphical user interface (GUI).
This project demonstrates how multiple clients can connect to a server and exchange messages seamlessly in a beautifully styled chatroom environment.

## 🚀 Features

- **Multi-client chatroom support**: Connect multiple users simultaneously
- **Threaded Server Architecture**: Efficiently handles multiple connections at once
- **Modern GUI Client**: Sleek `customtkinter` interface featuring automatic dark/light mode matching
- **Integrated Login Screen**: In-app nickname prompt with connection validation
- **Real-time message broadcasting**: Instantaneous chat experience
- **User-friendly interface**: Stylized input boxes, rounded buttons, and a scrollable text area

## 🛠️ Technologies Used

- **Python 3**
- **socket** (for networking layer)
- **threading** (for handling asynchronous background connections)
- **customtkinter** (for the modern GUI client)

## 📂 Project Structure
```text
├── server.py   # Server-side code to handle client connections
├── client.py   # Client-side GUI application
```

## ⚙️ Installation & Usage

### 1. Install Dependencies
Before running the client, you must install the UI framework:
```bash
pip install customtkinter
```

### 2. Start the Server
Run the server script to listen for incoming connections.
```bash
python server.py
```
The server will start listening on `127.0.0.1:55555`.

### 3. Start the Client(s)
Run the client script. The application window will open directly to a login screen.
```bash
python client.py
```
Enter a nickname and click **Join**. If the server is running, you will seamlessly transition into the chatroom where you can send and receive real-time messages!

---

## ✅ Future Improvements

- Add file sharing support
- Add message timestamps
- Create a persistent login/registration system across sessions

## 🤝 Contributing

Contributions are welcome! Feel free to fork this repo and submit a pull request with improvements.

## Contact
**Name**: Mayank Chaudhary  
**Email**: chaudharymayank8928@gmail.com  
**LinkedIn**: [www.linkedin.com/in/-mayank-chaudhary](https://www.linkedin.com/in/-mayank-chaudhary)
