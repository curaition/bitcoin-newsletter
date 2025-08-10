# Monitoring & Prompt Engineering
## Product Requirements Document (PRD)

### Executive Summary
A comprehensive monitoring and prompt engineering system that provides real-time visibility into the crypto newsletter pipeline while enabling dynamic optimization of AI agent behavior through interactive prompt engineering interfaces. This system ensures operational excellence and enables continuous improvement of signal detection and analysis quality.

---

## 1. Product Overview

### Vision
Create an intelligent monitoring and optimization platform that not only tracks system performance but enables users to dynamically adjust AI agent behavior, experiment with prompt configurations, and continuously improve the quality of signal detection and editorial output.

### Core Value Proposition
- **Real-Time Visibility**: Complete observability into all system components and agent performance
- **Dynamic Prompt Engineering**: Interactive interface for optimizing agent prompts and behaviors
- **Quality Optimization**: Tools for measuring and improving signal detection accuracy
- **Operational Control**: Manual overrides and intervention capabilities when needed
- **Continuous Improvement**: Data-driven insights for system enhancement
- **Cost Management**: Comprehensive tracking and optimization of operational expenses

---

## 2. System Architecture

### Technology Stack
- **Dashboard Framework**: Streamlit (interactive monitoring interface)
- **Prompt Engineering UI**: Custom Streamlit components with real-time testing
- **Observability**: LangFuse (agent interaction tracking)
- **Database**: Neon PostgreSQL (extends existing schema)
- **Caching**: Redis (dashboard performance and prompt testing)
- **Deployment**: Railway (integrated with main system)

### System Integration
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Main Pipeline  │───▶│   Monitoring    │◄───│ Prompt Engineer │
│   Components    │    │   Dashboard     │    │   Interface     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LangFuse      │    │   Performance   │    │   A/B Testing   │
│ Observability   │    │   Analytics     │    │   Framework     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 3. Functional Requirements

### 3.1 Real-Time System Monitoring
**Primary Responsibility**: Provide comprehensive visibility into all system components

**Core Monitoring Capabilities**:
- **Pipeline Status Tracking**: Real-time status of RSS ingestion, analysis, and newsletter generation
- **Agent Performance Monitoring**: Individual agent execution times, success rates, and quality scores
- **Signal Detection Quality**: Track signal accuracy, uniqueness scores, and pattern validation
- **Cost Tracking**: Real-time monitoring of LLM costs, API usage, and operational expenses
- **System Health**: Database performance, task queue status, and infrastructure metrics
- **Content Quality Metrics**: Newsletter engagement, reader feedback, and editorial quality scores

**Dashboard Views**:
- **Executive Dashboard**: High-level system health and key performance indicators
- **Pipeline Monitoring**: Detailed view of ingestion, analysis, and publishing workflows
- **Agent Analytics**: Individual agent performance, costs, and quality metrics
- **Signal Intelligence**: Visualization of detected patterns, signal strengths, and validation results
- **Content Performance**: Newsletter metrics, reader engagement, and feedback analysis
- **Cost Management**: Detailed cost breakdowns and budget tracking

**Technical Requirements**:
- Real-time updates with <30 second latency
- Historical data visualization with configurable time ranges
- Alert system for system failures and quality degradation
- Export capabilities for reports and analysis
- Mobile-responsive design for remote monitoring

**Success Criteria**:
- Dashboard response time <2 seconds for all views
- 100% system component visibility
- Alert accuracy >95% (minimal false positives)
- User satisfaction with monitoring interface >4.0/5.0

### 3.2 Interactive Prompt Engineering Interface
**Primary Responsibility**: Enable dynamic optimization of AI agent prompts and behaviors

**Core Engineering Capabilities**:
- **Dynamic Prompt Configuration**: Interactive sliders and controls for adjusting analysis parameters
- **Real-Time Prompt Testing**: Test prompt changes against sample articles immediately
- **A/B Testing Framework**: Compare different prompt configurations with controlled experiments
- **Prompt Template Management**: Save, version, and deploy prompt configurations
- **Parameter Optimization**: Guided optimization of prompt parameters based on performance data
- **Collaborative Editing**: Multi-user prompt development with change tracking

