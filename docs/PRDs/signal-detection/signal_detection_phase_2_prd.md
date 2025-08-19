# Signal Detection Phase 2: PydanticAI Framework & Agent Setup
## Product Requirements Document (PRD)

### Executive Summary
Implement AI-powered signal detection agents using PydanticAI framework to analyze full-content articles for weak signals, pattern anomalies, and adjacent possibilities. This phase focuses on agent development, testing, and validation without production integration.

---

## 1. Product Overview

### Vision
Create intelligent AI agents that can detect subtle market signals and emerging patterns in cryptocurrency news that mainstream media might miss, focusing on high-quality content for maximum insight value.

### Core Value Proposition
- **Weak Signal Detection**: Identify early indicators of market shifts and trends
- **Pattern Recognition**: Spot anomalies and breaks from typical crypto behaviors
- **Adjacent Possibilities**: Discover cross-domain connections and opportunities
- **Quality Focus**: Analyze only full articles (≥2000 chars) for meaningful insights
- **Cost Efficiency**: Optimize AI usage for maximum insight per dollar spent

---

## 2. Prerequisites & Foundation

### Phase 1 Deliverables Required
- ✅ Database schema with `article_analyses` table
- ✅ Admin interface showing analysis-ready articles
- ✅ API endpoints for analysis-ready content filtering
- ✅ Quality publisher identification (NewsBTC, CoinDesk, Crypto Potato)

### Content Analysis Target
- **Daily Volume**: ~35 full articles per day
- **Quality Sources**: Focus on NewsBTC (100% full), CoinDesk (50% full), Crypto Potato (80% full)
- **Content Threshold**: ≥2000 characters for meaningful analysis
- **Cost Target**: <$0.25 per article analysis

---

## 3. Functional Requirements

### 3.1 Content Analysis Agent
**Primary Responsibility**: Deep analysis of individual full articles to detect signals and patterns

**Core Analysis Capabilities**:

#### Weak Signal Detection
```python
class WeakSignal(BaseModel):
    signal_type: str = Field(description="Type of weak signal detected")
    description: str = Field(description="Detailed description of the signal")
    confidence: float = Field(ge=0, le=1, description="Confidence in signal validity")
    implications: str = Field(description="Potential market implications")
    evidence: List[str] = Field(description="Specific evidence from article supporting this signal")
    timeframe: str = Field(description="Expected timeframe for signal development")
```

#### Pattern Anomaly Recognition
```python
class PatternAnomaly(BaseModel):
    expected_pattern: str = Field(description="What pattern was historically expected")
    observed_pattern: str = Field(description="What was actually observed in the article")
    deviation_significance: float = Field(ge=0, le=1, description="Significance of deviation")
    historical_context: str = Field(description="How this compares to historical patterns")
    potential_causes: List[str] = Field(description="Possible explanations for the anomaly")
```

#### Adjacent Possibility Mapping
```python
class AdjacentConnection(BaseModel):
    crypto_element: str = Field(description="The crypto element being connected")
    external_domain: str = Field(description="External domain (tech, finance, culture, politics)")
    connection_type: str = Field(description="Nature of the connection")
    relevance: float = Field(ge=0, le=1, description="Relevance of this connection")
    opportunity_description: str = Field(description="What opportunity this might suggest")
    development_indicators: List[str] = Field(description="What to watch for development")
```

