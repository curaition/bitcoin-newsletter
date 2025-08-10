# Newsletter Generation & Publishing
## Product Requirements Document (PRD)

### Executive Summary
An intelligent synthesis system that transforms 24 hours of signal detection and analysis into compelling, insightful newsletters. This system selects the most revealing stories, weaves together emerging patterns, and delivers unique perspectives that position readers ahead of mainstream crypto narratives.

---

## 1. Product Overview

### Vision
Create an AI-powered editorial system that synthesizes detected signals into coherent, forward-looking narratives that reveal what crypto trends suggest about broader market evolution and emerging opportunities.

### Core Value Proposition
- **Signal Synthesis**: Weave together 24 hours of detected signals into coherent patterns
- **Editorial Intelligence**: Generate unique perspectives that mainstream crypto media misses
- **Strategic Curation**: Select stories based on signal strength and adjacent possibility potential
- **Forward-Looking Narrative**: Position insights ahead of mainstream conversations
- **Consistent Quality**: Maintain editorial standards and voice across all newsletters
- **Actionable Intelligence**: Provide insights readers can act upon

---

## 2. System Architecture

### Technology Stack
- **Agent Framework**: PydanticAI (newsletter synthesis and editorial logic)
- **LLM**: Gemini 2.5 Flash
- **Database**: Neon PostgreSQL (extends previous schema)
- **Scheduling**: Celery Beat (daily newsletter generation)
- **Content Delivery**: Email distribution system
- **Observability**: LangFuse (editorial quality and cost tracking)

### Synthesis Flow
```
24hr Signal Analysis → Story Selection → Pattern Synthesis → Editorial Generation → Quality Review → Publishing
        ↓                   ↓              ↓                ↓                 ↓             ↓
Daily Analysis Pool → Top 5 Stories → Cross-Story → Newsletter Draft → Quality Gates → Distribution
```

### Editorial Architecture
```
Newsletter Writer Agent ──┐
                          │
                          ▼
Story Selection Engine ───┤
                          │
                          ▼
Pattern Synthesis Engine ─┘
```

---

## 3. Functional Requirements

### 3.1 Story Selection Engine
**Primary Responsibility**: Identify the 5 most revealing stories from 24 hours of analysis

**Selection Criteria**:
- **Signal Strength**: Prioritize articles with high-confidence weak signals
- **Pattern Emergence**: Favor stories that contribute to emerging patterns
- **Adjacent Possibilities**: Select articles with strong cross-domain connections
- **Narrative Gaps**: Include stories that fill important perspective voids
- **Uniqueness Factor**: Emphasize insights not covered by mainstream crypto media
- **Temporal Relevance**: Balance breaking news with longer-term trend indicators

**Technical Requirements**:
- Analyze all articles from previous 24-hour period
- Score articles across multiple dimensions (signal strength, uniqueness, relevance)
- Ensure diverse story selection (avoid clustering around single topics)
- Handle edge cases where insufficient quality content is available
- Provide reasoning for story selection decisions

**Success Criteria**:
- Story selection completion within 30 minutes
- Selected stories achieve >4.0/5.0 average signal quality score
- 80% of selected stories provide unique angles not covered elsewhere
- Reader engagement correlation: selected stories drive 70% of newsletter engagement

### 3.2 Pattern Synthesis Engine
**Primary Responsibility**: Identify connections and patterns across selected stories

**Synthesis Capabilities**:
- **Cross-Story Connections**: Find thematic links between seemingly unrelated articles
- **Emerging Pattern Recognition**: Identify broader trends suggested by multiple signals
- **Timeline Integration**: Understand how current signals fit into longer-term patterns
- **Market Psychology Insights**: Understand the behavioral and sentiment patterns underlying the news
- **Adjacent Domain Integration**: Weave in cross-domain connections discovered in analysis
- **Contrarian Perspective Development**: Identify where conventional wisdom might be wrong

**Technical Requirements**:
- Process analysis results from all selected stories simultaneously
- Generate synthesis themes that connect multiple articles
- Identify meta-patterns that emerge from individual signal combinations
- Produce editorial angles that provide unique market perspectives
- Create narrative frameworks that tie disparate signals together

**Success Criteria**:
- Synthesis completion within 45 minutes
- Generate 2-3 major themes that connect selected stories
- Produce unique editorial angles in 90% of newsletters
- Pattern accuracy validation: 60% of synthesized patterns show relevance within 14 days

