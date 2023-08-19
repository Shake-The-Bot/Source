-- Revises: V1

-- Creation Date: 2023-05-31 16:09:56.109551 UTC

-- Reason: Initial migration

CREATE TABLE
    IF NOT EXISTS commands (
        id SERIAL PRIMARY KEY,
        guild_id BIGINT,
        channel_id BIGINT,
        author_id BIGINT,
        used TIMESTAMP,
        prefix TEXT,
        command TEXT,
        failed BOOLEAN,
        app_command BOOLEAN
    );

CREATE INDEX
    IF NOT EXISTS commands_guild_id_idx ON commands (guild_id);

CREATE INDEX
    IF NOT EXISTS commands_author_id_idx ON commands (author_id);

CREATE INDEX IF NOT EXISTS commands_used_idx ON commands (used);

CREATE INDEX
    IF NOT EXISTS commands_command_idx ON commands (command);

CREATE INDEX IF NOT EXISTS commands_failed_idx ON commands (failed);

CREATE INDEX
    IF NOT EXISTS commands_app_command_idx ON commands (app_command);

CREATE TABLE
    IF NOT EXISTS rtfm (
        id SERIAL PRIMARY KEY,
        user_id BIGINT UNIQUE,
        count INTEGER DEFAULT (1)
    );

CREATE INDEX IF NOT EXISTS rtfm_user_id_idx ON rtfm (user_id);

CREATE TABLE
    IF NOT EXISTS locale (
        id SERIAL PRIMARY KEY,
        object_id BIGINT UNIQUE,
        locale TEXT
    );

CREATE INDEX
    IF NOT EXISTS locale_object_id_idx ON locale (object_id);