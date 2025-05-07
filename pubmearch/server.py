#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PubMed Analysis MCP Server

This module implements an MCP server for analyzing PubMed search results,
providing tools to identify research hotspots, trends, and publication statistics.

Note:
    - Firstly, always use search_pubmed pubmearch.tool to generate new results.
    - Secondly, for results analysis, always use JSON format files.
"""

import os
import sys
import subprocess
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

# Add parent directory to path to import PubMedSearcher from parent
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from .pubmed_searcher import PubMedSearcher
from .analyzer import PubMedAnalyzer

# Import FastMCP
from mcp.server.fastmcp import FastMCP, Context

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(parent_dir, "pubmed_server.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("pubmed-mcp-server")

# make sure results directory exists
now = datetime.now()
time_string = now.strftime("%Y%m%d%H%M%S")
results_dir = Path(__file__).resolve().parent / "results"
os.makedirs(results_dir, exist_ok=True)
logger.info(f"Results directory: {results_dir}")

# Initialize analyzer
analyzer = PubMedAnalyzer(results_dir=results_dir)

# Initialize MCP server
pubmearch = FastMCP(
    "PubMed Analyzer",
    description="MCP server for analyzing PubMed search results"
)

@pubmearch.tool()
async def search_pubmed(
    advanced_search: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    max_results: int = 1000,
    output_filename: Optional[str] = None,
) -> Dict[str, Any]:
    try:
        logger.info(f"Starting PubMed search with query: {advanced_search}")
        NCBI_USER_EMAIL = os.getenv('NCBI_USER_EMAIL')
        NCBI_USER_API_KEY = os.getenv('NCBI_USER_API_KEY')

        if not NCBI_USER_EMAIL:
            logger.error("Email not provided and NCBI_USER_EMAIL environment variable not set")
            return {
                "success": False,
                "error": "Server configuration error: NCBI User Email is not set."
            }
        logger.info(f"Use email address: {NCBI_USER_EMAIL}")
        
        if NCBI_USER_API_KEY:
            logger.info(f"Using API key from environment.")
        else:
            logger.warning(f"NCBI_USER_API_KEY environment variable not found. Proceeding without API key.")
        
        searcher = PubMedSearcher(email = NCBI_USER_EMAIL, api_key = NCBI_USER_API_KEY)
        
        # Create date range if dates are provided
        # Note: The formats of start_date and end_date is always YYYY/MM/DD
        date_range = None
        if start_date or end_date:
            # Validate date formats
            date_pattern = re.compile(r'^\d{4}/\d{2}/\d{2}$')
            if start_date and not date_pattern.match(start_date):
                raise ValueError(f"Invalid start_date format: {start_date}. Must be YYYY/MM/DD")
            if end_date and not date_pattern.match(end_date):
                raise ValueError(f"Invalid end_date format: {end_date}. Must be YYYY/MM/DD")
            
            date_range = (start_date, end_date) if start_date and end_date else None
        
        # Perform search
        records = searcher.search(
            advanced_search=advanced_search,
            date_range=date_range,
            max_results=max_results
        )
        
        if not records:
            logger.warning("No results found for the search criteria")
            return {
                "success": False,
                "error": "No results found for the given criteria."
            }
        
        # Export both TXT and JSON formats
        if not output_filename:
            base_filename = f"pubmed_results_{time_string}"
            json_filename = f"{base_filename}.json"
            txt_filename = f"{base_filename}.txt"
        else:
            # Remove any existing extension
            base_filename = output_filename.rsplit('.', 1)[0] + f"_{time_string}"
            json_filename = f"{base_filename}.json"
            txt_filename = f"{base_filename}.txt"
        
        # Export both formats
        json_path = os.path.abspath(searcher.export_to_json(records, json_filename))
        txt_path = os.path.abspath(searcher.export_to_txt(records, txt_filename))
        
        # Verify if files were saved successfully
        if not os.path.exists(json_path):
            logger.error(f"Failed to create JSON file at {json_path}")
            return {
                "success": False,
                "error": f"Failed to save JSON results file."
            }
            
        logger.info(f"Successfully saved {len(records)} articles to JSON: {json_path}")
        
        return {
            "success": True,
            "message": f"Search completed successfully. Found {len(records)} articles.",
            "json_file": os.path.basename(json_path),
            "txt_file": os.path.basename(txt_path),
            "note": "JSON files are recommended for AI model analysis.",
            "article_count": len(records)
        }
        
    except ValueError as ve: 
        logger.error(f"ValueError in search_pubmed: {str(ve)}", exc_info=True)
        return {"success": False, "error": str(ve)}
    except Exception as e:
        logger.error(f"Error in search_pubmed: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"Error during search: {str(e)}"
        }

@pubmearch.tool()
async def list_result_files() -> Dict[str, Any]:
    """Lists all available PubMed result files.

    Two types of files are returned:
    - JSON files (recommended): structured data, suitable for AI model analysis
    - TXT files (alternative): plain text format, for backward compatibility
    """
    try:
        logger.info(f"Listing result files in: {results_dir}")
        
        if not os.path.exists(results_dir):
            logger.warning(f"Results directory does not exist: {results_dir}")
            os.makedirs(results_dir, exist_ok=True)
            logger.info(f"Created results directory: {results_dir}")
            return {
                "success": True,
                "files": [],
                "count": 0,
                "directory": results_dir
            }
        
        # Get JSON and TXT files separately
        json_files = [f for f in os.listdir(results_dir) if f.endswith('.json')]
        txt_files = [f for f in os.listdir(results_dir) if f.endswith('.txt')]
        
        return {
            "success": True,
            "files": {
                "recommended": json_files,  # JSON files (recommended)
                "alternative": txt_files    # TXT files (alternative)
            },
            "count": len(json_files) + len(txt_files),
            "directory": results_dir,
            "note": "Always use JSON files first."
        }
    except Exception as e:
        logger.error(f"Error in list_result_files: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "directory": results_dir if 'results_dir' in locals() else "unknown"
        }

@pubmearch.tool()
async def analyze_research_keywords(filename: str, top_n: int = 20, include_trends: bool = True) -> Dict[str, Any]:
    """Analyze the research hotspots and trends in PubMed result files according keywords.
    
    Note: It is recommended to use JSON format files for better analysis results.
    
    Args:
        filename: File name of results. (.json format is recommended)
        top_n: Return the top n hot keywords.
        include_trends: Boolean value to determine whether to include trends analysis. Default is True.
    """
    try:
        filepath = os.path.join(results_dir, filename)
        logger.info(f"Analyzing research keywords from file: {filepath}")
        
        # Check if the file exists
        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            # JSON first
            json_files = [f for f in os.listdir(results_dir) if f.endswith('.json')]
            txt_files = [f for f in os.listdir(results_dir) if f.endswith('.txt')]
            return {
                "success": False,
                "error": f"File not found: {filepath}",
                "available_files": {
                    "recommended": json_files,
                    "alternative": txt_files
                },
                "note": "Always use JSON files first."
            }
        
        # Parse the result file
        articles = analyzer.parse_results_file(filepath)
        
        if not articles:
            logger.warning(f"No articles found in file: {filepath}")
            return {
                "success": False,
                "error": "No articles found in the file."
            }
        
        # Analyze keywords
        analysis_results = analyzer.analyze_research_keywords(articles, top_n, include_trends)
        
        return {
            "success": True,
            "file_analyzed": filename,
            "article_count": len(articles),
            "keyword_analysis": analysis_results
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_research_keywords: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

@pubmearch.tool()
async def analyze_publication_count(filename: str, months_per_period: int = 3) -> Dict[str, Any]:
    """Analyze publication counts over time from a PubMed results file.
    
    Note: It is recommended to use JSON format files for better analysis results.
    
    Args:
        filename: File name of results. (.json format is recommended)
        months_per_period: Number of months per analysis period
    """
    try:
        filepath = os.path.join(results_dir, filename)
        logger.info(f"Analyzing publication counts from file: {filepath}")
        
        # Check if the file exists
        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            json_files = [f for f in os.listdir(results_dir) if f.endswith('.json')]
            txt_files = [f for f in os.listdir(results_dir) if f.endswith('.txt')]
            return {
                "success": False,
                "error": f"File not found: {filepath}",
                "available_files": {
                    "recommended": json_files,
                    "alternative": txt_files
                },
                "note": "Always use JSON files first."
            }
        
        # Parse the result file
        articles = analyzer.parse_results_file(filepath)
        
        if not articles:
            logger.warning(f"No articles found in file: {filepath}")
            return {
                "success": False,
                "error": "No articles found in the file."
            }
        
        # Analyze publication counts
        pub_counts = analyzer.analyze_publication_count(articles, months_per_period)
        
        return {
            "success": True,
            "file_analyzed": filename,
            "article_count": len(articles),
            "publication_counts": pub_counts
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_publication_count: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

@pubmearch.tool()
async def generate_comprehensive_analysis(
    filename: str,
    top_keywords: int = 20,
    months_per_period: int = 3
) -> Dict[str, Any]:
    """Generate a comprehensive analysis of a PubMed results file.
    
    Note: It is recommended to use JSON format files for better analysis results.
    
    Args:
        filename: File name of results. (.json format is recommended)
        top_keywords: Number of top keywords to analyze
        months_per_period: Number of months per analysis period
    """
    try:
        filepath = os.path.join(results_dir, filename)
        logger.info(f"Generating comprehensive analysis from file: {filepath}")
        
        # Check if the file exists
        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            json_files = [f for f in os.listdir(results_dir) if f.endswith('.json')]
            txt_files = [f for f in os.listdir(results_dir) if f.endswith('.txt')]
            return {
                "success": False,
                "error": f"File not found: {filepath}",
                "available_files": {
                    "recommended": json_files,
                    "alternative": txt_files
                },
                "note": "Always use JSON files first."
            }
        
        # Generate comprehensive analysis directly
        results = analyzer.generate_comprehensive_analysis(
            filepath,
            top_keywords=top_keywords,
            months_per_period=months_per_period
        )
        
        if "error" in results:
            logger.error(f"Error in analysis: {results['error']}")
            return {
                "success": False,
                "error": results["error"]
            }
        
        logger.info("Comprehensive analysis completed successfully")
        return {
            "success": True,
            "analysis": results
        }
        
    except Exception as e:
        logger.error(f"Error in generate_comprehensive_analysis: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    os.makedirs(results_dir, exist_ok=True)
    pubmearch.run()