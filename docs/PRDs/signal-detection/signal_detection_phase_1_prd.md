# Signal Detection Phase 1: Database Preparation & Admin Interface
## Product Requirements Document (PRD)

### Executive Summary
Prepare the database infrastructure and admin interface to support AI-powered signal detection analysis. This phase creates the foundation for storing analysis results and provides admin visibility into analysis-ready content without implementing AI agents.

---

## 1. Product Overview

### Vision
Create a robust data foundation for signal detection that focuses on high-quality content and provides clear admin visibility into analysis readiness and results.

### Core Value Proposition
- **Quality Focus**: Filter and prioritize analysis-ready articles (≥2000 characters)
- **Admin Visibility**: Clear interface for monitoring analysis pipeline and results
- **Infrastructure Ready**: Database schema prepared for AI analysis integration
- **Production Integration**: Seamless extension of existing system

---

## 2. Current State Analysis

### Production Data Insights (Last 24 Hours)
- **Total Articles**: 86 articles ingested
- **Analysis-Ready Articles**: 35 full articles (≥2000 chars) = 40.7%
- **Quality Publishers**: NewsBTC (100% full), CoinDesk (50% full), Crypto Potato (80% full)
- **Skip Publishers**: CoinTelegraph, Bitcoin.com, Decrypt (summary-only content)

### Content Quality Assessment
| Publisher | Full Articles | Quality Rating | Analysis Priority |
|-----------|---------------|----------------|-------------------|
| NewsBTC | 19/19 (100%) | ⭐⭐⭐⭐⭐ Excellent | High |
| CoinDesk | 8/16 (50%) | ⭐⭐⭐⭐ Good | High |
| Crypto Potato | 8/10 (80%) | ⭐⭐⭐⭐ Good | Medium |
| Others | 0% full articles | ⭐ Poor | Skip |

---

## 3. Functional Requirements

### 3.1 Database Schema Extensions
**Primary Responsibility**: Create tables to store analysis results and metadata

**Core Tables to Add**:

#### Article Analyses Table
```sql
CREATE TABLE article_analyses (
    id BIGSERIAL PRIMARY KEY,
    article_id BIGINT REFERENCES articles(id) NOT NULL,
    analysis_version VARCHAR(10) DEFAULT '1.0',

    -- Core Analysis Fields
    sentiment TEXT CHECK (sentiment IN ('POSITIVE', 'NEGATIVE', 'NEUTRAL', 'MIXED')),
    impact_score DECIMAL(3,2) CHECK (impact_score BETWEEN 0 AND 1),
    summary TEXT,
    context TEXT,

    -- Signal Detection Fields (JSONB for flexibility)
    weak_signals JSONB DEFAULT '[]',
    pattern_anomalies JSONB DEFAULT '[]',
    adjacent_connections JSONB DEFAULT '[]',
    narrative_gaps JSONB DEFAULT '[]',
    edge_indicators JSONB DEFAULT '[]',

    -- Validation Fields
    verified_facts JSONB DEFAULT '[]',
    research_sources JSONB DEFAULT '[]',
    validation_status TEXT DEFAULT 'PENDING' CHECK (validation_status IN ('PENDING', 'VALIDATED', 'FAILED')),

    -- Quality Metrics
    analysis_confidence DECIMAL(3,2) CHECK (analysis_confidence BETWEEN 0 AND 1),
    signal_strength DECIMAL(3,2) CHECK (signal_strength BETWEEN 0 AND 1),
    uniqueness_score DECIMAL(3,2) CHECK (uniqueness_score BETWEEN 0 AND 1),

    -- Processing Metadata
    processing_time_ms INTEGER,
    token_usage INTEGER,
    cost_usd DECIMAL(6,4),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_article_analyses_article_id ON article_analyses(article_id);
CREATE INDEX idx_article_analyses_validation_status ON article_analyses(validation_status);
CREATE INDEX idx_article_analyses_signal_strength ON article_analyses(signal_strength);
CREATE INDEX idx_article_analyses_created_at ON article_analyses(created_at);
```

