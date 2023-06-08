-- Revises: V3
-- Creation Date: 2023-06-04 06:25:39.025836 UTC
-- Reason: Initial migration


CREATE TABLE IF NOT EXISTS aboveme (
    id SERIAL PRIMARY KEY,
    channel_id BIGINT UNIQUE,
    count BIGINT DEFAULT 0,
    guild_id BIGINT,
    user_id BIGINT,
    used TIMESTAMP,
    phrases TEXT[],
    hardcore BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS aboveme_guild_id_idx ON aboveme (guild_id);
CREATE INDEX IF NOT EXISTS aboveme_used_id_idx ON aboveme (used);
CREATE INDEX IF NOT EXISTS aboveme_user_id_idx ON aboveme (user_id);


CREATE TABLE IF NOT EXISTS counting (
    id SERIAL PRIMARY KEY,
    channel_id BIGINT UNIQUE,
    count BIGINT DEFAULT 0,
    guild_id BIGINT,
    user_id BIGINT,
    streak BIGINT,
    best BIGINT,
    goal BIGINT,
    used TIMESTAMP,
    numbers BOOLEAN DEFAULT FALSE,
    hardcore BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS counting_guild_id_idx ON counting (guild_id);
CREATE INDEX IF NOT EXISTS counting_used_id_idx ON counting (used);
CREATE INDEX IF NOT EXISTS counting_user_id_idx ON counting (user_id);