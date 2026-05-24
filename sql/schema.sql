-- BRAHMO Citation Safety Engine - Database Schema
-- MySQL

CREATE TABLE IF NOT EXISTS citation_patterns (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pattern_name VARCHAR(50) NOT NULL UNIQUE,
    regex VARCHAR(500) NOT NULL,
    format_template VARCHAR(200),
    example VARCHAR(200),
    jurisdiction VARCHAR(100) DEFAULT 'India',
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS section_mappings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    old_section VARCHAR(50) NOT NULL,
    new_section VARCHAR(50) NOT NULL,
    old_act VARCHAR(100) NOT NULL,
    new_act VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_mapping (old_section, new_section)
);

CREATE TABLE IF NOT EXISTS verification_cache (
    id INT AUTO_INCREMENT PRIMARY KEY,
    citation_text VARCHAR(200) NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'UNVERIFIED',
    ik_doc_id VARCHAR(50) DEFAULT NULL,
    case_name VARCHAR(500) DEFAULT NULL,
    court VARCHAR(200) DEFAULT NULL,
    date_of_judgment VARCHAR(50) DEFAULT NULL,
    verified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME DEFAULT (CURRENT_TIMESTAMP + INTERVAL 7 DAY),
    INDEX idx_citation (citation_text),
    INDEX idx_expires (expires_at)
);

CREATE TABLE IF NOT EXISTS legal_matters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    client_name VARCHAR(100) NOT NULL,
    practice_area VARCHAR(50) NOT NULL,
    court VARCHAR(100) NOT NULL,
    query TEXT NOT NULL,
    scenario_type VARCHAR(50) DEFAULT NULL,
    sample_output TEXT DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);