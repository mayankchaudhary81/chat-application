# Deployment Guide

This application consists of a Python Socket.IO server, designed to handle long-running real-time connections, and a CustomTkinter Python client.

Because of the WebSocket requirement, serverless hostings like **Vercel** or **AWS Lambda** are not suitable as they are built for short HTTP requests and will kill idle or long running connections after ~60 seconds.

## Recommended: Deploying to Render

Render supports Docker containers and Background/Web Services seamlessly, which is perfect for Socket.IO. We've included a `render.yaml` Blueprint to make this a 1-click process.

### Steps for Render
1. Push your repository to GitHub.
2. Sign in to [Render](https://render.com).
3. Click "New" -> "Blueprint".
4. Connect your GitHub repository.
5. Render will detect the `render.yaml` and automate the creation of a Web Service equipped with a persistent 1GB SSD disk to safely store the SQLite database (`users.db`).
6. After deployment, update your client's hostname to the Render URL (e.g. `https://socket-chat-server.onrender.com`), and ensure the client connection uses WebSockets/polling accordingly.

## Deploying Locally via Docker

We have added a `Dockerfile` and `docker-compose.yml` for isolated container setups.

### Steps for Docker Compose
1. Ensure Docker Desktop is installed.
2. Run `docker-compose up --build -d`
3. The server will launch bound to `0.0.0.0:55555`.
4. A local volume is automatically created, so restarting the container won't wipe your users database.

## Security Controls Implemented

The server has been equipped with rate limiting mechanisms:
- Maximum 30 messages per minute per user/IP.
- Strict timeout on repetitive authentications.
- Payload limits preventing extremely large file uploads via WebSockets, mitigating DoS via enormous Base64 streams.