#### Analysis Quality Tracking
```sql
CREATE TABLE analysis_quality_metrics (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    publisher_id BIGINT REFERENCES publishers(id),

    -- Volume Metrics
    total_articles INTEGER DEFAULT 0,
    analysis_ready_articles INTEGER DEFAULT 0,
    analyzed_articles INTEGER DEFAULT 0,

    -- Quality Metrics
    avg_signal_strength DECIMAL(3,2),
    avg_confidence_score DECIMAL(3,2),
    high_quality_signals INTEGER DEFAULT 0,

    -- Cost Metrics
    total_cost_usd DECIMAL(8,4) DEFAULT 0,
    avg_cost_per_article DECIMAL(6,4),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_analysis_quality_date_publisher ON analysis_quality_metrics(date, publisher_id);
```

**Technical Requirements**:
- Use Alembic migration for schema changes
- Maintain backward compatibility with existing data
- Add appropriate indexes for query performance
- Include foreign key constraints for data integrity

**Success Criteria**:
- Migration completes successfully on production database
- All existing functionality continues to work
- New tables are ready for analysis data storage

### 3.2 Admin Dashboard Enhancements
**Primary Responsibility**: Provide visibility into analysis-ready content and pipeline status

**Core Enhancements**:

#### Article Browser Filtering
- **Analysis Ready Filter**: Show only articles ≥2000 characters
- **Publisher Quality Filter**: Filter by analysis-worthy publishers
- **Analysis Status Column**: Show analysis completion status
- **Content Length Display**: Show character count for each article

#### Article Detail Page Enhancement
```typescript
// Add new "Analysis" tab to article detail
interface ArticleAnalysisTab {
  analysisStatus: 'pending' | 'completed' | 'failed' | 'not_eligible';
  contentLength: number;
  analysisEligible: boolean;
  analysisResults?: AnalysisResult;
}

// Analysis readiness indicator
function AnalysisReadinessIndicator({ article }: { article: Article }) {
  const isReady = article.body.length >= 2000;
  return (
    <Badge variant={isReady ? "success" : "secondary"}>
      {isReady ? `Analysis Ready (${article.body.length} chars)` : `Too Short (${article.body.length} chars)`}
    </Badge>
  );
}
```

#### New Signal Dashboard Route
- **Route**: `/signals` (new page)
- **Purpose**: Overview of analysis pipeline and results
- **Components**:
  - Analysis pipeline status cards
  - Publisher quality metrics
  - Recent analysis results
  - Cost tracking dashboard

**Technical Requirements**:
- Extend existing React admin dashboard
- Use established Shadcn/ui component patterns
- Integrate with existing API structure
- Maintain responsive design standards

**Success Criteria**:
- All analysis-ready articles clearly identifiable
- Admin can easily access analysis pipeline status
- New Signal Dashboard provides actionable insights

### 3.3 Backend API Extensions
**Primary Responsibility**: Provide API endpoints for analysis data and filtering

**Core API Endpoints**:

#### Analysis-Ready Articles
```python
@router.get("/api/articles/analysis-ready")
async def get_analysis_ready_articles(
    limit: int = 20,
    offset: int = 0,
    publisher_filter: Optional[str] = None
) -> List[Article]:
    """Get articles with ≥2000 characters, prioritized by quality publishers"""

    quality_publishers = ["NewsBTC", "CoinDesk", "Crypto Potato"]

    query = select(Article).where(
        Article.status == "ACTIVE",
        func.length(Article.body) >= 2000
    )

    if publisher_filter:
        query = query.join(Publisher).where(Publisher.name == publisher_filter)
    else:
        # Prioritize quality publishers
        query = query.join(Publisher).order_by(
            case(
                (Publisher.name.in_(quality_publishers), 1),
                else_=2
            ),
            Article.published_on.desc()
        )

    return await db.execute(query.offset(offset).limit(limit))
```

#### Analysis Results API
```python
@router.get("/api/articles/{article_id}/analysis")
async def get_article_analysis(article_id: int) -> Optional[ArticleAnalysis]:
    """Get analysis results for specific article"""

@router.get("/api/analysis/pipeline-status")
async def get_analysis_pipeline_status() -> AnalysisPipelineStatus:
    """Get overall analysis pipeline health and metrics"""

@router.get("/api/analysis/publisher-quality")
async def get_publisher_quality_metrics() -> List[PublisherQualityMetric]:
    """Get analysis quality metrics by publisher"""
```

