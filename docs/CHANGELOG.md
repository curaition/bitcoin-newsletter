# Changelog

All notable changes to the Bitcoin Newsletter project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2024-12-19

### Added - Enhanced Newsletter Generation System

#### 🔧 Critical Bug Fixes
- **Fixed broken field mapping** in signal data formatting that caused "Unknown" to appear everywhere
  - Corrected `signal.get('signal')` to `signal.get('signal_type')`
  - Corrected `pattern.get('pattern')` to `pattern.get('expected_pattern')`
  - Corrected `conn.get('connection')` to `conn.get('connection_type')`
- **Added article URLs** to newsletter generation context for proper citations
- **Preserved rich signal context** including confidence scores, timeframes, and significance levels

#### 📊 Real-time Progress Tracking
- **Database schema**: New `newsletter_generation_progress` table with JSONB columns
- **Step-by-step visualization**: Selection → Synthesis → Writing → Storage
- **Quality metrics tracking**: Stories selected, quality scores, citations, word count
- **Intermediate results preview**: Selected stories, themes, newsletter preview
- **Estimated completion times** and progress percentages
- **Enhanced orchestrator**: `ProgressAwareNewsletterOrchestrator` with quality validation

#### 🎨 Frontend Integration
- **Real-time progress components**:
  - `NewsletterGenerationProgress`: Live step-by-step tracking
  - `NewsletterGenerationComplete`: Success state with details
  - `NewsletterGenerationError`: Error handling with retry options
- **Progress polling**: Every 2 seconds during generation
- **Quality metrics display**: Visual indicators for all quality metrics
- **Enhanced API client**: `getGenerationProgress()` method with TypeScript types

#### 🤖 AI Quality Improvements
- **Enhanced agent prompts** with citation requirements and signal utilization
- **Quality validation framework** at each generation step
- **Proper article citations** with URLs in newsletters
- **Signal utilization** with confidence scores and timeframes
- **Newsletter writer agent** updated with comprehensive citation requirements

#### 🚨 Monitoring and Alerting System
- **Newsletter generation metrics collection** with quality tracking
- **Comprehensive alert system**:
  - Quality score alerts (WARNING < 0.7, CRITICAL < 0.5)
  - Citation count alerts (WARNING < 5, CRITICAL < 3)
  - Failure rate alerts (WARNING > 20%, CRITICAL > 50%)
  - Stuck generation detection (> 2 hours)
- **Structured logging integration** following existing project patterns
- **Celery task scheduling** for periodic alert checking (every 15 minutes)
- **Health check integration** with existing monitoring system

#### 🔄 Enhanced Task Management
- **Enhanced Celery tasks**: `generate_newsletter_manual_task_enhanced` with progress tracking
- **Progress tracker service**: Async context manager for database operations
- **Quality validation classes**: `SelectionQuality`, `SynthesisQuality`, `WritingQuality`
- **Alert management**: `NewsletterAlertManager` with configurable thresholds

### Changed
- **Newsletter generation endpoint** now returns `progress_endpoint` URL for frontend polling
- **Admin dashboard** updated to use enhanced generation with progress tracking
- **Health check system** extended to include newsletter generation progress monitoring
- **Celery beat schedule** updated with newsletter alert checking task

### Technical Details
- **Database migration**: Added progress tracking table with proper indexes
- **API endpoints**: New `/admin/tasks/{task_id}/progress` endpoint
- **Frontend types**: Enhanced TypeScript interfaces for progress tracking
- **Monitoring integration**: Extended existing metrics collection system
- **Alert thresholds**: Configurable via environment variables

### Performance Improvements
- **Progress tracking**: Efficient database queries with proper indexing
- **Real-time updates**: Optimized polling with 2-second intervals
- **Quality validation**: Fast validation at each generation step
- **Alert checking**: Lightweight periodic monitoring every 15 minutes

### Documentation Updates
- **MONITORING.md**: Added newsletter generation progress tracking section
- **API documentation**: Updated with new progress tracking endpoints
- **Frontend documentation**: Added progress visualization components
- **Alert configuration**: Environment variable documentation

## [2.0.0] - 2024-12-15

### Added - Signal Analysis System
- **PydanticAI-powered multi-agent system** for signal detection
- **Content analysis agent** for weak signal identification
- **Signal validation agent** for quality assurance
- **Batch processing system** for analyzing multiple articles
- **Cost tracking and budget management**
- **Comprehensive signal analysis models**

### Added - Newsletter Generation
- **Automated daily and weekly newsletter generation**
- **Story selection agent** for identifying revealing articles
- **Synthesis agent** for pattern identification
- **Newsletter writer agent** for content creation
- **Quality scoring and validation**

### Added - Infrastructure
- **Railway deployment configuration**
- **Neon PostgreSQL database integration**
- **Redis caching and task queue**
- **Celery worker and beat services**
- **Comprehensive monitoring and health checks**

## [1.0.0] - 2024-12-01

### Added - Core Data Pipeline
- **CoinDesk API integration** for article ingestion
- **Article processing and storage**
- **Publisher and category management**
- **Basic web interface for article viewing**
- **Health monitoring system**
- **Scheduled article ingestion every 4 hours**

### Infrastructure
- **FastAPI web framework**
- **SQLAlchemy ORM with async support**
- **Alembic database migrations**
- **Docker containerization**
- **Basic logging and error handling**