**Parameter Control Interface**:
- **Signal Detection Sensitivity** (0-100%): Adjust threshold for weak signal identification
- **Cross-Domain Focus Weights**: Distribute attention across Tech/Finance/Culture/Politics domains
- **Time Horizon Bias** (0-100%): Weight between short-term vs long-term signal preferences
- **Narrative Gap Emphasis** (0-100%): Focus level on identifying missing perspectives
- **Pattern Anomaly Threshold** (0-100%): Sensitivity for flagging unusual patterns
- **Adjacent Possibility Depth** (1-5): How extensively to explore cross-domain connections
- **Contrarian Thinking Level** (0-100%): Emphasis on challenging conventional wisdom
- **Editorial Voice Tone** (Analytical/Conversational/Authoritative): Newsletter writing style

**Technical Requirements**:
- Real-time prompt generation from parameter settings
- Instant testing against sample articles and recent content
- Version control and rollback capabilities for prompt configurations
- Integration with production agents for seamless deployment
- Performance impact tracking for prompt changes

**Success Criteria**:
- Prompt generation time <5 seconds
- Test execution time <30 seconds per sample
- Successful production deployment rate >98%
- User adoption rate >80% among power users

### 3.3 Quality Assessment & Optimization
**Primary Responsibility**: Measure and improve system output quality through data-driven insights

**Assessment Capabilities**:
- **Signal Accuracy Tracking**: Validate detected signals against subsequent market developments
- **Pattern Recognition Evaluation**: Measure accuracy of identified patterns over time
- **Content Uniqueness Analysis**: Compare generated insights against existing crypto media
- **Reader Engagement Correlation**: Connect content quality metrics with reader behavior
- **Editorial Consistency Monitoring**: Track voice and quality consistency across newsletters
- **Competitive Analysis**: Benchmark content quality against other crypto newsletters

**Optimization Tools**:
- **Quality Trend Analysis**: Identify patterns in quality degradation or improvement
- **Parameter Impact Analysis**: Understand how prompt changes affect output quality
- **Content Gap Identification**: Find areas where signal detection could be improved
- **Reader Feedback Integration**: Incorporate reader ratings and comments into quality assessment
- **Automated Quality Alerts**: Notify when quality metrics fall below thresholds
- **Improvement Recommendations**: AI-driven suggestions for prompt and parameter optimization

**Technical Requirements**:
- Automated quality scoring with manual validation capabilities
- Historical quality tracking with trend analysis
- Integration with reader feedback systems
- Correlation analysis between parameters and quality outcomes
- Recommendation engine for optimization suggestions

**Success Criteria**:
- Quality assessment completion within 24 hours of content publication
- Accuracy of quality predictions >80%
- Quality improvement recommendations adoption rate >60%
- Measurable quality improvement over time

### 3.4 Operational Control & Intervention
**Primary Responsibility**: Provide manual controls and emergency intervention capabilities

**Control Capabilities**:
- **Pipeline Control**: Pause, resume, or restart any system component
- **Manual Content Review**: Interface for reviewing and editing generated content
- **Emergency Overrides**: Bypass automated systems for critical situations
- **Content Injection**: Manually add or modify newsletter content when needed
- **Agent Behavior Modification**: Real-time adjustments to agent parameters
- **Quality Gate Management**: Adjust quality thresholds and approval processes

**Intervention Tools**:
- **Alert Management**: Configure alerts for various system conditions
- **Manual Newsletter Generation**: Override automated scheduling when needed
- **Content Approval Workflow**: Human review and approval for sensitive content
- **System Health Recovery**: Tools for diagnosing and resolving system issues
- **Data Correction**: Interface for correcting misanalyzed content or errors
- **Performance Tuning**: Real-time adjustments to system performance parameters

**Technical Requirements**:
- Immediate system response to control commands
- Audit trail for all manual interventions
- Role-based access control for different intervention levels
- Safe fallback modes for critical system failures
- Integration with all system components for comprehensive control

**Success Criteria**:
- Control command response time <5 seconds
- Successful intervention rate >95%
- Zero unplanned system downtime through proactive intervention
- Clear audit trail for all manual actions

---

## 4. Technical Specifications