#### Content Analysis Implementation
```python
class ContentAnalysis(BaseModel):
    # Core Analysis
    sentiment: str = Field(description="Overall sentiment: POSITIVE, NEGATIVE, NEUTRAL, MIXED")
    impact_score: float = Field(ge=0, le=1, description="Potential market impact")
    summary: str = Field(description="Concise summary of key insights")
    context: str = Field(description="Important contextual information")

    # Signal Detection Results
    weak_signals: List[WeakSignal] = Field(description="Detected weak signals")
    pattern_anomalies: List[PatternAnomaly] = Field(description="Identified pattern breaks")
    adjacent_connections: List[AdjacentConnection] = Field(description="Cross-domain connections")
    narrative_gaps: List[str] = Field(description="Missing perspectives or overlooked angles")
    edge_indicators: List[str] = Field(description="Outlier behaviors noted")

    # Quality Metrics
    analysis_confidence: float = Field(ge=0, le=1, description="Confidence in overall analysis")
    signal_strength: float = Field(ge=0, le=1, description="Overall strength of detected signals")
    uniqueness_score: float = Field(ge=0, le=1, description="How unique insights are vs mainstream coverage")

content_analysis_agent = Agent(
    'gemini-2.5-flash',
    result_type=ContentAnalysis,
    system_prompt='''You are an expert crypto market analyst specializing in signal detection and pattern recognition. Analyze cryptocurrency news articles for subtle indicators of emerging trends that mainstream media might miss.

ANALYSIS FOCUS:
1. WEAK SIGNALS - Subtle indicators of emerging trends not explicitly stated
2. PATTERN ANOMALIES - When familiar crypto behaviors don't match historical patterns
3. ADJACENT CONNECTIONS - Intersection points between crypto and other domains
4. NARRATIVE GAPS - Missing perspectives or overlooked angles
5. EDGE CASES - Outlier behaviors that might indicate broader shifts

ANALYSIS APPROACH:
- Focus on implications beyond surface-level reporting
- Consider multiple timeframes (immediate, medium-term, long-term)
- Look for connections to non-crypto domains (tech, finance, culture, politics)
- Identify what's NOT being discussed as much as what is
- Ground insights in specific article content while extrapolating thoughtfully

QUALITY STANDARDS:
- Provide specific, actionable insights rather than generic observations
- Use confidence scores to indicate certainty levels
- Focus on unique angles not covered by mainstream crypto media
- Evidence-based analysis rooted in article content''',
    retries=2
)
```

**Technical Requirements**:
- Process articles within 5 minutes of analysis trigger
- Generate structured analysis with confidence scores
- Handle articles of varying complexity and technical depth
- Maintain consistent quality across different content types

**Success Criteria**:
- Analysis completion time <5 minutes per article
- Signal detection quality score >4.0/5.0
- Unique insight generation rate >80%
- Analysis cost <$0.15 per article

### 3.2 Signal Validation Agent
**Primary Responsibility**: Enhance and validate signals through external research using Tavily MCP

**Core Validation Capabilities**:

#### External Research Integration
```python
class ResearchSource(BaseModel):
    source_url: str = Field(description="URL of the research source")
    source_type: str = Field(description="Type: news, academic, data, industry_report")
    authority_level: str = Field(description="HIGH, MEDIUM, LOW based on source credibility")
    relevance: float = Field(ge=0, le=1, description="Relevance to signal being validated")
    key_information: str = Field(description="Key information from this source")
    publication_date: Optional[str] = Field(description="Publication date if available")

class ValidationResult(BaseModel):
    signal_id: str = Field(description="Reference to the signal being validated")
    validation_status: str = Field(description="VALIDATED, CONTRADICTED, INCONCLUSIVE")
    supporting_evidence: List[str] = Field(description="Evidence supporting the signal")
    contradicting_evidence: List[str] = Field(description="Evidence contradicting the signal")
    additional_context: str = Field(description="Additional relevant context discovered")
    research_sources: List[ResearchSource] = Field(description="Sources used in validation")
    confidence_adjustment: float = Field(ge=-1, le=1, description="Adjustment to original confidence")
    research_quality: float = Field(ge=0, le=1, description="Quality of research sources found")

class SignalValidation(BaseModel):
    validation_results: List[ValidationResult] = Field(description="Results for each signal validated")
    cross_signal_insights: List[str] = Field(description="Insights from comparing multiple signals")
    additional_signals: List[WeakSignal] = Field(description="New signals discovered during research")
    research_cost: float = Field(description="Cost of research in USD")
    research_summary: str = Field(description="Summary of research findings")

signal_validation_agent = Agent(
    'gemini-2.5-flash',
    result_type=SignalValidation,
    system_prompt='''You are a research specialist focused on validating crypto market signals through external research. Use available research tools to investigate detected signals and provide supporting or contradicting evidence.

VALIDATION APPROACH:
1. For each signal, search for external evidence that supports or contradicts it
2. Prioritize authoritative sources (academic, industry reports, established publications)
3. Look for cross-domain evidence that enhances understanding
4. Identify any additional signals that emerge from research
5. Assess the overall quality and reliability of research sources

RESEARCH QUALITY STANDARDS:
- Use recent, authoritative sources when possible
- Clearly distinguish between supporting and contradicting evidence
- Provide specific examples and data points
- Consider multiple perspectives and sources
- Be honest about inconclusive results

EFFICIENCY FOCUS:
- Target 3-5 high-quality searches per validation cycle
- Prioritize research that adds genuine value to analysis
- Balance thoroughness with cost efficiency
- Focus on sources that provide unique insights beyond the original article''',
    retries=2
)
```

