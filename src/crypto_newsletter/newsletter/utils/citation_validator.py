"""Citation validation utilities for newsletter content quality."""

import re
import asyncio
from typing import Dict, List, Any
from urllib.parse import urlparse

import aiohttp
from loguru import logger


class CitationValidator:
    """Validates citations and source references in newsletter content."""

    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=10)

    def validate_citations(self, content: str) -> Dict[str, Any]:
        """
        Enhanced citation validation with multiple patterns.
        
        Args:
            content: Newsletter content to validate
            
        Returns:
            Dictionary with citation metrics and validation results
        """
        # Pattern for markdown links: [text](url)
        markdown_pattern = r'\[([^\]]+)\]\(https?://[^\)]+\)'
        
        # Pattern for inline citations: "According to [Source](url)"
        inline_pattern = r'According to \[([^\]]+)\]\(https?://[^\)]+\)'
        
        # Pattern for signal references with confidence scores
        signal_pattern = r'signal.*?\((\d+\.\d+)\)'
        
        # Pattern for institutional/market references
        institutional_pattern = r'(institutional|market|regulatory).*?signal.*?\((\d+\.\d+)\)'
        
        # Extract all URLs for validation
        url_pattern = r'https?://[^\s\)]+' 
        urls = re.findall(url_pattern, content)
        
        # Count different citation types
        markdown_citations = re.findall(markdown_pattern, content)
        inline_citations = re.findall(inline_pattern, content)
        signal_references = re.findall(signal_pattern, content, re.IGNORECASE)
        institutional_signals = re.findall(institutional_pattern, content, re.IGNORECASE)
        
        # Validate Bitcoin-specific terminology usage
        bitcoin_terms = self._count_bitcoin_terminology(content)
        
        return {
            'total_citations': len(markdown_citations),
            'inline_citations': len(inline_citations),
            'signal_references': len(signal_references),
            'institutional_signals': len(institutional_signals),
            'unique_urls': len(set(urls)),
            'bitcoin_terminology': bitcoin_terms,
            'citation_density': len(markdown_citations) / max(len(content.split()), 1) * 1000,  # per 1000 words
            'meets_minimum_citations': len(markdown_citations) >= 8,
            'urls_for_validation': list(set(urls))
        }

    def _count_bitcoin_terminology(self, content: str) -> Dict[str, int]:
        """Count usage of Bitcoin-specific terminology."""
        bitcoin_terms = {
            'bitcoin': r'\bbitcoin\b',
            'btc': r'\bBTC\b',
            'cryptocurrency': r'\bcryptocurrency\b',
            'blockchain': r'\bblockchain\b',
            'hashrate': r'\bhashrate\b',
            'mining': r'\bmining\b',
            'institutional': r'\binstitutional\b',
            'adoption': r'\badoption\b',
            'regulatory': r'\bregulatory\b',
            'defi': r'\bDeFi\b',
            'etf': r'\bETF\b',
            'custody': r'\bcustody\b'
        }
        
        term_counts = {}
        content_lower = content.lower()
        
        for term, pattern in bitcoin_terms.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            term_counts[term] = len(matches)
            
        return term_counts

    async def validate_source_urls(self, urls: List[str]) -> Dict[str, bool]:
        """
        Verify citation URLs are accessible.
        
        Args:
            urls: List of URLs to validate
            
        Returns:
            Dictionary mapping URLs to their accessibility status
        """
        if not urls:
            return {}
            
        results = {}
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            tasks = []
            for url in urls:
                if self._is_valid_url(url):
                    tasks.append(self._check_url_accessibility(session, url))
                else:
                    results[url] = False
                    
            if tasks:
                url_results = await asyncio.gather(*tasks, return_exceptions=True)
                for i, result in enumerate(url_results):
                    url = urls[i] if i < len(urls) else None
                    if url and isinstance(result, tuple):
                        results[result[0]] = result[1]
                    elif url:
                        results[url] = False
                        
        return results

    async def _check_url_accessibility(self, session: aiohttp.ClientSession, url: str) -> tuple[str, bool]:
        """Check if a single URL is accessible."""
        try:
            async with session.head(url, allow_redirects=True) as response:
                is_accessible = response.status < 400
                logger.debug(f"URL {url} accessibility: {is_accessible} (status: {response.status})")
                return url, is_accessible
        except Exception as e:
            logger.warning(f"Failed to check URL {url}: {e}")
            return url, False

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL has valid format."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def validate_content_length(self, content_sections: Dict[str, str]) -> Dict[str, bool]:
        """
        Validate content meets length requirements.
        
        Args:
            content_sections: Dictionary with section names and content
            
        Returns:
            Dictionary with validation results for each section
        """
        length_requirements = {
            'main_analysis': (800, 1200),
            'pattern_spotlight': (300, 400),
            'adjacent_watch': (200, 300),
            'signal_radar': (100, 150)
        }
        
        results = {}
        
        for section_name, content in content_sections.items():
            if section_name in length_requirements:
                word_count = len(content.split())
                min_words, max_words = length_requirements[section_name]
                results[f'{section_name}_valid'] = min_words <= word_count <= max_words
                results[f'{section_name}_word_count'] = word_count
                results[f'{section_name}_target_range'] = f"{min_words}-{max_words}"
            else:
                # For other sections, just count words
                results[f'{section_name}_word_count'] = len(content.split())
                
        return results

    def generate_quality_report(self, content: str, content_sections: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Generate comprehensive quality report for newsletter content.
        
        Args:
            content: Full newsletter content
            content_sections: Optional dictionary of individual sections
            
        Returns:
            Comprehensive quality report
        """
        citation_metrics = self.validate_citations(content)
        
        length_metrics = {}
        if content_sections:
            length_metrics = self.validate_content_length(content_sections)
            
        # Calculate overall quality score
        quality_factors = {
            'citations_adequate': citation_metrics['meets_minimum_citations'],
            'signal_references_present': citation_metrics['signal_references'] > 0,
            'bitcoin_terminology_used': sum(citation_metrics['bitcoin_terminology'].values()) >= 5,
            'citation_density_good': citation_metrics['citation_density'] >= 5.0  # 5 per 1000 words
        }
        
        quality_score = sum(quality_factors.values()) / len(quality_factors)
        
        return {
            'citation_metrics': citation_metrics,
            'length_metrics': length_metrics,
            'quality_factors': quality_factors,
            'overall_quality_score': quality_score,
            'recommendations': self._generate_recommendations(citation_metrics, quality_factors)
        }

    def _generate_recommendations(self, citation_metrics: Dict[str, Any], quality_factors: Dict[str, bool]) -> List[str]:
        """Generate improvement recommendations based on validation results."""
        recommendations = []
        
        if not quality_factors['citations_adequate']:
            recommendations.append(f"Add more citations (current: {citation_metrics['total_citations']}, minimum: 8)")
            
        if not quality_factors['signal_references_present']:
            recommendations.append("Include signal references with confidence scores")
            
        if not quality_factors['bitcoin_terminology_used']:
            recommendations.append("Use more Bitcoin-specific terminology for better context")
            
        if not quality_factors['citation_density_good']:
            recommendations.append(f"Increase citation density (current: {citation_metrics['citation_density']:.1f} per 1000 words)")
            
        return recommendations


# Global validator instance
citation_validator = CitationValidator()
