# Signal Detection & Analysis
## Product Requirements Document (PRD)

### Executive Summary
An intelligent multi-agent system that analyzes cryptocurrency news articles to detect weak signals, identify pattern anomalies, and surface adjacent possibilities that mainstream crypto media might miss. This system transforms raw news into actionable insights through sophisticated AI analysis.

---

## 1. Product Overview

### Vision
Create AI agents that can read between the lines of crypto news, identifying emerging patterns and adjacent possibilities that position users ahead of mainstream narratives while maintaining factual accuracy.

### Core Value Proposition
- **Weak Signal Detection**: Identify early indicators of shifts others miss
- **Pattern Recognition**: Spot anomalies and breaks from familiar crypto behaviors
- **Adjacent Possibilities**: Surface cross-domain connections and emerging trends
- **Narrative Gap Analysis**: Find perspective blind spots in crypto discourse
- **Edge Case Identification**: Flag outlier activities indicating emerging trends
- **Validated Insights**: Combine AI analysis with external research validation

---

## 2. System Architecture

### Technology Stack
- **Agent Framework**: PydanticAI (agent orchestration and LLM interactions)
- **LLM**: Gemini 2.5 Flash
- **External Research**: Tavily MCP (signal validation and context enhancement)
- **Database**: Neon PostgreSQL (extends Core Data Pipeline schema)
- **Task Integration**: Celery workers (triggered by Core Data Pipeline)
- **Observability**: LangFuse (agent performance and cost tracking)

### Agent Ecosystem
```
Content Analysis Agent ────┐
                          │
                          ▼
                   Signal Validation Agent ────► Analysis Storage
                          ▲
                          │
External Research ────────┘
(Tavily MCP)
```

### Data Flow
```
New Articles → Content Analysis → Signal Detection → Validation Research → Structured Analysis → Database Storage
     ↓              ↓                ↓                 ↓                    ↓               ↓
Triggering → Pattern Recognition → Cross-Domain → Research Enhancement → Quality Scoring → Ready for Newsletter
```

---

## 3. Functional Requirements

### 3.1 Content Analysis Agent
**Primary Responsibility**: Deep analysis of individual articles to detect signals and patterns

**Core Analysis Capabilities**:
- **Weak Signal Detection**: Identify subtle indicators of emerging trends not explicitly stated
- **Pattern Anomaly Recognition**: Detect when familiar crypto behaviors don't match expectations
- **Narrative Gap Identification**: Find missing perspectives or angles in the discourse
- **Cross-Domain Mapping**: Identify intersection points between crypto and other domains
- **Edge Case Flagging**: Highlight outlier behaviors that might indicate broader shifts
- **Contextual Understanding**: Understand what stories suggest beyond their surface meaning

**Technical Requirements**:
- Process articles within 2 hours of ingestion
- Generate structured analysis output with confidence scores
- Maintain consistent quality across different article types and sources
- Handle various content formats (news, analysis, opinion, technical content)
- Scale to process 50-200 articles per day

**Success Criteria**:
- Analysis completion time <5 minutes per article
- Signal detection quality score >4.0/5.0 (validated through subsequent trend tracking)
- Unique insight generation rate >80% (insights not covered in mainstream crypto media)
- Pattern recognition accuracy >70% (validated over 30-day periods)

### 3.2 Signal Validation Agent
**Primary Responsibility**: Enhance and validate signals through external research

**Core Validation Capabilities**:
- **Signal Verification**: Research detected signals for additional context and validation
- **Cross-Domain Research**: Investigate connections between crypto trends and other industries
- **Context Enhancement**: Gather additional information that strengthens or refutes detected patterns
- **Evidence Gathering**: Find supporting or contradicting evidence for identified signals
- **Trend Validation**: Research whether detected patterns align with broader market movements

**Technical Requirements**:
- Integrate with Tavily MCP for external research
- Process validation requests from Content Analysis Agent
- Generate research reports with source attribution
- Handle rate limiting and API failures gracefully
- Optimize search queries for relevance and cost efficiency

**Success Criteria**:
- Validation completion time <3 minutes per signal
- Research relevance score >4.0/5.0
- Signal verification accuracy >95% for validated claims
- Cost efficiency <$0.50 per validation cycle

### 3.3 Analysis Orchestration
**Primary Responsibility**: Coordinate agent interactions and manage analysis workflow

**Core Orchestration Capabilities**:
- **Workflow Management**: Coordinate between Content Analysis and Signal Validation agents
- **Quality Control**: Ensure analysis meets quality thresholds before storage
- **Error Handling**: Manage agent failures and retry logic
- **Performance Monitoring**: Track agent performance and resource usage
- **Cost Management**: Monitor and optimize LLM token usage

