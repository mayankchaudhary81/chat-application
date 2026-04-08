import os
import sys
from dotenv import load_dotenv

# Load explicitly handled .env variables
load_dotenv(".env")
DEFAULT_HOST = os.getenv('HOST', '127.0.0.1')
DEFAULT_PORT = int(os.getenv('PORT', 55555))

import socket
import json
import time
import threading

def run_mock_client(username):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((DEFAULT_HOST, DEFAULT_PORT))
    except Exception as e:
        print(f"{username} failed to connect: {e}")
        return

    def send_json(data):
        client.send((json.dumps(data) + '\n').encode('utf-8'))

    def receive():
        buffer = ""
        while True:
            try:
                data = client.recv(1024)
                if not data: break
                buffer += data.decode('utf-8')
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    if not line: continue
                    print(f"[{username} RECEIVED]: {line}")
            except Exception as e:
                print(f"{username} disconnected.")
                break

    threading.Thread(target=receive, daemon=True).start()

    # Login
    print(f"{username} sending LOGIN...")
    send_json({"type": "LOGIN", "username": username, "password": "password"})
    time.sleep(2) # Keep alive for a bit

if __name__ == "__main__":
    import database
    # Register test users just in case
    database.register_user("test1", "password")
    database.register_user("test2", "password")

    print("Starting client test1...")
    run_mock_client("test1")
    time.sleep(1)
    print("Starting client test2...")
    run_mock_client("test2")
    time.sleep(2)
