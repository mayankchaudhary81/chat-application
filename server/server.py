import socket
import threading
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

HOST = os.getenv('HOST', '127.0.0.1')
PORT = int(os.getenv('PORT', 55555))

clients = []
nicknames = []

def broadcast(message):
    for client in clients:
        try:
            client.send(message)
        except Exception as e:
            # Clean error handling on broadcast drop
            print(f"Error broadcasting to a client: {e}")

def handle_client(client):
    while True:
        try:
            message = client.recv(1024)
            if not message:
                raise Exception("Client disconnected gracefully")
            broadcast(message)
        except Exception as e:
            # Clean exit handling
            if client in clients:
                index = clients.index(client)
                clients.remove(client)
                nickname = nicknames[index]
                clean_msg = f'{nickname} has left the chat!'
                print(clean_msg)
                broadcast(clean_msg.encode('utf-8'))
                nicknames.remove(nickname)
            try:
                client.close()
            except:
                pass
            break

def receive():
    while True:
        try:
            client, address = server.accept()
            print(f'Connected with {str(address)}')

            client.send('NICK'.encode('utf-8'))
            nickname = client.recv(1024).decode('utf-8')
            nicknames.append(nickname)
            clients.append(client)

            print(f'Nickname of the client is {nickname}')
            broadcast(f'{nickname} has joined the chat!'.encode('utf-8'))
            client.send('Connected to the server!'.encode('utf-8'))

            thread = threading.Thread(target=handle_client, args=(client,))
            thread.start()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            server.close()
            break
        except Exception as e:
            print(f"Server accept error: {e}")

# Set up server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Allow quick reuse of the port
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVER STARTED] Listening heavily on {HOST}:{PORT}...")
    receive()
except Exception as e:
    print(f"Failed to start server: {e}")