### 4.1 Database Schema Extensions
```sql
-- Monitoring Tables (extends existing schema)
system_metrics (
    id BIGSERIAL PRIMARY KEY,
    component_name TEXT NOT NULL,
    metric_type TEXT NOT NULL,
    metric_value DECIMAL(10,4),
    metric_unit TEXT,
    tags JSONB, -- Additional metadata for filtering and grouping
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_system_metrics_component_time ON system_metrics(component_name, recorded_at);
CREATE INDEX idx_system_metrics_type_time ON system_metrics(metric_type, recorded_at);

-- Prompt Engineering Tables
prompt_templates (
    id BIGSERIAL PRIMARY KEY,
    template_name TEXT NOT NULL UNIQUE,
    agent_type TEXT NOT NULL CHECK (agent_type IN ('content_analysis', 'signal_validation', 'newsletter_writer')),
    
    -- Template Content
    system_prompt TEXT NOT NULL,
    user_prompt_template TEXT,
    
    -- Configuration Parameters
    parameter_config JSONB NOT NULL, -- Slider values and settings
    model_config JSONB NOT NULL, -- Temperature, max_tokens, etc.
    
    -- Metadata
    created_by TEXT,
    description TEXT,
    version TEXT DEFAULT '1.0',
    parent_template_id BIGINT REFERENCES prompt_templates(id),
    
    -- Status
    status TEXT DEFAULT 'DRAFT' CHECK (status IN ('DRAFT', 'TESTING', 'ACTIVE', 'ARCHIVED')),
    deployed_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Prompt Testing Results
prompt_test_results (
    id BIGSERIAL PRIMARY KEY,
    template_id BIGINT REFERENCES prompt_templates(id) NOT NULL,
    test_article_id BIGINT REFERENCES articles(id),
    
    -- Test Configuration
    test_parameters JSONB NOT NULL,
    test_input TEXT NOT NULL,
    
    -- Results
    generated_output JSONB NOT NULL,
    execution_time_ms INTEGER,
    token_usage INTEGER,
    cost_usd DECIMAL(6,4),
    
    -- Quality Assessment
    quality_score DECIMAL(3,2),
    human_rating INTEGER CHECK (human_rating BETWEEN 1 AND 5),
    notes TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- A/B Testing Framework
ab_tests (
    id BIGSERIAL PRIMARY KEY,
    test_name TEXT NOT NULL UNIQUE,
    description TEXT,
    
    -- Test Configuration
    control_template_id BIGINT REFERENCES prompt_templates(id) NOT NULL,
    variant_template_id BIGINT REFERENCES prompt_templates(id) NOT NULL,
    
    -- Test Parameters
    traffic_split DECIMAL(3,2) DEFAULT 0.5 CHECK (traffic_split BETWEEN 0 AND 1),
    sample_size_target INTEGER,
    
    -- Test Status
    status TEXT DEFAULT 'DRAFT' CHECK (status IN ('DRAFT', 'RUNNING', 'COMPLETED', 'CANCELLED')),
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    
    -- Results
    control_performance JSONB,
    variant_performance JSONB,
    statistical_significance DECIMAL(3,2),
    winner TEXT CHECK (winner IN ('CONTROL', 'VARIANT', 'INCONCLUSIVE')),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Quality Assessments
quality_assessments (
    id BIGSERIAL PRIMARY KEY,
    content_type TEXT NOT NULL CHECK (content_type IN ('analysis', 'newsletter', 'signal')),
    content_id BIGINT NOT NULL,
    
    -- Assessment Scores
    accuracy_score DECIMAL(3,2) CHECK (accuracy_score BETWEEN 0 AND 1),
    uniqueness_score DECIMAL(3,2) CHECK (uniqueness_score BETWEEN 0 AND 1),
    coherence_score DECIMAL(3,2) CHECK (coherence_score BETWEEN 0 AND 1),
    actionability_score DECIMAL(3,2) CHECK (actionability_score BETWEEN 0 AND 1),
    overall_score DECIMAL(3,2) CHECK (overall_score BETWEEN 0 AND 1),
    
    -- Assessment Details
    assessment_method TEXT NOT NULL, -- 'automated', 'human', 'hybrid'
    assessor_id TEXT, -- User ID for human assessments
    assessment_notes TEXT,
    
    -- Validation Data
    validated_predictions JSONB, -- Track prediction accuracy over time
    market_validation_score DECIMAL(3,2), -- How well predictions matched reality
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User Interactions and Feedback
user_interactions (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    interaction_type TEXT NOT NULL,
    
    -- Interaction Data
    target_type TEXT NOT NULL, -- 'prompt', 'dashboard', 'content'
    target_id TEXT NOT NULL,
    interaction_data JSONB,
    
    -- Context
    session_id TEXT,
    ip_address INET,
    user_agent TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_user_interactions_user_time ON user_interactions(user_id, created_at);
CREATE INDEX idx_user_interactions_type_time ON user_interactions(interaction_type, created_at);
```

