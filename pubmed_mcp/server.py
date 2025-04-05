#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PubMed Analysis MCP Server

This module implements an MCP server for analyzing PubMed search results,
providing tools to identify research hotspots, trends, and publication statistics.
"""

import os
import sys
import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

# Add parent directory to path to import PubMedSearcher from parent
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from pubmed_searcher import PubMedSearcher
from pubmed_mcp.analyzer import PubMedAnalyzer

# 更新为最新的MCP导入
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

# 确保结果目录存在
results_dir = os.path.join(parent_dir, "results")
os.makedirs(results_dir, exist_ok=True)
logger.info(f"Results directory: {results_dir}")

# Initialize analyzer
analyzer = PubMedAnalyzer(results_dir=results_dir)

# 使用FastMCP替代自定义实现
mcp_server = FastMCP(
    "PubMed Analyzer",
    description="MCP server for analyzing PubMed search results"
)

@mcp_server.tool()
def search_pubmed(
    email: str,
    advanced_search: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    max_results: int = 1000,
    output_filename: Optional[str] = None
) -> Dict[str, Any]:
    
    try:
        logger.info(f"Starting PubMed search with query: {advanced_search}")
        searcher = PubMedSearcher(email)
        
        # Create date range if dates are provided
        date_range = None
        if start_date and end_date:
            date_range = (start_date, end_date)
        
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
        
        # 确保输出文件名唯一
        if output_filename is None:
            # 使用默认文件名
            output_filename = f"pubmed_results_{len(records)}_articles.txt"
        
        # 确保文件扩展名为.txt
        if not output_filename.endswith('.txt'):
            output_filename += '.txt'
        
        # 导出到文件
        output_path = searcher.export_to_txt(records, output_filename)
        
        # 验证文件是否成功保存并可以访问
        if not os.path.exists(output_path):
            logger.error(f"Failed to create output file at {output_path}")
            return {
                "success": False,
                "error": f"Failed to save results to file. Path {output_path} does not exist."
            }
        
        logger.info(f"Successfully saved {len(records)} articles to {output_path}")
        
        # 确保分析器可以找到此文件
        copied_path = os.path.join(results_dir, os.path.basename(output_path))
        if output_path != copied_path:
            try:
                # 确保文件也在results_dir目录
                import shutil
                shutil.copy2(output_path, copied_path)
                logger.info(f"Copied results file to: {copied_path}")
            except Exception as e:
                logger.error(f"Failed to copy file to results directory: {e}")
        
        return {
            "success": True,
            "message": f"Search completed successfully. Found {len(records)} articles.",
            "result_file": os.path.basename(output_path),
            "article_count": len(records)
        }
        
    except Exception as e:
        logger.error(f"Error in search_pubmed: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"Error during search: {str(e)}"
        }

@mcp_server.tool()
def list_result_files() -> Dict[str, Any]:
    """List all available PubMed result files."""
    try:
        logger.info(f"Listing result files in: {results_dir}")
        
        # 直接检查目录内容，不依赖analyzer
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
        
        # 获取目录中的所有txt文件
        files = [f for f in os.listdir(results_dir) if f.endswith('.txt')]
        logger.info(f"Found {len(files)} result files")
        
        return {
            "success": True,
            "files": files,
            "count": len(files),
            "directory": results_dir
        }
    except Exception as e:
        logger.error(f"Error in list_result_files: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "directory": results_dir if 'results_dir' in locals() else "unknown"
        }

@mcp_server.tool()
def analyze_research_hotspots(filename: str, top_n: int = 20) -> Dict[str, Any]:
    """Analyze research hotspots from a PubMed results file."""
    try:
        filepath = os.path.join(results_dir, filename)
        logger.info(f"Analyzing research hotspots from file: {filepath}")
        
        # 检查文件是否存在
        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            available_files = [f for f in os.listdir(results_dir) if f.endswith('.txt')]
            return {
                "success": False,
                "error": f"File not found: {filepath}",
                "available_files": available_files
            }
        
        # 解析结果文件
        articles = analyzer.parse_results_file(filepath)
        
        if not articles:
            logger.warning(f"No articles found in file: {filepath}")
            return {
                "success": False,
                "error": "No articles found in the file."
            }
        
        # 分析热点
        hotspots = analyzer.analyze_research_hotspots(articles, top_n)
        
        return {
            "success": True,
            "file_analyzed": filename,
            "article_count": len(articles),
            "research_hotspots": hotspots
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_research_hotspots: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

@mcp_server.tool()
def analyze_research_trends(filename: str, top_n: int = 10) -> Dict[str, Any]:
    """Analyze research trends over time from a PubMed results file."""
    try:
        filepath = os.path.join(results_dir, filename)
        logger.info(f"Analyzing research trends from file: {filepath}")
        
        # 检查文件是否存在
        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            available_files = [f for f in os.listdir(results_dir) if f.endswith('.txt')]
            return {
                "success": False,
                "error": f"File not found: {filepath}",
                "available_files": available_files
            }
        
        # 解析结果文件
        articles = analyzer.parse_results_file(filepath)
        
        if not articles:
            logger.warning(f"No articles found in file: {filepath}")
            return {
                "success": False,
                "error": "No articles found in the file."
            }
        
        # 分析趋势
        trends = analyzer.analyze_research_trends(articles, top_n)
        
        return {
            "success": True,
            "file_analyzed": filename,
            "article_count": len(articles),
            "research_trends": trends
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_research_trends: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

@mcp_server.tool()
def analyze_publication_count(filename: str, months_per_period: int = 3) -> Dict[str, Any]:
    """Analyze publication counts over time from a PubMed results file."""
    try:
        filepath = os.path.join(results_dir, filename)
        logger.info(f"Analyzing publication counts from file: {filepath}")
        
        # 检查文件是否存在
        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            available_files = [f for f in os.listdir(results_dir) if f.endswith('.txt')]
            return {
                "success": False,
                "error": f"File not found: {filepath}",
                "available_files": available_files
            }
        
        # 解析结果文件
        articles = analyzer.parse_results_file(filepath)
        
        if not articles:
            logger.warning(f"No articles found in file: {filepath}")
            return {
                "success": False,
                "error": "No articles found in the file."
            }
        
        # 分析出版计数
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

@mcp_server.tool()
def generate_comprehensive_analysis(
    filename: str,
    top_keywords: int = 20,
    trend_keywords: int = 10,
    months_per_period: int = 3
) -> Dict[str, Any]:
    """Generate a comprehensive analysis of a PubMed results file."""
    try:
        filepath = os.path.join(results_dir, filename)
        logger.info(f"Generating comprehensive analysis from file: {filepath}")
        
        # 检查文件是否存在
        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            available_files = [f for f in os.listdir(results_dir) if f.endswith('.txt')]
            return {
                "success": False,
                "error": f"File not found: {filepath}",
                "available_files": available_files
            }
        
        # 直接生成综合分析
        results = analyzer.generate_comprehensive_analysis(
            filepath,
            top_keywords=top_keywords,
            trend_keywords=trend_keywords,
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

def main():
    """Start the PubMed MCP server."""
    try:
        # 确保必要目录存在
        os.makedirs(results_dir, exist_ok=True)
        logger.info(f"Verified results directory: {results_dir}")
        
        # 启动服务器
        logger.info("Starting PubMed MCP server")
        mcp_server.run()
    except Exception as e:
        logger.critical(f"Failed to start server: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()