#### Admin Status Extensions
```python
@router.get("/admin/analysis-status")
async def get_analysis_status() -> AnalysisSystemStatus:
    """Extended admin status including analysis pipeline metrics"""
    return {
        "analysis_pipeline": {
            "articles_pending_analysis": await count_pending_analysis(),
            "daily_analysis_volume": await get_daily_analysis_count(),
            "average_processing_time": await get_avg_processing_time(),
            "cost_today": await get_daily_cost(),
            "quality_publishers_active": await count_active_quality_publishers()
        },
        "content_quality": {
            "analysis_ready_percentage": await get_analysis_ready_percentage(),
            "top_quality_publishers": await get_top_quality_publishers(),
            "content_length_distribution": await get_content_length_stats()
        }
    }
```

**Technical Requirements**:
- Extend existing FastAPI router structure
- Use existing database connection patterns
- Implement proper error handling and validation
- Add appropriate caching for expensive queries

**Success Criteria**:
- All endpoints return data within 200ms
- Filtering and pagination work correctly
- Analysis-ready articles are properly prioritized

---

## 4. Technical Specifications

### 4.1 Migration Scripts
```python
# alembic/versions/add_analysis_tables.py
def upgrade():
    # Create article_analyses table
    op.create_table(
        'article_analyses',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('article_id', sa.BigInteger(), nullable=False),
        # ... (full table definition)
    )

    # Create indexes
    op.create_index('idx_article_analyses_article_id', 'article_analyses', ['article_id'])

    # Create analysis_quality_metrics table
    op.create_table('analysis_quality_metrics', ...)

def downgrade():
    op.drop_table('analysis_quality_metrics')
    op.drop_table('article_analyses')
```

### 4.2 Database Models
```python
# src/crypto_newsletter/shared/models/analysis.py
class ArticleAnalysis(Base):
    __tablename__ = "article_analyses"

    id = Column(BigInteger, primary_key=True)
    article_id = Column(BigInteger, ForeignKey("articles.id"), nullable=False)
    analysis_version = Column(String(10), default="1.0")

    # Core analysis fields
    sentiment = Column(String, CheckConstraint("sentiment IN ('POSITIVE', 'NEGATIVE', 'NEUTRAL', 'MIXED')"))
    impact_score = Column(Numeric(3, 2), CheckConstraint("impact_score BETWEEN 0 AND 1"))
    summary = Column(Text)
    context = Column(Text)

    # Signal detection fields (JSONB)
    weak_signals = Column(JSON, default=list)
    pattern_anomalies = Column(JSON, default=list)
    adjacent_connections = Column(JSON, default=list)
    narrative_gaps = Column(JSON, default=list)
    edge_indicators = Column(JSON, default=list)

    # Validation fields
    verified_facts = Column(JSON, default=list)
    research_sources = Column(JSON, default=list)
    validation_status = Column(String, default="PENDING")

    # Quality metrics
    analysis_confidence = Column(Numeric(3, 2))
    signal_strength = Column(Numeric(3, 2))
    uniqueness_score = Column(Numeric(3, 2))

    # Processing metadata
    processing_time_ms = Column(Integer)
    token_usage = Column(Integer)
    cost_usd = Column(Numeric(6, 4))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    article = relationship("Article", back_populates="analysis")
```

### 4.3 Frontend Component Updates
```typescript
// src/components/articles/AnalysisReadinessCard.tsx
interface AnalysisReadinessProps {
  article: Article;
}

export function AnalysisReadinessCard({ article }: AnalysisReadinessProps) {
  const contentLength = article.body?.length || 0;
  const isAnalysisReady = contentLength >= 2000;

  return (
    <Card className="p-4">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="font-medium">Analysis Readiness</h4>
          <p className="text-sm text-muted-foreground">
            {contentLength.toLocaleString()} characters
          </p>
        </div>
        <Badge variant={isAnalysisReady ? "success" : "secondary"}>
          {isAnalysisReady ? "Ready" : "Too Short"}
        </Badge>
      </div>

      {isAnalysisReady && (
        <div className="mt-3 pt-3 border-t">
          <p className="text-xs text-muted-foreground">
            ✓ Eligible for AI signal detection
          </p>
        </div>
      )}
    </Card>
  );
}
```

