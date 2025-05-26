"""
GitHub API Demo Script

This script demonstrates how to use the GitHub API to search for repositories.
It will be used to test the GitHub MCP server once it's connected.
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get GitHub Personal Access Token from environment variable
github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")

if not github_token:
    print("Error: GitHub Personal Access Token not found in environment variables.")
    print("Please set the GITHUB_PERSONAL_ACCESS_TOKEN environment variable.")
    exit(1)

# Set up headers for GitHub API requests
headers = {
    "Authorization": f"token {github_token}",
    "Accept": "application/vnd.github.v3+json"
}

def search_repositories(query, sort="stars", order="desc", per_page=5):
    """
    Search for GitHub repositories based on the given query.
    
    Args:
        query (str): Search query
        sort (str): Sort field (stars, forks, help-wanted-issues, updated)
        order (str): Sort order (asc, desc)
        per_page (int): Number of results per page
        
    Returns:
        dict: JSON response from GitHub API
    """
    url = "https://api.github.com/search/repositories"
    params = {
        "q": query,
        "sort": sort,
        "order": order,
        "per_page": per_page
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def main():
    print("GitHub API Demo")
    print("---------------")
    
    # Search for repositories related to "modelcontextprotocol"
    print("\nSearching for repositories related to 'modelcontextprotocol'...")
    results = search_repositories("modelcontextprotocol")
    
    if results:
        print(f"Total count: {results['total_count']}")
        print("\nTop repositories:")
        
        for i, repo in enumerate(results["items"], 1):
            print(f"\n{i}. {repo['full_name']}")
            print(f"   Description: {repo['description']}")
            print(f"   Stars: {repo['stargazers_count']}")
            print(f"   URL: {repo['html_url']}")
    
    print("\nDemo completed!")

if __name__ == "__main__":
    main()