### 3.3 Newsletter Writer Agent
**Primary Responsibility**: Transform synthesis into compelling, readable newsletter content

**Editorial Capabilities**:
- **Compelling Narrative Construction**: Create engaging story flow that maintains reader interest
- **Signal Integration**: Seamlessly weave detected signals into natural editorial commentary
- **Forward-Looking Perspective**: Position insights as indicators of future developments
- **Authoritative Voice**: Maintain consistent editorial tone that builds reader trust
- **Actionable Insights**: Provide specific takeaways readers can apply
- **Citation Integration**: Include verified sources and links to original material

**Content Structure Requirements**:
- **Executive Summary**: Key insights and takeaways (2-3 bullet points)
- **Main Analysis**: Deep dive into selected stories with signal insights (800-1200 words)
- **Pattern Spotlight**: Focus on one major emerging pattern (300-400 words)
- **Adjacent Possibilities**: Brief exploration of cross-domain connections (200-300 words)
- **Signal Watch**: Weak signals to monitor for future newsletters (100-150 words)
- **Source Links**: Curated links to 5 most important original articles

**Technical Requirements**:
- Generate newsletter content within 60 minutes
- Maintain consistent voice and quality across all newsletters
- Include proper attribution and source links
- Handle cases where synthesis provides insufficient material
- Implement quality gates before publishing

**Success Criteria**:
- Newsletter generation completion within 90 minutes total
- Editorial quality score >4.0/5.0 (based on reader feedback)
- Reader engagement rate >25% (open rate)
- Content uniqueness: 85% of insights not found in other crypto newsletters

### 3.4 Quality Control & Publishing
**Primary Responsibility**: Ensure newsletter quality and manage distribution

**Quality Control Gates**:
- **Factual Accuracy Review**: Verify all cited facts and figures
- **Editorial Consistency**: Check voice, tone, and style alignment
- **Link Validation**: Ensure all source links are functional and relevant
- **Content Completeness**: Verify all required sections are present and substantive
- **Signal Coherence**: Ensure insights logically flow from detected signals

**Publishing Requirements**:
- **Multi-Format Generation**: HTML email, web version, PDF archive
- **Responsive Design**: Ensure readability across devices
- **Distribution Management**: Handle subscriber lists and delivery
- **Archive Management**: Maintain searchable newsletter archive
- **Performance Tracking**: Monitor delivery rates and engagement metrics

**Success Criteria**:
- Quality review completion within 15 minutes
- 99% successful delivery rate
- <2% bounce rate for email distribution
- Archive accessibility and searchability

---

## 4. Technical Specifications

