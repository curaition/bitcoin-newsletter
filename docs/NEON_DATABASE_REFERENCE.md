# 🗄️ Neon Database Reference - Bitcoin Newsletter

## 📊 Database Overview

The Bitcoin Newsletter uses **Neon PostgreSQL** as its primary database, featuring AI-ready capabilities including vector extensions, database branching, and time travel. The database stores article content, publisher information, and AI-generated insights.

**Database URL**: `postgresql+asyncpg://neondb_owner:npg_prKBLEUJ1f8P@ep-purple-firefly-ab009z0a-pooler.eu-west-2.aws.neon.tech/neondb`

## 🏗️ Database Architecture

### Core Data Flow
```
CoinDesk API → Article Ingestion → Processing Pipeline → Database Storage
     ↓              ↓                    ↓                    ↓
• Fetch Articles • Deduplication    • Publisher Mgmt    • PostgreSQL
• Rate Limiting  • Validation       • Category Tagging  • Indexing
• Error Handling • Transformation   • Content Analysis  • Relationships
```

### AI-Ready Features
- ✅ **Vector Extensions**: Enabled for semantic search and embeddings
- ✅ **Database Branching**: Create isolated environments for testing
- ✅ **Time Travel**: Query historical data states
- ✅ **Auto-scaling**: Handles variable workloads automatically

## 📋 Table Reference

### 🏢 Core Content Tables

#### `publishers`
**Purpose**: Manages news sources and publication outlets
```sql
CREATE TABLE publishers (
    id BIGSERIAL PRIMARY KEY,
    source_id INTEGER UNIQUE NOT NULL,        -- CoinDesk API source ID
    source_key TEXT NOT NULL,                 -- API source identifier
    name TEXT NOT NULL,                       -- Publisher display name
    image_url TEXT,                          -- Publisher logo/image
    url TEXT,                                -- Publisher website
    lang TEXT,                               -- Language code (EN, etc.)
    source_type TEXT,                        -- Type of source
    launch_date TIMESTAMPTZ,                 -- When source was launched
    sort_order INTEGER DEFAULT 0,           -- Display ordering
    benchmark_score INTEGER,                 -- Quality/reliability score
    status TEXT DEFAULT 'ACTIVE',           -- ACTIVE/INACTIVE
    last_updated_ts TIMESTAMPTZ,            -- Last API update
    created_on TIMESTAMPTZ,                 -- Record creation
    updated_on TIMESTAMPTZ,                 -- Record modification
    created_at TIMESTAMPTZ DEFAULT NOW(),   -- System timestamp
    updated_at TIMESTAMPTZ DEFAULT NOW()    -- System timestamp
);
```
**Current Data**: 5+ active publishers (Bitcoin.com, CoinTelegraph, NewsBTC, CoinDesk, Crypto Potato)

#### `categories`
**Purpose**: Cryptocurrency topic classification system
```sql
CREATE TABLE categories (
    id BIGSERIAL PRIMARY KEY,
    category_id INTEGER UNIQUE NOT NULL,     -- CoinDesk API category ID
    name TEXT NOT NULL,                      -- Category display name
    category TEXT NOT NULL,                  -- Category identifier
    created_at TIMESTAMPTZ DEFAULT NOW(),   -- System timestamp
    updated_at TIMESTAMPTZ DEFAULT NOW()    -- System timestamp
);
```
**Current Data**: 10+ categories (BTC, TRADING, CRYPTOCURRENCY, MARKET, ETH, BUSINESS, etc.)

#### `articles`
**Purpose**: Core article content and metadata storage
```sql
CREATE TABLE articles (
    id BIGSERIAL PRIMARY KEY,
    external_id BIGINT UNIQUE NOT NULL,      -- CoinDesk API article ID
    guid TEXT UNIQUE NOT NULL,               -- Unique article identifier
    title TEXT NOT NULL,                     -- Article headline
    subtitle TEXT,                           -- Article subheading
    authors TEXT,                            -- Article authors
    url TEXT UNIQUE NOT NULL,                -- Article URL
    body TEXT,                               -- Full article content
    keywords TEXT,                           -- SEO keywords
    language TEXT,                           -- Content language
    image_url TEXT,                          -- Featured image
    published_on TIMESTAMPTZ,               -- Publication timestamp
    published_on_ns BIGINT,                 -- Nanosecond precision timestamp
    upvotes INTEGER DEFAULT 0,              -- Community engagement
    downvotes INTEGER DEFAULT 0,            -- Community engagement
    score INTEGER DEFAULT 0,                -- Calculated relevance score
    sentiment TEXT,                          -- POSITIVE/NEGATIVE/NEUTRAL
    status TEXT DEFAULT 'ACTIVE',           -- ACTIVE/INACTIVE/DELETED
    created_on TIMESTAMPTZ,                 -- API creation timestamp
    updated_on TIMESTAMPTZ,                 -- API update timestamp
    publisher_id BIGINT REFERENCES publishers(id), -- Publisher relationship
    source_id INTEGER,                       -- API source reference
    created_at TIMESTAMPTZ DEFAULT NOW(),   -- System timestamp
    updated_at TIMESTAMPTZ DEFAULT NOW()    -- System timestamp
);
```
**Current Data**: 29+ articles and growing automatically every 4 hours

