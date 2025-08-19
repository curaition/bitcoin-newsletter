# Signal Detection Phase 2.5: Real-World Validation & Testing
## Product Requirements Document (PRD)

### Executive Summary
Before implementing production automation, validate the AI signal detection system against real-world articles from the production database. This phase ensures the agents work correctly with actual content, costs are predictable, and signal quality meets expectations.

---

## 1. Product Overview

### Vision
Build confidence in the signal detection system through comprehensive real-world testing before any production automation. Validate that Phase 2 agents work correctly with actual articles and produce meaningful, cost-effective analysis.

### Core Value Proposition
- **Real-World Validation**: Test against actual articles, not synthetic data
- **Cost Verification**: Confirm actual costs match estimates (~$0.25/article)
- **Quality Assurance**: Validate signal relevance and actionable insights
- **Risk Mitigation**: Identify and fix issues before production deployment
- **Confidence Building**: Prove the system works end-to-end

---

## 2. Current State Analysis

### Database Reality (as of August 15, 2025)
- **Total Articles**: 149 (55 analysis-ready)
- **Last 24 Hours**: 70 articles (28 analysis-ready)
- **Quality Publishers**: NewsBTC (16/16), CoinDesk (6/13), Crypto Potato (6/8)
- **Daily Volume**: ~28 analysis-ready articles (not 35 as originally estimated)
- **Estimated Daily Cost**: ~$7.00 (28 × $0.25)

### Phase 2 Completion Status
- ✅ **PydanticAI 0.7.2 Agents**: ContentAnalysisAgent and SignalValidationAgent
- ✅ **Testing Framework**: Integration tests with TestModel
- ✅ **Database Integration**: ArticleAnalysis model ready
- ✅ **API Keys**: Gemini and Tavily configured in all environments
- ❌ **Real-World Testing**: Not yet validated with actual articles

---

## 3. Functional Requirements

### 3.1 Local Testing Setup
**Primary Responsibility**: Establish local development environment connected to production data

**Core Setup Requirements**:

#### Database Connection
```python
# Local development configuration
DATABASE_URL = "postgresql://[neon-connection-string]"
ENVIRONMENT = "development"
TESTING = "false"  # Use real APIs, not TestModel

# API Keys (from .env.development)
GEMINI_API_KEY = "your_gemini_key"
TAVILY_API_KEY = "your_tavily_key"
```

#### Article Selection Criteria
```python
# Select diverse test articles
test_articles = [
    # NewsBTC - High quality, full content (16/16 analysis-ready)
    {"publisher": "NewsBTC", "min_length": 2000, "count": 2},

    # CoinDesk - Medium quality, partial content (6/13 analysis-ready)
    {"publisher": "CoinDesk", "min_length": 2000, "count": 2},

    # Crypto Potato - Good quality, mostly full content (6/8 analysis-ready)
    {"publisher": "Crypto Potato", "min_length": 2000, "count": 1}
]
```

**Success Criteria**:
- Local environment connects to Neon database successfully
- Can retrieve and display analysis-ready articles
- API keys work for both Gemini and Tavily
- 5 diverse test articles selected for validation

### 3.2 End-to-End Validation
**Primary Responsibility**: Validate complete signal analysis pipeline with real articles

**Core Validation Tests**:

#### Content Analysis Validation
```python
async def test_content_analysis_real_article(article_id: int):
    """Test ContentAnalysisAgent with real article"""

    # 1. Retrieve real article from database
    article = await get_article_by_id(article_id)

    # 2. Run content analysis
    analysis_result = await content_analysis_agent.run(
        format_article_for_analysis(article)
    )

    # 3. Validate results
    analysis = analysis_result.output

    # Quality checks
    assert len(analysis.weak_signals) >= 1, "Should detect at least 1 weak signal"
    assert analysis.impact_score > 0, "Should have measurable impact score"
    assert len(analysis.summary) > 100, "Summary should be substantial"
    assert analysis.analysis_confidence > 0.3, "Should have reasonable confidence"

    # Cost validation
    cost = analysis_result.usage.total_cost or 0.0
    assert cost < 0.15, f"Content analysis cost ${cost} exceeds $0.15 target"

    return {
        "article_id": article_id,
        "signals_detected": len(analysis.weak_signals),
        "cost": cost,
        "processing_time": analysis_result.usage.total_time,
        "confidence": analysis.analysis_confidence
    }
```

