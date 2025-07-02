-- MySQL Migration Script for Email Notifications Feature
-- Run this script in MySQL Workbench

-- Add email_notifications column to users table if it doesn't exist
SET @sql = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE TABLE_SCHEMA = DATABASE() 
     AND TABLE_NAME = 'users' 
     AND COLUMN_NAME = 'email_notifications') = 0,
    'ALTER TABLE users ADD COLUMN email_notifications BOOLEAN DEFAULT FALSE',
    'SELECT "Column email_notifications already exists" as message'
));

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Update existing users to have email notifications enabled by default
UPDATE users 
SET email_notifications = TRUE 
WHERE email_notifications IS NULL OR email_notifications = FALSE;

-- Create index for better performance on email notification queries
-- Step 1: Declare a variable
SET @index_exists := (
    SELECT COUNT(*) 
    FROM information_schema.statistics 
    WHERE table_schema = 'your_database_name' 
      AND table_name = 'users' 
      AND index_name = 'idx_users_email_notifications'
);

-- Step 2: Prepare & execute only if index does NOT exist
-- Use dynamic SQL to avoid syntax error
SET @stmt := IF(@index_exists = 0, 
    'CREATE INDEX idx_users_email_notifications ON users(email_notifications)', 
    'SELECT "Index already exists"');

-- Step 3: Prepare & execute
PREPARE run_stmt FROM @stmt;
EXECUTE run_stmt;
DEALLOCATE PREPARE run_stmt;

-- Verify the changes
SELECT 
    COUNT(*) as total_users, 
    SUM(CASE WHEN email_notifications = TRUE THEN 1 ELSE 0 END) as users_with_notifications,
    SUM(CASE WHEN email_notifications = FALSE THEN 1 ELSE 0 END) as users_without_notifications
FROM users;

-- Show the updated table structure
DESCRIBE users;

-- Display success message
SELECT 'Migration completed successfully! Email notifications column added to users table.' as status;
