import os
from supabase import create_client

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
BUCKET = os.getenv("SUPABASE_BUCKET", "imagevault")

def upload_file(file_data, filename, content_type, size):
    supabase.storage.from_(BUCKET).upload(filename, file_data.read(), {"content-type": content_type})
    return f"{os.getenv('SUPABASE_URL')}/storage/v1/object/public/{BUCKET}/{filename}"

def delete_file(filename):
    supabase.storage.from_(BUCKET).remove([filename])
