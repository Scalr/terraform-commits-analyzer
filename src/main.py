#!/usr/bin/env python3
import os
import sys
import json
from datetime import datetime, timedelta
from typing import List, Dict

from providers.github import GitHubProvider
from analyzers.terraform import TerraformAnalyzer
from analyzers.usage_predictor import UsagePredictor

def create_monthly_breakdown(start_date: datetime, all_repos_data: List[Dict]) -> List[int]:
    """Create monthly breakdown of commits."""
    monthly_data = []
    for month in range(12):
        month_start = start_date + timedelta(days=30*month)
        month_end = month_start + timedelta(days=30)
        month_commits = sum(
            len([c for c in repo['commits'] if month_start <= c['date'] < month_end])
            for repo in all_repos_data
        )
        monthly_data.append(month_commits)
    return monthly_data

def generate_report(
    org_name: str,
    start_date: datetime,
    end_date: datetime,
    branch: str,
    all_repos_data: List[Dict],
    monthly_data: List[int]
) -> Dict:
    """Generate the final report."""
    total_commits = sum(repo['total_commits'] for repo in all_repos_data)
    avg_monthly = sum(monthly_data) / len(monthly_data)
    predictions = UsagePredictor.predict(monthly_data)
    
    return {
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
    
    # Initialize provider and analyzer
    provider = GitHubProvider(github_token, org_name)
    analyzer = TerraformAnalyzer(provider)
    
    # Calculate date range (last 12 months)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    # Analyze all repositories
    all_repos_data = []
    for repo in provider.get_repositories():
        print(f"Analyzing repository: {repo['name']}")
        repo_data = analyzer.analyze_repository(repo['name'], start_date, end_date, branch)
        all_repos_data.append({
            'repo_name': repo['name'],
            'total_commits': repo_data['total_commits'],
            'commits': repo_data['commits']
        })
    
    # Create monthly breakdown
    monthly_data = create_monthly_breakdown(start_date, all_repos_data)
    
    # Generate and save report
    report = generate_report(org_name, start_date, end_date, branch, all_repos_data, monthly_data)
    
    with open('terraform_usage_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("\nAnalysis complete! Report saved to terraform_usage_report.json")
    print(f"\nSummary:")
    print(f"Branch analyzed: {branch or 'all'}")
    print(f"Total Terraform commits: {report['total_commits']}")
    print(f"Average monthly commits: {report['average_monthly_commits']}")
    print(f"Predicted monthly usage: {report['predictions']['monthly']}")
    print(f"Predicted annual usage: {report['predictions']['annual']}")

if __name__ == "__main__":
    main() 