### 4.2 Streamlit Dashboard Components

#### Main Dashboard Layout
```python
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

class MonitoringDashboard:
    def __init__(self):
        self.setup_page_config()
        self.initialize_session_state()
    
    def setup_page_config(self):
        st.set_page_config(
            page_title="Crypto Newsletter Analytics",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def render_dashboard(self):
        # Sidebar Navigation
        page = st.sidebar.selectbox(
            "Navigation",
            ["Executive Overview", "Pipeline Monitor", "Agent Analytics", 
             "Signal Intelligence", "Content Performance", "Cost Management",
             "Prompt Engineering", "Quality Assessment", "System Controls"]
        )
        
        # Main Content Area
        if page == "Executive Overview":
            self.render_executive_overview()
        elif page == "Pipeline Monitor":
            self.render_pipeline_monitor()
        elif page == "Agent Analytics":
            self.render_agent_analytics()
        elif page == "Signal Intelligence":
            self.render_signal_intelligence()
        elif page == "Content Performance":
            self.render_content_performance()
        elif page == "Cost Management":
            self.render_cost_management()
        elif page == "Prompt Engineering":
            self.render_prompt_engineering()
        elif page == "Quality Assessment":
            self.render_quality_assessment()
        elif page == "System Controls":
            self.render_system_controls()
    
    def render_executive_overview(self):
        st.title("📈 Executive Overview")
        
        # Key Metrics Row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            self.render_metric_card(
                "System Health", 
                self.get_system_health_score(), 
                "98.5%", 
                "success"
            )
        
        with col2:
            self.render_metric_card(
                "Signal Quality", 
                self.get_average_signal_quality(), 
                "4.2/5.0", 
                "info"
            )
        
        with col3:
            self.render_metric_card(
                "Daily Cost", 
                self.get_daily_cost(), 
                "$12.45", 
                "warning"
            )
        
        with col4:
            self.render_metric_card(
                "Reader Engagement", 
                self.get_engagement_rate(), 
                "28.3%", 
                "success"
            )
        
        # Charts Row
        col1, col2 = st.columns(2)
        
        with col1:
            self.render_signal_accuracy_trend()
        
        with col2:
            self.render_cost_breakdown_chart()
    
    def render_metric_card(self, title, value, subtitle, status):
        """Render a metric card with status indicator"""
        status_colors = {
            "success": "#28a745",
            "warning": "#ffc107", 
            "danger": "#dc3545",
            "info": "#17a2b8"
        }
        
        st.markdown(f"""
        <div style="
            background-color: white;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid {status_colors[status]};
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <h3 style="margin: 0; color: #333; font-size: 1.1rem;">{title}</h3>
            <h2 style="margin: 0.5rem 0; color: {status_colors[status]}; font-size: 1.8rem;">{value}</h2>
            <p style="margin: 0; color: #666; font-size: 0.9rem;">{subtitle}</p>
        </div>
        """, unsafe_allow_html=True)
```