### 4.1 Database Schema Extensions
```sql
-- Newsletter Tables (extends Signal Detection schema)
newsletters (
    id BIGSERIAL PRIMARY KEY,
    publication_date DATE NOT NULL UNIQUE,
    title TEXT NOT NULL,
    executive_summary TEXT NOT NULL,
    content_html TEXT NOT NULL,
    content_text TEXT NOT NULL,
    
    -- Story Selection
    selected_articles INTEGER[] NOT NULL, -- References to article IDs
    selection_reasoning JSONB, -- Why these stories were chosen
    
    -- Synthesis Results
    synthesis_themes JSONB, -- Major themes identified
    pattern_insights JSONB, -- Cross-story patterns discovered
    adjacent_connections JSONB, -- Cross-domain insights featured
    signal_highlights JSONB, -- Key weak signals emphasized
    
    -- Quality Metrics
    editorial_quality_score DECIMAL(3,2),
    signal_coherence_score DECIMAL(3,2),
    uniqueness_score DECIMAL(3,2),
    
    -- Performance Metrics
    generation_time_ms INTEGER,
    token_usage INTEGER,
    generation_cost_usd DECIMAL(6,4),
    
    -- Publishing Data
    publish_status TEXT DEFAULT 'DRAFT' CHECK (publish_status IN ('DRAFT', 'REVIEW', 'PUBLISHED', 'ARCHIVED')),
    published_at TIMESTAMPTZ,
    email_sent_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Newsletter Performance Tracking
newsletter_metrics (
    id BIGSERIAL PRIMARY KEY,
    newsletter_id BIGINT REFERENCES newsletters(id) NOT NULL,
    
    -- Engagement Metrics
    emails_sent INTEGER DEFAULT 0,
    emails_delivered INTEGER DEFAULT 0,
    emails_opened INTEGER DEFAULT 0,
    links_clicked INTEGER DEFAULT 0,
    
    -- Content Performance
    read_time_avg_seconds INTEGER,
    scroll_depth_avg DECIMAL(3,2),
    social_shares INTEGER DEFAULT 0,
    
    -- Reader Feedback
    feedback_ratings JSONB, -- Array of reader ratings and comments
    avg_rating DECIMAL(3,2),
    
    measured_at TIMESTAMPTZ DEFAULT NOW()
);

-- Editorial Templates and Configuration
editorial_config (
    id BIGSERIAL PRIMARY KEY,
    config_name TEXT NOT NULL UNIQUE,
    
    -- Selection Parameters
    story_selection_weights JSONB, -- Weights for different selection criteria
    min_stories INTEGER DEFAULT 3,
    max_stories INTEGER DEFAULT 7,
    
    -- Editorial Style
    voice_guidelines TEXT,
    tone_parameters JSONB,
    content_structure_template JSONB,
    
    -- Quality Thresholds
    min_signal_strength DECIMAL(3,2) DEFAULT 0.6,
    min_uniqueness_score DECIMAL(3,2) DEFAULT 0.7,
    
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.2 PydanticAI Agent Specifications

#### Story Selection Specification
```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class StoryScore(BaseModel):
    article_id: int = Field(description="Article ID being scored")
    signal_strength: float = Field(ge=0, le=1, description="Strength of detected signals")
    uniqueness_factor: float = Field(ge=0, le=1, description="How unique the insights are")
    pattern_contribution: float = Field(ge=0, le=1, description="Contribution to emerging patterns")
    adjacent_value: float = Field(ge=0, le=1, description="Value of cross-domain connections")
    overall_score: float = Field(ge=0, le=1, description="Composite selection score")
    selection_reasoning: str = Field(description="Why this story should/shouldn't be selected")

class StorySelection(BaseModel):
    selection_date: datetime = Field(description="Date of story selection")
    total_articles_reviewed: int = Field(description="Total articles considered")
    selected_stories: List[StoryScore] = Field(description="Top selected stories with scores")
    rejected_highlights: List[StoryScore] = Field(description="Notable stories not selected and why")
    selection_themes: List[str] = Field(description="Common themes across selected stories")
    coverage_gaps: List[str] = Field(description="Important topics not covered in selection")

story_selection_agent = Agent(
    'gemini-2.5-flash',
    result_type=StorySelection,
    system_prompt='''You are an expert editorial curator for a crypto newsletter focused on signal detection and emerging patterns. Your role is to select the 5 most revealing stories from the past 24 hours that best demonstrate emerging trends and adjacent possibilities.

Selection Criteria Priority:
1. SIGNAL STRENGTH: Stories with high-confidence weak signals and pattern anomalies
2. UNIQUENESS: Insights not covered by mainstream crypto media
3. FORWARD-LOOKING: Stories that suggest future developments rather than just reporting current events
4. CROSS-CONNECTIONS: Articles that reveal interesting adjacent possibilities
5. PATTERN EMERGENCE: Stories that contribute to broader trend identification

Editorial Judgment:
- Prioritize stories that help readers think differently about crypto markets
- Balance breaking news with longer-term trend indicators
- Ensure diverse coverage (avoid over-clustering on single topics)
- Select stories that work well together to tell a coherent narrative
- Consider what will be most valuable to readers seeking market edge

Quality over Quantity:
- Better to select 3 exceptional stories than 5 mediocre ones
- Each selected story must offer genuine insight beyond surface-level reporting
- Provide clear reasoning for why each story made the cut
- Identify important stories that didn't make the selection and explain why''',
    retries=2
)
```

#### Newsletter Synthesis Agent
```python
class SynthesisTheme(BaseModel):
    theme_title: str = Field(description="Title of the synthesis theme")
    theme_description: str = Field(description="Detailed description of the theme")
    supporting_articles: List[int] = Field(description="Article IDs that support this theme")
    signal_connections: List[str] = Field(description="How different signals connect to support this theme")
    future_implications: str = Field(description="What this theme suggests about future developments")

