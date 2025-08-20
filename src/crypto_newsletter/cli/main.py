"""Main CLI application for crypto newsletter management."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from crypto_newsletter.core.ingestion import (
    pipeline_health_check,
    quick_ingestion_test,
    run_article_ingestion,
)
from crypto_newsletter.core.storage import get_recent_articles_with_stats
from crypto_newsletter.shared.config.settings import get_settings
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Rich console for enhanced output
console = Console()

app = typer.Typer(
    name="crypto-newsletter",
    help="Crypto Newsletter CLI - Manage article ingestion and processing",
    rich_markup_mode="rich",
)


@app.command()
def health() -> None:
    """Check the health of all pipeline components."""
    console.print("🔍 [bold blue]Checking pipeline health...[/bold blue]")

    async def _health_check():
        try:
            health_status = await pipeline_health_check()

            if health_status["status"] == "healthy":
                console.print("✅ [bold green]Pipeline is healthy![/bold green]")
                console.print(f"   Timestamp: {health_status['timestamp']}")

                # Create table for health checks
                table = Table(title="Health Check Results")
                table.add_column("Component", style="cyan")
                table.add_column("Status", style="green")
                table.add_column("Message", style="yellow")

                for check_name, check_result in health_status["checks"].items():
                    status_text = (
                        "✅ Healthy"
                        if check_result["status"] == "healthy"
                        else "❌ Unhealthy"
                    )
                    table.add_row(check_name, status_text, check_result["message"])

                console.print(table)
            else:
                console.print("❌ [bold red]Pipeline has health issues![/bold red]")

                # Create table for health issues
                table = Table(title="Health Check Issues")
                table.add_column("Component", style="cyan")
                table.add_column("Status", style="red")
                table.add_column("Message", style="yellow")

                for check_name, check_result in health_status["checks"].items():
                    status_text = (
                        "✅ Healthy"
                        if check_result["status"] == "healthy"
                        else "❌ Unhealthy"
                    )
                    table.add_row(check_name, status_text, check_result["message"])

                console.print(table)

        except Exception as e:
            console.print(f"❌ [bold red]Health check failed:[/bold red] {e}")
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
    hours: int = typer.Option(
        24, "--hours", "-h", help="Hours back to filter articles"
    ),
    categories: Optional[str] = typer.Option(
        None, "--categories", "-c", help="Comma-separated categories"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
) -> None:
    """Run article ingestion from CoinDesk API."""
    if verbose:
        logger.remove()
        logger.add(lambda msg: typer.echo(msg, err=True), level="DEBUG")

    category_list = categories.split(",") if categories else None

    typer.echo("📰 Starting article ingestion...")
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
            typer.echo("\n✅ Ingestion completed!")
            typer.echo(f"   📊 Articles fetched: {summary['articles_fetched']}")
            typer.echo(f"   💾 Articles processed: {summary['articles_processed']}")
            typer.echo(f"   🔄 Duplicates skipped: {summary['duplicates_skipped']}")
            typer.echo(f"   ⚡ Success rate: {summary['success_rate']:.1%}")
            typer.echo(
                f"   ⏱️  Processing time: {results['processing_time_seconds']:.2f}s"
            )

            if summary["errors"] > 0:
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

            typer.echo("\n📈 Article Statistics:")
            typer.echo(f"   Total articles: {stats['total_articles']}")
            typer.echo(f"   Recent (24h): {stats['recent_articles_24h']}")
            typer.echo(f"   Last updated: {stats['last_updated']}")

            if stats["top_publishers"]:
                typer.echo("\n🏢 Top Publishers:")
                for pub in stats["top_publishers"][:5]:
                    typer.echo(f"   • {pub['publisher']}: {pub['count']} articles")

            if stats["top_categories"]:
                typer.echo("\n🏷️  Top Categories:")
                for cat in stats["top_categories"][:5]:
                    typer.echo(f"   • {cat['category']}: {cat['count']} articles")

            if articles:
                typer.echo(f"\n📰 Recent Articles ({len(articles)}):")
                for article in articles[:5]:
                    title = (
                        article["title"][:60] + "..."
                        if len(article["title"]) > 60
                        else article["title"]
                    )
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
    production: bool = typer.Option(
        False, "--production", help="Enable production mode"
    ),
    workers: int = typer.Option(1, "--workers", help="Number of worker processes"),
) -> None:
    """Start the FastAPI web service."""
    if dev and production:
        typer.echo("❌ Cannot enable both dev and production modes")
        raise typer.Exit(1)

    try:
        from crypto_newsletter.web.main import start_server

        if production:
            typer.echo(
                f"🚀 Starting production web service on {host}:{port} with {workers} workers..."
            )
            start_server(host=host, port=port, reload=False, workers=workers)
        elif dev:
            typer.echo(
                f"🔧 Starting development web service on {host}:{port} with reload..."
            )
            start_server(host=host, port=port, reload=True, workers=1)
        else:
            typer.echo("❌ Must specify either --dev or --production mode")
            raise typer.Exit(1)

    except ImportError as e:
        typer.echo(f"❌ FastAPI not available: {e}")
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Failed to start web service: {e}")
        raise typer.Exit(1)


@app.command()
def version() -> None:
    """Show version information."""
    typer.echo("Crypto Newsletter CLI v0.1.0")
    typer.echo("Built with FastAPI, SQLAlchemy, and Celery")


@app.command()
def worker(
    loglevel: str = typer.Option("INFO", help="Logging level"),
    concurrency: int = typer.Option(10, help="Number of async worker tasks"),
    queues: str = typer.Option(
        "default,ingestion,monitoring,maintenance,batch_processing,newsletter,publishing",
        help="Queues to consume from"
    ),
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
        if status["date_done"]:
            typer.echo(f"   Completed: {status['date_done']}")
        if status["traceback"]:
            typer.echo(f"   Error: {status['traceback']}")

    except ImportError:
        typer.echo("❌ Celery not available")
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Failed to get task status: {e}")
        raise typer.Exit(1)


@app.command()
def schedule_ingest(
    limit: Optional[int] = typer.Option(
        None, help="Maximum number of articles to fetch"
    ),
    hours: int = typer.Option(4, help="Hours back to look for articles"),
) -> None:
    """Schedule an immediate article ingestion task."""
    typer.echo("📅 Scheduling article ingestion task...")

    try:
        from crypto_newsletter.core.scheduling.tasks import manual_ingest

        result = manual_ingest.delay(limit=limit, hours_back=hours)

        typer.echo("✅ Task scheduled successfully!")
        typer.echo(f"   Task ID: {result.id}")
        typer.echo(f"   Status: {result.status}")
        typer.echo(f"   Use 'task-status {result.id}' to check progress")

    except ImportError:
        typer.echo("❌ Celery not available")
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Failed to schedule task: {e}")
        raise typer.Exit(1)


@app.command()
def batch_analyze(
    force: bool = typer.Option(
        False, help="Force processing even with budget constraints"
    ),
) -> None:
    """Initiate batch processing of unanalyzed articles."""
    typer.echo("🔬 Initiating batch article analysis...")

    try:
        from crypto_newsletter.newsletter.batch.tasks import initiate_batch_processing

        result = initiate_batch_processing.delay(force_processing=force)

        typer.echo("✅ Batch processing initiated successfully!")
        typer.echo(f"   Task ID: {result.id}")
        typer.echo(f"   Status: {result.status}")
        typer.echo(f"   Force processing: {force}")
        typer.echo(f"   Use 'task-status {result.id}' to check progress")

    except ImportError:
        typer.echo("❌ Celery not available. Install with: uv add celery[redis]")
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Failed to initiate batch processing: {e}")
        raise typer.Exit(1)


# Database Management Commands
@app.command()
def db_status() -> None:
    """Check database connection and basic statistics."""
    console.print("🗄️  [bold blue]Checking database status...[/bold blue]")

    async def _db_status():
        try:
            from crypto_newsletter.core.storage.repository import ArticleRepository
            from crypto_newsletter.shared.database.connection import get_db_session

            async with get_db_session() as db:
                repo = ArticleRepository(db)
                stats = await repo.get_article_statistics()

                # Create a rich table for database stats
                table = Table(title="Database Statistics")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")

                table.add_row("Total Articles", str(stats["total_articles"]))
                table.add_row("Recent (24h)", str(stats["recent_articles_24h"]))
                table.add_row("Last Updated", stats["last_updated"])

                console.print(table)

                if stats["top_publishers"]:
                    console.print("\n🏢 [bold]Top Publishers:[/bold]")
                    for pub in stats["top_publishers"][:3]:
                        console.print(
                            f"   • {pub['publisher']}: {pub['count']} articles"
                        )

                console.print(
                    "\n✅ [bold green]Database connection successful![/bold green]"
                )

        except Exception as e:
            console.print(f"❌ [bold red]Database connection failed:[/bold red] {e}")
            raise typer.Exit(1)

    asyncio.run(_db_status())


@app.command()
def db_cleanup(
    days: int = typer.Option(30, help="Delete articles older than N days"),
    dry_run: bool = typer.Option(
        True, help="Show what would be deleted without actually deleting"
    ),
) -> None:
    """Clean up old articles from the database."""
    if dry_run:
        console.print(
            f"🧹 [bold yellow]DRY RUN:[/bold yellow] Checking articles older than {days} days..."
        )
    else:
        console.print(
            f"🧹 [bold red]DELETING[/bold red] articles older than {days} days..."
        )

    async def _cleanup():
        try:
            from crypto_newsletter.core.scheduling.tasks import cleanup_old_articles

            # Run cleanup task
            result = await cleanup_old_articles.apply_async(
                kwargs={"days_old": days, "dry_run": dry_run}
            ).get()

            if dry_run:
                console.print(
                    f"📊 Would delete {result.get('articles_to_delete', 0)} articles"
                )
            else:
                console.print(f"✅ Deleted {result.get('articles_deleted', 0)} articles")

        except Exception as e:
            console.print(f"❌ [bold red]Cleanup failed:[/bold red] {e}")
            raise typer.Exit(1)

    asyncio.run(_cleanup())


# Task Management Commands
@app.command()
def tasks_active() -> None:
    """Show currently active Celery tasks."""
    console.print("📋 [bold blue]Fetching active tasks...[/bold blue]")

    try:
        from crypto_newsletter.core.scheduling.tasks import get_active_tasks

        tasks = get_active_tasks()

        if not any(tasks.values()):
            console.print("✨ [bold green]No active tasks[/bold green]")
            return

        # Create table for active tasks
        table = Table(title="Active Tasks")
        table.add_column("Worker", style="cyan")
        table.add_column("Task", style="yellow")
        table.add_column("Status", style="green")

        for worker, worker_tasks in tasks.get("active", {}).items():
            for task in worker_tasks:
                table.add_row(worker, task.get("name", "Unknown"), "Running")

        console.print(table)

    except ImportError:
        console.print("❌ [bold red]Celery not available[/bold red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"❌ [bold red]Failed to get active tasks:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def task_cancel(task_id: str) -> None:
    """Cancel a specific Celery task."""
    console.print(f"🛑 [bold yellow]Cancelling task:[/bold yellow] {task_id}")

    try:
        from crypto_newsletter.core.scheduling.tasks import cancel_task

        success = cancel_task(task_id)

        if success:
            console.print("✅ [bold green]Task cancelled successfully[/bold green]")
        else:
            console.print("❌ [bold red]Failed to cancel task[/bold red]")
            raise typer.Exit(1)

    except ImportError:
        console.print("❌ [bold red]Celery not available[/bold red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"❌ [bold red]Failed to cancel task:[/bold red] {e}")
        raise typer.Exit(1)


# Configuration Commands
@app.command()
def config_show() -> None:
    """Show current configuration settings."""
    console.print("⚙️  [bold blue]Current Configuration:[/bold blue]")

    try:
        settings = get_settings()

        # Create configuration table
        table = Table(title="Application Settings")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Source", style="yellow")

        # Environment settings
        table.add_row(
            "Environment", settings.railway_environment, "RAILWAY_ENVIRONMENT"
        )
        table.add_row("Service Type", settings.service_type, "SERVICE_TYPE")
        table.add_row("Debug Mode", str(settings.debug), "DEBUG")

        # Database
        db_url = settings.database_url
        if len(db_url) > 50:
            db_url = db_url[:47] + "..."
        table.add_row("Database URL", db_url, "DATABASE_URL")

        # Redis
        redis_url = settings.redis_url
        if len(redis_url) > 50:
            redis_url = redis_url[:47] + "..."
        table.add_row("Redis URL", redis_url, "REDIS_URL")

        # API
        table.add_row(
            "CoinDesk Base URL", settings.coindesk_base_url, "COINDESK_BASE_URL"
        )
        api_key = (
            "***" + settings.coindesk_api_key[-4:]
            if settings.coindesk_api_key
            else "Not set"
        )
        table.add_row("CoinDesk API Key", api_key, "COINDESK_API_KEY")

        # Celery
        table.add_row("Celery Enabled", str(settings.enable_celery), "ENABLE_CELERY")

        console.print(table)

    except Exception as e:
        console.print(f"❌ [bold red]Failed to load configuration:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def config_test() -> None:
    """Test configuration and external connections."""
    console.print("🧪 [bold blue]Testing configuration...[/bold blue]")

    async def _test_config():
        settings = get_settings()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Test database connection
            task1 = progress.add_task("Testing database connection...", total=None)
            try:
                from crypto_newsletter.shared.database.connection import get_db_session

                async with get_db_session() as db:
                    await db.execute("SELECT 1")
                progress.update(task1, description="✅ Database connection: OK")
            except Exception as e:
                progress.update(
                    task1, description=f"❌ Database connection: FAILED - {e}"
                )

            # Test Redis connection
            task2 = progress.add_task("Testing Redis connection...", total=None)
            try:
                import redis

                r = redis.from_url(settings.redis_url)
                r.ping()
                progress.update(task2, description="✅ Redis connection: OK")
            except Exception as e:
                progress.update(task2, description=f"❌ Redis connection: FAILED - {e}")

            # Test CoinDesk API
            task3 = progress.add_task("Testing CoinDesk API...", total=None)
            try:
                from crypto_newsletter.core.ingestion.coindesk_client import (
                    CoinDeskAPIClient,
                )

                client = CoinDeskAPIClient()
                # Test with minimal request
                await client.fetch_articles(limit=1)
                progress.update(task3, description="✅ CoinDesk API: OK")
            except Exception as e:
                progress.update(task3, description=f"❌ CoinDesk API: FAILED - {e}")

    asyncio.run(_test_config())


# Development Commands
@app.command()
def dev_setup() -> None:
    """Set up development environment."""
    console.print("🔧 [bold blue]Setting up development environment...[/bold blue]")

    # Check for required files
    required_files = [".env.development", "pyproject.toml"]
    missing_files = []

    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)

    if missing_files:
        console.print(
            f"❌ [bold red]Missing required files:[/bold red] {', '.join(missing_files)}"
        )
        console.print("Please ensure you have the required configuration files.")
        raise typer.Exit(1)

    console.print("✅ [bold green]Development environment ready![/bold green]")
    console.print("\n📋 [bold]Next steps:[/bold]")
    console.print("1. Start Redis: [cyan]redis-server[/cyan]")
    console.print(
        "2. Start worker: [cyan]python -m crypto_newsletter.cli.main worker[/cyan]"
    )
    console.print(
        "3. Start beat: [cyan]python -m crypto_newsletter.cli.main beat[/cyan]"
    )
    console.print(
        "4. Start web: [cyan]python -m crypto_newsletter.cli.main serve --dev[/cyan]"
    )


@app.command()
def dev_reset() -> None:
    """Reset development environment (clear caches, etc.)."""
    console.print("🔄 [bold yellow]Resetting development environment...[/bold yellow]")

    try:
        # Clear Redis cache
        settings = get_settings()
        import redis

        r = redis.from_url(settings.redis_url)
        r.flushdb()
        console.print("✅ Cleared Redis cache")

        # Clear any temporary files
        temp_files = [".celerybeat-schedule", "celerybeat.pid"]
        for file in temp_files:
            if Path(file).exists():
                Path(file).unlink()
                console.print(f"✅ Removed {file}")

        console.print(
            "✅ [bold green]Development environment reset complete![/bold green]"
        )

    except Exception as e:
        console.print(f"❌ [bold red]Reset failed:[/bold red] {e}")
        raise typer.Exit(1)


# Monitoring Commands
@app.command()
def monitor() -> None:
    """Start real-time monitoring dashboard."""
    console.print("📊 [bold blue]Starting monitoring dashboard...[/bold blue]")

    async def _monitor():
        try:
            while True:
                # Clear screen
                console.clear()

                # Header
                console.print(
                    Panel.fit(
                        "[bold blue]Crypto Newsletter - Live Monitor[/bold blue]",
                        border_style="blue",
                    )
                )

                # System status
                console.print("\n🔍 [bold]System Status:[/bold]")

                # Database stats
                try:
                    from crypto_newsletter.core.storage.repository import (
                        ArticleRepository,
                    )
                    from crypto_newsletter.shared.database.connection import (
                        get_db_session,
                    )

                    async with get_db_session() as db:
                        repo = ArticleRepository(db)
                        stats = await repo.get_article_statistics()

                        console.print(
                            f"📊 Articles: {stats['total_articles']} total, {stats['recent_articles_24h']} recent"
                        )
                except Exception as e:
                    console.print(f"❌ Database: {e}")

                # Task status
                try:
                    from crypto_newsletter.core.scheduling.tasks import get_active_tasks

                    tasks = get_active_tasks()
                    active_count = sum(
                        len(worker_tasks)
                        for worker_tasks in tasks.get("active", {}).values()
                    )
                    console.print(f"⚙️  Active Tasks: {active_count}")
                except Exception as e:
                    console.print(f"❌ Tasks: {e}")

                console.print(
                    f"\n⏰ Last updated: {datetime.now().strftime('%H:%M:%S')}"
                )
                console.print("Press Ctrl+C to exit")

                # Wait 5 seconds
                await asyncio.sleep(5)

        except KeyboardInterrupt:
            console.print("\n👋 [bold green]Monitoring stopped[/bold green]")

    asyncio.run(_monitor())


@app.command()
def logs(
    service: str = typer.Option(
        "all", help="Service to show logs for (web/worker/beat/all)"
    ),
    lines: int = typer.Option(50, help="Number of lines to show"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
) -> None:
    """Show application logs."""
    console.print(f"📋 [bold blue]Showing logs for {service}...[/bold blue]")

    # This would integrate with your logging system
    # For now, show a placeholder
    console.print(f"📝 Last {lines} lines for {service} service:")
    console.print("(Log integration would be implemented here)")

    if follow:
        console.print("Following logs... Press Ctrl+C to exit")
        try:
            while True:
                # In a real implementation, this would tail the logs
                asyncio.sleep(1)
        except KeyboardInterrupt:
            console.print("\n👋 [bold green]Log following stopped[/bold green]")


# Utility Commands
@app.command()
def shell() -> None:
    """Start an interactive Python shell with app context."""
    console.print("🐍 [bold blue]Starting interactive shell...[/bold blue]")

    try:
        import IPython
        from crypto_newsletter.shared.config.settings import get_settings
        from crypto_newsletter.shared.database.connection import get_db_session

        # Set up shell context
        context = {
            "settings": get_settings(),
            "get_db_session": get_db_session,
        }

        console.print("Available objects: settings, get_db_session")
        IPython.start_ipython(argv=[], user_ns=context)

    except ImportError:
        console.print("❌ IPython not available. Install with: uv add ipython")
        raise typer.Exit(1)


@app.command()
def export_data(
    output: str = typer.Option("articles.json", help="Output file path"),
    format: str = typer.Option("json", help="Export format (json/csv)"),
    days: int = typer.Option(7, help="Days of data to export"),
) -> None:
    """Export article data to file."""
    console.print(
        f"📤 [bold blue]Exporting {days} days of data to {output}...[/bold blue]"
    )

    async def _export():
        try:
            import csv
            import json

            from crypto_newsletter.core.storage.repository import ArticleRepository
            from crypto_newsletter.shared.database.connection import get_db_session

            async with get_db_session() as db:
                repo = ArticleRepository(db)
                articles = await repo.get_recent_articles(hours=days * 24, limit=1000)

                # Convert to dict format
                data = []
                for article in articles:
                    data.append(
                        {
                            "id": article.id,
                            "title": article.title,
                            "url": article.url,
                            "published_on": article.published_on.isoformat()
                            if article.published_on
                            else None,
                            "publisher_id": article.publisher_id,
                        }
                    )

                # Export based on format
                if format.lower() == "json":
                    with open(output, "w") as f:
                        json.dump(data, f, indent=2)
                elif format.lower() == "csv":
                    with open(output, "w", newline="") as f:
                        if data:
                            writer = csv.DictWriter(f, fieldnames=data[0].keys())
                            writer.writeheader()
                            writer.writerows(data)

                console.print(
                    f"✅ [bold green]Exported {len(data)} articles to {output}[/bold green]"
                )

        except Exception as e:
            console.print(f"❌ [bold red]Export failed:[/bold red] {e}")
            raise typer.Exit(1)

    asyncio.run(_export())


# Help and Information Commands
@app.command()
def commands() -> None:
    """Show all available commands with descriptions."""
    console.print("📋 [bold blue]Available Commands:[/bold blue]")

    # Create command categories
    categories = {
        "🔍 Health & Monitoring": [
            ("health", "Check pipeline health"),
            ("test", "Run quick pipeline test"),
            ("monitor", "Start real-time monitoring"),
            ("logs", "Show application logs"),
        ],
        "📊 Data Management": [
            ("ingest", "Manual article ingestion"),
            ("schedule-ingest", "Schedule ingestion task"),
            ("stats", "Show article statistics"),
            ("db-status", "Check database status"),
            ("db-cleanup", "Clean up old articles"),
        ],
        "⚙️ Task Management": [
            ("tasks-active", "Show active tasks"),
            ("task-status", "Get task status"),
            ("task-cancel", "Cancel a task"),
        ],
        "🔧 Services": [
            ("serve", "Start web service"),
            ("worker", "Start Celery worker"),
            ("beat", "Start Celery beat"),
            ("flower", "Start Flower monitoring"),
        ],
        "⚙️ Configuration": [
            ("config-show", "Show configuration"),
            ("config-test", "Test configuration"),
        ],
        "🛠️ Development": [
            ("dev-setup", "Setup dev environment"),
            ("dev-reset", "Reset dev environment"),
            ("shell", "Interactive shell"),
        ],
        "📤 Utilities": [
            ("export-data", "Export article data"),
            ("version", "Show version info"),
        ],
    }

    for category, commands in categories.items():
        console.print(f"\n{category}")
        for cmd, desc in commands:
            console.print(f"  [cyan]{cmd:<20}[/cyan] {desc}")

    console.print(
        "\n💡 [bold]Usage:[/bold] python -m crypto_newsletter.cli.main [cyan]<command>[/cyan] [yellow]--help[/yellow]"
    )
    console.print(
        "📖 [bold]Example:[/bold] python -m crypto_newsletter.cli.main [cyan]health[/cyan]"
    )


def main() -> None:
    """Main entry point for the CLI application."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n👋 [bold yellow]Interrupted by user[/bold yellow]")
        raise typer.Exit(0)
    except Exception as e:
        console.print(f"\n❌ [bold red]Unexpected error:[/bold red] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    main()
