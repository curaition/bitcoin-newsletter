"""Main CLI application for crypto newsletter management."""

import asyncio
import json
from typing import List, Optional

import typer
from loguru import logger

from crypto_newsletter.core.ingestion import (
    pipeline_health_check,
    quick_ingestion_test,
    run_article_ingestion,
)
from crypto_newsletter.core.storage import get_recent_articles_with_stats

app = typer.Typer(
    name="crypto-newsletter",
    help="Crypto Newsletter CLI - Manage article ingestion and processing",
)


@app.command()
def health() -> None:
    """Check the health of all pipeline components."""
    typer.echo("🔍 Checking pipeline health...")
    
    async def _health_check():
        try:
            health_status = await pipeline_health_check()
            
            if health_status["status"] == "healthy":
                typer.echo("✅ Pipeline is healthy!")
                typer.echo(f"   Timestamp: {health_status['timestamp']}")
                
                for check_name, check_result in health_status["checks"].items():
                    status_icon = "✅" if check_result["status"] == "healthy" else "❌"
                    typer.echo(f"   {status_icon} {check_name}: {check_result['message']}")
            else:
                typer.echo("❌ Pipeline has health issues!")
                for check_name, check_result in health_status["checks"].items():
                    status_icon = "✅" if check_result["status"] == "healthy" else "❌"
                    typer.echo(f"   {status_icon} {check_name}: {check_result['message']}")
                    
        except Exception as e:
            typer.echo(f"❌ Health check failed: {e}")
            raise typer.Exit(1)
    
    asyncio.run(_health_check())


@app.command()
def test() -> None:
    """Run a quick pipeline test with minimal data."""
    typer.echo("🧪 Running pipeline test...")
    
    async def _test():
        try:
            success = await quick_ingestion_test()
            if success:
                typer.echo("✅ Pipeline test successful!")
            else:
                typer.echo("❌ Pipeline test failed!")
                raise typer.Exit(1)
        except Exception as e:
            typer.echo(f"❌ Pipeline test error: {e}")
            raise typer.Exit(1)
    
    asyncio.run(_test())