class PatternInsight(BaseModel):
    pattern_name: str = Field(description="Name of the identified pattern")
    pattern_description: str = Field(description="Detailed description of the pattern")
    historical_context: str = Field(description="How this pattern relates to historical trends")
    confidence_level: float = Field(ge=0, le=1, description="Confidence in pattern validity")
    monitoring_indicators: List[str] = Field(description="What to watch to validate this pattern")

class AdjacentOpportunity(BaseModel):
    crypto_element: str = Field(description="The crypto element being connected")
    external_domain: str = Field(description="The external domain of opportunity")
    opportunity_description: str = Field(description="Description of the adjacent opportunity")
    development_timeline: str = Field(description="Expected timeline for opportunity development")
    key_catalysts: List[str] = Field(description="What would accelerate this opportunity")

class NewsletterSynthesis(BaseModel):
    synthesis_themes: List[SynthesisTheme] = Field(description="Major themes connecting selected stories")
    pattern_insights: List[PatternInsight] = Field(description="Emerging patterns identified")
    adjacent_opportunities: List[AdjacentOpportunity] = Field(description="Cross-domain opportunities")
    contrarian_angles: List[str] = Field(description="Where conventional wisdom might be wrong")
    signal_priorities: List[str] = Field(description="Most important signals to monitor going forward")
    editorial_angle: str = Field(description="Overall editorial perspective for this newsletter")

synthesis_agent = Agent(
    'gemini-2.5-flash',
    result_type=NewsletterSynthesis,
    system_prompt='''You are an expert crypto market synthesist who identifies patterns and connections across multiple news stories and signal analyses. Your role is to weave together individual insights into coherent themes that reveal larger market dynamics.

Synthesis Approach:
1. PATTERN RECOGNITION: Look for common threads and emerging patterns across selected stories
2. SIGNAL INTEGRATION: Connect weak signals from different sources to identify stronger trends
3. CONTRARIAN THINKING: Identify where the collective insights challenge conventional wisdom
4. FORWARD PROJECTION: Understand what current signals suggest about future developments
5. ADJACENT EXPLORATION: Find opportunities where crypto intersects with other domains

Editorial Perspective:
- Focus on what the signals collectively suggest that isn't obvious from individual stories
- Identify inflection points and potential paradigm shifts
- Look for gaps between market perception and emerging reality
- Consider multiple timeframes (immediate, medium-term, long-term implications)
- Maintain healthy skepticism while being open to paradigm shifts

Output Quality:
- Provide specific, actionable synthesis rather than generic observations
- Connect dots between stories in meaningful ways
- Identify the "so what" implications of detected patterns
- Balance optimism with realism in opportunity identification
- Give readers frameworks for understanding market evolution''',
    retries=2
)
```

#### Newsletter Writer Agent
```python
class NewsletterContent(BaseModel):
    title: str = Field(description="Compelling newsletter title")
    executive_summary: List[str] = Field(description="3-4 key takeaways for busy readers")
    main_analysis: str = Field(description="Primary analysis section (800-1200 words)")
    pattern_spotlight: str = Field(description="Deep dive on one major pattern (300-400 words)")
    adjacent_watch: str = Field(description="Cross-domain developments to monitor (200-300 words)")
    signal_radar: str = Field(description="Weak signals for future monitoring (100-150 words)")
    action_items: List[str] = Field(description="Specific takeaways readers can act upon")
    source_citations: List[str] = Field(description="Links to original articles and key sources")
    estimated_read_time: int = Field(description="Estimated read time in minutes")

