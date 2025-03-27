import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.providers.github import GitHubProvider
from src.analyzers.terraform import TerraformAnalyzer
from src.analyzers.usage_predictor import UsagePredictor

def create_monthly_breakdown(start_date: datetime, end_date: datetime, commits: List[Dict]) -> List[int]:
    """Create monthly breakdown of commits."""
    # Calculate number of months between dates
    months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
    monthly_data = []
    
    current_date = start_date
    while current_date <= end_date:
        # Calculate end of current month
        if current_date.month == 12:
            month_end = datetime(current_date.year + 1, 1, 1)
        else:
            month_end = datetime(current_date.year, current_date.month + 1, 1)
        
        # Count commits in this month
        month_commits = len([
            c for c in commits 
            if current_date <= c['date'] < month_end
        ])
        monthly_data.append(month_commits)
        
        # Move to next month
        current_date = month_end
    
    return monthly_data

def predict_usage(monthly_data: List[int]) -> Dict:
    """Predict future usage based on historical data."""
    predictor = UsagePredictor(growth_rate=0.1)  # 10% monthly growth rate
    return predictor.predict_usage(monthly_data)

def analyze_repository(provider: GitHubProvider, repo: Dict, start_date: datetime, end_date: datetime) -> Optional[Dict]:
    """Analyze a single repository and return its statistics."""
    print(f"\nAnalyzing repository: {repo['name']}")
    
    # Clone repository
    repo_path = provider.clone_repository(repo['name'], repo)
    if not repo_path:
        print("Failed to clone repository")
        return None
        
    try:
        # Get commits
        commits = provider.get_commits(repo_path, start_date, end_date, repo['default_branch'])

        # Analyze commits
        print("Analyzing Terraform commits...")
        analyzer = TerraformAnalyzer(provider)
        result = analyzer.analyze_repository(repo['name'], start_date, end_date, commits)
        print(f"Found {len(result['commits'])} commits")
        
        # Create monthly breakdown
        monthly_data = create_monthly_breakdown(start_date, end_date, result['commits'])
        
        # Generate predictions
        predictions = predict_usage(monthly_data)
        
        return {
            'name': repo['name'],
            'total_commits': result['total_commits'],
            'monthly_data': monthly_data,
            'predictions': predictions,
            'commits': result['commits']  # Include the commits in the returned statistics
        }
        
    finally:
        # Clean up cloned repository
        provider.cleanup(repo_path)

def aggregate_statistics(repo_stats: List[Dict]) -> Dict:
    """Aggregate statistics from all repositories."""
    if not repo_stats:
        return {
            'total_commits': 0,
            'monthly_data': [],
            'predictions': {
                'monthly': 0,
                'annual': 0,
                'confidence': 'low',
                'factors': {
                    'historical_trend': 0,
                    'growth_rate': 0,
                    'variance': 0
                }
            }
        }
    
    # Filter out non-active repositories (those with no commits)
    active_repo_stats = [stat for stat in repo_stats if stat['total_commits'] > 0]
    
    if not active_repo_stats:
        return {
            'total_commits': 0,
            'monthly_data': [],
            'predictions': {
                'monthly': 0,
                'annual': 0,
                'confidence': 'low',
                'factors': {
                    'historical_trend': 0,
                    'growth_rate': 0,
                    'variance': 0
                }
            }
        }
    
    # Get the length of monthly data from the first repository
    monthly_length = len(active_repo_stats[0]['monthly_data'])
    
    # Sum up all monthly data
    monthly_data = [0] * monthly_length
    for stat in active_repo_stats:
        for i, count in enumerate(stat['monthly_data']):
            monthly_data[i] += count
    
    # Calculate total commits
    total_commits = sum(stat['total_commits'] for stat in active_repo_stats)
    
    # Generate predictions for aggregated data
    predictions = predict_usage(monthly_data)
    
    return {
        'total_commits': total_commits,
        'monthly_data': monthly_data,
        'predictions': predictions,
        'active_repos': len(active_repo_stats),
        'total_repos': len(repo_stats)
    }