@app.command()
def ingest(
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum articles to fetch"),
    hours: int = typer.Option(24, "--hours", "-h", help="Hours back to filter articles"),
    categories: Optional[str] = typer.Option(None, "--categories", "-c", help="Comma-separated categories"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """Run article ingestion from CoinDesk API."""
    if verbose:
        logger.remove()
        logger.add(lambda msg: typer.echo(msg, err=True), level="DEBUG")
    
    category_list = categories.split(",") if categories else None
    
    typer.echo(f"📰 Starting article ingestion...")
    typer.echo(f"   Limit: {limit} articles")
    typer.echo(f"   Time window: {hours} hours")
    typer.echo(f"   Categories: {category_list or ['BTC']}")
    
    async def _ingest():
        try:
            results = await run_article_ingestion(
                limit=limit,
                hours_back=hours,
                categories=category_list,
            )
            
            # Display results
            summary = results["summary"]
            typer.echo(f"\n✅ Ingestion completed!")
            typer.echo(f"   📊 Articles fetched: {summary['articles_fetched']}")
            typer.echo(f"   💾 Articles processed: {summary['articles_processed']}")
            typer.echo(f"   🔄 Duplicates skipped: {summary['duplicates_skipped']}")
            typer.echo(f"   ⚡ Success rate: {summary['success_rate']:.1%}")
            typer.echo(f"   ⏱️  Processing time: {results['processing_time_seconds']:.2f}s")
            
            if summary['errors'] > 0:
                typer.echo(f"   ⚠️  Errors: {summary['errors']}")
                
        except Exception as e:
            typer.echo(f"❌ Ingestion failed: {e}")
            raise typer.Exit(1)
    
    asyncio.run(_ingest())


@app.command()
def stats() -> None:
    """Show article statistics and recent data."""
    typer.echo("📊 Fetching article statistics...")
    
    async def _stats():
        try:
            data = await get_recent_articles_with_stats(hours=24)
            
            stats = data["statistics"]
            articles = data["articles"]
            
            typer.echo(f"\n📈 Article Statistics:")
            typer.echo(f"   Total articles: {stats['total_articles']}")
            typer.echo(f"   Recent (24h): {stats['recent_articles_24h']}")
            typer.echo(f"   Last updated: {stats['last_updated']}")
            
            if stats["top_publishers"]:
                typer.echo(f"\n🏢 Top Publishers:")
                for pub in stats["top_publishers"][:5]:
                    typer.echo(f"   • {pub['publisher']}: {pub['count']} articles")
            
            if stats["top_categories"]:
                typer.echo(f"\n🏷️  Top Categories:")
                for cat in stats["top_categories"][:5]:
                    typer.echo(f"   • {cat['category']}: {cat['count']} articles")
            
            if articles:
                typer.echo(f"\n📰 Recent Articles ({len(articles)}):")
                for article in articles[:5]:
                    title = article["title"][:60] + "..." if len(article["title"]) > 60 else article["title"]
                    publisher_id = article["publisher_id"] or "Unknown"
                    typer.echo(f"   • {title} (Publisher ID: {publisher_id})")
                    
        except Exception as e:
            typer.echo(f"❌ Failed to fetch statistics: {e}")
            raise typer.Exit(1)
    
    asyncio.run(_stats())


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", help="Port to bind to"),
    dev: bool = typer.Option(False, "--dev", help="Enable development mode"),
    production: bool = typer.Option(False, "--production", help="Enable production mode"),
) -> None:
    """Start the FastAPI web service."""
    if dev and production:
        typer.echo("❌ Cannot enable both dev and production modes")
        raise typer.Exit(1)
    
    if production:
        typer.echo("🚀 Starting production web service...")
        # TODO: Import and start production FastAPI app
        typer.echo("❌ Production mode not yet implemented")
        raise typer.Exit(1)
    elif dev:
        typer.echo("🔧 Starting development web service...")
        # TODO: Import and start development FastAPI app
        typer.echo("❌ Development mode not yet implemented")
        raise typer.Exit(1)
    else:
        typer.echo("❌ Must specify either --dev or --production mode")
        raise typer.Exit(1)


@app.command()
def version() -> None:
    """Show version information."""
    typer.echo("Crypto Newsletter CLI v0.1.0")
    typer.echo("Built with FastAPI, SQLAlchemy, and Celery")


@app.command()
def worker(
    loglevel: str = typer.Option("INFO", help="Logging level"),
    concurrency: int = typer.Option(2, help="Number of worker processes"),
    queues: str = typer.Option("default,ingestion,monitoring,maintenance", help="Queues to consume from"),
) -> None:
    """Start Celery worker for background task processing."""
    typer.echo("🔄 Starting Celery worker...")

    try:
        from crypto_newsletter.shared.celery.worker import start_worker
        start_worker(loglevel=loglevel, concurrency=concurrency, queues=queues)
    except ImportError:
        typer.echo("❌ Celery not available. Install with: uv add celery[redis]")
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Failed to start worker: {e}")
        raise typer.Exit(1)


@app.command()
def beat() -> None:
    """Start Celery beat scheduler for periodic tasks."""
    typer.echo("⏰ Starting Celery beat scheduler...")

    try:
        from crypto_newsletter.shared.celery.worker import start_beat
        start_beat()
    except ImportError:
        typer.echo("❌ Celery not available. Install with: uv add celery[redis]")
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Failed to start beat: {e}")
        raise typer.Exit(1)


@app.command()
def flower(
    port: int = typer.Option(5555, help="Port to run Flower on"),
) -> None:
    """Start Flower monitoring interface for Celery."""
    typer.echo(f"🌸 Starting Flower monitoring on port {port}...")

    try:
        from crypto_newsletter.shared.celery.worker import start_flower
        start_flower(port=port)
    except ImportError:
        typer.echo("❌ Flower not available. Install with: uv add flower")
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Failed to start Flower: {e}")
        raise typer.Exit(1)


@app.command()
def task_status(task_id: str) -> None:
    """Get status of a specific Celery task."""
    try:
        from crypto_newsletter.core.scheduling.tasks import get_task_status

        status = get_task_status(task_id)

        typer.echo(f"📋 Task Status: {task_id}")
        typer.echo(f"   Status: {status['status']}")
        typer.echo(f"   Result: {status['result']}")
        if status['date_done']:
            typer.echo(f"   Completed: {status['date_done']}")
        if status['traceback']:
            typer.echo(f"   Error: {status['traceback']}")

    except ImportError:
        typer.echo("❌ Celery not available")
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Failed to get task status: {e}")
        raise typer.Exit(1)


@app.command()
def schedule_ingest(
    limit: Optional[int] = typer.Option(None, help="Maximum number of articles to fetch"),
    hours: int = typer.Option(4, help="Hours back to look for articles"),
) -> None:
    """Schedule an immediate article ingestion task."""
    typer.echo("📅 Scheduling article ingestion task...")

    try:
        from crypto_newsletter.core.scheduling.tasks import manual_ingest

        result = manual_ingest.delay(limit=limit, hours_back=hours)

        typer.echo(f"✅ Task scheduled successfully!")
        typer.echo(f"   Task ID: {result.id}")
        typer.echo(f"   Status: {result.status}")
        typer.echo(f"   Use 'task-status {result.id}' to check progress")

    except ImportError:
        typer.echo("❌ Celery not available")
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Failed to schedule task: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
