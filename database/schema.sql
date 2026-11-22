-- ========================================================
-- Multimodal AI Companion - MySQL Schema (8.0+)
-- ========================================================

CREATE DATABASE IF NOT EXISTS multimodal_companion
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE multimodal_companion;

-- 1. Conversations Table
CREATE TABLE IF NOT EXISTS conversations (
    conversation_id VARCHAR(36) NOT NULL,
    title VARCHAR(255) NOT NULL DEFAULT 'New Conversation',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (conversation_id),
    INDEX idx_conversations_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Messages Table
CREATE TABLE IF NOT EXISTS messages (
    message_id VARCHAR(36) NOT NULL,
    conversation_id VARCHAR(36) NOT NULL,
    sender ENUM('user', 'assistant', 'system') NOT NULL,
    message_content LONGTEXT NOT NULL,
    modality ENUM('text', 'image', 'document', 'audio', 'multimodal') NOT NULL DEFAULT 'text',
    metadata_json JSON NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (message_id),
    CONSTRAINT fk_messages_conversation
        FOREIGN KEY (conversation_id)
        REFERENCES conversations (conversation_id)
        ON DELETE CASCADE,
    INDEX idx_messages_conv_created (conversation_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Documents Table
CREATE TABLE IF NOT EXISTS documents (
    document_id VARCHAR(36) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size INT NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    upload_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processing_status ENUM('pending', 'processing', 'completed', 'failed') NOT NULL DEFAULT 'pending',
    error_message TEXT NULL,
    PRIMARY KEY (document_id),
    INDEX idx_documents_hash (file_hash),
    INDEX idx_documents_status (processing_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Document Chunks Table (with FULLTEXT index for lexical search)
CREATE TABLE IF NOT EXISTS document_chunks (
    chunk_id VARCHAR(36) NOT NULL,
    document_id VARCHAR(36) NOT NULL,
    chunk_index INT NOT NULL,
    chunk_text LONGTEXT NOT NULL,
    embedding JSON NULL,
    chunk_metadata JSON NULL,
    PRIMARY KEY (chunk_id),
    CONSTRAINT fk_chunks_document
        FOREIGN KEY (document_id)
        REFERENCES documents (document_id)
        ON DELETE CASCADE,
    INDEX idx_chunks_doc (document_id),
    FULLTEXT INDEX ft_chunk_text (chunk_text)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Knowledge Sources Table
CREATE TABLE IF NOT EXISTS knowledge_sources (
    source_id VARCHAR(36) NOT NULL,
    document_id VARCHAR(36) NOT NULL,
    source_name VARCHAR(255) NOT NULL,
    source_metadata JSON NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (source_id),
    CONSTRAINT fk_sources_document
        FOREIGN KEY (document_id)
        REFERENCES documents (document_id)
        ON DELETE CASCADE,
    INDEX idx_sources_doc (document_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
