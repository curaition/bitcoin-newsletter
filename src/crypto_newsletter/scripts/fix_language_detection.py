#!/usr/bin/env python3
"""
Script to fix language detection issues in existing articles.

This script will:
1. Scan all articles in the database
2. Detect actual language from title and body content
3. Update articles with incorrect language detection
4. Optionally remove non-English articles
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from loguru import logger
from sqlalchemy import select, update

from crypto_newsletter.shared.database.connection import get_db_session
from crypto_newsletter.shared.models import Article
from crypto_newsletter.shared.utils.language_detection import (
    detect_language_from_content,
    is_english_content
)


async def scan_and_fix_languages(dry_run: bool = True, remove_non_english: bool = False):
    """
    Scan all articles and fix language detection issues.
    
    Args:
        dry_run: If True, only report issues without making changes
        remove_non_english: If True, delete non-English articles
    """
    logger.info("Starting language detection fix...")
    
    async with get_db_session() as db:
        # Get all articles
        query = select(Article).where(Article.status == 'ACTIVE')
        result = await db.execute(query)
        articles = result.scalars().all()
        
        logger.info(f"Found {len(articles)} active articles to check")
        
        issues_found = 0
        fixed_count = 0
        removed_count = 0
        
        for article in articles:
            # Detect actual language
            detected_lang = detect_language_from_content(
                article.title or '', 
                article.body or ''
            )
            
            # Check if there's a mismatch
            if article.language != detected_lang:
                issues_found += 1
                logger.warning(
                    f"Article {article.id}: Language mismatch - "
                    f"DB: {article.language}, Detected: {detected_lang}"
                )
                logger.info(f"  Title: {article.title[:100]}...")
                
                if not dry_run:
                    if remove_non_english and detected_lang != 'EN':
                        # Remove non-English article
                        article.status = 'DELETED'
                        removed_count += 1
                        logger.info(f"  -> Marked for deletion (non-English)")
                    else:
                        # Update language
                        article.language = detected_lang
                        fixed_count += 1
                        logger.info(f"  -> Updated language to {detected_lang}")
        
        if not dry_run:
            await db.commit()
            logger.info(f"Changes committed to database")
        
        # Summary
        logger.info("=" * 60)
        logger.info("LANGUAGE DETECTION FIX SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total articles checked: {len(articles)}")
        logger.info(f"Language issues found: {issues_found}")
        
        if dry_run:
            logger.info("DRY RUN - No changes made")
        else:
            logger.info(f"Articles fixed: {fixed_count}")
            logger.info(f"Articles removed: {removed_count}")


async def get_language_statistics():
    """Get current language statistics from the database."""
    logger.info("Getting language statistics...")
    
    async with get_db_session() as db:
        query = select(Article).where(Article.status == 'ACTIVE')
        result = await db.execute(query)
        articles = result.scalars().all()
        
        # Count by database language field
        db_lang_counts = {}
        # Count by detected language
        detected_lang_counts = {}
        
        for article in articles:
            # Database language
            db_lang = article.language or 'NULL'
            db_lang_counts[db_lang] = db_lang_counts.get(db_lang, 0) + 1
            
            # Detected language
            detected_lang = detect_language_from_content(
                article.title or '', 
                article.body or ''
            )
            detected_lang_counts[detected_lang] = detected_lang_counts.get(detected_lang, 0) + 1
        
        logger.info("=" * 60)
        logger.info("LANGUAGE STATISTICS")
        logger.info("=" * 60)
        logger.info("Database Language Field:")
        for lang, count in sorted(db_lang_counts.items()):
            logger.info(f"  {lang}: {count}")
        
        logger.info("\nDetected from Content:")
        for lang, count in sorted(detected_lang_counts.items()):
            logger.info(f"  {lang}: {count}")


async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix language detection issues")
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Only report issues without making changes"
    )
    parser.add_argument(
        "--remove-non-english", 
        action="store_true", 
        help="Remove non-English articles instead of updating language"
    )
    parser.add_argument(
        "--stats-only", 
        action="store_true", 
        help="Only show language statistics"
    )
    
    args = parser.parse_args()
    
    if args.stats_only:
        await get_language_statistics()
    else:
        await scan_and_fix_languages(
            dry_run=args.dry_run,
            remove_non_english=args.remove_non_english
        )


if __name__ == "__main__":
    asyncio.run(main())
