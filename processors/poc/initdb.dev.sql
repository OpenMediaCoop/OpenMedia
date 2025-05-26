CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS news (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    embedding VECTOR(384),
    summary_embedding VECTOR(384),
    topic_classification JSONB,
    writing_analysis JSONB,
    published_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    author_id INTEGER,
    facts JSONB,
    entities JSONB,
    keywords TEXT[],
    ambiguity_score FLOAT,
    context_score FLOAT,
    relevance_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE scraping_metadata (
    id SERIAL PRIMARY KEY,
    news_id INT REFERENCES news(id),
    source TEXT,
    url TEXT,
    original_published_at TIMESTAMPTZ,
    http_status INT,
    headers JSONB,
    raw_html TEXT
);