def test_github_provider():
    """Test the GitHub provider with all repositories."""
    # Replace with your GitHub token and owner (organization or user)
    token = os.getenv('GITHUB_TOKEN')
    owner_name = os.getenv('GITHUB_OWNER')  # Can be either organization or user
    analysis_days = int(os.getenv('ANALYSIS_DAYS', '730'))
    
    if not token or not owner_name:
        print("Please set GITHUB_TOKEN and GITHUB_OWNER environment variables")
        print("GITHUB_OWNER can be either an organization name or a username")
        return
    
    try:
        # Initialize provider
        print(f"\nInitializing GitHub provider for owner: {owner_name}")
        provider = GitHubProvider(token, owner_name)
        
        # Get repositories with Terraform files
        print("\nSearching for repositories with Terraform files...")
        repos = provider.get_repositories(sort='updated', direction='desc')
        
        if not repos:
            print("No repositories with Terraform files found")
            return
            
        print(f"\nFound {len(repos)} repositories with Terraform files")
        
        # Calculate date range
        end_date = datetime.now()
        if analysis_days > 0:
            start_date = end_date - timedelta(days=analysis_days)
            print(f"\nAnalyzing last {analysis_days} days")
        else:
            # For all-time analysis, we'll let the provider determine the start date
            start_date = None
            print("\nAnalyzing all-time commits")
        
        print(f"Analysis period: {start_date.strftime('%Y-%m-%d') if start_date else 'repository creation'} to {end_date.strftime('%Y-%m-%d')}")
        
        # Analyze all repositories
        repo_stats = []
        for repo in repos:
            stats = analyze_repository(provider, repo, start_date, end_date)
            if stats:
                repo_stats.append(stats)
        
        # Aggregate statistics
        aggregated = aggregate_statistics(repo_stats)
        
        # Print results with clear totals
        print("\n" + "="*50)
        print("TOTAL ACROSS ALL REPOSITORIES")
        print("="*50)
        print(f"Owner type: {'Organization' if provider.is_org else 'User'}")
        print(f"Total repositories analyzed: {aggregated['total_repos']}")
        print(f"Active repositories: {aggregated['active_repos']}")
        print(f"Total Terraform commits: {aggregated['total_commits']}")
        print(f"Average monthly commits: {sum(aggregated['monthly_data']) / len(aggregated['monthly_data']):.1f}")
        print(f"Predicted commits next month: {aggregated['predictions']['monthly']} (Confidence: {aggregated['predictions']['confidence']})")
        print(f"Predicted commits next year: {aggregated['predictions']['annual']} (Confidence: {aggregated['predictions']['confidence']})")
        print("="*50)
        
        print("\nMonthly Breakdown:")
        # Find the earliest commit date from all repositories
        earliest_date = None
        for stat in repo_stats:
            if stat['commits']:
                repo_earliest = min(commit['date'] for commit in stat['commits'])
                if earliest_date is None or repo_earliest < earliest_date:
                    earliest_date = repo_earliest
        
        # Use the earliest commit date or start_date if specified
        current_date = start_date if start_date else earliest_date
        if current_date:
            for count in aggregated['monthly_data']:
                print(f"- {current_date.strftime('%Y-%m')}: {count} commits")
                # Move to next month
                if current_date.month == 12:
                    current_date = datetime(current_date.year + 1, 1, 1)
                else:
                    current_date = datetime(current_date.year, current_date.month + 1, 1)
        
        # Print per-repository breakdown
        print("\nPer-Repository Breakdown:")
        active_repos = []
        inactive_repos = []
        
        for stat in repo_stats:
            if stat['total_commits'] > 0:
                active_repos.append(stat)
            else:
                inactive_repos.append(stat['name'])
        
        # Print active repositories with full details
        for stat in active_repos:
            print(f"\n{stat['name']}:")
            print(f"- Total commits: {stat['total_commits']}")
            print(f"- Average monthly: {sum(stat['monthly_data']) / len(stat['monthly_data']):.1f}")
            print(f"- Predicted monthly: {stat['predictions']['monthly']}")
        
        # Print inactive repositories summary
        if inactive_repos:
            print(f"\nInactive Repositories (excluded from predictions):")
            print(f"- {', '.join(inactive_repos)}")
        
        # Print prediction factors
        print("\nPrediction Factors (Based on Active Repositories):")
        print(f"- Historical trend: {aggregated['predictions']['factors']['historical_trend']} commits/month")
        print(f"- Growth rate: {aggregated['predictions']['factors']['growth_rate'] * 100}%")
        print(f"- Data variance: {aggregated['predictions']['factors']['variance']}")
        
        # Save report to file
        report = {
            'owner': {
                'name': owner_name,
                'type': 'organization' if provider.is_org else 'user'
            },
            'analysis_period': {
                'start_date': start_date.strftime('%Y-%m-%d') if start_date else 'repository creation',
                'end_date': end_date.strftime('%Y-%m-%d'),
                'days_analyzed': analysis_days if analysis_days > 0 else 'all-time'
            },
            'total_repositories': aggregated['total_repos'],
            'active_repositories': aggregated['active_repos'],
            'total_commits': aggregated['total_commits'],
            'average_monthly_commits': sum(aggregated['monthly_data']) / len(aggregated['monthly_data']),
            'monthly_breakdown': {
                # Create monthly breakdown using end_date as reference
                (end_date - timedelta(days=30*(len(aggregated['monthly_data'])-i-1))).strftime('%Y-%m'): count
                for i, count in enumerate(aggregated['monthly_data'])
            },
            'predictions': aggregated['predictions'],
            'repository_details': {
                'active': [
                    {
                        'name': stat['name'],
                        'total_commits': stat['total_commits'],
                        'average_monthly': sum(stat['monthly_data']) / len(stat['monthly_data']),
                        'predictions': stat['predictions']
                    }
                    for stat in active_repos
                ],
                'inactive': inactive_repos
            }
        }
        
        with open('terraform_usage_report.json', 'w') as f:
            import json
            json.dump(report, f, indent=2)
            
    except Exception as e:
        print(f"\nError during analysis: {str(e)}")
        if "Not Found" in str(e):
            print("\nPossible issues:")
            print("1. The organization name might be incorrect")
            print("2. Your token might not have access to the organization")
            print("3. The organization might not exist")
        elif "Bad credentials" in str(e):
            print("\nAuthentication error: Please check your GitHub token")
        else:
            print("\nUnexpected error occurred. Please check the error message above.")

if __name__ == "__main__":
    test_github_provider() 