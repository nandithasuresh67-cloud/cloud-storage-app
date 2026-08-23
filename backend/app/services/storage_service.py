"""
Thin wrapper around Supabase Storage for the upload flow.

Kept separate from the routes so the signed-URL logic has one place to
change, and so it can be swapped for a different provider (e.g. S3) later
without touching route code - the spec lists AWS S3 as a fallback option.
"""

from app.core.supabase_client import get_supabase


class StorageNotConfiguredError(RuntimeError):
    """Raised when Supabase credentials aren't set yet."""


def create_signed_upload_url(bucket: str, path: str) -> dict:
    """
    Returns {"signed_url": ..., "token": ..., "path": ...}. The frontend
    uploads the file bytes directly to `signed_url` (PUT), never through
    this backend - keeps large files off our server entirely.
    """
    supabase = get_supabase()
    if supabase is None:
        raise StorageNotConfiguredError(
            "Supabase is not configured. Set SUPABASE_URL and "
            "SUPABASE_SERVICE_ROLE_KEY in backend/.env."
        )
    return supabase.storage.from_(bucket).create_signed_upload_url(path)


def object_exists(bucket: str, path: str) -> bool:
    """
    Confirms the uploaded object actually landed in storage before we mark
    a file "uploaded" in the DB - a client could call complete-upload
    without ever having PUT the bytes.
    """
    supabase = get_supabase()
    if supabase is None:
        raise StorageNotConfiguredError(
            "Supabase is not configured. Set SUPABASE_URL and "
            "SUPABASE_SERVICE_ROLE_KEY in backend/.env."
        )
    folder = "/".join(path.split("/")[:-1])
    filename = path.split("/")[-1]
    entries = supabase.storage.from_(bucket).list(folder)
    return any(entry.get("name") == filename for entry in entries)


def create_signed_download_url(bucket: str, path: str, expires_in: int) -> str:
    supabase = get_supabase()
    if supabase is None:
        raise StorageNotConfiguredError(
            "Supabase is not configured. Set SUPABASE_URL and "
            "SUPABASE_SERVICE_ROLE_KEY in backend/.env."
        )
    result = supabase.storage.from_(bucket).create_signed_url(path, expires_in)
    return result["signedURL"]
