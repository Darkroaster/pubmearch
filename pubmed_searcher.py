#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PubMed Searcher Module

This module provides functionality for searching PubMed and retrieving article data.
"""

import os
import re
import time
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any, Union
from Bio import Entrez
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class PubMedSearcher:
    """Class to search PubMed and retrieve article data."""
    
    def __init__(self, email: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize PubMed searcher with user email and optional API key.
        
        Args:
            email: User email (required by NCBI). If None, will use NCBI_USER_EMAIL from .env
            api_key: NCBI API key for higher request limits (optional)
        """
        self.email = email or os.getenv('NCBI_USER_EMAIL')
        if not self.email:
            raise ValueError("Email is required. Either pass it directly or set NCBI_USER_EMAIL in .env")
            
        self.api_key = api_key or os.getenv('NCBI_API_KEY')
        
        # Set up Entrez
        Entrez.email = self.email
        if self.api_key:
            Entrez.api_key = self.api_key
        
        # Create results directory if it doesn't exist
        self.results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
        os.makedirs(self.results_dir, exist_ok=True)
    
    def search(self, 
              advanced_search: str, 
              date_range: Optional[Tuple[str, str]] = None,
              max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Search PubMed using advanced search syntax.
        
        Args:
            advanced_search: PubMed advanced search query
            date_range: Optional tuple of (start_date, end_date) in format YYYY/MM/DD
            max_results: Maximum number of results to retrieve
            
        Returns:
            List of article dictionaries
        """
        search_term = advanced_search
        
        # Add date range to query if provided
        if date_range:
            start_date, end_date = date_range
            date_filter = f" AND (\"{start_date}\"[Date - Publication] : \"{end_date}\"[Date - Publication])"
            search_term += date_filter
        
        try:
            # Search PubMed
            print(f"Searching PubMed with query: {search_term}")
            search_handle = Entrez.esearch(db="pubmed", term=search_term, retmax=max_results, usehistory="y")
            search_results = Entrez.read(search_handle)
            search_handle.close()
            
            webenv = search_results["WebEnv"]
            query_key = search_results["QueryKey"]
            
            # Get the count of results
            count = int(search_results["Count"])
            print(f"Found {count} results, retrieving up to {max_results}")
            
            if count == 0:
                print("No results found")
                return []
            
            # Initialize an empty list to store articles
            articles = []
            
            # Fetch results in batches to avoid timeouts
            batch_size = 100
            for start in range(0, min(count, max_results), batch_size):
                end = min(count, start + batch_size, max_results)
                print(f"Retrieving records {start+1} to {end}")
                
                try:
                    # Fetch the records
                    fetch_handle = Entrez.efetch(
                        db="pubmed", 
                        retstart=start, 
                        retmax=batch_size,
                        webenv=webenv,
                        query_key=query_key,
                        retmode="xml"
                    )
                    
                    # Parse the records
                    records = Entrez.read(fetch_handle)["PubmedArticle"]
                    fetch_handle.close()
                    
                    # Process each record
                    for record in records:
                        article = self._parse_pubmed_record(record)
                        articles.append(article)
                    
                    # Sleep to avoid overloading the NCBI server
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"Error fetching batch {start+1} to {end}: {str(e)}")
                    continue
            
            return articles
            
        except Exception as e:
            print(f"Error searching PubMed: {str(e)}")
            return []
    
    def _parse_pubmed_record(self, record: Dict) -> Dict[str, Any]:
        """
        Parse a PubMed record into a structured article dictionary.
        
        Args:
            record: PubMed record from Entrez.read
            
        Returns:
            Dictionary containing structured article data
        """
        article_data = {}
        
        # Get MedlineCitation and Article
        medline_citation = record.get("MedlineCitation", {})
        article = medline_citation.get("Article", {})
        
        # Extract basic article information
        article_data["title"] = article.get("ArticleTitle", "")
        
        # Extract authors
        authors = []
        author_list = article.get("AuthorList", [])
        for author in author_list:
            if "LastName" in author and "ForeName" in author:
                authors.append(f"{author['LastName']} {author['ForeName']}")
            elif "LastName" in author and "Initials" in author:
                authors.append(f"{author['LastName']} {author['Initials']}")
            elif "LastName" in author:
                authors.append(author["LastName"])
            elif "CollectiveName" in author:
                authors.append(author["CollectiveName"])
        article_data["authors"] = authors
        
        # Extract journal information
        journal = article.get("Journal", {})
        article_data["journal"] = journal.get("Title", "")
        
        # Extract publication date
        pub_date = {}
        journal_issue = journal.get("JournalIssue", {})
        if "PubDate" in journal_issue:
            pub_date = journal_issue["PubDate"]
        
        pub_date_str = ""
        if "Year" in pub_date:
            pub_date_str = pub_date["Year"]
            if "Month" in pub_date:
                pub_date_str += f" {pub_date['Month']}"
                if "Day" in pub_date:
                    pub_date_str += f" {pub_date['Day']}"
                    
        article_data["publication_date"] = pub_date_str
        
        # Extract abstract
        abstract_text = ""
        if "Abstract" in article and "AbstractText" in article["Abstract"]:
            # Handle different abstract formats
            abstract_parts = article["Abstract"]["AbstractText"]
            if isinstance(abstract_parts, list):
                for part in abstract_parts:
                    if isinstance(part, str):
                        abstract_text += part + " "
                    elif isinstance(part, dict) and "#text" in part:
                        label = part.get("Label", "")
                        text = part["#text"]
                        if label:
                            abstract_text += f"{label}: {text} "
                        else:
                            abstract_text += text + " "
            else:
                abstract_text = str(abstract_parts)
        
        article_data["abstract"] = abstract_text.strip()
        
        # Extract keywords
        keywords = []
        # MeSH headings
        mesh_headings = medline_citation.get("MeshHeadingList", [])
        for heading in mesh_headings:
            if "DescriptorName" in heading:
                descriptor = heading["DescriptorName"]
                if isinstance(descriptor, dict) and "content" in descriptor:
                    keywords.append(descriptor["content"])
                elif isinstance(descriptor, str):
                    keywords.append(descriptor)
        
        # Keywords from KeywordList
        keyword_lists = medline_citation.get("KeywordList", [])
        for keyword_list in keyword_lists:
            if isinstance(keyword_list, list):
                for keyword in keyword_list:
                    if isinstance(keyword, str):
                        keywords.append(keyword)
                    elif isinstance(keyword, dict) and "content" in keyword:
                        keywords.append(keyword["content"])
        
        article_data["keywords"] = keywords
        
        # Extract PMID
        pmid = medline_citation.get("PMID", "")
        if isinstance(pmid, dict) and "content" in pmid:
            article_data["pmid"] = pmid["content"]
        else:
            article_data["pmid"] = str(pmid)
        
        # Extract DOI - Final attempt with careful iteration
        doi = ""
        try:
            pubmed_data = record.get("PubmedData")
            if pubmed_data:
                article_id_list = pubmed_data.get("ArticleIdList")
                # Iterate through article_id_list if it exists and is iterable
                if article_id_list:
                    try:
                        for id_element in article_id_list:
                            # Check if the element has attributes and the IdType is 'doi'
                            # Handles Bio.Entrez.Parser.StringElement and similar objects
                            if hasattr(id_element, 'attributes') and id_element.attributes.get('IdType') == 'doi':
                                doi = str(id_element).strip() # Get the string value
                                if doi: break # Found DOI, exit loop
                            # Fallback check for plain dictionary structure (less common)
                            elif isinstance(id_element, dict) and id_element.get('IdType') == 'doi':
                                doi = id_element.get('content', '').strip() or id_element.get('#text', '').strip()
                                if doi: break # Found DOI, exit loop
                    except TypeError:
                        # Handle cases where article_id_list might not be iterable (e.g., single element)
                        # Check if the single element itself is the DOI
                        if hasattr(article_id_list, 'attributes') and article_id_list.attributes.get('IdType') == 'doi':
                            doi = str(article_id_list).strip()

        except Exception as e:
            print(f"Warning: Error during DOI extraction for PMID {article_data.get('pmid', 'N/A')}: {e}")
            doi = "" # Reset DOI on error
        
        article_data["doi"] = doi
        
        return article_data
    
    def export_to_txt(self, articles: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """
        Export articles to a formatted text file.
        
        Args:
            articles: List of article dictionaries
            filename: Optional output filename
            
        Returns:
            Path to the created file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pubmed_results_{timestamp}.txt"
        
        filepath = os.path.join(self.results_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for i, article in enumerate(articles, 1):
                f.write(f"Article {i}\n")
                f.write("-" * 80 + "\n")
                f.write(f"Title: {article.get('title', '')}\n")
                f.write(f"Authors: {', '.join(article.get('authors', []))}\n")
                f.write(f"Journal: {article.get('journal', '')}\n")
                f.write(f"Publication Date: {article.get('publication_date', '')}\n")
                f.write(f"Abstract:\n{article.get('abstract', '')}\n")
                f.write(f"Keywords: {', '.join(article.get('keywords', []))}\n")
                f.write(f"PMID: {article.get('pmid', '')}\n")
                f.write(f"DOI: https://doi.org/{article.get('doi', '')}\n")
                f.write("=" * 80 + "\n\n")
        
        print(f"Exported {len(articles)} articles to {filepath}")
        return filepath
