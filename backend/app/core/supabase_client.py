from functools import lru_cache

from supabase import Client, create_client

from app.core.config import get_settings


@lru_cache
def get_supabase() -> Client | None:
    """
    Returns a Supabase client using the service-role key (server-side only —
    never expose this key to the frontend). Returns None if not yet
    configured, so the app can still boot on Day 1 before Supabase is wired.
    """
    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        return None
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
