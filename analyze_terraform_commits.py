#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timedelta
import pandas as pd
from github import Github
from typing import List, Dict, Optional
import numpy as np
from sklearn.linear_model import LinearRegression
import time

def get_terraform_files(commit) -> List[str]:
    """Get list of Terraform-related files in a commit."""
    terraform_extensions = {'.tf', '.tfvars', '.tfvars.json'}
    return [
        file.filename for file in commit.files
        if any(file.filename.endswith(ext) for ext in terraform_extensions)
    ]

def is_skip_ci(commit) -> bool:
    """Check if commit message contains [skip ci]."""
    return '[skip ci]' in commit.commit.message.lower()

def handle_rate_limit(g: Github) -> None:
    """Handle GitHub API rate limits by waiting if necessary."""
    rate_limit = g.get_rate_limit()
    if rate_limit.core.remaining == 0:
        reset_time = rate_limit.core.reset
        wait_time = (reset_time - datetime.now()).total_seconds()
        if wait_time > 0:
            print(f"Rate limit reached. Waiting {wait_time:.2f} seconds...")
            time.sleep(wait_time)

def analyze_repository(repo, start_date: datetime, end_date: datetime, branch: Optional[str] = None) -> Dict:
    """Analyze Terraform commits in a repository for a given date range."""
    handle_rate_limit(repo._requester._Requester__requester._Github__requester._Requester__requester)
    
    # If branch is specified, only analyze that branch
    if branch:
        try:
            commits = repo.get_commits(sha=branch, since=start_date, until=end_date)
        except Exception as e:
            print(f"Warning: Could not analyze branch '{branch}' in {repo.name}: {str(e)}")
            return {'total_commits': 0, 'commits': []}
    else:
        commits = repo.get_commits(since=start_date, until=end_date)
    
    terraform_commits = []
    
    for commit in commits:
        handle_rate_limit(repo._requester._Requester__requester._Github__requester._Requester__requester)
        
        if is_skip_ci(commit):
            continue
            
        terraform_files = get_terraform_files(commit)
        if terraform_files:
            terraform_commits.append({
                'date': commit.commit.author.date,
                'files': terraform_files,
                'message': commit.commit.message,
                'branch': branch or commit.commit.ref
            })
    
    return {
        'total_commits': len(terraform_commits),
        'commits': terraform_commits
    }

def predict_usage(monthly_data: List[int]) -> Dict:
    """Predict future usage based on historical data."""
    if not monthly_data:
        return {'monthly': 0, 'annual': 0}
    
    X = np.array(range(len(monthly_data))).reshape(-1, 1)
    y = np.array(monthly_data)
    
    model = LinearRegression()
    model.fit(X, y)
    
    next_month = len(monthly_data)
    predicted_monthly = max(0, model.predict([[next_month]])[0])
    
    return {
        'monthly': round(predicted_monthly),
        'annual': round(predicted_monthly * 12)
    }

def main():
    # Get GitHub token from environment variable
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable is not set")
        sys.exit(1)
    
    # Get organization name from environment variable
    org_name = os.getenv('GITHUB_ORG')
    if not org_name:
        print("Error: GITHUB_ORG environment variable is not set")
        sys.exit(1)
    
    # Get branch from environment variable (optional)
    branch = os.getenv('GITHUB_BRANCH')
    
    # Initialize GitHub client
    g = Github(github_token)
    org = g.get_organization(org_name)
    
    # Calculate date range (last 12 months)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    # Analyze all repositories
    all_repos_data = []
    for repo in org.get_repos():
        handle_rate_limit(g)
        print(f"Analyzing repository: {repo.name}")
        repo_data = analyze_repository(repo, start_date, end_date, branch)
        all_repos_data.append({
            'repo_name': repo.name,
            'total_commits': repo_data['total_commits'],
            'commits': repo_data['commits']
        })
    
    # Create monthly breakdown
    monthly_data = []
    for month in range(12):
        month_start = start_date + timedelta(days=30*month)
        month_end = month_start + timedelta(days=30)
        month_commits = sum(
            len([c for c in repo['commits'] if month_start <= c['date'] < month_end])
            for repo in all_repos_data
        )
        monthly_data.append(month_commits)
    
    # Calculate statistics
    total_commits = sum(repo['total_commits'] for repo in all_repos_data)
    avg_monthly = sum(monthly_data) / len(monthly_data)
    predictions = predict_usage(monthly_data)
    
    # Create detailed report
    report = {
        'organization': org_name,
        'analysis_period': {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        },
        'branch_analyzed': branch or 'all',
        'total_commits': total_commits,
        'average_monthly_commits': round(avg_monthly, 2),
        'monthly_breakdown': {
            (start_date + timedelta(days=30*i)).strftime('%Y-%m'): count
            for i, count in enumerate(monthly_data)
        },
        'predictions': predictions,
        'repository_details': [
            {
                'name': repo['repo_name'],
                'total_commits': repo['total_commits']
            }
            for repo in all_repos_data
        ]
    }
    
    # Save report to file
    with open('terraform_usage_report.json', 'w') as f:
        import json
        json.dump(report, f, indent=2)
    
    print("\nAnalysis complete! Report saved to terraform_usage_report.json")
    print(f"\nSummary:")
    print(f"Branch analyzed: {branch or 'all'}")
    print(f"Total Terraform commits: {total_commits}")
    print(f"Average monthly commits: {round(avg_monthly, 2)}")
    print(f"Predicted monthly usage: {predictions['monthly']}")
    print(f"Predicted annual usage: {predictions['annual']}")

if __name__ == "__main__":
    main() 