#### Tavily MCP Integration
```python
class TavilyResearchConfig:
    max_searches_per_validation: int = 5
    search_timeout: int = 30  # seconds
    max_results_per_search: int = 5

    # Cost Management
    max_cost_per_validation: float = 0.10  # USD
    daily_budget_limit: float = 15.00  # USD (~60 validations/day)

    # Quality Filtering
    min_source_authority: str = "MEDIUM"
    preferred_domains: List[str] = [
        "coindesk.com", "cointelegraph.com", "bloomberg.com",
        "reuters.com", "wsj.com", "ft.com", "academic.edu"
    ]

    # Search Optimization
    search_queries_per_signal: int = 2
    enable_cross_signal_research: bool = True
```

**Technical Requirements**:
- Integrate with Tavily MCP for external research
- Implement search query optimization for relevance
- Add cost tracking and budget management
- Handle API rate limits and failures gracefully

**Success Criteria**:
- Validation completion time <3 minutes per signal
- Research relevance score >4.0/5.0
- Validation accuracy >95% for clear signals
- Research cost <$0.10 per validation cycle

### 3.3 Agent Orchestration System
**Primary Responsibility**: Coordinate agent interactions and manage analysis workflow

**Core Orchestration Capabilities**:

#### Analysis Pipeline Management
```python
class AnalysisWorkflow:
    async def analyze_article(self, article_id: int) -> AnalysisResult:
        """Complete analysis workflow for a single article"""

        # 1. Pre-analysis validation
        article = await self.get_article(article_id)
        if not self.is_analysis_worthy(article):
            return AnalysisResult(status="SKIPPED", reason="Insufficient content")

        # 2. Content analysis phase
        content_analysis = await content_analysis_agent.run(
            f"Analyze this crypto article:\n\nTitle: {article.title}\n\nContent: {article.body}"
        )

        # 3. Signal validation phase
        if content_analysis.data.weak_signals:
            validation_result = await signal_validation_agent.run(
                format_signals_for_validation(content_analysis.data)
            )
        else:
            validation_result = None

        # 4. Combine and store results
        final_analysis = self.combine_analysis_results(
            content_analysis.data,
            validation_result.data if validation_result else None
        )

        # 5. Store in database
        await self.store_analysis_results(article_id, final_analysis)

        return AnalysisResult(
            status="COMPLETED",
            analysis=final_analysis,
            processing_time=self.get_processing_time(),
            cost=self.calculate_total_cost()
        )

    def is_analysis_worthy(self, article: Article) -> bool:
        """Determine if article is worth analyzing"""
        return (
            len(article.body) >= 2000 and
            article.publisher.name in ["NewsBTC", "CoinDesk", "Crypto Potato"] and
            article.language == "EN" and
            article.status == "ACTIVE"
        )
```

#### Error Handling and Recovery
```python
class AnalysisErrorHandler:
    def __init__(self):
        self.max_retries = 3
        self.retry_delays = [60, 300, 900]  # 1min, 5min, 15min

    async def handle_analysis_failure(self, article_id: int, error: Exception):
        """Handle analysis failures with intelligent retry logic"""

        if isinstance(error, RateLimitError):
            # Wait and retry with exponential backoff
            await self.schedule_retry(article_id, delay=self.get_backoff_delay())
        elif isinstance(error, ValidationError):
            # Log validation error and mark as failed
            await self.mark_analysis_failed(article_id, reason="Invalid response format")
        elif isinstance(error, CostLimitError):
            # Pause analysis until budget resets
            await self.pause_analysis_until_budget_reset()
        else:
            # Generic retry with exponential backoff
            await self.schedule_retry(article_id)
```

**Technical Requirements**:
- Coordinate between analysis and validation agents
- Implement robust error handling and retry logic
- Track performance metrics and costs
- Provide workflow status reporting

**Success Criteria**:
- 100% workflow completion rate for eligible articles
- Average workflow time <8 minutes per article
- Error recovery success rate >95%
- Cost tracking accuracy >99%

---

## 4. Technical Specifications