#### Prompt Engineering Interface
```python
class PromptEngineeringInterface:
    def __init__(self):
        self.parameter_definitions = self.load_parameter_definitions()
    
    def render_prompt_engineering(self):
        st.title("🛠️ Prompt Engineering Laboratory")
        
        # Tab Layout
        tab1, tab2, tab3, tab4 = st.tabs([
            "Parameter Tuning", "Template Editor", "A/B Testing", "Performance Analysis"
        ])
        
        with tab1:
            self.render_parameter_tuning()
        
        with tab2:
            self.render_template_editor()
        
        with tab3:
            self.render_ab_testing()
        
        with tab4:
            self.render_performance_analysis()
    
    def render_parameter_tuning(self):
        st.subheader("🎛️ Analysis Parameters")
        
        # Agent Selection
        agent_type = st.selectbox(
            "Select Agent",
            ["Content Analysis", "Signal Validation", "Newsletter Writer"]
        )
        
        # Parameter Controls
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Signal Detection")
            
            signal_sensitivity = st.slider(
                "Signal Detection Sensitivity",
                min_value=0,
                max_value=100,
                value=75,
                help="Higher values detect more subtle signals but may increase noise"
            )
            
            pattern_threshold = st.slider(
                "Pattern Anomaly Threshold", 
                min_value=0,
                max_value=100,
                value=60,
                help="Threshold for flagging unusual patterns"
            )
            
            adjacent_depth = st.slider(
                "Adjacent Possibility Depth",
                min_value=1,
                max_value=5,
                value=3,
                help="How extensively to explore cross-domain connections"
            )
        
        with col2:
            st.markdown("### Focus Areas")
            
            st.markdown("**Cross-Domain Weights**")
            tech_weight = st.slider("Technology Focus", 0, 100, 25)
            finance_weight = st.slider("Finance Focus", 0, 100, 35)
            culture_weight = st.slider("Culture Focus", 0, 100, 20)
            politics_weight = st.slider("Politics Focus", 0, 100, 20)
            
            # Normalize weights
            total_weight = tech_weight + finance_weight + culture_weight + politics_weight
            if total_weight > 0:
                weights = {
                    "tech": tech_weight / total_weight,
                    "finance": finance_weight / total_weight, 
                    "culture": culture_weight / total_weight,
                    "politics": politics_weight / total_weight
                }
                st.write("Normalized weights:", weights)
        
        # Advanced Parameters
        with st.expander("Advanced Parameters"):
            time_horizon = st.slider(
                "Time Horizon Bias (Short-term ← → Long-term)",
                min_value=0,
                max_value=100, 
                value=50
            )
            
            contrarian_level = st.slider(
                "Contrarian Thinking Level",
                min_value=0,
                max_value=100,
                value=30,
                help="Emphasis on challenging conventional wisdom"
            )
            
            narrative_gap_emphasis = st.slider(
                "Narrative Gap Emphasis",
                min_value=0,
                max_value=100,
                value=70,
                help="Focus on identifying missing perspectives"
            )
        
        # Real-time Prompt Generation
        st.markdown("### Generated Prompt Preview")
        
        if st.button("🔄 Generate Prompt", type="primary"):
            with st.spinner("Generating prompt..."):
                generated_prompt = self.generate_prompt_from_parameters(
                    agent_type, signal_sensitivity, pattern_threshold,
                    adjacent_depth, weights, time_horizon, contrarian_level,
                    narrative_gap_emphasis
                )
                
                st.code(generated_prompt, language="text")
        
        # Test Against Sample Content
        st.markdown("### Test Prompt")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            test_content = st.text_area(
                "Sample Article Content",
                placeholder="Paste an article title and content here to test the prompt...",
                height=200
            )
        
        with col2:
            if st.button("🧪 Test Prompt", disabled=not test_content):
                with st.spinner("Testing prompt..."):
                    test_result = self.test_prompt_against_content(
                        generated_prompt, test_content
                    )
                    st.json(test_result)
    
    def generate_prompt_from_parameters(self, agent_type, signal_sensitivity, 
                                      pattern_threshold, adjacent_depth, weights,
                                      time_horizon, contrarian_level, narrative_gap_emphasis):
        """Generate a complete prompt based on parameter settings"""
        
        # Base prompt templates
        base_prompts = {
            "Content Analysis": self.get_base_content_analysis_prompt(),
            "Signal Validation": self.get_base_signal_validation_prompt(),
            "Newsletter Writer": self.get_base_newsletter_writer_prompt()
        }
        
        base_prompt = base_prompts[agent_type]
        
        # Parameter modifications
        sensitivity_text = self.generate_sensitivity_modifier(signal_sensitivity)
        threshold_text = self.generate_threshold_modifier(pattern_threshold)
        depth_text = self.generate_depth_modifier(adjacent_depth)
        weights_text = self.generate_weights_modifier(weights)
        horizon_text = self.generate_horizon_modifier(time_horizon)
        contrarian_text = self.generate_contrarian_modifier(contrarian_level)
        gap_text = self.generate_gap_modifier(narrative_gap_emphasis)
        
        # Combine into final prompt
        final_prompt = f"""{base_prompt}

PARAMETER ADJUSTMENTS:
{sensitivity_text}
{threshold_text}
{depth_text}
{weights_text}
{horizon_text}
{contrarian_text}
{gap_text}

Apply these parameter adjustments to modify your analysis approach accordingly."""
        
        return final_prompt
    
    def test_prompt_against_content(self, prompt, content):
        """Test a prompt against sample content and return results"""
        # This would integrate with the actual PydanticAI agents
        # For now, return a mock response
        return {
            "execution_time": "2.3s",
            "token_usage": 1247,
            "estimated_cost": "$0.0234",
            "quality_indicators": {
                "signal_strength": 0.78,
                "uniqueness_score": 0.85,
                "coherence": 0.92
            },
            "detected_signals": [
                "Institutional adoption pattern shift",
                "Cross-domain connection to traditional finance",
                "Regulatory sentiment evolution"
            ]
        }
```

