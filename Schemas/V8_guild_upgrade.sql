-- Revises: V8
-- Creation Date: 2023-06-18 07:38:56.576025 UTC
-- Reason: upgrade


CREATE TABLE IF NOT EXISTS aboveme (
    id SERIAL PRIMARY KEY,
    channel_id BIGINT UNIQUE,
    guild_id BIGINT,
    count BIGINT DEFAULT 0,
    user_id BIGINT,
    used TIMESTAMP,
    phrases TEXT[],
    "react" BOOLEAN DEFAULT TRUE,
    hardcore BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS aboveme_guild_id_idx ON aboveme (guild_id);
CREATE INDEX IF NOT EXISTS aboveme_used_id_idx ON aboveme (used);
CREATE INDEX IF NOT EXISTS aboveme_user_id_idx ON aboveme (user_id);


CREATE TABLE IF NOT EXISTS counting (
    id SERIAL PRIMARY KEY,
    channel_id BIGINT UNIQUE,
    guild_id BIGINT,
    count BIGINT DEFAULT 0,
    user_id BIGINT,
    streak BIGINT DEFAULT 0,
    best BIGINT DEFAULT 0,
    goal BIGINT,
    used TIMESTAMP,
    "react" BOOLEAN DEFAULT TRUE,
    numbers BOOLEAN DEFAULT FALSE,
    hardcore BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS counting_guild_id_idx ON counting (guild_id);
CREATE INDEX IF NOT EXISTS counting_used_id_idx ON counting (used);
CREATE INDEX IF NOT EXISTS counting_user_id_idx ON counting (user_id);


CREATE TABLE IF NOT EXISTS oneword (
    id SERIAL PRIMARY KEY,
    channel_id BIGINT UNIQUE,
    guild_id BIGINT,
    user_id BIGINT,
    count BIGINT DEFAULT 0,
    words TEXT[],
    phrase TEXT,
    used TIMESTAMP,
    "react" BOOLEAN DEFAULT TRUE,
    hardcore BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS oneword_guild_id_idx ON oneword (guild_id);
CREATE INDEX IF NOT EXISTS oneword_used_id_idx ON oneword (used);
CREATE INDEX IF NOT EXISTS oneword_user_id_idx ON oneword (user_id);
