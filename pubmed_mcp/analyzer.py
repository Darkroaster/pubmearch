#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PubMed Analysis Module

This module provides analysis functionality for PubMed search results, 
including research hotspots, trends, and publication statistics.
"""

import os
import re
import json
from datetime import datetime
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple, Any, Union


class PubMedAnalyzer:
    """Class to analyze PubMed search results from text files."""
    
    def __init__(self, results_dir: str = "../results"):
        """
        Initialize the PubMed analyzer.
        
        Args:
            results_dir: Directory containing PubMed search result text files
        """
        self.results_dir = results_dir
        
    def parse_results_file(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Parse a PubMed results text file into structured data.
        
        Args:
            filepath: Path to the results text file
            
        Returns:
            List of dictionaries containing structured article data
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        articles = []
        current_article = None
        section = None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # New article marker
                if line.startswith("Article ") and "-" * 10 in lines[i+1]:
                    if current_article:
                        articles.append(current_article)
                    current_article = {
                        "title": "",
                        "authors": [],
                        "journal": "",
                        "publication_date": "",
                        "abstract": "",
                        "keywords": [],
                        "pmid": "",
                        "doi": ""
                    }
                    section = None
                    i += 2  # Skip the separator line
                
                # Section headers
                elif line.startswith("Title: "):
                    current_article["title"] = line[7:].strip()
                    section = "title"
                elif line.startswith("Authors: "):
                    authors_line = line[9:].strip()
                    if authors_line != "N/A":
                        current_article["authors"] = [a.strip() for a in authors_line.split(",")]
                    section = None
                elif line.startswith("Journal: "):
                    current_article["journal"] = line[9:].strip()
                    section = None
                elif line.startswith("Publication Date: "):
                    current_article["publication_date"] = line[18:].strip()
                    section = None
                elif line == "Abstract:":
                    section = "abstract"
                elif line.startswith("Keywords: "):
                    keywords_line = line[10:].strip()
                    current_article["keywords"] = [k.strip() for k in keywords_line.split(",")]
                    section = None
                elif line.startswith("PMID: "):
                    current_article["pmid"] = line[6:].strip()
                    section = None
                elif line.startswith("DOI: "):
                    current_article["doi"] = line[5:].strip()
                    section = None
                elif line.startswith("=" * 20):
                    section = None
                
                # Content sections
                elif section == "abstract" and line and not line.startswith("Keywords: "):
                    current_article["abstract"] += line + " "
                
                i += 1
            
            # Add the last article
            if current_article:
                articles.append(current_article)
        
        return articles

    def extract_publication_dates(self, articles: List[Dict[str, Any]]) -> List[Tuple[str, datetime]]:
        """
        Extract and parse publication dates from articles.
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            List of tuples containing (article_title, publication_date)
        """
        publication_dates = []
        
        for article in articles:
            date_str = article.get("publication_date", "")
            
            # Try different formats
            parsed_date = None
            
            # Format: YYYY MMM
            if re.match(r"^\d{4} [A-Za-z]{3}$", date_str):
                try:
                    parsed_date = datetime.strptime(date_str, "%Y %b")
                except ValueError:
                    pass
            
            # Format: YYYY MMM DD
            elif re.match(r"^\d{4} [A-Za-z]{3} \d{1,2}$", date_str):
                try:
                    parsed_date = datetime.strptime(date_str, "%Y %b %d")
                except ValueError:
                    pass
            
            # Format: YYYY MMM-MMM
            elif re.match(r"^\d{4} [A-Za-z]{3}-[A-Za-z]{3}$", date_str):
                try:
                    # Just use the first month
                    month_part = date_str.split(" ")[1].split("-")[0]
                    parsed_date = datetime.strptime(f"{date_str.split(' ')[0]} {month_part}", "%Y %b")
                except (ValueError, IndexError):
                    pass
            
            # Format: YYYY
            elif re.match(r"^\d{4}$", date_str):
                try:
                    parsed_date = datetime.strptime(date_str, "%Y")
                except ValueError:
                    pass
            
            if parsed_date:
                publication_dates.append((article.get("title", ""), parsed_date))
        
        return publication_dates
    
    def analyze_research_hotspots(self, articles: List[Dict[str, Any]], top_n: int = 20) -> Dict[str, Any]:
        """
        Analyze research hotspots based on keyword frequencies.
        
        Args:
            articles: List of article dictionaries
            top_n: Number of top keywords to include
            
        Returns:
            Dictionary with analysis results
        """
        # Extract all keywords
        all_keywords = []
        for article in articles:
            all_keywords.extend(article.get("keywords", []))
        
        # Count keyword frequencies
        keyword_counts = Counter(all_keywords)
        
        # Get top keywords
        top_keywords = keyword_counts.most_common(top_n)
        
        # Organize articles by keyword
        keyword_articles = defaultdict(list)
        for article in articles:
            article_keywords = article.get("keywords", [])
            for kw in article_keywords:
                if kw in dict(top_keywords):
                    keyword_articles[kw].append({
                        "title": article.get("title", ""),
                        "authors": article.get("authors", []),
                        "journal": article.get("journal", ""),
                        "publication_date": article.get("publication_date", ""),
                        "pmid": article.get("pmid", "")
                    })
        
        # Prepare results
        results = {
            "top_keywords": [{"keyword": kw, "count": count} for kw, count in top_keywords],
            "keyword_articles": {kw: articles for kw, articles in keyword_articles.items()}
        }
        
        return results
    
    def analyze_research_trends(self, articles: List[Dict[str, Any]], top_n: int = 10) -> Dict[str, Any]:
        """
        Analyze research trends over time based on monthly keyword frequencies.
        
        Args:
            articles: List of article dictionaries
            top_n: Number of top keywords to track trends for
            
        Returns:
            Dictionary with trend analysis results
        """
        # Extract all keywords first to find the most common ones
        all_keywords = []
        for article in articles:
            all_keywords.extend(article.get("keywords", []))
        
        keyword_counts = Counter(all_keywords)
        top_keywords = [kw for kw, _ in keyword_counts.most_common(top_n)]
        
        # Extract publication dates
        pub_dates = self.extract_publication_dates(articles)
        
        # Group by month
        monthly_keyword_counts = defaultdict(lambda: defaultdict(int))
        
        for article in articles:
            date_str = article.get("publication_date", "")
            article_keywords = article.get("keywords", [])
            
            # Try to parse the date
            parsed_date = None
            for title, date in pub_dates:
                if title == article.get("title", ""):
                    parsed_date = date
                    break
            
            if parsed_date:
                month_key = parsed_date.strftime("%Y-%m")
                for kw in article_keywords:
                    if kw in top_keywords:
                        monthly_keyword_counts[month_key][kw] += 1
        
        # Convert to sortable format and sort by date
        sorted_months = sorted(monthly_keyword_counts.keys())
        
        # Prepare trend data
        trend_data = {
            "months": sorted_months,
            "keywords": top_keywords,
            "counts": []
        }
        
        for keyword in top_keywords:
            keyword_trend = []
            for month in sorted_months:
                keyword_trend.append(monthly_keyword_counts[month][keyword])
            trend_data["counts"].append({
                "keyword": keyword,
                "monthly_counts": keyword_trend
            })
        
        return trend_data
    
    def analyze_publication_count(self, articles: List[Dict[str, Any]], months_per_period: int = 3) -> Dict[str, Any]:
        """
        Analyze publication counts over time.
        
        Args:
            articles: List of article dictionaries
            months_per_period: Number of months to group by
            
        Returns:
            Dictionary with publication count analysis
        """
        # Extract publication dates
        pub_dates = self.extract_publication_dates(articles)
        
        # Group by period
        period_counts = defaultdict(int)
        
        for _, date in pub_dates:
            # Calculate period key based on months_per_period
            year = date.year
            month = date.month
            period = (month - 1) // months_per_period
            period_key = f"{year}-P{period+1}"  # 1-indexed periods
            
            period_counts[period_key] += 1
        
        # Sort periods chronologically
        sorted_periods = sorted(period_counts.keys())
        
        # Prepare result
        results = {
            "periods": sorted_periods,
            "counts": [period_counts[period] for period in sorted_periods],
            "months_per_period": months_per_period,
            "total_publications": len(pub_dates)
        }
        
        return results
    
    def generate_comprehensive_analysis(self, filepath: str, top_keywords: int = 20,
                                        trend_keywords: int = 10, months_per_period: int = 3) -> Dict[str, Any]:
        """
        Generate a comprehensive analysis of PubMed results from a file.
        
        Args:
            filepath: Path to the results text file
            top_keywords: Number of top keywords for hotspot analysis
            trend_keywords: Number of keywords for trend analysis
            months_per_period: Number of months per period for publication count
            
        Returns:
            Dictionary with comprehensive analysis results
        """
        try:
            articles = self.parse_results_file(filepath)
            
            if not articles:
                return {"error": "No articles found in the file."}
            
            # Generate analysis components
            hotspots = self.analyze_research_hotspots(articles, top_keywords)
            trends = self.analyze_research_trends(articles, trend_keywords)
            pub_counts = self.analyze_publication_count(articles, months_per_period)
            
            # Combine results
            results = {
                "file_analyzed": os.path.basename(filepath),
                "analysis_timestamp": datetime.now().isoformat(),
                "article_count": len(articles),
                "research_hotspots": hotspots,
                "research_trends": trends,
                "publication_counts": pub_counts
            }
            
            return results
            
        except Exception as e:
            return {"error": str(e)}
    
    def list_result_files(self) -> List[str]:
        """
        List all result files in the results directory.
        
        Returns:
            List of filenames
        """
        if not os.path.exists(self.results_dir):
            return []
        
        return [f for f in os.listdir(self.results_dir) if f.endswith('.txt')]