newsletter_writer_agent = Agent(
    'gemini-2.5-flash',
    result_type=NewsletterContent,
    system_prompt='''You are an expert crypto newsletter writer who transforms signal analysis and synthesis into compelling, actionable content. Your voice is authoritative yet accessible, providing unique insights that help readers understand not just what's happening, but what it means and what to watch for next.

Editorial Voice & Style:
- AUTHORITATIVE: Confident analysis backed by detected signals and research
- FORWARD-LOOKING: Focus on implications and what's coming next
- ACTIONABLE: Provide specific takeaways readers can use
- ACCESSIBLE: Complex insights explained clearly without dumbing down
- UNIQUE: Perspectives and angles not found in mainstream crypto media

Content Structure Requirements:
1. EXECUTIVE SUMMARY: 3-4 bullet points capturing key insights for time-pressed readers
2. MAIN ANALYSIS: Primary narrative weaving together selected stories and synthesis
3. PATTERN SPOTLIGHT: Deep dive on the most significant emerging pattern
4. ADJACENT WATCH: Cross-domain developments that could impact crypto
5. SIGNAL RADAR: Weak signals to monitor for future newsletters
6. ACTION ITEMS: Specific, actionable takeaways for readers

Writing Principles:
- Lead with the most surprising or important insight
- Use concrete examples and specific data points
- Connect current signals to longer-term implications
- Maintain intellectual honesty about uncertainty and limitations
- Give readers frameworks for independent thinking
- Balance conviction with appropriate hedging

Quality Standards:
- Every paragraph should provide value to readers
- Avoid rehashing widely available information
- Focus on the "why" and "what's next" rather than just "what happened"
- Include specific citations and links for credibility
- End each section with clear takeaways''',
    retries=2
)
```

### 4.3 Celery Task Configuration
```python
class NewsletterTasks:
    @celery_app.task(bind=True)
    def generate_daily_newsletter(self):
        """Main task to generate daily newsletter"""
        try:
            # 1. Story Selection Phase
            selection_result = story_selection_agent.run(
                get_past_24h_analysis_summary()
            )
            
            # 2. Synthesis Phase
            synthesis_result = synthesis_agent.run(
                format_selected_stories_for_synthesis(selection_result.data)
            )
            
            # 3. Newsletter Writing Phase
            newsletter_result = newsletter_writer_agent.run(
                format_synthesis_for_writing(synthesis_result.data)
            )
            
            # 4. Quality Control
            quality_score = run_quality_control_checks(newsletter_result.data)
            
            # 5. Store and Prepare for Publishing
            newsletter_id = store_newsletter(
                newsletter_result.data, 
                selection_result.data,
                synthesis_result.data,
                quality_score
            )
            
            # 6. Trigger Publishing Pipeline
            publish_newsletter.delay(newsletter_id)
            
            return {"status": "success", "newsletter_id": newsletter_id}
            
        except Exception as exc:
            self.retry(exc=exc, countdown=300)  # 5 minute retry delay
    
    @celery_app.task
    def publish_newsletter(newsletter_id: int):
        """Handle newsletter publishing and distribution"""
        try:
            newsletter = get_newsletter_by_id(newsletter_id)
            
            # Generate multiple formats
            html_content = generate_html_newsletter(newsletter)
            text_content = generate_text_newsletter(newsletter)
            pdf_content = generate_pdf_newsletter(newsletter)
            
            # Distribute via email
            send_email_newsletter(html_content, text_content)
            
            # Update web archive
            update_web_archive(newsletter, html_content)
            
            # Track performance
            initialize_performance_tracking(newsletter_id)
            
            return {"status": "published", "newsletter_id": newsletter_id}
            
        except Exception as exc:
            logger.error(f"Newsletter publishing failed: {exc}")
            raise
```

### 4.4 Quality Control System
```python
class QualityController:
    def run_quality_checks(self, newsletter_content: NewsletterContent) -> Dict[str, float]:
        """Run comprehensive quality checks on generated newsletter"""
        scores = {}
        
        # Content Quality Checks
        scores['content_completeness'] = self.check_content_completeness(newsletter_content)
        scores['editorial_consistency'] = self.check_editorial_consistency(newsletter_content)
        scores['factual_accuracy'] = self.check_factual_accuracy(newsletter_content)
        scores['link_validity'] = self.validate_all_links(newsletter_content)
        
        # Signal Integration Checks
        scores['signal_coherence'] = self.check_signal_integration(newsletter_content)
        scores['insight_uniqueness'] = self.check_insight_uniqueness(newsletter_content)
        scores['forward_looking_ratio'] = self.check_forward_looking_content(newsletter_content)
        
        # Readability Checks
        scores['readability'] = self.check_readability_score(newsletter_content)
        scores['structure_quality'] = self.check_content_structure(newsletter_content)
        
        # Overall Quality Score
        scores['overall_quality'] = sum(scores.values()) / len(scores)
        
        return scores
    
    def check_content_completeness(self, content: NewsletterContent) -> float:
        """Verify all required sections are present and substantive"""
        required_sections = [
            content.executive_summary,
            content.main_analysis,
            content.pattern_spotlight,
            content.adjacent_watch,
            content.signal_radar,
            content.action_items
        ]
        
        completeness_scores = []
        for section in required_sections:
            if isinstance(section, list):
                score = 1.0 if len(section) >= 3 else len(section) / 3
            else:
                score = 1.0 if len(section.split()) >= 50 else len(section.split()) / 50
            completeness_scores.append(min(score, 1.0))
        
        return sum(completeness_scores) / len(completeness_scores)
    
    def check_signal_integration(self, content: NewsletterContent) -> float:
        """Check how well detected signals are integrated into the content"""
        # Implementation would analyze how naturally signals flow into the narrative
        # and whether insights build logically from detected patterns
        pass
