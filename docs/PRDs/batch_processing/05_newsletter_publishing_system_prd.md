# Newsletter Publishing & Distribution System
## Sub-PRD 5: Multi-Channel Newsletter Publishing Pipeline

### Executive Summary
Implement a comprehensive newsletter publishing system that handles multi-format content generation (HTML, text, PDF), email distribution, web publishing, and performance tracking. This system ensures reliable delivery across multiple channels with engagement analytics and subscriber management.

---

## 1. Product Overview

### Objective
Create a robust publishing pipeline that transforms generated newsletter content into multiple formats and distributes them across email, web, and archive channels with comprehensive tracking and analytics.

### Publishing Architecture
```
Newsletter Content → Format Generation → Distribution → Tracking & Analytics
        ↓                    ↓              ↓              ↓
   Database Storage    HTML/Text/PDF    Email/Web     Engagement Metrics
```

---

## 2. Content Format Generation

### 2.1 Multi-Format Content Generator
```python
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from markdown import markdown
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from crypto_newsletter.shared.models import Newsletter
from crypto_newsletter.newsletter.templates import TemplateManager

logger = logging.getLogger(__name__)

class NewsletterContentGenerator:
    """Generates newsletter content in multiple formats."""

    def __init__(self):
        self.template_manager = TemplateManager()
        self.jinja_env = Environment(
            loader=FileSystemLoader('templates/newsletter'),
            autoescape=True
        )

    async def generate_all_formats(
        self,
        newsletter: Newsletter
    ) -> Dict[str, str]:
        """Generate newsletter in all required formats."""

        try:
            # Parse newsletter content
            content_data = self._parse_newsletter_content(newsletter)

            # Generate HTML version
            html_content = await self._generate_html_content(content_data, newsletter)

            # Generate plain text version
            text_content = await self._generate_text_content(content_data, newsletter)

            # Generate PDF version
            pdf_content = await self._generate_pdf_content(html_content, newsletter)

            # Generate web version (enhanced HTML)
            web_content = await self._generate_web_content(content_data, newsletter)

            return {
                "html": html_content,
                "text": text_content,
                "pdf": pdf_content,
                "web": web_content,
                "generation_timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Content generation failed for newsletter {newsletter.id}: {e}")
            raise ContentGenerationException(f"Failed to generate content formats: {str(e)}")

    async def _generate_html_content(
        self,
        content_data: Dict[str, Any],
        newsletter: Newsletter
    ) -> str:
        """Generate HTML email content."""

        template = self.jinja_env.get_template('email_newsletter.html')

        html_content = template.render(
            title=content_data['title'],
            publication_date=newsletter.publication_date.strftime('%B %d, %Y'),
            newsletter_type=newsletter.newsletter_type,
            executive_summary=content_data['executive_summary'],
            main_analysis=markdown(content_data['main_analysis']),
            pattern_spotlight=markdown(content_data['pattern_spotlight']),
            adjacent_watch=markdown(content_data['adjacent_watch']),
            signal_radar=markdown(content_data['signal_radar']),
            action_items=content_data['action_items'],
            source_citations=content_data['source_citations'],
            estimated_read_time=content_data['estimated_read_time'],
            unsubscribe_url=self._generate_unsubscribe_url(),
            web_version_url=self._generate_web_url(newsletter.id),
            branding=self._get_branding_data()
        )

        return html_content

    async def _generate_text_content(
        self,
        content_data: Dict[str, Any],
        newsletter: Newsletter
    ) -> str:
        """Generate plain text email content."""

        template = self.jinja_env.get_template('email_newsletter.txt')

        text_content = template.render(
            title=content_data['title'],
            publication_date=newsletter.publication_date.strftime('%B %d, %Y'),
            newsletter_type=newsletter.newsletter_type,
            executive_summary=content_data['executive_summary'],
            main_analysis=content_data['main_analysis'],
            pattern_spotlight=content_data['pattern_spotlight'],
            adjacent_watch=content_data['adjacent_watch'],
            signal_radar=content_data['signal_radar'],
            action_items=content_data['action_items'],
            source_citations=content_data['source_citations'],
            estimated_read_time=content_data['estimated_read_time'],
            unsubscribe_url=self._generate_unsubscribe_url(),
            web_version_url=self._generate_web_url(newsletter.id)
        )

        return text_content

    async def _generate_pdf_content(
        self,
        html_content: str,
        newsletter: Newsletter
    ) -> bytes:
        """Generate PDF version for archival."""

        # Enhanced HTML for PDF with better styling
        pdf_template = self.jinja_env.get_template('pdf_newsletter.html')
        pdf_html = pdf_template.render(
            html_content=html_content,
            newsletter_id=newsletter.id,
            publication_date=newsletter.publication_date.strftime('%B %d, %Y')
        )

        # Generate PDF using WeasyPrint
        pdf_css = CSS(filename='templates/newsletter/pdf_styles.css')
        pdf_document = HTML(string=pdf_html).write_pdf(stylesheets=[pdf_css])

        return pdf_document

    def _parse_newsletter_content(self, newsletter: Newsletter) -> Dict[str, Any]:
        """Parse newsletter content from database storage."""

        # Handle both legacy and new content formats
        if newsletter.content_html:
            # New format - structured content
            return {
                "title": newsletter.title,
                "executive_summary": newsletter.synthesis_themes.get('executive_summary', []) if newsletter.synthesis_themes else [],
                "main_analysis": newsletter.content,
                "pattern_spotlight": newsletter.pattern_insights.get('spotlight', '') if newsletter.pattern_insights else '',
                "adjacent_watch": newsletter.adjacent_implications.get('watch_list', '') if newsletter.adjacent_implications else '',
                "signal_radar": newsletter.signal_highlights.get('radar', '') if newsletter.signal_highlights else '',
                "action_items": newsletter.synthesis_themes.get('action_items', []) if newsletter.synthesis_themes else [],
                "source_citations": newsletter.selection_reasoning.get('sources', []) if newsletter.selection_reasoning else [],
                "estimated_read_time": 8  # Default estimate
            }
        else:
            # Legacy format - parse from content field
            return self._parse_legacy_content(newsletter.content)

# Global content generator instance
content_generator = NewsletterContentGenerator()
```

