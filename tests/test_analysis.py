import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import numpy as np
from sklearn.linear_model import LinearRegression

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.providers.github import GitHubProvider
from src.analyzers.terraform import TerraformAnalyzer

def create_monthly_breakdown(start_date: datetime, commits: List[Dict]) -> List[int]:
    """Create monthly breakdown of commits."""
    monthly_data = []
    for month in range(12):
        month_start = start_date + timedelta(days=30*month)
        month_end = month_start + timedelta(days=30)
        month_commits = len([
            c for c in commits 
            if month_start <= c['date'] < month_end
        ])
        monthly_data.append(month_commits)
    return monthly_data

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
        print("Analyzing commits...")
        commits = provider.get_commits(repo_path, start_date, end_date, repo['default_branch'])
        print(f"Found {len(commits)} commits")
        
        # Analyze commits
        print("Analyzing Terraform commits...")
        analyzer = TerraformAnalyzer(provider)
        result = analyzer.analyze_repository(repo['name'], start_date, end_date, commits)
        
        # Create monthly breakdown
        monthly_data = create_monthly_breakdown(start_date, result['commits'])
        
        # Generate predictions
        predictions = predict_usage(monthly_data)
        
        return {
            'name': repo['name'],
            'total_commits': result['total_commits'],
            'monthly_data': monthly_data,
            'predictions': predictions
        }
        
    finally:
        # Clean up cloned repository
        provider.cleanup(repo_path)

def aggregate_statistics(repo_stats: List[Dict]) -> Dict:
    """Aggregate statistics from all repositories."""
    if not repo_stats:
        return {
            'total_commits': 0,
            'monthly_data': [0] * 12,
            'predictions': {'monthly': 0, 'annual': 0}
        }
    
    # Sum up all monthly data
    monthly_data = [0] * 12
    for stat in repo_stats:
        for i, count in enumerate(stat['monthly_data']):
            monthly_data[i] += count
    
    # Calculate total commits
    total_commits = sum(stat['total_commits'] for stat in repo_stats)
    
    # Generate predictions for aggregated data
    predictions = predict_usage(monthly_data)
    
    return {
        'total_commits': total_commits,
        'monthly_data': monthly_data,
        'predictions': predictions
    }

def test_github_provider():
    """Test the GitHub provider with all repositories."""
    # Replace with your GitHub token and organization
    token = os.getenv('GITHUB_TOKEN')
    org_name = os.getenv('GITHUB_ORG')
    
    if not token or not org_name:
        print("Please set GITHUB_TOKEN and GITHUB_ORG environment variables")
        return
    
    try:
        # Initialize provider
        print(f"\nInitializing GitHub provider for organization: {org_name}")
        provider = GitHubProvider(token, org_name)
        
        # Get repositories with Terraform files
        print("\nSearching for repositories with Terraform files...")
        repos = provider.get_repositories(sort='updated', direction='desc')
        
        if not repos:
            print("No repositories with Terraform files found")
            return
            
        print(f"\nFound {len(repos)} repositories with Terraform files")
        
        # Calculate date range (last 365 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        print(f"\nAnalysis period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
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
        print(f"Total repositories analyzed: {len(repo_stats)}")
        print(f"Total Terraform commits: {aggregated['total_commits']}")
        print(f"Average monthly commits: {sum(aggregated['monthly_data']) / len(aggregated['monthly_data']):.1f}")
        print(f"Predicted commits next month: {aggregated['predictions']['monthly']}")
        print(f"Predicted commits next year: {aggregated['predictions']['annual']}")
        print("="*50)
        
        print("\nMonthly Breakdown (All Repositories):")
        for i, count in enumerate(aggregated['monthly_data']):
            month_date = start_date + timedelta(days=30*i)
            print(f"- {month_date.strftime('%Y-%m')}: {count} commits")
        
        # Print per-repository breakdown
        print("\nPer-Repository Breakdown:")
        for stat in repo_stats:
            print(f"\n{stat['name']}:")
            print(f"- Total commits: {stat['total_commits']}")
            print(f"- Average monthly: {sum(stat['monthly_data']) / len(stat['monthly_data']):.1f}")
            print(f"- Predicted monthly: {stat['predictions']['monthly']}")
            
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