#### `article_categories`
**Purpose**: Many-to-many relationship between articles and categories
```sql
CREATE TABLE article_categories (
    id BIGSERIAL PRIMARY KEY,
    article_id BIGINT REFERENCES articles(id),    -- Article reference
    category_id BIGINT REFERENCES categories(id), -- Category reference
    created_at TIMESTAMPTZ DEFAULT NOW(),         -- Assignment timestamp
    UNIQUE(article_id, category_id)               -- Prevent duplicates
);
```
**Purpose**: Enables articles to belong to multiple categories for flexible classification

### 🤖 AI Agent Tables

#### `signals`
**Purpose**: AI-detected market signals and weak signals from articles
```sql
CREATE TABLE signals (
    id BIGSERIAL PRIMARY KEY,
    article_id BIGINT REFERENCES articles(id) NOT NULL, -- Source article
    signal_type VARCHAR(100) NOT NULL,          -- Type of signal detected
    description TEXT NOT NULL,                  -- Human-readable description
    confidence FLOAT NOT NULL,                  -- AI confidence score (0-1)
    implications TEXT,                          -- Potential market implications
    detected_at TIMESTAMPTZ DEFAULT NOW(),     -- Detection timestamp
    agent_version VARCHAR(50),                  -- AI agent version
    metadata JSONB,                            -- Additional signal data
    created_at TIMESTAMPTZ DEFAULT NOW(),      -- System timestamp
    updated_at TIMESTAMPTZ DEFAULT NOW()       -- System timestamp
);
```
**Purpose**: Stores AI-detected patterns, trends, and weak signals for newsletter generation

#### `signal_validations`
**Purpose**: Research validation results for detected signals
```sql
CREATE TABLE signal_validations (
    id BIGSERIAL PRIMARY KEY,
    signal_id BIGINT REFERENCES signals(id) NOT NULL, -- Signal being validated
    validation_status VARCHAR(20) NOT NULL,     -- CONFIRMED/REJECTED/UNCERTAIN
    evidence_summary TEXT,                      -- Research findings summary
    research_sources JSONB,                    -- External sources consulted
    validation_confidence FLOAT NOT NULL,      -- Validation confidence (0-1)
    research_cost_usd FLOAT,                   -- Cost of research APIs
    validated_at TIMESTAMPTZ DEFAULT NOW(),    -- Validation timestamp
    agent_version VARCHAR(50),                 -- Validation agent version
    created_at TIMESTAMPTZ DEFAULT NOW(),     -- System timestamp
    updated_at TIMESTAMPTZ DEFAULT NOW()      -- System timestamp
);
```
**Purpose**: Tracks research validation of AI-detected signals using external sources

#### `newsletters`
**Purpose**: Generated newsletter content and metadata
```sql
CREATE TABLE newsletters (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,               -- Newsletter title
    content TEXT NOT NULL,                     -- Full newsletter content
    summary TEXT,                              -- Executive summary
    generation_date DATE NOT NULL,            -- Publication date
    status VARCHAR(20) DEFAULT 'DRAFT',       -- DRAFT/REVIEW/PUBLISHED/ARCHIVED
    quality_score FLOAT,                       -- AI quality assessment
    agent_version VARCHAR(50),                 -- Generation agent version
    generation_metadata JSONB,                -- Generation parameters
    published_at TIMESTAMPTZ,                 -- Publication timestamp
    created_at TIMESTAMPTZ DEFAULT NOW(),     -- System timestamp
    updated_at TIMESTAMPTZ DEFAULT NOW()      -- System timestamp
);
```
**Purpose**: Stores AI-generated newsletter content with quality metrics

#### `newsletter_articles`
**Purpose**: Links newsletters to source articles
```sql
CREATE TABLE newsletter_articles (
    id BIGSERIAL PRIMARY KEY,
    newsletter_id BIGINT REFERENCES newsletters(id) NOT NULL, -- Newsletter reference
    article_id BIGINT REFERENCES articles(id) NOT NULL,       -- Source article
    inclusion_reason TEXT,                     -- Why article was selected
    weight FLOAT DEFAULT 1.0,                -- Article importance weight
    created_at TIMESTAMPTZ DEFAULT NOW(),    -- Link creation timestamp
    UNIQUE(newsletter_id, article_id)        -- Prevent duplicates
);
```
**Purpose**: Tracks which articles contributed to each newsletter

