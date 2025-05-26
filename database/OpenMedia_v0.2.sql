-- Versión 0.2 de la base de datos OpenMedia
---------------------------
-- Extensión pgvector (requiere privilegios de superusuario)
---------------------------
CREATE EXTENSION IF NOT EXISTS vector;

---------------------------
-- Tabla de Autores (Mejorada)
---------------------------
CREATE TABLE authors (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    organization TEXT,          -- Opcional
    profile TEXT,               -- Opcional
    social_media JSONB,         -- Opcional (ej: {"twitter": "@user", "linkedin": "url"})
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

---------------------------
-- Tabla Principal de Noticias (Con campos opcionales)
---------------------------
CREATE TABLE news (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,               -- Opcional (generado por procesador)
    embedding VECTOR(1536),     -- Opcional (depende de procesamiento)
    summary_embedding VECTOR(1536), -- Opcional
    topic_classification JSONB, -- Opcional (ej: {"main": "politica", "sub": "elecciones"})
    writing_analysis JSONB,     -- Opcional (análisis de redacción)
    published_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    author_id INTEGER REFERENCES authors(id) ON DELETE SET NULL, -- Opcional
    facts JSONB,                -- Opcional (hechos extraídos)
    entities JSONB,             -- Opcional (entidades reconocidas)
    keywords TEXT[],            -- Opcional (palabras clave)
    ambiguity_score FLOAT,      -- Opcional
    context_score FLOAT,        -- Opcional
    relevance_score FLOAT,      -- Opcional
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

---------------------------
-- Metadatos de Scraping (Obligatorios para trazabilidad)
---------------------------
CREATE TABLE scraping_metadata (
    id SERIAL PRIMARY KEY,
    news_id INTEGER NOT NULL REFERENCES news(id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    url TEXT NOT NULL,
    original_published_at TIMESTAMP WITH TIME ZONE, -- Opcional
    http_status SMALLINT,        -- Opcional
    headers JSONB,               -- Opcional
    raw_html TEXT,               -- Opcional (para debugging)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

---------------------------
-- Tabla de Etiquetas (Mejorada)
---------------------------
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL DEFAULT 'user' CHECK (type IN ('auto', 'user', 'system')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

---------------------------
-- Relación Noticias-Etiquetas (Mejorada)
---------------------------
CREATE TABLE news_tags (
    news_id INTEGER NOT NULL REFERENCES news(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    confidence FLOAT,            -- Opcional (para etiquetas automáticas)
    source TEXT,                 -- Opcional (ej: 'modelo-ner', 'usuario:123')
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (news_id, tag_id)
);

---------------------------
-- Tabla de Métricas de Calidad Periodística (Nueva)
---------------------------
CREATE TABLE journalistic_metrics (
    id SERIAL PRIMARY KEY,
    news_id INTEGER NOT NULL REFERENCES news(id) ON DELETE CASCADE,
    objectivity_score FLOAT,     -- Opcional
    source_transparency_score FLOAT, -- Opcional
    diversity_score FLOAT,       -- Opcional
    context_score FLOAT,         -- Opcional
    factual_consistency_score FLOAT, -- Opcional
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

---------------------------
-- Tabla de Estado de Procesamiento (Crítica para pipeline)
---------------------------
CREATE TABLE processing_status (
    news_id INTEGER PRIMARY KEY REFERENCES news(id) ON DELETE CASCADE,
    is_summarized BOOLEAN NOT NULL DEFAULT FALSE,
    is_vector_generated BOOLEAN NOT NULL DEFAULT FALSE,
    is_categorized BOOLEAN NOT NULL DEFAULT FALSE,
    is_quality_analyzed BOOLEAN NOT NULL DEFAULT FALSE,
    last_processed_at TIMESTAMP WITH TIME ZONE,
    retry_count INTEGER NOT NULL DEFAULT 0,
    error_log TEXT[]             -- Opcional (histórico de errores)
);

---------------------------
-- Índices Especializados (Optimización)
---------------------------
-- Índice para búsqueda semántica
CREATE INDEX idx_news_embedding_cosine 
    ON news USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 100);

-- Índice para búsqueda full-text
CREATE INDEX idx_news_content_search 
    ON news USING GIN (to_tsvector('spanish', content));

-- Índice para fechas de publicación
CREATE INDEX idx_news_published_at 
    ON news (published_at DESC);

-- Índice parcial para estado de procesamiento
CREATE INDEX idx_processing_status_pending 
    ON processing_status (news_id) 
    WHERE NOT (is_summarized AND is_vector_generated AND is_categorized);