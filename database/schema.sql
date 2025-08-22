-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS `trisphere_budget` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Use the new database
USE `trisphere_budget`;

-- Table for user authentication and information
CREATE TABLE `users` (
    `id` BINARY(16) NOT NULL PRIMARY KEY,
    `username` VARCHAR(255) NOT NULL UNIQUE,
    `email` VARCHAR(255) NOT NULL UNIQUE,
    `hashed_password` VARCHAR(255) NOT NULL,
    `is_active` BOOLEAN NOT NULL DEFAULT 1,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table for main financial accounts
CREATE TABLE `accounts` (
    `id` BINARY(16) NOT NULL PRIMARY KEY,
    `user_id` BINARY(16) NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `initial_balance` DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table for budget categories and sub-categories
CREATE TABLE `categories` (
    `id` BINARY(16) NOT NULL PRIMARY KEY,
    `user_id` BINARY(16) NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `type` ENUM('Cash', 'Monthly', 'Savings', 'Transfer') NOT NULL,
    `budgeted_amount` DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table for financial transactions
CREATE TABLE `transactions` (
    `id` BINARY(16) NOT NULL PRIMARY KEY,
    `user_id` BINARY(16) NOT NULL,
    `account_id` BINARY(16),
    `category_id` BINARY(16) NOT NULL,
    `amount` DECIMAL(10, 2) NOT NULL,
    `description` VARCHAR(255),
    `transaction_date` DATE NOT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`account_id`) REFERENCES `accounts` (`id`) ON DELETE SET NULL,
    FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;