**Technical Requirements**:
- Integrate with Celery task queue from Core Data Pipeline
- Handle concurrent analysis of multiple articles
- Implement circuit breakers for external API failures
- Provide real-time status updates for monitoring systems
- Maintain analysis state for recovery from failures

**Success Criteria**:
- 100% article coverage within 4 hours of ingestion
- Workflow success rate >98%
- Average cost per analysis <$0.25
- Error recovery success rate >95%

---

## 4. Technical Specifications

### 4.1 Database Schema Extensions
```sql
-- Analysis Tables (extends Core Data Pipeline)
article_analyses (
    id BIGSERIAL PRIMARY KEY,
    article_id BIGINT REFERENCES articles(id) NOT NULL,
    analysis_version VARCHAR(10) DEFAULT '1.0',
    
    -- Core Analysis Fields
    sentiment TEXT CHECK (sentiment IN ('POSITIVE', 'NEGATIVE', 'NEUTRAL', 'MIXED')),
    impact_score DECIMAL(3,2) CHECK (impact_score BETWEEN 0 AND 1),
    summary TEXT NOT NULL,
    context TEXT,
    
    -- Signal Detection Fields
    weak_signals JSONB, -- Array of detected weak signals with confidence scores
    pattern_anomalies JSONB, -- Identified pattern breaks and anomalies
    adjacent_connections JSONB, -- Cross-domain connections and intersections
    narrative_gaps JSONB, -- Missing perspectives and angles
    edge_indicators JSONB, -- Outlier behaviors and edge cases
    
    -- Validation Fields
    verified_facts JSONB, -- Facts verified through external research
    research_sources JSONB, -- Sources used for validation and enhancement
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

-- Signal Tracking Tables
signal_patterns (
    id BIGSERIAL PRIMARY KEY,
    pattern_type TEXT NOT NULL, -- 'weak_signal', 'pattern_anomaly', 'cross_domain', etc.
    pattern_description TEXT NOT NULL,
    first_detected TIMESTAMPTZ NOT NULL,
    last_observed TIMESTAMPTZ NOT NULL,
    confidence_score DECIMAL(3,2) CHECK (confidence_score BETWEEN 0 AND 1),
    validation_status TEXT DEFAULT 'UNVALIDATED' CHECK (validation_status IN ('UNVALIDATED', 'VALIDATED', 'DISPROVEN')),
    related_articles INTEGER[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

cross_domain_connections (
    id BIGSERIAL PRIMARY KEY,
    crypto_entity TEXT NOT NULL,
    external_domain TEXT NOT NULL,
    connection_type TEXT NOT NULL,
    connection_description TEXT,
    strength_score DECIMAL(3,2) CHECK (strength_score BETWEEN 0 AND 1),
    supporting_articles INTEGER[] DEFAULT '{}',
    first_identified TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agent Performance Tracking
agent_interactions (
    id BIGSERIAL PRIMARY KEY,
    agent_type TEXT NOT NULL CHECK (agent_type IN ('content_analysis', 'signal_validation')),
    article_id BIGINT REFERENCES articles(id),
    operation_type TEXT NOT NULL,
    input_data JSONB,
    output_data JSONB,
    processing_duration_ms INTEGER,
    token_usage INTEGER,
    cost_usd DECIMAL(6,4),
    success BOOLEAN NOT NULL,
    error_details TEXT,
    quality_score DECIMAL(3,2) CHECK (quality_score BETWEEN 0 AND 1),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.2 PydanticAI Agent Specifications

#### Content Analysis Agent
```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from pydantic_ai import Agent

class WeakSignal(BaseModel):
    signal_type: str = Field(description="Type of weak signal detected")
    description: str = Field(description="Description of the signal")
    confidence: float = Field(ge=0, le=1, description="Confidence in signal validity")
    implications: str = Field(description="Potential implications of this signal")

class PatternAnomaly(BaseModel):
    expected_pattern: str = Field(description="What pattern was expected")
    observed_pattern: str = Field(description="What was actually observed")
    deviation_significance: float = Field(ge=0, le=1, description="How significant the deviation is")
    potential_causes: List[str] = Field(description="Possible explanations for the anomaly")

class AdjacentConnection(BaseModel):
    crypto_element: str = Field(description="The crypto element being connected")
    external_domain: str = Field(description="The external domain or field")
    connection_type: str = Field(description="Nature of the connection")
    relevance: float = Field(ge=0, le=1, description="Relevance of this connection")
    implications: str = Field(description="What this connection might suggest")

class NarrativeGap(BaseModel):
    missing_perspective: str = Field(description="What perspective is missing")
    gap_significance: float = Field(ge=0, le=1, description="How significant this gap is")
    potential_insights: str = Field(description="What insights might emerge from filling this gap")

