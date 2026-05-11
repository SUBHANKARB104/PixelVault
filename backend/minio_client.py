from minio import Minio
from minio.error import S3Error
import os

# ── MinIO connection ──────────────
secure_env = os.getenv("MINIO_SECURE", "False").lower() in ("true", "1", "t")

minio_client = Minio(
    endpoint   = os.getenv("MINIO_ENDPOINT", "localhost:9000"),
    access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
    secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin123"),
    secure     = secure_env
)

BUCKET_NAME = os.getenv("MINIO_BUCKET", "my-images")

# ── Ensure bucket exists ──────────
def ensure_bucket():
    try:
        if not minio_client.bucket_exists(BUCKET_NAME):
            minio_client.make_bucket(BUCKET_NAME)
            print(f"[OK] Bucket '{BUCKET_NAME}' created.")
        else:
            print(f"[OK] Bucket '{BUCKET_NAME}' already exists.")
    except S3Error as e:
        print(f"[ERROR] MinIO error: {e}")

# ── Upload file to MinIO ──────────
def upload_file(file_data, filename: str, content_type: str, size: int) -> str:
    try:
        minio_client.put_object(
            bucket_name  = BUCKET_NAME,
            object_name  = filename,
            data         = file_data,
            length       = size,
            content_type = content_type
        )
        # Return public URL
        public_url_base = os.getenv(
            "MINIO_PUBLIC_URL", 
            f"http://{os.getenv('MINIO_ENDPOINT', 'localhost:9000')}/{BUCKET_NAME}"
        )
        public_url_base = public_url_base.rstrip('/')
        url = f"{public_url_base}/{filename}"
        return url
    except S3Error as e:
        raise Exception(f"MinIO upload failed: {e}")

# ── Delete file from MinIO ────────
def delete_file(filename: str):
    try:
        minio_client.remove_object(BUCKET_NAME, filename)
    except S3Error as e:
        raise Exception(f"MinIO delete failed: {e}")