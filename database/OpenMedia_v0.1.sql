-- 1. Ensure pgvector extension is enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Authors table
CREATE TABLE authors (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    organization TEXT,
    profile TEXT
);

-- 3. Main news table
CREATE TABLE news (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    embedding VECTOR(1536),
    topic_classification TEXT,
    writing_analysis JSONB,
    published_at TIMESTAMP DEFAULT now(),
    author_id INTEGER REFERENCES authors(id) ON DELETE SET NULL
);

-- 4. Scraping metadata table
CREATE TABLE scraping_metadata (
    id SERIAL PRIMARY KEY,
    news_id INTEGER REFERENCES news(id) ON DELETE CASCADE,
    source TEXT,
    url TEXT,
    original_published_at TIMESTAMP,
    extra JSONB
);

-- 5. Tags table
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE
);

-- 6. Many-to-many relation between news and tags
CREATE TABLE news_tags (
    news_id INTEGER REFERENCES news(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (news_id, tag_id)
);

-- 7. (Optional) Vector search index using cosine similarity
CREATE INDEX idx_news_embedding_cosine 
    ON news USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 100);
