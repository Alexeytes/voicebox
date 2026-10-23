-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Banners table
CREATE TABLE IF NOT EXISTS banners (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    image_url TEXT,
    target_url TEXT,
    alt_text TEXT,
    weight INTEGER,
    active_from TIMESTAMP,
    active_to TIMESTAMP,
    enabled BOOLEAN NOT NULL DEFAULT 1,
    position TEXT,
    html_snippet TEXT
);

-- Stats events
CREATE TABLE IF NOT EXISTS stats_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT NOT NULL,
    ip_hash TEXT,
    lang TEXT,
    voice_id TEXT,
    engine TEXT,
    duration_ms INTEGER,
    status TEXT,
    meta_json TEXT
);

CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