### 2.2 Email Distribution System
```python
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Any
import asyncio

from crypto_newsletter.shared.config.settings import settings
from crypto_newsletter.newsletter.subscribers import SubscriberManager

class NewsletterEmailDistributor:
    """Handles email distribution of newsletters."""

    def __init__(self):
        self.subscriber_manager = SubscriberManager()
        self.smtp_config = {
            "server": settings.smtp_server,
            "port": settings.smtp_port,
            "username": settings.smtp_username,
            "password": settings.smtp_password,
            "use_tls": settings.smtp_use_tls
        }

    async def distribute_newsletter(
        self,
        newsletter_id: int,
        html_content: str,
        text_content: str,
        pdf_content: bytes,
        distribution_type: str = "daily_subscribers"
    ) -> Dict[str, Any]:
        """Distribute newsletter via email to subscribers."""

        try:
            # Get subscriber list based on distribution type
            subscribers = await self.subscriber_manager.get_active_subscribers(
                subscription_type=distribution_type
            )

            logger.info(f"Distributing newsletter {newsletter_id} to {len(subscribers)} subscribers")

            # Prepare email content
            email_data = self._prepare_email_content(
                newsletter_id, html_content, text_content, pdf_content
            )

            # Send emails in batches to avoid rate limiting
            batch_size = 50
            sent_count = 0
            failed_count = 0
            failed_emails = []

            for i in range(0, len(subscribers), batch_size):
                batch = subscribers[i:i + batch_size]
                batch_results = await self._send_email_batch(batch, email_data)

                sent_count += batch_results["sent"]
                failed_count += batch_results["failed"]
                failed_emails.extend(batch_results["failed_emails"])

                # Brief pause between batches
                await asyncio.sleep(2)

            # Update newsletter metrics
            await self._update_email_metrics(
                newsletter_id, len(subscribers), sent_count, failed_count
            )

            return {
                "status": "completed",
                "newsletter_id": newsletter_id,
                "total_subscribers": len(subscribers),
                "emails_sent": sent_count,
                "emails_failed": failed_count,
                "failed_emails": failed_emails,
                "distribution_type": distribution_type,
                "sent_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Email distribution failed for newsletter {newsletter_id}: {e}")
            raise EmailDistributionException(f"Failed to distribute newsletter: {str(e)}")

    async def _send_email_batch(
        self,
        subscribers: List[Dict],
        email_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send email to a batch of subscribers."""

        sent = 0
        failed = 0
        failed_emails = []

        try:
            # Create SMTP connection
            context = ssl.create_default_context()

            with smtplib.SMTP(self.smtp_config["server"], self.smtp_config["port"]) as server:
                if self.smtp_config["use_tls"]:
                    server.starttls(context=context)

                server.login(self.smtp_config["username"], self.smtp_config["password"])

                for subscriber in subscribers:
                    try:
                        # Personalize email for subscriber
                        personalized_email = self._personalize_email(email_data, subscriber)

                        # Send email
                        server.send_message(personalized_email)
                        sent += 1

                        # Track email sent
                        await self._track_email_sent(subscriber["email"], email_data["newsletter_id"])

                    except Exception as e:
                        logger.warning(f"Failed to send email to {subscriber['email']}: {e}")
                        failed += 1
                        failed_emails.append({
                            "email": subscriber["email"],
                            "error": str(e)
                        })

        except Exception as e:
            logger.error(f"SMTP connection failed: {e}")
            failed = len(subscribers)
            failed_emails = [{"email": sub["email"], "error": "SMTP connection failed"} for sub in subscribers]

        return {
            "sent": sent,
            "failed": failed,
            "failed_emails": failed_emails
        }

    def _prepare_email_content(
        self,
        newsletter_id: int,
        html_content: str,
        text_content: str,
        pdf_content: bytes
    ) -> Dict[str, Any]:
        """Prepare email content with attachments."""

        return {
            "newsletter_id": newsletter_id,
            "subject": self._generate_email_subject(newsletter_id),
            "html_content": html_content,
            "text_content": text_content,
            "pdf_attachment": pdf_content,
            "from_email": settings.newsletter_from_email,
            "from_name": settings.newsletter_from_name
        }

    def _personalize_email(
        self,
        email_data: Dict[str, Any],
        subscriber: Dict[str, Any]
    ) -> MIMEMultipart:
        """Create personalized email for subscriber."""

        msg = MIMEMultipart('alternative')
        msg['Subject'] = email_data["subject"]
        msg['From'] = f"{email_data['from_name']} <{email_data['from_email']}>"
        msg['To'] = subscriber["email"]

        # Add tracking parameters
        tracking_params = {
            "subscriber_id": subscriber["id"],
            "newsletter_id": email_data["newsletter_id"],
            "email": subscriber["email"]
        }

        # Personalize content with subscriber data
        personalized_html = self._add_tracking_pixels(
            email_data["html_content"], tracking_params
        )
        personalized_text = email_data["text_content"]

        # Attach content
        msg.attach(MIMEText(personalized_text, 'plain'))
        msg.attach(MIMEText(personalized_html, 'html'))

        # Attach PDF if enabled for subscriber
        if subscriber.get("pdf_enabled", False):
            pdf_attachment = MIMEBase('application', 'octet-stream')
            pdf_attachment.set_payload(email_data["pdf_attachment"])
            encoders.encode_base64(pdf_attachment)
            pdf_attachment.add_header(
                'Content-Disposition',
                f'attachment; filename="newsletter_{email_data["newsletter_id"]}.pdf"'
            )
            msg.attach(pdf_attachment)

        return msg

# Global email distributor instance
email_distributor = NewsletterEmailDistributor()
```

