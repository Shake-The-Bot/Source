-- Revises: V11

-- Creation Date: 2023-06-29 13:51:04.914648 UTC

-- Reason: update

CREATE TABLE
    IF NOT EXISTS counting (
        id SERIAL PRIMARY KEY,
        channel_id BIGINT UNIQUE,
        guild_id BIGINT,
        message_id BIGINT,
        count BIGINT DEFAULT 0,
        user_id BIGINT,
        streak BIGINT DEFAULT 0,
        best BIGINT DEFAULT 0,
        goal BIGINT,
        webhook BOOLEAN,
        start BIGINT,
        done BOOLEAN DEFAULT false,
        used TIMESTAMP,
        math BOOLEAN,
        direction BOOLEAN,
        react BOOLEAN DEFAULT true,
        numbers BOOLEAN DEFAULT false,
        hardcore BOOLEAN DEFAULT false
    );

CREATE INDEX
    IF NOT EXISTS counting_message_id_idx ON counting (message_id);

CREATE INDEX
    IF NOT EXISTS counting_guild_id_idx ON counting (guild_id);

CREATE INDEX IF NOT EXISTS counting_used_id_idx ON counting (used);

CREATE INDEX
    IF NOT EXISTS counting_user_id_idx ON counting (user_id);

CREATE TABLE
    IF NOT EXISTS countings (
        id SERIAL PRIMARY KEY,
        channel_id BIGINT,
        guild_id BIGINT,
        direction BOOLEAN,
        user_id BIGINT,
        used TIMESTAMP,
        count BIGINT DEFAULT 0,
        failed BOOLEAN DEFAULT False
    );

CREATE INDEX
    IF NOT EXISTS countings_guild_id_idx ON countings (guild_id);

CREATE INDEX
    IF NOT EXISTS countings_channel_id_idx ON countings (channel_id);

CREATE INDEX
    IF NOT EXISTS countings_user_id_idx ON countings (user_id);

CREATE INDEX IF NOT EXISTS countings_used_idx ON countings (used);

CREATE INDEX IF NOT EXISTS countings_count_idx ON countings (count);

CREATE INDEX
    IF NOT EXISTS countings_failed_idx ON countings (failed);

CREATE TABLE
    IF NOT EXISTS aboveme (
        id SERIAL PRIMARY KEY,
        channel_id BIGINT UNIQUE,
        guild_id BIGINT,
        message_id BIGINT,
        count BIGINT DEFAULT 0,
        user_id BIGINT,
        used TIMESTAMP,
        phrases TEXT [],
        react BOOLEAN DEFAULT TRUE
    );

CREATE INDEX
    IF NOT EXISTS aboveme_message_id_idx ON aboveme (message_id);

CREATE INDEX
    IF NOT EXISTS aboveme_guild_id_idx ON aboveme (guild_id);

CREATE INDEX IF NOT EXISTS aboveme_used_id_idx ON aboveme (used);

CREATE INDEX IF NOT EXISTS aboveme_user_id_idx ON aboveme (user_id);

CREATE TABLE
    IF NOT EXISTS abovemes (
        id SERIAL PRIMARY KEY,
        channel_id BIGINT,
        guild_id BIGINT,
        user_id BIGINT,
        used TIMESTAMP,
        phrase Text,
        failed BOOLEAN DEFAULT False
    );

CREATE INDEX
    IF NOT EXISTS abovemes_guild_id_idx ON abovemes (guild_id);

CREATE INDEX
    IF NOT EXISTS abovemes_channel_id_idx ON abovemes (channel_id);

CREATE INDEX
    IF NOT EXISTS abovemes_user_id_idx ON abovemes (user_id);

CREATE INDEX IF NOT EXISTS abovemes_used_idx ON abovemes (used);

CREATE INDEX IF NOT EXISTS abovemes_phrase_idx ON abovemes (phrase);

CREATE INDEX IF NOT EXISTS abovemes_failed_idx ON abovemes (failed);

CREATE TABLE
    IF NOT EXISTS oneword (
        id SERIAL PRIMARY KEY,
        channel_id BIGINT UNIQUE,
        guild_id BIGINT,
        message_id BIGINT,
        user_id BIGINT,
        count BIGINT DEFAULT 0,
        words TEXT [],
        phrase TEXT,
        used TIMESTAMP,
        react BOOLEAN DEFAULT TRUE
    );

CREATE INDEX
    IF NOT EXISTS oneword_message_id_idx ON oneword (message_id);

CREATE INDEX
    IF NOT EXISTS oneword_guild_id_idx ON oneword (guild_id);

CREATE INDEX IF NOT EXISTS oneword_used_id_idx ON oneword (used);

CREATE INDEX IF NOT EXISTS oneword_user_id_idx ON oneword (user_id);

CREATE TABLE
    IF NOT EXISTS onewords (
        id SERIAL PRIMARY KEY,
        channel_id BIGINT,
        guild_id BIGINT,
        user_id BIGINT,
        used TIMESTAMP,
        failed BOOLEAN DEFAULT False
    );

CREATE INDEX
    IF NOT EXISTS onewords_guild_id_idx ON onewords (guild_id);

CREATE INDEX
    IF NOT EXISTS onewords_channel_id_idx ON onewords (channel_id);

CREATE INDEX
    IF NOT EXISTS onewords_user_id_idx ON onewords (user_id);

CREATE INDEX IF NOT EXISTS onewords_used_idx ON onewords (used);

CREATE INDEX IF NOT EXISTS onewords_count_idx ON onewords (count);

CREATE INDEX IF NOT EXISTS onewords_failed_idx ON onewords (failed);