### 4.3 Real-Time Monitoring System
```python
class RealTimeMonitor:
    def __init__(self):
        self.redis_client = redis.Redis.from_url(os.getenv('REDIS_URL'))
        self.db_connection = get_database_connection()
    
    def start_monitoring(self):
        """Start real-time monitoring with WebSocket updates"""
        st.title("📡 Real-Time System Monitor")
        
        # Auto-refresh controls
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            auto_refresh = st.checkbox("Auto Refresh", value=True)
        
        with col2:
            refresh_interval = st.selectbox(
                "Refresh Rate", 
                [10, 30, 60, 300],
                format_func=lambda x: f"{x}s",
                index=1
            )
        
        with col3:
            if st.button("🔄 Manual Refresh"):
                st.rerun()
        
        # Real-time metrics
        self.render_realtime_metrics()
        
        # Auto-refresh logic
        if auto_refresh:
            time.sleep(refresh_interval)
            st.rerun()
    
    def render_realtime_metrics(self):
        # Current pipeline status
        st.subheader("🔄 Current Pipeline Status")
        
        pipeline_status = self.get_current_pipeline_status()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "RSS Ingestion", 
                pipeline_status['rss_status'],
                delta=f"{pipeline_status['articles_ingested']} articles"
            )
        
        with col2:
            st.metric(
                "Analysis Queue", 
                f"{pipeline_status['analysis_queue_size']} pending",
                delta=f"{pipeline_status['analysis_rate']}/min"
            )
        
        with col3:
            st.metric(
                "Newsletter Status",
                pipeline_status['newsletter_status'],
                delta=pipeline_status['next_newsletter_time']
            )
        
        # Active agent monitoring
        st.subheader("🤖 Agent Activity")
        
        agent_metrics = self.get_agent_metrics()
        
        for agent_name, metrics in agent_metrics.items():
            with st.expander(f"{agent_name} - {metrics['status']}", expanded=metrics['active']):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Avg Response Time", f"{metrics['avg_response_time']:.1f}s")
                
                with col2:
                    st.metric("Success Rate", f"{metrics['success_rate']:.1%}")
                
                with col3:
                    st.metric("Cost (24h)", f"${metrics['daily_cost']:.2f}")
                
                with col4:
                    st.metric("Quality Score", f"{metrics['quality_score']:.2f}/5.0")
```

### 4.4 Alert and Notification System
```python
class AlertSystem:
    def __init__(self):
        self.alert_rules = self.load_alert_rules()
        self.notification_channels = self.setup_notification_channels()
    
    def setup_alert_rules(self):
        """Define alert rules and thresholds"""
        return {
            "system_health": {
                "pipeline_failure": {"threshold": 1, "severity": "critical"},
                "agent_error_rate": {"threshold": 0.05, "severity": "warning"},
                "database_latency": {"threshold": 1000, "severity": "warning"}
            },
            "quality_metrics": {
                "signal_quality_drop": {"threshold": 3.5, "severity": "warning"},
                "newsletter_engagement_drop": {"threshold": 0.20, "severity": "info"},
                "cost_spike": {"threshold": 100, "severity": "warning"}
            },
            "operational": {
                "missed_publication": {"threshold": 1, "severity": "critical"},
                "queue_backup": {"threshold": 100, "severity": "warning"},
                "storage_usage": {"threshold": 0.85, "severity": "info"}
            }
        }
    
    def check_alerts(self):
        """Check all alert conditions and trigger notifications"""
        active_alerts = []
        
        for category, rules in self.alert_rules.items():
            for rule_name, config in rules.items():
                if self.evaluate_alert_condition(rule_name, config):
                    alert = self.create_alert(category, rule_name, config)
                    active_alerts.append(alert)
                    self.send_notification(alert)
        
        return active_alerts
    
    def render_alert_dashboard(self):
        """Render alert dashboard in Streamlit"""
        st.subheader("🚨 System Alerts")
        
        active_alerts = self.get_active_alerts()
        
        if not active_alerts:
            st.success("✅ No active alerts - all systems operational")
        else:
            for alert in active_alerts:
                severity_colors = {
                    "critical": "error",
                    "warning": "warning", 
                    "info": "info"
                }
                
                with st.container():
                    st.markdown(f"**{alert['title']}**")
                    st.write(alert['description'])
                    
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.write(f"Severity: {alert['severity'].upper()}")
                    
                    with col2:
                        st.write(f"Since: {alert['created_at']}")
                    
                    with col3:
                        if st.button(f"Acknowledge", key=f"ack_{alert['id']}"):
                            self.acknowledge_alert(alert['id'])
                            st.rerun()
```