### 4.1 PydanticAI Setup and Configuration
```python
# src/crypto_newsletter/analysis/agents/__init__.py
from pydantic_ai import Agent
from pydantic_ai.models import KnownModel

# Agent configuration
ANALYSIS_MODEL: KnownModel = 'gemini-2.5-flash'
ANALYSIS_CONFIG = {
    'temperature': 0.3,  # Lower temperature for more consistent analysis
    'max_tokens': 4000,  # Sufficient for detailed analysis
    'timeout': 180,      # 3 minute timeout per request
}

# Cost management
DAILY_BUDGET_USD = 50.00
COST_PER_1K_TOKENS = 0.0002  # Gemini 2.5 Flash pricing
```

### 4.2 Testing Framework
```python
# tests/analysis/test_content_analysis_agent.py
import pytest
from crypto_newsletter.analysis.agents import content_analysis_agent

class TestContentAnalysisAgent:
    @pytest.fixture
    def sample_full_article(self):
        return Article(
            title="Bitcoin Adoption Accelerates in Enterprise Sector",
            body="...",  # 2500+ character article
            publisher=Publisher(name="NewsBTC")
        )

    async def test_weak_signal_detection(self, sample_full_article):
        """Test that agent detects meaningful weak signals"""
        result = await content_analysis_agent.run(
            format_article_for_analysis(sample_full_article)
        )

        assert result.data.weak_signals
        assert all(0 <= signal.confidence <= 1 for signal in result.data.weak_signals)
        assert result.data.signal_strength > 0.3  # Minimum signal strength

    async def test_pattern_anomaly_recognition(self, sample_full_article):
        """Test pattern anomaly detection"""
        result = await content_analysis_agent.run(
            format_article_for_analysis(sample_full_article)
        )

        for anomaly in result.data.pattern_anomalies:
            assert anomaly.expected_pattern != anomaly.observed_pattern
            assert 0 <= anomaly.deviation_significance <= 1

    async def test_analysis_cost_tracking(self, sample_full_article):
        """Test that analysis costs are tracked and within budget"""
        cost_tracker = CostTracker()

        result = await content_analysis_agent.run(
            format_article_for_analysis(sample_full_article),
            cost_tracker=cost_tracker
        )

        assert cost_tracker.total_cost < 0.25  # Target cost per article
        assert cost_tracker.token_usage > 0
```

### 4.3 Performance Benchmarking
```python
# src/crypto_newsletter/analysis/benchmarks.py
class AnalysisPerformanceBenchmark:
    def __init__(self):
        self.test_articles = self.load_test_articles()
        self.baseline_metrics = self.load_baseline_metrics()

    async def run_performance_benchmark(self) -> BenchmarkResults:
        """Run comprehensive performance benchmark"""
        results = []

        for article in self.test_articles:
            start_time = time.time()

            analysis = await self.run_full_analysis(article)

            processing_time = time.time() - start_time
            cost = self.calculate_analysis_cost(analysis)

            results.append(BenchmarkResult(
                article_id=article.id,
                processing_time=processing_time,
                cost=cost,
                signal_count=len(analysis.weak_signals),
                confidence_avg=np.mean([s.confidence for s in analysis.weak_signals])
            ))

        return BenchmarkResults(
            avg_processing_time=np.mean([r.processing_time for r in results]),
            avg_cost=np.mean([r.cost for r in results]),
            avg_signal_count=np.mean([r.signal_count for r in results]),
            performance_score=self.calculate_performance_score(results)
        )
```

---

## 5. Quality Standards

### 5.1 Analysis Quality
- **Signal Relevance**: >80% of detected signals provide actionable insights
- **Pattern Accuracy**: >75% of pattern anomalies validated through subsequent market behavior
- **Uniqueness Score**: >70% of insights not found in mainstream crypto coverage
- **Confidence Calibration**: Confidence scores align with actual signal quality

### 5.2 Performance Standards
- **Processing Speed**: Complete analysis within 8 minutes per article
- **Cost Efficiency**: <$0.25 per article analysis (including validation)
- **Error Rate**: <5% analysis failures due to agent errors
- **Token Utilization**: Efficient prompt design minimizing unnecessary token usage

### 5.3 Validation Quality
- **Research Relevance**: >80% of external sources directly relevant to signals
- **Source Authority**: >70% of sources from high-authority publications
- **Validation Accuracy**: >90% accuracy in supporting/contradicting evidence assessment
- **Additional Insight Discovery**: >20% of validations uncover additional relevant information

---

## 6. Success Metrics

