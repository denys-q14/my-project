-- SQL RBAC policy for PostgreSQL

-- 1. Create roles
CREATE ROLE user_role;
CREATE ROLE service_account_role;

-- 2. Grant permissions to roles
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE notes TO user_role;
GRANT SELECT ON TABLE notes TO service_account_role;

-- 3. Enable Row-Level Security
ALTER TABLE notes ENABLE ROW LEVEL SECURITY;

-- 4. Policy: users see only their notes
CREATE POLICY user_notes_policy ON notes
    FOR SELECT TO user_role
    USING (user_id = current_setting('app.current_user_id')::int);

-- 5. Policy: service account sees all notes
CREATE POLICY service_account_policy ON notes
    FOR SELECT TO service_account_role
    USING (true);

-- 6. Example: assign roles to users
-- GRANT user_role TO user1;
-- GRANT service_account_role TO service_account;

-- EXPLAIN ANALYZE SELECT * FROM notes WHERE title = '...' OR created_at = '...';
