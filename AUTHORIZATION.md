# TabletCAD Authorization

TabletCAD uses access-code authorization without collecting personal data.
There are no emails, passwords, usernames, or OAuth providers.

## Access Codes

- A user receives a random access code in the format `XXXXX-XXXXX-XXXXX-XXXXX`.
- The browser stores the code in `localStorage` through Dash `dcc.Store`.
- The server stores only a token hash in SQLite.
- If `TABCAD_TOKEN_SECRET` is set, token hashes use HMAC-SHA256.
- If `TABCAD_TOKEN_SECRET` is not set, token hashes fall back to SHA-256.

Set `TABCAD_TOKEN_SECRET` before first production use and keep it stable. If the
secret changes later, existing access codes will no longer resolve to their
stored presets.

## UI Behavior

Unauthenticated users can use the CAD workspace, calculations, 2D view, 3D view,
and STL export.

Unauthenticated users cannot:

- load presets;
- save presets;
- delete presets;
- export PDF files.

Authenticated users can:

- load/save/delete presets scoped to their access code;
- export PDF files;
- use STL export with token-based rate limits.

The right panel shows the current access-code status. Only a shortened code is
shown after sign-in.

## SQLite Schema

The application uses `presets.db` by default. In production, set `TABCAD_DB_PATH`
to a persistent Docker volume or bind mount path.

Tables:

- `users` — stores `id`, `token_hash`, `preset_limit`, `created_at`, `last_used_at`.
- `presets` — stores preset data scoped by `user_id`.
- `rate_limit_events` — stores hashed identities and timestamps for PDF/STL limits.

Old global preset databases are migrated safely: the old `presets` table is
renamed to `presets_legacy_<timestamp>`, and a new user-scoped `presets` table is
created.

## Rate Limits

PDF and STL exports are rate-limited server-side before expensive geometry,
Matplotlib, Kaleido, or STL generation starts.

Default limits:

- PDF: 10 exports per hour, 20 seconds cooldown.
- STL: 20 exports per hour, 10 seconds cooldown.

Rate-limiter identities are hashed. For authenticated users, the limiter uses
the user id. For unauthenticated STL export, it uses the client IP address from
the Flask request, respecting `X-Forwarded-For`.

## Admin Access Codes

Admin access codes are configured through `TABCAD_ADMIN_TOKENS`.

Admin codes:

- bypass PDF/STL rate limits;
- receive `TABCAD_ADMIN_PRESET_LIMIT`.

Do not commit real admin tokens to the repository. Configure them only through
server environment variables.

## Environment Variables

```bash
TABCAD_DB_PATH="/app/data/presets.db"
TABCAD_TOKEN_SECRET="replace-with-long-random-secret"
TABCAD_ADMIN_TOKENS="ABCDE-12345-FGHIJ-67890"
TABCAD_DEFAULT_PRESET_LIMIT=50
TABCAD_ADMIN_PRESET_LIMIT=1000000
TABCAD_PDF_LIMIT_PER_HOUR=10
TABCAD_PDF_COOLDOWN_SECONDS=20
TABCAD_STL_LIMIT_PER_HOUR=20
TABCAD_STL_COOLDOWN_SECONDS=10
```

For Docker deployments, mount a persistent directory:

```yaml
environment:
  TABCAD_DB_PATH: /app/data/presets.db
  TABCAD_TOKEN_SECRET: "replace-with-long-random-secret"
  TABCAD_ADMIN_TOKENS: "ABCDE-12345-FGHIJ-67890"
volumes:
  - ./data:/app/data
```