class ContentAnalysis(BaseModel):
    sentiment: str = Field(description="Overall sentiment of the article")
    impact_score: float = Field(ge=0, le=1, description="Potential market impact")
    summary: str = Field(description="Key points summary")
    context: str = Field(description="Important contextual information")
    weak_signals: List[WeakSignal] = Field(description="Detected weak signals")
    pattern_anomalies: List[PatternAnomaly] = Field(description="Identified pattern anomalies")
    adjacent_connections: List[AdjacentConnection] = Field(description="Cross-domain connections")
    narrative_gaps: List[NarrativeGap] = Field(description="Missing perspectives")
    edge_indicators: List[str] = Field(description="Outlier behaviors noted")
    analysis_confidence: float = Field(ge=0, le=1, description="Confidence in overall analysis")
    signal_strength: float = Field(ge=0, le=1, description="Strength of detected signals")

content_analysis_agent = Agent(
    'gemini-2.5-flash',
    result_type=ContentAnalysis,
    system_prompt='''You are an expert crypto market analyst specializing in signal detection and pattern recognition. Your role is to analyze cryptocurrency news articles not just for what they explicitly say, but for what they suggest about emerging trends, pattern changes, and adjacent possibilities.

Key Analysis Focus Areas:
1. WEAK SIGNALS: Look for subtle indicators of emerging trends not explicitly stated
2. PATTERN ANOMALIES: Identify when familiar crypto behaviors don't match historical patterns
3. ADJACENT CONNECTIONS: Find intersection points between crypto and other domains
4. NARRATIVE GAPS: Identify missing perspectives or overlooked angles
5. EDGE CASES: Flag outlier behaviors that might indicate broader shifts

Analysis Approach:
- Read between the lines - what does this story suggest beyond its surface meaning?
- Consider what's NOT being said as much as what is
- Look for breaks in familiar patterns or unexpected behaviors
- Identify connections to non-crypto domains that might be relevant
- Consider multiple timeframes and levels of impact

Quality Standards:
- Provide specific, actionable insights rather than generic observations
- Use confidence scores to indicate certainty levels
- Focus on unique angles not covered by mainstream crypto media
- Ground insights in the actual content while extrapolating thoughtfully''',
    retries=2
)
```

#### Signal Validation Agent
```python
class ResearchSource(BaseModel):
    source_url: str = Field(description="URL of the research source")
    source_type: str = Field(description="Type of source (news, academic, data, etc.)")
    relevance: float = Field(ge=0, le=1, description="Relevance to the signal being validated")
    summary: str = Field(description="Key information from this source")

class ValidationResult(BaseModel):
    signal_id: str = Field(description="ID of the signal being validated")
    validation_status: str = Field(description="VALIDATED, CONTRADICTED, or INCONCLUSIVE")
    supporting_evidence: List[str] = Field(description="Evidence supporting the signal")
    contradicting_evidence: List[str] = Field(description="Evidence contradicting the signal")
    additional_context: str = Field(description="Additional relevant context discovered")
    research_sources: List[ResearchSource] = Field(description="Sources used in validation")
    confidence_adjustment: float = Field(ge=-1, le=1, description="Adjustment to original confidence (-1 to +1)")

class SignalValidation(BaseModel):
    validation_results: List[ValidationResult] = Field(description="Results for each signal validated")
    additional_insights: List[str] = Field(description="New insights discovered during research")
    research_cost: float = Field(description="Cost of research in USD")

signal_validation_agent = Agent(
    'gemini-2.5-flash',
    result_type=SignalValidation,
    system_prompt='''You are a research specialist focused on validating and enhancing crypto market signals through external research. Your role is to investigate detected signals, gather supporting or contradicting evidence, and provide additional context.

Research Approach:
1. For each signal, search for external evidence that supports or contradicts it
2. Look for additional context that enhances understanding of the signal
3. Investigate cross-domain connections by researching related industries/trends
4. Find authoritative sources that add credibility to the analysis
5. Identify any additional insights that emerge from the research process

Research Quality Standards:
- Use authoritative, recent sources when possible
- Clearly distinguish between supporting and contradicting evidence
- Provide specific examples and data points rather than general statements
- Consider multiple perspectives and sources of information
- Be honest about inconclusive results - not every signal can be validated

Focus on efficiency:
- Target 3-5 high-quality searches per validation cycle
- Prioritize recent, authoritative sources
- Focus on sources that add genuine value to the analysis''',
    retries=2
)
```

### 4.3 Tavily Integration Configuration
```python
class TavilyConfig:
    # Search Parameters
    max_searches_per_validation: int = 5
    search_timeout: int = 30  # seconds
    max_results_per_search: int = 5
    
    # Search Optimization
    search_domains_priority: List[str] = [
        "coindesk.com", "cointelegraph.com", "bloomberg.com", 
        "reuters.com", "wsj.com", "ft.com"
    ]
    
    # Cost Management
    max_cost_per_validation: float = 0.50  # USD
    daily_budget_limit: float = 50.00  # USD
    
    # Cache Configuration
    cache_duration_hours: int = 48
    cache_similar_queries: bool = True
