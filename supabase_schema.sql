-- Supabase Tables for KT App
-- Run these SQL commands in your Supabase SQL Editor

-- Table: user_logins
-- Stores user login events (one record per user with latest login time)
CREATE TABLE IF NOT EXISTS user_logins (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    login_time TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: file_uploads
-- Stores file upload information
CREATE TABLE IF NOT EXISTS file_uploads (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    upload_time TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_user_logins_email ON user_logins(email);
CREATE INDEX IF NOT EXISTS idx_user_logins_time ON user_logins(login_time);
CREATE INDEX IF NOT EXISTS idx_file_uploads_email ON file_uploads(email);
CREATE INDEX IF NOT EXISTS idx_file_uploads_time ON file_uploads(upload_time);

-- Enable Row Level Security (RLS) - Optional
-- ALTER TABLE user_logins ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE file_uploads ENABLE ROW LEVEL SECURITY;

-- Create policies if you want to restrict access
-- For now, we'll allow all operations (you can customize later)
-- CREATE POLICY "Allow all operations on user_logins" ON user_logins FOR ALL USING (true);
-- CREATE POLICY "Allow all operations on file_uploads" ON file_uploads FOR ALL USING (true);

