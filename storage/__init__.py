from core.config import settings

if settings.STORAGE_ENGINE == "s3":
    from .s3 import save_upload_file, delete_file, generate_download_url
else:
    from .local import save_upload_file, delete_file, generate_download_url