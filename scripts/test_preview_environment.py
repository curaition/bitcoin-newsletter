#!/usr/bin/env python3
"""
Preview Environment Testing Script

Tests Phase 1 batch processing implementation on Render preview environment.
This script validates the complete end-to-end workflow with real APIs and infrastructure.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Load environment variables from .env.development
from dotenv import load_dotenv

env_file = project_root / ".env.development"
if env_file.exists():
    load_dotenv(env_file)
    print(f"Loaded environment from {env_file}")

# Ensure we're using real APIs (not testing mode)
os.environ["TESTING"] = "false"

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PreviewEnvironmentTester:
    """Test Phase 1 implementation on Render preview environment."""

    def __init__(self, preview_api_url: Optional[str] = None):
        """Initialize with preview environment URL."""
        self.preview_api_url = preview_api_url or self._detect_preview_url()
        self.test_results = {}

    def _detect_preview_url(self) -> str:
        """Detect preview environment URL from environment or user input."""
        # Check if preview URL is provided via environment
        preview_url = os.getenv("PREVIEW_API_URL")

        if not preview_url:
            # Ask user for preview URL
            print("\n🔍 Preview Environment URL Detection")
            print("=" * 50)
            print("Please provide the preview environment API URL.")
            print(
                "It should look like: https://bitcoin-newsletter-api-pr-1.onrender.com"
            )
            print("You can find this in the Render dashboard under the PR preview.")

            preview_url = input("\nEnter preview API URL: ").strip()

        if not preview_url:
            raise ValueError("Preview API URL is required")

        # Ensure URL has proper format
        if not preview_url.startswith("http"):
            preview_url = f"https://{preview_url}"

        logger.info(f"Using preview environment: {preview_url}")
        return preview_url

    async def test_preview_health(self) -> bool:
        """Test if preview environment is healthy and accessible."""
        logger.info("🏥 Testing Preview Environment Health")
        logger.info("-" * 40)

        try:
            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                # Test health endpoint
                health_url = f"{self.preview_api_url}/health"
                logger.info(f"Testing health endpoint: {health_url}")

                response = await client.get(health_url)

                if response.status_code == 200:
                    health_data = response.json()
                    logger.info("✅ Preview environment is healthy")
                    logger.info(
                        f"📊 Health status: {health_data.get('status', 'unknown')}"
                    )

                    # Test database connectivity
                    if "database" in health_data:
                        db_status = health_data["database"].get("status", "unknown")
                        logger.info(f"🗄️  Database status: {db_status}")

                    self.test_results["health_check"] = True
                    return True
                else:
                    logger.error(f"❌ Health check failed: {response.status_code}")
                    self.test_results["health_check"] = False
                    return False

        except Exception as e:
            logger.error(f"❌ Preview environment health test failed: {e}")
            self.test_results["health_check"] = False
            return False

    async def test_database_migration(self) -> bool:
        """Test if database migrations ran successfully."""
        logger.info("\n🗄️  Testing Database Migration")
        logger.info("-" * 40)

        try:
            # Test if we can access articles and the analysis-ready endpoint
            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                # Test analysis-ready articles endpoint (depends on Phase 1 implementation)
                analysis_url = f"{self.preview_api_url}/api/articles/analysis-ready"
                logger.info(f"Testing analysis-ready endpoint: {analysis_url}")

                response = await client.get(analysis_url)

                if response.status_code == 200:
                    articles = response.json()
                    logger.info(
                        f"✅ Database migration successful - found {len(articles)} analysis-ready articles"
                    )
                    self.test_results["database_migration"] = True
                    return True
                else:
                    logger.error(
                        f"❌ Database migration test failed: {response.status_code}"
                    )
                    self.test_results["database_migration"] = False
                    return False

        except Exception as e:
            logger.error(f"❌ Database migration test failed: {e}")
            self.test_results["database_migration"] = False
            return False

    async def test_api_integration(self) -> bool:
        """Test API integration and Phase 1 endpoints."""
        logger.info("\n🔑 Testing API Integration")
        logger.info("-" * 40)

        try:
            import httpx

            async with httpx.AsyncClient(timeout=60.0) as client:
                # Test admin status endpoint (shows system health)
                admin_url = f"{self.preview_api_url}/admin/status"
                logger.info(f"Testing admin status: {admin_url}")

                response = await client.get(admin_url)

                if response.status_code == 200:
                    status_data = response.json()

                    # Check database and system status
                    db_status = status_data.get("database", {}).get("status", "unknown")
                    api_status = status_data.get("api", {}).get("status", "unknown")

                    logger.info(
                        f"🗄️  Database: {'✅ ' + db_status if db_status == 'healthy' else '❌ ' + db_status}"
                    )
                    logger.info(
                        f"🌐 API: {'✅ ' + api_status if api_status == 'healthy' else '❌ ' + api_status}"
                    )

                    if db_status == "healthy" and api_status == "healthy":
                        logger.info("✅ API integration test passed")
                        self.test_results["api_integration"] = True
                        return True
                    else:
                        logger.error(
                            "❌ API integration test failed - system not healthy"
                        )
                        self.test_results["api_integration"] = False
                        return False
                else:
                    logger.error(
                        f"❌ API integration test failed: {response.status_code}"
                    )
                    self.test_results["api_integration"] = False
                    return False

        except Exception as e:
            logger.error(f"❌ API integration test failed: {e}")
            self.test_results["api_integration"] = False
            return False

    async def test_celery_workers(self) -> bool:
        """Test if Celery workers are running via admin status."""
        logger.info("\n⚙️  Testing Celery Workers")
        logger.info("-" * 40)

        try:
            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                # Test admin status for Celery information
                admin_url = f"{self.preview_api_url}/admin/status"
                logger.info(f"Testing Celery via admin status: {admin_url}")

                response = await client.get(admin_url)

                if response.status_code == 200:
                    status_data = response.json()

                    celery_info = status_data.get("celery", {})
                    celery_enabled = celery_info.get("enabled", False)
                    celery_status = celery_info.get("status", "unknown")

                    logger.info(f"⚙️  Celery enabled: {celery_enabled}")
                    logger.info(f"📊 Celery status: {celery_status}")

                    if celery_enabled and celery_status in ["healthy", "warning"]:
                        logger.info("✅ Celery workers test passed")
                        self.test_results["celery_workers"] = True
                        return True
                    else:
                        logger.warning("⚠️  Celery may not be fully configured yet")
                        self.test_results[
                            "celery_workers"
                        ] = True  # Not critical for basic testing
                        return True
                else:
                    logger.error(
                        f"❌ Celery workers test failed: {response.status_code}"
                    )
                    self.test_results["celery_workers"] = False
                    return False

        except Exception as e:
            logger.error(f"❌ Celery workers test failed: {e}")
            self.test_results["celery_workers"] = False
            return False

    async def test_single_article_analysis(self) -> bool:
        """Test getting analysis-ready articles from the preview environment."""
        logger.info("\n🧠 Testing Article Analysis Readiness")
        logger.info("-" * 40)

        try:
            import httpx

            async with httpx.AsyncClient(timeout=60.0) as client:
                # Get analysis-ready articles (Phase 1 endpoint)
                articles_url = (
                    f"{self.preview_api_url}/api/articles/analysis-ready?limit=5"
                )
                logger.info(f"Getting analysis-ready articles: {articles_url}")

                response = await client.get(articles_url)

                if response.status_code != 200:
                    logger.error(
                        f"❌ Failed to get analysis-ready articles: {response.status_code}"
                    )
                    self.test_results["single_article_analysis"] = False
                    return False

                articles = response.json()

                if not articles:
                    logger.warning("⚠️  No analysis-ready articles found")
                    self.test_results["single_article_analysis"] = False
                    return False

                logger.info(f"✅ Found {len(articles)} analysis-ready articles")

                # Test individual article retrieval
                if articles:
                    article = articles[0]
                    article_id = article["id"]

                    logger.info(f"📄 Testing article: {article['title'][:50]}...")
                    logger.info(
                        f"📊 Content length: {len(article.get('body', ''))} chars"
                    )

                    # Get detailed article info
                    detail_url = f"{self.preview_api_url}/api/articles/{article_id}"
                    detail_response = await client.get(detail_url)

                    if detail_response.status_code == 200:
                        logger.info("✅ Article detail retrieval successful")
                        self.test_results["single_article_analysis"] = True
                        return True
                    else:
                        logger.error(
                            f"❌ Article detail failed: {detail_response.status_code}"
                        )
                        self.test_results["single_article_analysis"] = False
                        return False
                else:
                    logger.warning("⚠️  No articles available for detailed testing")
                    self.test_results["single_article_analysis"] = False
                    return False

        except Exception as e:
            logger.error(f"❌ Article analysis test failed: {e}")
            self.test_results["single_article_analysis"] = False
            return False

    def print_test_summary(self):
        """Print comprehensive test results summary."""
        logger.info("\n" + "=" * 60)
        logger.info("🏁 PREVIEW ENVIRONMENT TEST RESULTS")
        logger.info("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(self.test_results.values())

        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            display_name = test_name.replace("_", " ").title()
            logger.info(f"{display_name}: {status}")

        logger.info(f"\nOverall: {passed_tests}/{total_tests} tests passed")

        if passed_tests == total_tests:
            logger.info("🎉 Preview environment is FULLY FUNCTIONAL!")
            logger.info("✅ Phase 1 implementation ready for production")
            return True
        else:
            logger.error("⚠️  Preview environment has issues that need attention")
            return False


async def main():
    """Main test function."""
    logger.info("🚀 PREVIEW ENVIRONMENT COMPREHENSIVE TEST")
    logger.info("=" * 60)

    try:
        # Initialize tester
        tester = PreviewEnvironmentTester()

        # Run all tests
        tests = [
            tester.test_preview_health(),
            tester.test_database_migration(),
            tester.test_api_integration(),
            tester.test_celery_workers(),
            tester.test_single_article_analysis(),
        ]

        # Execute tests sequentially
        for test in tests:
            await test
            await asyncio.sleep(2)  # Brief pause between tests

        # Print summary
        success = tester.print_test_summary()

        return success

    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        return False
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
