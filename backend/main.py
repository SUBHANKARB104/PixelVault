"""
ImageVault — FastAPI backend
Provides JWT-authenticated image upload/download/delete via MinIO object storage
backed by a PostgreSQL metadata database.
"""

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from pathlib import Path
import uuid
import os

# ── Local modules ─────────────────────────────────────────────────────
from database import engine, get_db, Base
import models
import schemas
from auth import hash_password, verify_password, create_token, get_current_user
from storage import upload_file, delete_file

# ── Create tables & app ──────────────────────────────────────────────
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ImageVault API",
    description="Secure image storage with Supabase Storage and Neon PostgreSQL",
    version="1.0.0",
)

@app.get("/")
def home():
    return {
        "status": "running",
        "message": "PixelVault API is live"
    }

# ── CORS (allow frontend) ────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Startup event ────────────────────────────────────────────────────


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AUTH ROUTES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.post("/auth/register", response_model=schemas.UserOut, status_code=201)
def register(req: schemas.RegisterRequest, db: Session = Depends(get_db)):
    """Create a new user account."""
    # Check for duplicate email
    if db.query(models.User).filter(models.User.email == req.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = models.User(
        name=req.name,
        email=req.email,
        password=hash_password(req.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=schemas.LoginResponse)
def login(req: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Authenticate and return a JWT access token."""
    user = db.query(models.User).filter(models.User.email == req.email).first()
    if not user or not verify_password(req.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_token({"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


# OAuth2-compatible login (used by Swagger "Authorize" button)
@app.post("/auth/token")
def login_for_swagger(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """OAuth2 form login — lets Swagger UI send the Authorize header."""
    user = db.query(models.User).filter(models.User.email == form.username).first()
    if not user or not verify_password(form.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  USER ROUTES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/users/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    return current_user


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  IMAGE ROUTES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml"}
MAX_SIZE = 10 * 1024 * 1024  # 10 MB


@app.post("/images/upload", response_model=schemas.ImageOut, status_code=201)
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Upload an image to MinIO and store its metadata in Postgres."""
    # ── Validate MIME type ──
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}. "
                   f"Allowed: {', '.join(ALLOWED_TYPES)}",
        )

    # ── Read file bytes & check size ──
    contents = await file.read()
    size = len(contents)
    if size > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large ({size} bytes). Max allowed: {MAX_SIZE} bytes.",
        )

    # ── Unique object name to avoid collisions ──
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_name = f"{current_user.id}/{uuid.uuid4().hex}{ext}"

    # ── Upload to MinIO ──
    from io import BytesIO
    url = upload_file(
        file_data=BytesIO(contents),
        filename=unique_name,
        content_type=file.content_type,
        size=size,
    )

    # ── Save metadata to Postgres ──
    image = models.Image(
        filename=unique_name,
        url=url,
        size_bytes=size,
        mime_type=file.content_type,
        user_id=current_user.id,
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


@app.get("/images", response_model=List[schemas.ImageOut])
def list_images(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """List all images belonging to the authenticated user."""
    return (
        db.query(models.Image)
        .filter(models.Image.user_id == current_user.id)
        .order_by(models.Image.created_at.desc())
        .all()
    )


@app.get("/images/{image_id}", response_model=schemas.ImageOut)
def get_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get metadata for a single image owned by the current user."""
    image = (
        db.query(models.Image)
        .filter(models.Image.id == image_id, models.Image.user_id == current_user.id)
        .first()
    )
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image


@app.delete("/images/{image_id}", status_code=204)
def delete_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Delete an image from MinIO and remove its metadata from Postgres."""
    image = (
        db.query(models.Image)
        .filter(models.Image.id == image_id, models.Image.user_id == current_user.id)
        .first()
    )
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Remove from object storage first
    delete_file(image.filename)

    # Then remove DB record
    db.delete(image)
    db.commit()
    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HEALTH CHECK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/health")
def health_check():
    """Simple liveness probe."""
    return {"status": "healthy", "service": "ImageVault API"}


# ── Serve frontend ───────────────────────────────────────────────────
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

@app.get("/")
def serve_frontend():
    """Serve the ImageVault frontend at the root URL."""
    return FileResponse(FRONTEND_DIR / "imagevault.html")


# ── Run with: uvicorn main:app --reload ──────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