#### `article_embeddings`
**Purpose**: Vector embeddings for semantic search and similarity
```sql
CREATE TABLE article_embeddings (
    id BIGSERIAL PRIMARY KEY,
    article_id BIGINT REFERENCES articles(id) NOT NULL, -- Source article
    embedding FLOAT[] NOT NULL,               -- Vector embedding (will use vector type)
    embedding_model VARCHAR(100) NOT NULL,   -- Model used (e.g., "text-embedding-3-small")
    embedding_version VARCHAR(50) NOT NULL,  -- Model version
    created_at TIMESTAMPTZ DEFAULT NOW(),    -- Generation timestamp
    UNIQUE(article_id, embedding_model, embedding_version) -- Prevent duplicates
);
```
**Purpose**: Enables semantic search, article similarity, and AI content analysis

#### `agent_executions`
**Purpose**: Tracks AI agent runs and performance metrics
```sql
CREATE TABLE agent_executions (
    id BIGSERIAL PRIMARY KEY,
    agent_type VARCHAR(100) NOT NULL,        -- Type of agent (signal_detection, newsletter_generation)
    execution_status VARCHAR(20) NOT NULL,   -- RUNNING/COMPLETED/FAILED
    started_at TIMESTAMPTZ DEFAULT NOW(),    -- Execution start time
    completed_at TIMESTAMPTZ,                -- Execution completion time
    execution_time_ms INTEGER,               -- Duration in milliseconds
    tokens_used INTEGER,                     -- LLM tokens consumed
    cost_usd FLOAT,                          -- Execution cost
    error_message TEXT,                      -- Error details if failed
    metadata JSONB,                          -- Execution parameters
    created_at TIMESTAMPTZ DEFAULT NOW(),   -- System timestamp
    updated_at TIMESTAMPTZ DEFAULT NOW()    -- System timestamp
);
```
**Purpose**: Monitors AI agent performance, costs, and reliability

## 🔍 Database Indexes

### Performance Indexes
```sql
-- Article lookups
CREATE INDEX idx_articles_external_id ON articles(external_id);
CREATE INDEX idx_articles_published_on ON articles(published_on);
CREATE INDEX idx_articles_status ON articles(status);
CREATE INDEX idx_articles_publisher_id ON articles(publisher_id);

-- Signal analysis
CREATE INDEX idx_signals_article_id ON signals(article_id);
CREATE INDEX idx_signals_type_confidence ON signals(signal_type, confidence);
CREATE INDEX idx_signals_detected_at ON signals(detected_at);

-- Newsletter generation
CREATE INDEX idx_newsletters_generation_date ON newsletters(generation_date);
CREATE INDEX idx_newsletters_status ON newsletters(status);

-- Agent monitoring
CREATE INDEX idx_agent_executions_type_status ON agent_executions(agent_type, execution_status);
CREATE INDEX idx_agent_executions_started_at ON agent_executions(started_at);
```

## 📊 Current Database Status

### Production Metrics
- **Total Articles**: 29+ and growing every 4 hours
- **Active Publishers**: 5 major cryptocurrency news sources
- **Categories**: 10+ cryptocurrency topics
- **Recent Activity**: 15 articles ingested in last 24 hours
- **Growth Rate**: ~30 new articles per day

### Data Quality
- **Deduplication**: Prevents duplicate articles by external_id, guid, and URL
- **Validation**: All articles validated before storage
- **Relationships**: Proper foreign key constraints maintain data integrity
- **Timestamps**: Full audit trail with created_at/updated_at

## 🚀 AI Capabilities

### Vector Search Ready
- **Extension**: `vector` extension enabled for embeddings
- **Semantic Search**: Article similarity and content analysis
- **Clustering**: Group related articles by topic/sentiment

### Database Branching
- **Development**: Create isolated branches for testing
- **Experimentation**: Test AI models without affecting production
- **Rollback**: Time travel to previous database states

### Scaling Features
- **Auto-scaling**: Handles variable article ingestion loads
- **Connection Pooling**: Optimized for concurrent access
- **Read Replicas**: Can scale read operations independently

## 🔧 Maintenance

### Automated Tasks
- **Article Ingestion**: Every 4 hours via Celery Beat
- **Cleanup**: Daily removal of old/inactive records
- **Statistics**: Real-time metrics via admin endpoints

### Monitoring
- **Health Checks**: Database connectivity monitoring
- **Performance**: Query performance tracking
- **Growth**: Article count and publisher activity

**The Neon database provides a robust, AI-ready foundation for the Bitcoin Newsletter with automatic scaling, vector capabilities, and comprehensive article management.** 🎉
