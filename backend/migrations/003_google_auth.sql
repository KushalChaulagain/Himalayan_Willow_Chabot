-- Himalayan Willow Chatbot Database Schema
-- Migration 003: Google Auth - Users table for OAuth tracking

-- Users table for Google-authenticated users
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    google_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    full_name VARCHAR(255),
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);

-- Add foreign key to chat_sessions (user_id already exists as nullable)
ALTER TABLE chat_sessions
ADD CONSTRAINT fk_chat_sessions_user
FOREIGN KEY (user_id) REFERENCES users(id);

COMMENT ON TABLE users IS 'Google-authenticated users for tracking conversations and orders';