```

### 4.4 Celery Task Configuration
```python
class AnalysisTasks:
    @celery_app.task(bind=True, max_retries=3)
    def analyze_article(self, article_id: int):
        """Main task to analyze a single article"""
        try:
            # 1. Load article from database
            article = get_article_by_id(article_id)
            
            # 2. Run content analysis
            analysis_result = content_analysis_agent.run(
                f"Analyze this crypto article: {article.title}\n\n{article.body}"
            )
            
            # 3. Run signal validation
            validation_result = signal_validation_agent.run(
                f"Validate these signals: {analysis_result.data}"
            )
            
            # 4. Store results
            store_analysis_results(article_id, analysis_result, validation_result)
            
            return {"status": "success", "article_id": article_id}
            
        except Exception as exc:
            # Exponential backoff retry
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    
    @celery_app.task
    def batch_analyze_articles(article_ids: List[int]):
        """Batch analysis task for multiple articles"""
        results = []
        for article_id in article_ids:
            result = analyze_article.delay(article_id)
            results.append(result.id)
        return results
```

---

## 5. Quality Standards

### 5.1 Analysis Quality
- **Signal Detection Quality**: >4.0/5.0 average score (validated through trend tracking)
- **Unique Insight Ratio**: >80% content not covered in mainstream crypto media
- **Pattern Recognition Accuracy**: >70% signal validation over 30-day periods
- **Analysis Confidence Calibration**: Confidence scores align with actual accuracy

### 5.2 Performance Standards
- **Processing Speed**: Analysis completion within 5 minutes per article
- **System Reliability**: 98% successful analysis completion rate
- **Cost Efficiency**: <$0.25 average cost per article analysis
- **Scalability**: Handle 200+ articles per day without performance degradation

### 5.3 Research Quality
- **Source Authority**: >80% of research sources from authoritative publications
- **Research Relevance**: >4.0/5.0 average relevance score for validation research
- **Fact Verification**: >95% accuracy for verified claims
- **Research Efficiency**: Complete validation within 3 minutes per signal

---

## 6. Success Metrics

### 6.1 Intelligence Metrics
- **Signal Accuracy**: 70% of detected weak signals show relevance within 30 days
- **Pattern Recognition**: 75% of identified anomalies lead to meaningful insights
- **Cross-Domain Value**: 60% of adjacent connections provide actionable intelligence
- **Narrative Gap Value**: 50% of identified gaps become relevant discussion topics

### 6.2 Operational Metrics
- **Processing Coverage**: 100% of ingested articles analyzed within 4 hours
- **System Uptime**: 99% availability during processing windows
- **Cost Management**: Stay within $100/month budget for analysis operations
- **Quality Consistency**: <10% variance in analysis quality scores across different content types

---

## 7. Implementation Roadmap

### Week 1: Agent Foundation
- PydanticAI agent setup and basic prompt development
- Database schema extensions implementation
- Celery task integration with Core Data Pipeline
- Basic analysis workflow (without external research)

### Week 2: Intelligence Enhancement
- Advanced prompt engineering for signal detection
- Tavily integration for signal validation
- Quality scoring and confidence calibration
- Error handling and retry logic implementation

### Week 3: Optimization & Validation
- Performance optimization and cost management
- Analysis quality validation through manual review
- A/B testing of different prompt approaches
- LangFuse integration for observability

### Week 4: Production Readiness
- Load testing with production article volumes
- Final prompt refinement based on results
- Documentation and deployment procedures
- Integration testing with newsletter generation pipeline

---

## 8. Risk Assessment

### Technical Risks
- **LLM Consistency**: Mitigation through prompt engineering and quality scoring
- **API Rate Limits**: Mitigation through intelligent queuing and fallback strategies  
- **Cost Overruns**: Mitigation through budget monitoring and usage optimization

### Quality Risks
- **Signal Accuracy**: Mitigation through validation processes and feedback loops
- **Analysis Bias**: Mitigation through diverse training examples and regular review
- **Context Misunderstanding**: Mitigation through external research validation

---

## 9. Dependencies

### External Dependencies
- **Core Data Pipeline**: Clean article data and ingestion triggers
- **Gemini 2.5 Flash**: LLM availability and performance
- **Tavily MCP**: External research capabilities
- **LangFuse**: Observability and monitoring

### Internal Dependencies
- **Database Schema**: Extensions to Core Data Pipeline schema
- **Task Queue**: Integration with existing Celery infrastructure
- **Monitoring Systems**: Dashboard integration points for analysis metrics

---

*Document Version: 1.0*
*Last Updated: August 10, 2025*
*Status: Ready for Implementation*
*Prerequisite: Core Data Pipeline PRD completion*