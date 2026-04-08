import socket
import threading
import os
import json
import jwt
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import database

# Load environment variables
load_dotenv()

HOST = os.getenv('HOST', '127.0.0.1')
PORT = int(os.getenv('PORT', 55555))
JWT_SECRET = os.getenv('JWT_SECRET', 'super_secret_jwt_key_for_testing')

# Mapping of client socket object to username
clients = {}

def broadcast(message_dict):
    """Broadcast a JSON message to all connected clients."""
    msg_str = json.dumps(message_dict) + '\n'
    for client in list(clients.keys()):
        try:
            client.send(msg_str.encode('utf-8'))
        except Exception as e:
            print(f"Error broadcasting to a client: {e}")

def broadcast_online_users():
    users = list(clients.values())
    broadcast({"type": "ONLINE_USERS", "users": users})

def handle_client(client, address):
    # Buffer for partial JSON messages
    buffer = ""
    authenticated_username = None

    def send_json(data):
        client.send((json.dumps(data) + '\n').encode('utf-8'))

    while True:
        try:
            data = client.recv(1024)
            if not data:
                break
            
            buffer += data.decode('utf-8')
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                line = line.strip()
                if not line:
                    continue
                
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    print(f"Invalid JSON received: {line}")
                    continue

                msg_type = payload.get("type")

                if msg_type == "REGISTER":
                    username = payload.get("username")
                    password = payload.get("password")
                    success, msg = database.register_user(username, password)
                    if success:
                        send_json({"type": "AUTH_SUCCESS", "message": "Registered successfully. Please login."})
                    else:
                        send_json({"type": "AUTH_ERROR", "message": msg})

                elif msg_type == "LOGIN":
                    username = payload.get("username")
                    password = payload.get("password")
                    success, msg = database.authenticate_user(username, password)
                    if success:
                        # Generate JWT
                        token = jwt.encode({
                            "username": username,
                            "exp": datetime.now(timezone.utc) + timedelta(hours=24)
                        }, JWT_SECRET, algorithm="HS256")
                        
                        authenticated_username = username
                        clients[client] = username
                        send_json({"type": "AUTH_SUCCESS", "token": token, "username": username})
                        
                        # System Message
                        broadcast({"type": "SYS_MSG", "message": f"{username} has joined the chat!"})
                        broadcast_online_users()
                    else:
                        send_json({"type": "AUTH_ERROR", "message": msg})

                elif msg_type == "AUTH":
                    token = payload.get("token")
                    try:
                        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
                        username = decoded.get("username")
                        authenticated_username = username
                        clients[client] = username
                        send_json({"type": "AUTH_SUCCESS", "token": token, "username": username})
                        
                        broadcast({"type": "SYS_MSG", "message": f"{username} has joined the chat!"})
                        broadcast_online_users()
                    except jwt.ExpiredSignatureError:
                        send_json({"type": "AUTH_ERROR", "message": "Session expired. Please log in again."})
                    except jwt.InvalidTokenError:
                        send_json({"type": "AUTH_ERROR", "message": "Invalid token. Please log in again."})

                elif msg_type == "MSG":
                    if authenticated_username:
                        text = payload.get("text")
                        timestamp = datetime.now().strftime('%H:%M')
                        broadcast({
                            "type": "MSG",
                            "username": authenticated_username,
                            "text": text,
                            "timestamp": timestamp
                        })

                elif msg_type == "TYPING":
                    if authenticated_username:
                        broadcast({
                            "type": "TYPING",
                            "username": authenticated_username
                        })

        except Exception as e:
            print(f"Error handling client {address}: {e}")
            break

    # Clean up on disconnect
    if client in clients:
        username = clients[client]
        del clients[client]
        # Notify others
        broadcast({"type": "SYS_MSG", "message": f"{username} has left the chat!"})
        broadcast_online_users()
    try:
        client.close()
    except:
        pass

def receive():
    while True:
        try:
            client, address = server.accept()
            print(f'Connected with {str(address)}')
            thread = threading.Thread(target=handle_client, args=(client, address))
            thread.daemon = True
            thread.start()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            break
        except Exception as e:
            print(f"Server accept error: {e}")
            break

# Set up server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVER STARTED] Listening heavily on {HOST}:{PORT}...")
    receive()
except Exception as e:
    print(f"Failed to start server: {e}")
except KeyboardInterrupt:
    print("Server stopped")
finally:
    server.close()