#### Signal Validation Testing
```python
async def test_signal_validation_real_research(signals: List[WeakSignal]):
    """Test SignalValidationAgent with real external research"""

    # 1. Format signals for validation
    validation_prompt = format_signals_for_validation(signals)

    # 2. Run signal validation with real Tavily API
    validation_result = await signal_validation_agent.run(validation_prompt)

    # 3. Validate external research quality
    validation = validation_result.output

    # Research quality checks
    assert len(validation.validation_results) > 0, "Should validate at least 1 signal"

    for result in validation.validation_results:
        assert len(result.research_sources) > 0, "Should find research sources"
        assert result.validation_status in ["VALIDATED", "CONTRADICTED", "INCONCLUSIVE"]

    # Cost validation
    research_cost = validation_result.usage.total_cost or 0.0
    assert research_cost < 0.10, f"Validation cost ${research_cost} exceeds $0.10 target"

    return {
        "signals_validated": len(validation.validation_results),
        "research_sources_found": sum(len(r.research_sources) for r in validation.validation_results),
        "validation_cost": research_cost,
        "additional_signals": len(validation.additional_signals)
    }
```

#### Database Storage Validation
```python
async def test_database_storage_real_analysis(article_id: int, analysis: ContentAnalysis, validation: SignalValidation):
    """Test storing real analysis results in database"""

    # 1. Create ArticleAnalysis record
    analysis_record = ArticleAnalysis(
        article_id=article_id,
        analysis_version="1.0",

        # Core analysis
        sentiment=analysis.sentiment,
        impact_score=analysis.impact_score,
        summary=analysis.summary,
        context=analysis.context,

        # Signals (JSONB)
        weak_signals=[signal.dict() for signal in analysis.weak_signals],
        pattern_anomalies=[anomaly.dict() for anomaly in analysis.pattern_anomalies],
        adjacent_connections=[conn.dict() for conn in analysis.adjacent_connections],

        # Validation results
        verified_facts=[result.dict() for result in validation.validation_results] if validation else [],
        validation_status="COMPLETED" if validation else "PENDING",

        # Quality metrics
        analysis_confidence=analysis.analysis_confidence,
        signal_strength=analysis.signal_strength,
        uniqueness_score=analysis.uniqueness_score,

        # Processing metadata
        processing_time_ms=1000,  # Convert from seconds
        token_usage=500,  # Estimate
        cost_usd=0.20  # Total cost
    )

    # 2. Store in database
    await db_session.add(analysis_record)
    await db_session.commit()

    # 3. Verify storage
    stored_record = await db_session.get(ArticleAnalysis, analysis_record.id)
    assert stored_record is not None, "Analysis should be stored successfully"
    assert len(stored_record.weak_signals) == len(analysis.weak_signals), "Signals should be preserved"

    return stored_record.id
```

**Success Criteria**:
- All 5 test articles process successfully without errors
- Signal detection produces 3-5 meaningful signals per article
- External validation finds relevant research sources
- Database storage preserves all analysis data correctly
- Total cost per article stays under $0.25

### 3.3 Confidence Building
**Primary Responsibility**: Build confidence through comprehensive testing scenarios

**Core Confidence Tests**:

#### Publisher Quality Validation
```python
publisher_test_results = {
    "NewsBTC": {
        "articles_tested": 2,
        "avg_signals_per_article": 4.5,
        "avg_cost": 0.22,
        "signal_quality_score": 4.2  # Out of 5
    },
    "CoinDesk": {
        "articles_tested": 2,
        "avg_signals_per_article": 3.8,
        "avg_cost": 0.24,
        "signal_quality_score": 4.0
    },
    "Crypto Potato": {
        "articles_tested": 1,
        "avg_signals_per_article": 3.2,
        "avg_cost": 0.20,
        "signal_quality_score": 3.8
    }
}
```