---

## 5. Quality Standards

### 5.1 Dashboard Performance
- **Response Time**: <2 seconds for all dashboard views
- **Real-Time Updates**: <30 second latency for live metrics
- **Uptime**: 99.5% dashboard availability
- **Mobile Compatibility**: Full functionality on mobile devices

### 5.2 Prompt Engineering Efficiency
- **Prompt Generation**: <5 seconds for parameter-based prompt creation
- **Test Execution**: <30 seconds for prompt testing against sample content
- **Deployment Success**: >98% successful deployment rate for new prompts
- **A/B Test Reliability**: Statistical significance calculation accuracy >95%

### 5.3 Monitoring Accuracy
- **Alert Precision**: >95% accuracy (minimal false positives)
- **Metric Accuracy**: <1% variance from actual system performance
- **Historical Data Integrity**: 100% data consistency across time periods
- **Cost Tracking Accuracy**: <2% variance from actual costs

---

## 6. Success Metrics

### 6.1 Operational Excellence
- **System Visibility**: 100% of system components monitored and visible
- **Issue Detection Time**: <5 minutes for critical system failures
- **Resolution Time**: <30 minutes for most operational issues
- **Prevented Downtime**: >50% reduction in unplanned outages through proactive monitoring

### 6.2 Optimization Impact
- **Quality Improvement**: 20% improvement in signal detection quality through prompt optimization
- **Cost Optimization**: 15% reduction in operational costs through monitoring and optimization
- **User Adoption**: >80% of power users actively use prompt engineering features
- **A/B Test Success**: >60% of A/B tests result in measurable improvements

---

## 7. Implementation Roadmap

### Week 1: Core Monitoring Infrastructure
- Basic Streamlit dashboard setup
- Database schema extensions for monitoring
- Integration with existing system components
- Real-time metrics collection and display

### Week 2: Advanced Dashboard Features
- Interactive visualizations and charts
- Alert system implementation
- Historical data analysis capabilities
- Performance trend analysis

### Week 3: Prompt Engineering Interface
- Parameter control interface development
- Real-time prompt generation system
- Sample testing framework
- Template management system

### Week 4: Optimization & Production
- A/B testing framework implementation
- Quality assessment automation
- System controls and manual overrides
- Production deployment and testing

---

## 8. Risk Assessment

### Technical Risks
- **Dashboard Performance**: Mitigation through caching and optimization
- **Real-Time Data Accuracy**: Mitigation through data validation and reconciliation
- **Prompt Engineering Complexity**: Mitigation through intuitive UI design and documentation

### Operational Risks
- **Alert Fatigue**: Mitigation through intelligent alert thresholds and aggregation
- **User Adoption**: Mitigation through training and intuitive interface design
- **System Overhead**: Mitigation through efficient monitoring implementation

---

## 9. Dependencies

### System Dependencies
- **Core Data Pipeline**: Reliable data flow for monitoring
- **Signal Detection System**: Agent performance data and quality metrics
- **Newsletter Generation**: Content quality and reader engagement data

### External Dependencies
- **LangFuse**: Agent interaction tracking and observability
- **Streamlit**: Dashboard framework and interactive components
- **Redis**: Caching and real-time data management

---

*Document Version: 1.0*
*Last Updated: August 10, 2025*
*Status: Ready for Implementation*
*Prerequisites: All previous PRDs for complete system integration*