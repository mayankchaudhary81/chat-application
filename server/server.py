import eventlet
import socketio
import os
import json
import jwt
import uuid
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import database

# Load environment variables
load_dotenv()

HOST = os.getenv('HOST', '127.0.0.1')
PORT = int(os.getenv('PORT', 55555))
JWT_SECRET = os.getenv('JWT_SECRET', 'super_secret_jwt_key_for_testing')

sio = socketio.Server(cors_allowed_origins='*')
app = socketio.WSGIApp(sio)

# Map sid -> username
clients = {}

def get_online_users():
    return list(clients.values())

def broadcast_online_users():
    sio.emit('online_users', {'users': get_online_users()})

@sio.event
def connect(sid, environ, auth):
    print(f"Client connected: {sid}")

@sio.event
def disconnect(sid):
    print(f"Client disconnected: {sid}")
    if sid in clients:
        username = clients[sid]
        del clients[sid]
        try:
            sio.emit('sys_msg', {'message': f"{username} has left the chat!"}, room='global')
        except:
            pass
        broadcast_online_users()

@sio.event
def register(sid, data):
    username = data.get("username")
    password = data.get("password")
    success, msg = database.register_user(username, password)
    if success:
        sio.emit('auth_success', {"message": "Registered successfully. Please login."}, to=sid)
    else:
        sio.emit('auth_error', {"message": msg}, to=sid)

def setup_user_session(sid, username):
    clients[sid] = username
    groups = database.get_user_groups(username)
    for g in groups:
        sio.enter_room(sid, g['id'])
    
    # Enter a personal room
    sio.enter_room(sid, sid)
    
    history = database.get_messages(group_id='global', limit=100)
    
    sio.emit('sys_msg', {'message': f"{username} has joined the chat!"}, room='global')
    broadcast_online_users()
    
    return groups, history

@sio.event
def login(sid, data):
    username = data.get("username")
    password = data.get("password")
    success, msg = database.authenticate_user(username, password)
    if success:
        token = jwt.encode({
            "username": username,
            "exp": datetime.now(timezone.utc) + timedelta(hours=24)
        }, JWT_SECRET, algorithm="HS256")
        
        groups, history = setup_user_session(sid, username)
        sio.emit('auth_success', {"token": token, "username": username, "groups": groups, "history": history}, to=sid)
    else:
        sio.emit('auth_error', {"message": msg}, to=sid)

@sio.event
def auth_token(sid, data):
    token = data.get("token")
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        username = decoded.get("username")
        groups, history = setup_user_session(sid, username)
        sio.emit('auth_success', {"token": token, "username": username, "groups": groups, "history": history}, to=sid)
    except jwt.ExpiredSignatureError:
        sio.emit('auth_error', {"message": "Session expired. Please log in again."}, to=sid)
    except jwt.InvalidTokenError:
        sio.emit('auth_error', {"message": "Invalid token. Please log in again."}, to=sid)

@sio.event
def send_message(sid, data):
    if sid not in clients:
        return
    username = clients[sid]
    text = data.get("text", "")
    msg_type = data.get("msg_type", "text")
    file_data = data.get("file_data")
    group_id = data.get("group_id", "global")
    
    timestamp = datetime.now().strftime('%H:%M')
    msg_id = str(uuid.uuid4())
    
    # Save to db
    database.save_message(msg_id, username, text, msg_type, file_data, timestamp, group_id)
    
    msg_obj = {
        "id": msg_id,
        "username": username,
        "text": text,
        "msg_type": msg_type,
        "file_data": file_data,
        "timestamp": timestamp,
        "is_edited": False,
        "deleted": False,
        "read_by": [],
        "group_id": group_id
    }
    sio.emit('new_message', msg_obj, room=group_id)

@sio.event
def edit_message(sid, data):
    if sid not in clients:
        return
    msg_id = data.get("id")
    new_text = data.get("text")
    group_id = data.get("group_id", "global")
    if database.update_message(msg_id, new_text):
        sio.emit('message_edited', {"id": msg_id, "text": new_text, "group_id": group_id}, room=group_id)

@sio.event
def delete_message(sid, data):
    if sid not in clients:
        return
    msg_id = data.get("id")
    group_id = data.get("group_id", "global")
    if database.delete_message(msg_id):
        sio.emit('message_deleted', {"id": msg_id, "group_id": group_id}, room=group_id)

@sio.event
def mark_read(sid, data):
    if sid not in clients:
        return
    username = clients[sid]
    msg_id = data.get("id")
    group_id = data.get("group_id", "global")
    if database.mark_message_read(msg_id, username):
        sio.emit('message_read', {"id": msg_id, "username": username, "group_id": group_id}, room=group_id)

@sio.event
def typing(sid, data):
    if sid in clients:
        username = clients[sid]
        group_id = data.get("group_id", "global")
        sio.emit('typing', {"username": username, "group_id": group_id}, room=group_id, skip_sid=sid)

@sio.event
def create_group(sid, data):
    if sid not in clients: return
    username = clients[sid]
    name = data.get("name")
    group_id = str(uuid.uuid4())
    if database.create_group(group_id, name, username):
        sio.enter_room(sid, group_id)
        groups = database.get_user_groups(username)
        sio.emit('user_groups', {"groups": groups}, to=sid)
        sio.emit('sys_msg', {'message': f"Group '{name}' created!"}, to=sid)

@sio.event
def join_group(sid, data):
    if sid not in clients: return
    username = clients[sid]
    group_id = data.get("group_id")
    if database.join_group(group_id, username):
        sio.enter_room(sid, group_id)
        groups = database.get_user_groups(username)
        sio.emit('user_groups', {"groups": groups}, to=sid)
        sio.emit('sys_msg', {'message': f"Joined group successfully!"}, to=sid)
        sio.emit('sys_msg', {'message': f"{username} joined the group!"}, room=group_id)

@sio.event
def fetch_history(sid, data):
    if sid not in clients: return
    group_id = data.get("group_id", "global")
    history = database.get_messages(group_id=group_id, limit=100)
    sio.emit('history', {"messages": history, "group_id": group_id}, to=sid)

@sio.event
def explore_groups(sid, data=None):
    if sid not in clients: return
    all_groups = database.get_all_groups()
    sio.emit('all_groups', {"groups": all_groups}, to=sid)

if __name__ == '__main__':
    print(f"[SERVER STARTED] Listening heavily on {HOST}:{PORT} using Socket.IO...")
    eventlet.wsgi.server(eventlet.listen((HOST, PORT)), app)