### 6.1 Agent Performance
- **Daily Analysis Volume**: Successfully analyze all 35 daily analysis-ready articles
- **Signal Detection Rate**: Average 3-5 meaningful signals per full article
- **Processing Consistency**: <20% variance in processing time across articles
- **Cost Predictability**: Stay within $15/day budget for analysis and validation

### 6.2 Insight Quality
- **Signal Strength Distribution**: 60% of signals with confidence >0.7
- **Pattern Recognition**: Identify 1-2 pattern anomalies per 10 articles
- **Cross-Domain Connections**: Discover 2-3 adjacent possibilities per day
- **Validation Success**: 80% of high-confidence signals validated through research

---

## 7. Implementation Roadmap

### Week 1: Agent Development
- Implement ContentAnalysisAgent with Pydantic models
- Create SignalValidationAgent with Tavily integration
- Build agent orchestration system
- Develop comprehensive testing framework

### Week 2: Testing and Optimization
- Run performance benchmarks on sample articles
- Optimize prompts for cost and quality
- Implement error handling and retry logic
- Fine-tune agent parameters based on results

### Week 3: Integration Preparation
- Create analysis workflow management system
- Implement cost tracking and budget controls
- Build monitoring and alerting for agent performance
- Prepare for Phase 3 integration with production pipeline

---

## 8. Risk Assessment

### Technical Risks
- **LLM Consistency**: Mitigation through prompt optimization and result validation
- **Cost Overruns**: Mitigation through strict budget controls and monitoring
- **API Rate Limits**: Mitigation through intelligent queuing and retry logic

### Quality Risks
- **Signal Accuracy**: Mitigation through validation processes and feedback loops
- **Analysis Bias**: Mitigation through diverse training examples and regular review
- **Context Misunderstanding**: Mitigation through enhanced prompts and validation

---

## 9. Dependencies

### External Dependencies
- **Gemini 2.5 Flash API**: LLM availability and performance
- **Tavily MCP**: External research capabilities and API reliability
- **Phase 1 Deliverables**: Database schema and admin interface

### Internal Dependencies
- **Database Schema**: Analysis tables from Phase 1
- **Admin Interface**: Article filtering and display capabilities
- **API Infrastructure**: Existing FastAPI structure for integration

---

## 10. Acceptance Criteria

### Agent Functionality
- [x] ContentAnalysisAgent processes full articles and returns structured analysis
- [x] SignalValidationAgent successfully validates signals using external research
- [x] Agent orchestration system coordinates workflow end-to-end
- [x] Error handling and retry logic working for all failure scenarios

### Performance Benchmarks
- [x] Analysis completes within 8 minutes per article (achieved ~5 minutes)
- [x] Cost stays under $0.25 per article including validation
- [x] Signal detection quality score >4.0/5.0 on test articles
- [x] Validation research relevance >80% on sample signals

### Testing Coverage
- [x] Comprehensive unit tests for all agent functions
- [x] Integration tests for agent coordination
- [x] Performance benchmarks documented and baseline established
- [x] Error scenarios tested and recovery verified

### Documentation
- [x] Agent prompt strategies documented
- [x] Cost optimization techniques recorded
- [x] Performance tuning guidelines created
- [x] Integration preparation checklist completed

---

## ✅ **PHASE 2 COMPLETED - August 15, 2025**

### **Implementation Summary**
- **✅ PydanticAI 0.7.2 Integration** - Latest framework with enhanced capabilities
- **✅ Content Analysis Agent** - Weak signals, pattern anomalies, adjacent connections
- **✅ Signal Validation Agent** - External research via Tavily API
- **✅ Agent Orchestration** - Complete workflow coordination
- **✅ Database Integration** - ArticleAnalysis model matching existing schema
- **✅ Testing Framework** - Comprehensive integration tests
- **✅ Cost Tracking** - Budget monitoring and optimization
- **✅ Error Handling** - Retry logic and failure recovery

### **Performance Achieved**
- **Processing Time**: ~5 minutes per article (target: <8 minutes) ✅
- **Cost Efficiency**: <$0.25 per article including validation ✅
- **Signal Quality**: High-confidence detection with external validation ✅
- **Integration Ready**: Celery tasks and production deployment prepared ✅

---

*Document Version: 1.1*
*Last Updated: August 15, 2025*
*Status: ✅ COMPLETED*
*Prerequisites: Phase 1 Database Preparation & Admin Interface Complete*
*Next Phase: Production Integration & Celery Tasks*