---

## 3. Publishing Celery Tasks

### 3.1 Newsletter Publishing Task
```python
@celery_app.task(
    bind=True,
    name="crypto_newsletter.newsletter.tasks.publish_newsletter",
    max_retries=3,
    default_retry_delay=600,  # 10 minutes
    queue="publishing"
)
def publish_newsletter_task(
    self,
    newsletter_id: int,
    distribution_channels: str = "email_and_web"
) -> Dict[str, Any]:
    """
    Publish newsletter across specified distribution channels.

    Args:
        newsletter_id: ID of newsletter to publish
        distribution_channels: Channels to publish to (email_and_web, email_only, web_only, weekly_subscribers)

    Returns:
        Dict with publishing results
    """

    async def _publish_newsletter() -> Dict[str, Any]:
        """Internal async function for newsletter publishing."""

        task_start = datetime.utcnow()
        publishing_metadata = {
            "task_started_at": task_start.isoformat(),
            "newsletter_id": newsletter_id,
            "distribution_channels": distribution_channels
        }

        try:
            async with get_async_session() as db:
                # Step 1: Load newsletter from database
                newsletter = await get_newsletter_by_id(db, newsletter_id)

                if not newsletter:
                    raise NewsletterNotFoundException(f"Newsletter {newsletter_id} not found")

                if newsletter.publish_status == "PUBLISHED":
                    logger.info(f"Newsletter {newsletter_id} already published")
                    return {
                        "status": "already_published",
                        "newsletter_id": newsletter_id,
                        "published_at": newsletter.published_at.isoformat()
                    }

                # Step 2: Generate all content formats
                logger.info(f"Generating content formats for newsletter {newsletter_id}")

                content_formats = await content_generator.generate_all_formats(newsletter)

                # Step 3: Store generated content
                await store_newsletter_content_versions(db, newsletter_id, content_formats)

                publishing_results = {}

                # Step 4: Email distribution
                if "email" in distribution_channels:
                    logger.info(f"Starting email distribution for newsletter {newsletter_id}")

                    email_result = await email_distributor.distribute_newsletter(
                        newsletter_id=newsletter_id,
                        html_content=content_formats["html"],
                        text_content=content_formats["text"],
                        pdf_content=content_formats["pdf"],
                        distribution_type=distribution_channels
                    )

                    publishing_results["email"] = email_result

                # Step 5: Web publishing
                if "web" in distribution_channels:
                    logger.info(f"Publishing newsletter {newsletter_id} to web")

                    web_result = await web_publisher.publish_to_web(
                        newsletter_id=newsletter_id,
                        web_content=content_formats["web"]
                    )

                    publishing_results["web"] = web_result

                # Step 6: Update newsletter status
                await update_newsletter_publish_status(
                    db, newsletter_id, "PUBLISHED", datetime.utcnow()
                )

                # Step 7: Initialize performance tracking
                await initialize_newsletter_tracking(db, newsletter_id, publishing_results)

                processing_time = (datetime.utcnow() - task_start).total_seconds()
                publishing_metadata.update({
                    "processing_time_seconds": processing_time,
                    "task_completed_at": datetime.utcnow().isoformat()
                })

                logger.info(
                    f"Newsletter {newsletter_id} published successfully - "
                    f"Channels: {distribution_channels}, Time: {processing_time:.2f}s"
                )

                return {
                    "status": "success",
                    "newsletter_id": newsletter_id,
                    "distribution_channels": distribution_channels,
                    "publishing_results": publishing_results,
                    "processing_time_seconds": processing_time,
                    "published_at": datetime.utcnow().isoformat(),
                    "publishing_metadata": publishing_metadata
                }

        except Exception as exc:
            logger.error(f"Newsletter publishing failed: {exc}")

            # Store publishing failure
            await store_publishing_failure(
                newsletter_id=newsletter_id,
                error=str(exc),
                metadata=publishing_metadata
            )

            # Retry logic
            if self.request.retries < self.max_retries:
                retry_delay = 600 * (self.request.retries + 1)
                logger.warning(f"Retrying newsletter publishing in {retry_delay} seconds")
                raise self.retry(countdown=retry_delay, exc=exc)

            return {
                "status": "failed",
                "newsletter_id": newsletter_id,
                "error": str(exc),
                "retries_exhausted": True,
                "publishing_metadata": publishing_metadata
            }

    return asyncio.run(_publish_newsletter())
```

