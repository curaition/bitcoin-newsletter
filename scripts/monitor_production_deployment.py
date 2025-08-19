#!/usr/bin/env python3
"""
Production Deployment Monitor

Monitors the Phase 1 production deployment and validates all systems
are working correctly after deployment completes.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ProductionDeploymentMonitor:
    """Monitor and validate Phase 1 production deployment."""

    def __init__(self):
        """Initialize production monitoring."""
        self.production_api_url = "https://bitcoin-newsletter-api.onrender.com"
        self.production_admin_url = "https://bitcoin-newsletter-admin.onrender.com"
        self.deployment_status = {}

    async def check_deployment_status(self) -> bool:
        """Check if all services have completed deployment."""
        logger.info("🔍 Checking production deployment status...")

        # In a real implementation, we would use Render MCP tools here
        # For now, we'll test the endpoints directly

        try:
            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                # Test production API health
                health_response = await client.get(f"{self.production_api_url}/health")

                if health_response.status_code == 200:
                    logger.info("✅ Production API is responding")
                    return True
                else:
                    logger.warning(
                        f"⚠️  Production API returned {health_response.status_code}"
                    )
                    return False

        except Exception as e:
            logger.warning(f"⚠️  Production API not ready yet: {e}")
            return False

    async def validate_phase_1_deployment(self) -> bool:
        """Validate Phase 1 implementation in production."""
        logger.info("\n🧪 Validating Phase 1 Production Deployment")
        logger.info("=" * 60)

        validation_results = {}

        try:
            import httpx

            async with httpx.AsyncClient(timeout=60.0) as client:
                # Test 1: Health Check
                logger.info("1. 🏥 Testing Production Health")
                health_response = await client.get(f"{self.production_api_url}/health")

                if health_response.status_code == 200:
                    health_data = health_response.json()
                    logger.info(f"✅ Health: {health_data.get('status', 'unknown')}")
                    validation_results["health"] = True
                else:
                    logger.error(
                        f"❌ Health check failed: {health_response.status_code}"
                    )
                    validation_results["health"] = False

                # Test 2: Database Migration
                logger.info("\n2. 🗄️  Testing Database Migration")
                analysis_response = await client.get(
                    f"{self.production_api_url}/api/articles/analysis-ready?limit=1"
                )

                if analysis_response.status_code == 200:
                    articles = analysis_response.json()
                    logger.info(
                        f"✅ Analysis-ready endpoint working, found {len(articles)} articles"
                    )
                    validation_results["database"] = True
                else:
                    logger.error(
                        f"❌ Analysis-ready endpoint failed: {analysis_response.status_code}"
                    )
                    validation_results["database"] = False

                # Test 3: Admin Status
                logger.info("\n3. ⚙️  Testing Admin Status")
                admin_response = await client.get(
                    f"{self.production_api_url}/admin/status"
                )

                if admin_response.status_code == 200:
                    admin_data = admin_response.json()
                    db_status = admin_data.get("database", {}).get("status", "unknown")
                    celery_status = admin_data.get("celery", {}).get(
                        "status", "unknown"
                    )

                    logger.info(f"✅ Database: {db_status}")
                    logger.info(f"✅ Celery: {celery_status}")
                    validation_results["admin"] = True
                else:
                    logger.error(f"❌ Admin status failed: {admin_response.status_code}")
                    validation_results["admin"] = False

                # Test 4: Frontend
                logger.info("\n4. 🖥️  Testing Admin Dashboard")
                frontend_response = await client.get(self.production_admin_url)

                if frontend_response.status_code == 200:
                    logger.info("✅ Admin dashboard is accessible")
                    validation_results["frontend"] = True
                else:
                    logger.error(
                        f"❌ Admin dashboard failed: {frontend_response.status_code}"
                    )
                    validation_results["frontend"] = False

                # Summary
                passed_tests = sum(validation_results.values())
                total_tests = len(validation_results)

                logger.info(
                    f"\n📊 Validation Results: {passed_tests}/{total_tests} tests passed"
                )

                if passed_tests == total_tests:
                    logger.info("🎉 Phase 1 production deployment SUCCESSFUL!")
                    return True
                else:
                    logger.error("⚠️  Phase 1 production deployment has issues")
                    return False

        except Exception as e:
            logger.error(f"❌ Production validation failed: {e}")
            return False

    async def monitor_deployment(self) -> bool:
        """Monitor deployment until complete, then validate."""
        logger.info("🚀 PHASE 1 PRODUCTION DEPLOYMENT MONITOR")
        logger.info("=" * 60)

        max_wait_time = 900  # 15 minutes
        check_interval = 60  # 1 minute
        elapsed_time = 0

        logger.info("⏳ Waiting for production deployment to complete...")
        logger.info("This typically takes 5-10 minutes for all services.")

        while elapsed_time < max_wait_time:
            logger.info(f"⏱️  Elapsed time: {elapsed_time // 60}m {elapsed_time % 60}s")

            # Check if deployment is complete
            deployment_ready = await self.check_deployment_status()

            if deployment_ready:
                logger.info("✅ Production deployment appears complete!")

                # Wait a bit more for all services to stabilize
                logger.info("⏳ Waiting 30 seconds for services to stabilize...")
                await asyncio.sleep(30)

                # Run validation
                validation_success = await self.validate_phase_1_deployment()
                return validation_success

            # Wait before next check
            logger.info(
                f"⏳ Deployment still in progress, checking again in {check_interval}s..."
            )
            await asyncio.sleep(check_interval)
            elapsed_time += check_interval

        logger.error("⚠️  Timeout waiting for deployment completion")
        return False


async def main():
    """Main monitoring function."""
    try:
        monitor = ProductionDeploymentMonitor()
        success = await monitor.monitor_deployment()

        if success:
            logger.info("\n🎉 PHASE 1 PRODUCTION DEPLOYMENT COMPLETE!")
            logger.info("✅ All systems validated and working correctly")
            logger.info("\n🔗 Production URLs:")
            logger.info("   🌐 API: https://bitcoin-newsletter-api.onrender.com")
            logger.info("   🖥️  Admin: https://bitcoin-newsletter-admin.onrender.com")
            logger.info("\n🎯 Next Steps:")
            logger.info("   - Phase 1 batch processing system is ready")
            logger.info("   - Can now run batch analysis on production data")
            logger.info("   - Ready to begin Phase 2 development")
            return True
        else:
            logger.error("\n⚠️  PRODUCTION DEPLOYMENT VALIDATION FAILED")
            logger.error("Please check the Render dashboard for deployment issues")
            return False

    except KeyboardInterrupt:
        logger.info("Monitoring interrupted by user")
        return False
    except Exception as e:
        logger.error(f"Monitoring failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
