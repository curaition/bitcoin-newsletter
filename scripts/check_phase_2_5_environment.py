#!/usr/bin/env python3
"""
Phase 2.5 Environment Check Script

Validates that the local environment is properly configured for real-world testing
of the Bitcoin Newsletter Signal Analysis system.

Usage:
    python scripts/check_phase_2_5_environment.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Load environment variables from .env.development
from dotenv import load_dotenv

env_file = Path(__file__).parent.parent / ".env.development"
if env_file.exists():
    load_dotenv(env_file)
    print(f"📁 Loaded environment from: {env_file}")
else:
    print("⚠️  .env.development file not found")

print("🔧 Phase 2.5 Environment Check")
print("=" * 50)


def check_environment_variables():
    """Check required environment variables."""
    print("\n1. 🔑 Environment Variables")
    print("-" * 30)

    required_vars = {
        "DATABASE_URL": "Neon PostgreSQL connection",
        "GEMINI_API_KEY": "Google Gemini API access",
        "TAVILY_API_KEY": "Tavily search API access",
    }

    optional_vars = {
        "TESTING": 'Should be "false" for real-world testing',
        "CONTENT_ANALYSIS_AGENT_MODEL": "Gemini model for content analysis",
        "SIGNAL_VALIDATION_AGENT_MODEL": "Gemini model for signal validation",
    }

    all_good = True

    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "KEY" in var or "URL" in var:
                masked = f"{value[:10]}...{value[-4:]}" if len(value) > 14 else "***"
                print(f"✅ {var}: {masked} ({description})")
            else:
                print(f"✅ {var}: {value} ({description})")
        else:
            print(f"❌ {var}: Missing ({description})")
            all_good = False

    print("\nOptional variables:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value} ({description})")
        else:
            print(f"⚠️  {var}: Not set ({description})")

    return all_good


async def check_database_connection():
    """Check database connectivity."""
    print("\n2. 🗄️  Database Connection")
    print("-" * 30)

    try:
        from crypto_newsletter.shared.database.connection import get_db_session
        from crypto_newsletter.shared.models.models import Article
        from sqlalchemy import func, select

        async with get_db_session() as db:
            # Test basic connectivity
            result = await db.execute(select(func.count(Article.id)))
            total_articles = result.scalar()

            # Test analysis-ready articles query
            analysis_ready_result = await db.execute(
                select(func.count(Article.id)).where(
                    Article.status == "ACTIVE",
                    func.length(Article.body) >= 2000,
                    Article.body.is_not(None),
                )
            )
            analysis_ready = analysis_ready_result.scalar()

            print("✅ Database connection successful")
            print(f"✅ Total articles: {total_articles:,}")
            print(f"✅ Analysis-ready articles: {analysis_ready:,}")

            if analysis_ready < 5:
                print("⚠️  Warning: Less than 5 analysis-ready articles available")
                return False

            return True

    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False


async def check_analysis_agents():
    """Check analysis agent imports and configuration."""
    print("\n3. 🤖 Analysis Agents")
    print("-" * 30)

    try:
        # Import analysis components
        from crypto_newsletter.analysis.agents.settings import analysis_settings

        print("✅ Analysis agents imported successfully")

        # Check settings
        print(f"✅ Testing mode: {analysis_settings.testing}")
        print(f"✅ Content analysis model: {analysis_settings.content_analysis_model}")
        print(f"✅ Signal validation model: {analysis_settings.signal_validation_model}")

        if analysis_settings.testing:
            print("⚠️  Warning: TESTING=true - will use TestModel instead of real APIs")
            return False

        # Check API keys in settings
        if not analysis_settings.gemini_api_key:
            print("❌ Gemini API key not available in settings")
            return False

        if not analysis_settings.tavily_api_key:
            print("❌ Tavily API key not available in settings")
            return False

        print("✅ API keys configured in analysis settings")
        return True

    except Exception as e:
        print(f"❌ Analysis agent check failed: {str(e)}")
        return False


async def check_model_providers():
    """Check model provider configuration."""
    print("\n4. 🧠 Model Providers")
    print("-" * 30)

    try:
        from crypto_newsletter.analysis.agents.providers import (
            get_content_analysis_model,
            get_signal_validation_model,
        )

        # Test model creation (without actually calling the models)
        content_model = get_content_analysis_model()
        validation_model = get_signal_validation_model()

        print(f"✅ Content analysis model: {type(content_model).__name__}")
        print(f"✅ Signal validation model: {type(validation_model).__name__}")

        # Check if we're using real models
        from pydantic_ai.models.test import TestModel

        if isinstance(content_model, TestModel):
            print("⚠️  Warning: Using TestModel for content analysis")
            return False

        if isinstance(validation_model, TestModel):
            print("⚠️  Warning: Using TestModel for signal validation")
            return False

        print("✅ Using real API models (not TestModel)")
        return True

    except Exception as e:
        print(f"❌ Model provider check failed: {str(e)}")
        return False


def check_dependencies():
    """Check Python dependencies."""
    print("\n5. 📦 Dependencies")
    print("-" * 30)

    required_packages = [
        ("pydantic_ai", "PydanticAI framework"),
        ("sqlalchemy", "Database ORM"),
        ("asyncpg", "PostgreSQL async driver"),
        ("tavily", "Tavily API client"),
    ]

    all_good = True

    for package, description in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}: Available ({description})")
        except ImportError:
            print(f"❌ {package}: Missing ({description})")
            all_good = False

    # Check PydanticAI version
    try:
        import pydantic_ai

        version = pydantic_ai.__version__
        print(f"✅ PydanticAI version: {version}")

        # Check if it's the expected version
        if not version.startswith("0.7"):
            print(f"⚠️  Warning: Expected PydanticAI 0.7.x, got {version}")
    except:
        pass

    return all_good


async def main():
    """Run all environment checks."""
    print("Checking Phase 2.5 environment configuration...\n")

    checks = [
        ("Environment Variables", check_environment_variables()),
        ("Database Connection", await check_database_connection()),
        ("Analysis Agents", await check_analysis_agents()),
        ("Model Providers", await check_model_providers()),
        ("Dependencies", check_dependencies()),
    ]

    print("\n" + "=" * 50)
    print("📋 ENVIRONMENT CHECK SUMMARY")
    print("=" * 50)

    all_passed = True
    for check_name, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name:<25} {status}")
        if not result:
            all_passed = False

    print("\n" + "=" * 50)

    if all_passed:
        print("🎉 Environment is ready for Phase 2.5 testing!")
        print("\nNext steps:")
        print("1. Run: python scripts/select_test_articles.py --recommend")
        print(
            "2. Run: python scripts/phase_2_5_real_world_testing.py --select-articles"
        )
    else:
        print("❌ Environment issues detected. Please fix the above problems.")
        print("\nCommon fixes:")
        print("• Check .env.development file has all required variables")
        print("• Ensure TESTING=false for real-world testing")
        print("• Verify API keys are valid and not expired")
        print("• Check database connection string is correct")

    return all_passed


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