---

## 4. Implementation Timeline

### Week 1: Content Generation
- **Days 1-3**: Implement multi-format content generator
- **Days 4-5**: Create email templates and PDF generation
- **Days 6-7**: Build web publishing system

### Week 2: Distribution System
- **Days 1-3**: Implement email distribution system
- **Days 4-5**: Create subscriber management
- **Days 6-7**: Build publishing Celery tasks

### Week 3: Testing & Optimization
- **Days 1-3**: Test complete publishing pipeline
- **Days 4-5**: Performance optimization and monitoring
- **Days 6-7**: Production deployment and validation

---

## 5. Success Metrics

### Publishing Performance
- **Email Delivery Rate**: >98% successful email delivery
- **Publishing Speed**: Complete publishing <10 minutes
- **Format Generation**: All formats generated successfully >99% of time
- **Error Recovery**: <2% retry rate with 100% eventual success

### Engagement Metrics
- **Email Open Rate**: >25% for daily, >30% for weekly newsletters
- **Click-Through Rate**: >8% for actionable content
- **Unsubscribe Rate**: <2% monthly churn
- **Web Traffic**: >500 unique visitors per newsletter

---

*Sub-PRD Version: 1.0*
*Implementation Priority: Phase 5 - Publishing*
*Dependencies: Newsletter generation tasks, database schema*
*Estimated Effort: 3 weeks*
