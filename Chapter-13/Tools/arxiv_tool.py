# tools/arxiv_tool.py
import requests
import xml.etree.ElementTree as ET
from agents import function_tool
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

# --- Pydantic Models for Structured API Data ---
class ArxivPaper(BaseModel):
    """A data structure to hold the details of a single ArXiv paper."""
    paper_id: str = Field(description="The unique ArXiv URL identifier for the paper.")
    title: str
    summary: str
    published_date: str = Field(description="The publication date of the paper.")

class ArxivSearchResult(BaseModel):
    """A data structure to hold a list of papers from an ArXiv search."""
    papers: List[ArxivPaper]

# --- Updated Tool Function ---
@function_tool
def search_arxiv(query: str, max_results: int = 5) -> ArxivSearchResult:
    """
    Searches the ArXiv API for papers matching a query and returns a structured
    list of paper objects, including their publication dates.
    """
    print(f"🛠️  [Tool Call] Searching ArXiv for: '{query}'")
    base_url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        papers = []
        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            # Extract all the necessary fields from the XML response
            paper_id = entry.find('{http://www.w3.org/2005/Atom}id').text
            title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip()
            summary = entry.find('{http://www.w3.org/2005/Atom}summary').text.strip()
            published = entry.find('{http://www.w3.org/2005/Atom}published').text
            
            # Create an instance of our Pydantic model
            papers.append(ArxivPaper(
                paper_id=paper_id,
                title=title,
                summary=summary,
                # Format the date for better readability
                published_date=datetime.fromisoformat(published.replace('Z', '+00:00')).strftime('%Y-%m-%d')
            ))
        
        # Return the structured result
        return ArxivSearchResult(papers=papers)
    except requests.RequestException as e:
        print(f"Error connecting to ArXiv: {e}")
        return ArxivSearchResult(papers=[])