from minio import Minio
from minio.error import S3Error
import os

# ── MinIO connection ──────────────
minio_client = Minio(
    endpoint   = os.getenv("MINIO_ENDPOINT", "localhost:9000"),
    access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
    secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin123"),
    secure     = False  # True if using HTTPS
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
        url = f"http://{os.getenv('MINIO_ENDPOINT', 'localhost:9000')}/{BUCKET_NAME}/{filename}"
        return url
    except S3Error as e:
        raise Exception(f"MinIO upload failed: {e}")

# ── Delete file from MinIO ────────
def delete_file(filename: str):
    try:
        minio_client.remove_object(BUCKET_NAME, filename)
    except S3Error as e:
        raise Exception(f"MinIO delete failed: {e}")