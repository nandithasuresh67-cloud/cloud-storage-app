# ER Diagram — Cloud Storage Service (Day 1)

Covers the 8 core tables from the spec (section 6). Renders natively on GitHub.

```mermaid
erDiagram
    USERS ||--o{ FOLDERS : owns
    USERS ||--o{ FILES : owns
    USERS ||--o{ SHARES : "shares with / from"
    USERS ||--o{ LINK_SHARES : creates
    USERS ||--o{ STARS : stars
    USERS ||--o{ ACTIVITIES : performs
    FOLDERS ||--o{ FOLDERS : "parent_id (nested)"
    FOLDERS ||--o{ FILES : contains
    FILES ||--o{ FILE_VERSIONS : "has versions"
    FILES ||--o{ SHARES : "shared as"
    FILES ||--o{ LINK_SHARES : "linked as"
    FILES ||--o{ STARS : "starred as"
    FOLDERS ||--o{ SHARES : "shared as"
    FOLDERS ||--o{ LINK_SHARES : "linked as"

    USERS {
        uuid id PK
        string email UK
        string full_name
        string password_hash
        string oauth_provider
        string oauth_sub
        boolean is_active
        bigint storage_quota_bytes
        datetime created_at
        datetime updated_at
    }

    FOLDERS {
        uuid id PK
        string name
        uuid owner_id FK
        uuid parent_id FK "self-ref, nullable = root"
        boolean is_trashed
        datetime trashed_at
        datetime created_at
        datetime updated_at
    }

    FILES {
        uuid id PK
        string name
        uuid owner_id FK
        uuid folder_id FK "nullable = root"
        string storage_bucket
        string storage_path UK
        string mime_type
        bigint size_bytes
        boolean is_starred
        boolean is_trashed
        datetime trashed_at
        datetime created_at
        datetime updated_at
    }

    FILE_VERSIONS {
        uuid id PK
        uuid file_id FK
        int version_number
        string storage_path
        bigint size_bytes
        uuid created_by FK
        datetime created_at
    }

    SHARES {
        uuid id PK
        uuid file_id FK "nullable"
        uuid folder_id FK "nullable, exactly one of file/folder set"
        uuid shared_with_user_id FK
        uuid shared_by_user_id FK
        enum role "viewer | editor"
        datetime created_at
    }

    LINK_SHARES {
        uuid id PK
        uuid file_id FK "nullable"
        uuid folder_id FK "nullable"
        string token UK
        string password_hash "nullable"
        datetime expires_at "nullable"
        uuid created_by FK
        datetime created_at
    }

    STARS {
        uuid id PK
        uuid user_id FK
        uuid file_id FK "nullable"
        uuid folder_id FK "nullable"
        datetime created_at
    }

    ACTIVITIES {
        uuid id PK
        uuid user_id FK "nullable, SET NULL on user delete"
        string action
        uuid file_id FK "nullable"
        uuid folder_id FK "nullable"
        jsonb meta
        datetime created_at
    }
```

## Design notes

- **UUID primary keys** everywhere — safe for public URLs (shareable links, signed API responses) without leaking sequential IDs.
- **`folders.parent_id` is self-referencing** (nullable) to give nested folder hierarchy; a `NULL` parent means a root-level folder for that owner.
- **`files.storage_bucket` + `storage_path`** are the pointer into Supabase Storage — the DB never stores file bytes, only metadata + the object path.
- **Soft delete** via `is_trashed` + `trashed_at` on `folders` and `files` (Trash & Restore feature, Day 6) instead of hard deletes.
- **`shares`** has a check constraint requiring exactly one of `file_id` / `folder_id` — a share always targets either a file or a folder, never both/neither.
- **`link_shares`** supports the "public shareable link" feature with optional password (`password_hash`) and optional `expires_at`.
- **`activities`** stores a generic `meta` JSONB blob so new action types (Phase 2 activity log) don't require schema migrations.
- **`file_versions`** is modeled now (Phase 2 feature) so the FK shape is right from day one, even though the version-upload flow isn't built until later.
