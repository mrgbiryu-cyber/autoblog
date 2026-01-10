-- A. Users & Subscription
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    subscription_tier VARCHAR(20) DEFAULT 'Starter', -- Starter, Pro, Enterprise
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- B. User Blogs & Growth Metrics
CREATE TABLE user_blogs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    platform_type VARCHAR(20), -- Naver, WordPress, Tistory
    blog_url TEXT NOT NULL,
    api_key_data JSONB, -- Encrypted API Keys
    current_tier INTEGER DEFAULT 1, -- Tier 1 (Seed), 2 (Growth), 3 (Authority)
    daily_visitors INTEGER DEFAULT 0,
    updated_at TIMESTAMP
);

-- C. Personalization & Persona (New)
CREATE TABLE user_presets (
    id SERIAL PRIMARY KEY,
    blog_id INTEGER REFERENCES user_blogs(id),
    persona_prompt TEXT,          -- e.g., "Friendly IT Expert"
    target_audience VARCHAR(100), -- e.g., "20-30s Beginners"
    category_keywords TEXT[],     -- e.g., ["AI", "Investment"]
    style_preference VARCHAR(50)  -- e.g., "Review-style", "Informative"
);

-- D. Content & SEO Logs
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    blog_id INTEGER REFERENCES user_blogs(id),
    target_keyword VARCHAR(100),
    title TEXT,
    content TEXT, -- Markdown
    seo_score INTEGER,
    status VARCHAR(20), -- DRAFT, PUBLISHED
    published_at TIMESTAMP
);

-- E. Crawler Sync Log (For Ontology)
CREATE TABLE crawl_sync_logs (
    id SERIAL PRIMARY KEY,
    blog_id INTEGER REFERENCES user_blogs(id),
    last_synced_at TIMESTAMP,
    new_entities_count INTEGER
);