```

---

## 5. Quality Standards

### 5.1 Editorial Quality
- **Content Uniqueness**: 85% of insights not found in other crypto newsletters
- **Editorial Consistency**: Maintain consistent voice and quality across all newsletters
- **Forward-Looking Ratio**: 70% of content focused on implications and future developments
- **Signal Integration**: Seamless integration of detected signals into narrative flow

### 5.2 Production Quality
- **Generation Speed**: Complete newsletter within 90 minutes
- **Publishing Reliability**: 99% successful publication rate
- **Content Accuracy**: >98% factual accuracy for all cited information
- **Link Validity**: 100% functional links at time of publication

### 5.3 Reader Engagement
- **Open Rate**: >25% average email open rate
- **Read Completion**: >60% average read-through rate
- **Reader Satisfaction**: >4.0/5.0 average reader rating
- **Share Rate**: >5% of readers share content on social media

---

## 6. Success Metrics

### 6.1 Content Performance
- **Insight Accuracy**: 70% of forward-looking insights prove relevant within 30 days
- **Pattern Validation**: 60% of highlighted patterns show development within 14 days
- **Reader Value**: 80% of readers report gaining actionable insights
- **Competitive Differentiation**: Clear unique value vs. other crypto newsletters

### 6.2 Operational Excellence
- **Production Consistency**: Zero missed publication dates
- **Cost Efficiency**: <$5 per newsletter generation (including all LLM costs)
- **Quality Consistency**: <15% variance in quality scores across newsletters
- **Subscriber Growth**: 10% monthly subscriber growth rate

---

## 7. Implementation Roadmap

### Week 1: Core Generation Pipeline
- Story selection engine implementation
- Basic synthesis logic development
- Newsletter writer agent setup
- Database schema implementation

### Week 2: Editorial Intelligence
- Advanced synthesis algorithms
- Quality control system implementation
- Editorial voice calibration and testing
- Content structure optimization

### Week 3: Publishing Infrastructure
- Multi-format content generation (HTML, text, PDF)
- Email distribution system setup
- Web archive implementation
- Performance tracking systems

### Week 4: Optimization & Launch
- Quality threshold calibration
- A/B testing of editorial approaches
- Performance optimization and cost management
- Production deployment and monitoring

---

## 8. Risk Assessment

### Editorial Risks
- **Content Quality Inconsistency**: Mitigation through quality gates and feedback loops
- **Signal Misinterpretation**: Mitigation through validation processes and human review
- **Editorial Bias**: Mitigation through diverse signal sources and contrarian thinking

### Technical Risks
- **Generation Failures**: Mitigation through robust error handling and fallback content
- **Publishing Delays**: Mitigation through early generation and buffer time
- **Cost Overruns**: Mitigation through token usage monitoring and optimization

### Business Risks
- **Reader Churn**: Mitigation through quality consistency and engagement monitoring
- **Competitive Pressure**: Mitigation through unique signal-based differentiation
- **Content Relevance**: Mitigation through continuous feedback and adaptation

---

## 9. Dependencies

### Upstream Dependencies
- **Signal Detection & Analysis**: Quality signal analysis and synthesis data
- **Core Data Pipeline**: Reliable article ingestion and storage
- **External Research**: Tavily validation and context enhancement

### Infrastructure Dependencies
- **Database Performance**: Fast queries for 24-hour analysis retrieval
- **Task Scheduling**: Reliable daily newsletter generation triggers
- **Email Infrastructure**: Reliable email delivery for subscriber distribution

---

*Document Version: 1.0*
*Last Updated: August 10, 2025*
*Status: Ready for Implementation*
*Prerequisites: Core Data Pipeline + Signal Detection & Analysis PRD completion*