---

## 5. Quality Standards

### 5.1 Database Performance
- **Query Response Time**: <100ms for standard article queries
- **Migration Time**: <30 seconds for production deployment
- **Index Efficiency**: All analysis queries use appropriate indexes
- **Data Integrity**: Zero foreign key violations or constraint errors

### 5.2 Admin Interface Performance
- **Page Load Time**: <2 seconds for analysis dashboard
- **Filter Response Time**: <500ms for article filtering
- **Responsive Design**: Full functionality on mobile devices
- **Error Handling**: Graceful degradation for API failures

### 5.3 API Performance
- **Endpoint Response Time**: <200ms for analysis-ready articles
- **Concurrent Requests**: Handle 10+ simultaneous requests
- **Data Accuracy**: 100% accurate content length filtering
- **Pagination Efficiency**: Consistent performance across all pages

---

## 6. Success Metrics

### 6.1 Infrastructure Readiness
- **Database Migration**: Successfully deployed to production
- **API Endpoints**: All new endpoints functional and tested
- **Admin Interface**: Analysis features accessible and working
- **Data Quality**: Analysis-ready articles properly identified

### 6.2 Content Quality Insights
- **Daily Analysis Volume**: ~35 analysis-ready articles identified per day
- **Publisher Quality**: Clear distinction between high-quality and summary-only publishers
- **Content Distribution**: Accurate reporting of content length distribution
- **Filter Accuracy**: 100% accurate filtering by content length and publisher quality

---

## 7. Implementation Roadmap

### Day 1-2: Database Foundation
- Create database migration for new tables
- Implement SQLAlchemy models for analysis data
- Test migration on development environment
- Deploy migration to production

### Day 3-4: Backend API Development
- Implement analysis-ready articles endpoint
- Add analysis status endpoints
- Create publisher quality metrics API
- Test all endpoints with real data

### Day 5-7: Frontend Enhancement
- Add analysis readiness indicators to article browser
- Create analysis tab for article detail pages
- Implement signal dashboard route
- Test responsive design and user experience

---

## 8. Risk Assessment

### Technical Risks
- **Migration Complexity**: Mitigation through thorough testing and rollback plan
- **Performance Impact**: Mitigation through proper indexing and query optimization
- **Data Consistency**: Mitigation through careful foreign key relationships

### Operational Risks
- **Admin Training**: Mitigation through clear UI design and documentation
- **Feature Confusion**: Mitigation through progressive disclosure and help text
- **Performance Degradation**: Mitigation through monitoring and optimization

---

## 9. Dependencies

### Upstream Dependencies
- **Existing Database Schema**: Current articles and publishers tables
- **Admin Dashboard**: Existing React frontend structure
- **API Framework**: Current FastAPI router patterns

### Downstream Dependencies
- **Phase 2**: PydanticAI agents will use this database schema
- **Phase 3**: Analysis pipeline will populate these tables
- **Phase 4**: Admin interface will display analysis results

---

## 10. Acceptance Criteria

### Database Readiness
- [ ] All new tables created successfully
- [ ] Foreign key relationships working correctly
- [ ] Indexes providing expected query performance
- [ ] Migration rollback tested and working

### Admin Interface Functionality
- [ ] Analysis-ready articles clearly identified
- [ ] Content length displayed accurately
- [ ] Publisher quality filtering working
- [ ] Signal dashboard route accessible

### API Functionality
- [ ] Analysis-ready endpoint returning correct articles
- [ ] Filtering by publisher working correctly
- [ ] Pipeline status endpoint providing useful metrics
- [ ] All endpoints documented and tested

---

*Document Version: 1.0*
*Last Updated: August 14, 2025*
*Status: Ready for Implementation*
*Prerequisites: Current production system operational*
*Next Phase: PydanticAI Framework & Agent Setup*