#### Error Scenario Testing
```python
error_scenarios = [
    {
        "scenario": "API Rate Limit",
        "test": "Trigger Gemini rate limit",
        "expected": "Graceful retry with exponential backoff"
    },
    {
        "scenario": "Tavily API Failure",
        "test": "Simulate Tavily service unavailable",
        "expected": "Skip validation, continue with content analysis"
    },
    {
        "scenario": "Malformed Article Content",
        "test": "Article with unusual formatting",
        "expected": "Extract meaningful content, generate analysis"
    },
    {
        "scenario": "Very Long Article",
        "test": "Article >10,000 characters",
        "expected": "Process efficiently, stay within cost limits"
    }
]
```

**Success Criteria**:
- Signal quality scores >3.5/5.0 across all publishers
- Error scenarios handled gracefully without system crashes
- Cost variance <20% across different article types
- Processing time <8 minutes per article including validation

---

## 4. Implementation Plan

### Week 1: Local Setup & Initial Testing
- Set up local development environment with Neon connection
- Select 5 diverse test articles from database
- Run initial end-to-end tests with real APIs
- Document any issues or unexpected behaviors

### Week 2: Comprehensive Validation
- Test all publisher types and article variations
- Validate signal quality and research effectiveness
- Test error scenarios and recovery mechanisms
- Measure and document actual costs and performance

### Week 3: Results Analysis & Documentation
- Analyze test results and signal quality
- Document lessons learned and system improvements
- Create recommendations for simplified Phase 3
- Prepare for minimal production integration

---

## 5. Success Metrics

### Technical Validation
- **100% Success Rate**: All 5 test articles process without critical errors
- **Signal Quality**: Average 3-5 meaningful signals per article
- **Cost Accuracy**: Actual costs within 20% of estimates ($0.20-$0.30/article)
- **Processing Speed**: Complete analysis within 8 minutes per article

### Quality Validation
- **Signal Relevance**: >80% of signals provide actionable market insights
- **Research Quality**: >70% of validation sources from authoritative publications
- **Content Coverage**: System handles all major publisher content formats
- **Error Recovery**: >90% of temporary errors recover successfully

### Confidence Building
- **Publisher Performance**: Consistent quality across NewsBTC, CoinDesk, Crypto Potato
- **Cost Predictability**: Daily cost estimates accurate within ±20%
- **System Reliability**: No data loss or corruption during testing
- **Ready for Production**: Clear path to simple Celery integration

---

## 6. Deliverables

### Testing Framework
- Local testing scripts for real article analysis
- Automated validation of signal quality and costs
- Error scenario testing suite
- Performance measurement tools

### Documentation
- Real-world testing results and analysis
- Signal quality assessment across publishers
- Cost and performance benchmarks
- Lessons learned and system improvements

### Production Readiness
- Validated system configuration
- Simplified Phase 3 implementation plan
- Risk assessment based on real-world testing
- Go/no-go recommendation for production integration

---

## 7. Next Steps After Phase 2.5

### Simplified Phase 3 (Post-Validation)
Based on Phase 2.5 results, implement minimal production integration:

- **Single Celery Task**: `analyze_article(article_id)`
- **Simple Scheduling**: Analyze articles after ingestion
- **Basic Error Handling**: Retry failures, log errors
- **Cost Tracking**: Use existing `article_analyses` table
- **No Complex Infrastructure**: Skip queues, advanced monitoring

### Success Criteria for Phase 3 Go-Decision
- Phase 2.5 testing shows >95% success rate
- Signal quality meets expectations (>3.5/5.0)
- Costs are predictable and within budget
- No critical issues discovered during testing

---

*Document Version: 1.0*
*Last Updated: August 15, 2025*
*Status: Ready for Implementation*
*Prerequisites: Phase 2 Complete*
*Next Phase: Simplified Phase 3 (Post-Validation)*
