# ImageVault

ImageVault is a full-stack image storage application featuring a FastAPI backend, a PostgreSQL database for metadata, MinIO for scalable object storage, and JWT-based authentication. 

## Features

- **JWT Authentication:** Secure user registration and login.
- **Image Management:** Upload, list, view, and delete images securely.
- **Object Storage:** Stores actual image files using MinIO.
- **Metadata Database:** Keeps track of uploaded images, their sizes, and ownership in PostgreSQL.
- **Frontend Dashboard:** Simple web interface for interacting with the API.

## Project Structure

```
imagevault/
├── backend/            # FastAPI application (main.py, models.py, auth.py, etc.)
├── frontend/           # HTML/JS/CSS frontend served by the backend
├── docker-compose.yml  # Docker Compose file for MinIO & PostgreSQL
└── README.md
```

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed & running.
- [Python 3.10+](https://www.python.org/downloads/) installed.

## Setup Instructions

### 1. Start the Databases (Docker)

Use Docker Compose to start the PostgreSQL and MinIO services in the background:

```bash
docker-compose up -d
```

**Services created:**
- **PostgreSQL:** Running on port `5433` (User: `admin` | Password: `admin123` | DB: `imagevault`)
- **MinIO Console:** Running on [http://localhost:9001](http://localhost:9001) (User: `minioadmin` | Password: `minioadmin123`)
- **MinIO API:** Running on port `9000`

### 2. Setup the Python Environment

Navigate to the `backend` directory and install the required dependencies:

```bash
cd backend
pip install -r requirements.txt
```

> **Note:** Due to a known compatibility issue between `passlib` and newer versions of `bcrypt`, ensure `bcrypt` is downgraded to version `4.0.1`:
> ```bash
> pip install bcrypt==4.0.1
> ```

### 3. Run the FastAPI Server

Start the application backend:

```bash
python main.py
```
*(Alternatively, you can run `uvicorn main:app --reload`)*

The server will automatically create the necessary database tables and MinIO buckets upon startup.

## Accessing the Application

- **Frontend App:** [http://localhost:8000/](http://localhost:8000/)
- **API Documentation (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **MinIO Storage Console:** [http://localhost:9001](http://localhost:9001) 
  - *Login:* `minioadmin` / `minioadmin123`

## API Endpoints Overview

### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/login` - Obtain a JWT token

### User
- `GET /users/me` - Get profile of the current user

### Images
- `POST /images/upload` - Upload an image (Max size: 10MB)
- `GET /images` - List all uploaded images
- `GET /images/{image_id}` - Get image details
- `DELETE /images/{image_id}` - Delete an image and its metadata

## Stopping the Application

To stop the FastAPI server, press `Ctrl+C` in your terminal.
To stop and remove the Docker containers, run:

```bash
docker-compose down
```
*(Append `-v` if you also want to clear all the data inside Postgres and MinIO).*
