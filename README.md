# Terraform Commits Analysis

This tool analyzes Terraform-related commits across repositories in a GitHub organization or user account to provide insights into infrastructure changes and predict future usage.

## Features

- Analyzes commits affecting Terraform files (`.tf`, `.tfvars`, `.tfvars.json`)
- Excludes commits with `[skip ci]` in the message
- Provides monthly breakdown of Terraform commits
- Calculates average monthly usage
- Predicts future monthly and annual usage based on historical data and growth factors
- Generates detailed JSON report with repository-specific information
- Efficiently analyzes commits using local Git operations
- Handles private repositories with proper authentication
- Supports both organization and individual user repositories

## Setup

1. Fork or clone this repository
2. Create a Personal Access Token (PAT):
   - Go to GitHub Settings → Developer Settings → Personal Access Tokens → Tokens (classic)
   - Generate a new token with the following permissions:
     - `repo` (Full control of private repositories)
     - `read:org` (Read organization data, if analyzing organization repositories)
   - Copy the generated token

3. Set up the required secrets in your GitHub repository:
   - `PAT_TOKEN`: The Personal Access Token you created (required for accessing private repositories)
   - Note: The default `GITHUB_TOKEN` is not sufficient as it can only access the current repository and public repositories

## Usage

### GitHub Actions

The analysis can be triggered manually from the Actions tab in your GitHub repository:

1. Go to the "Actions" tab in your repository
2. Select the "Analyze Terraform Commits" workflow
3. Click "Run workflow" and optionally select:
   - Branch to analyze
   - Owner (organization or username) to analyze
   - Number of days to analyze
4. Wait for the analysis to complete
5. View the results in the workflow logs
6. Download the detailed report from the artifacts section

### Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables:
   ```bash
   export GITHUB_TOKEN=your_personal_access_token
   export GITHUB_OWNER=organization_or_username  # Can be either an organization name or a username
   ```

3. Run the analysis:
   ```bash
   python tests/test_analysis.py
   ```

## Report Format

The generated report (`terraform_usage_report.json`) includes:

- Owner information (organization or user)
- Analysis period
- Total number of Terraform commits
- Average monthly commits
- Monthly breakdown of commits
- Usage predictions for next month and year
- Repository-specific details
- Prediction confidence level and factors

### Sample Output
```
==================================================
TOTAL ACROSS ALL REPOSITORIES
==================================================
Owner type: Organization/User
Total repositories analyzed: X
Active repositories: Y
Total Terraform commits: Z
Average monthly commits: A
Predicted commits next month: B (Confidence: high/medium/low)
Predicted commits next year: C (Confidence: high/medium/low)

Monthly Breakdown:
- 2023-04: N commits
- 2023-05: M commits
...

Per-Repository Breakdown:
- repo1: X commits
- repo2: Y commits
...

Inactive Repositories (excluded from predictions):
- inactive-repo1, inactive-repo2

Prediction Factors:
- Historical trend: +X commits/month
- Growth rate: Y%
- Data variance: Z
```

## Usage Predictions

The tool provides usage predictions based on historical commit data and several factors:

### Prediction Factors
1. Historical Trend
   - Linear regression analysis of commit patterns
   - Weighted by recent activity
   - Adjusted for seasonal variations

2. Growth Rate
   - Default assumption of 10% monthly growth
   - Accounts for team expansion
   - Considers infrastructure complexity changes

3. Confidence Level
   - Based on data variance and sample size
   - Indicates prediction reliability
   - Helps in decision making

### Prediction Limitations

The predictions are based on commit history and may not accurately reflect actual Terraform runs due to several factors:

1. Multiple Workspaces
   - One folder may be used by different workspaces
   - Each workspace may execute multiple runs
   - Some workspaces may be more active than others

2. Various Trigger Methods
   - Runs can be triggered by VCS commits
   - Manual runs via UI/API/CLI
   - Scheduled runs
   - External integrations

3. Growth Factors
   - Usage may start small and grow as more workspaces are added
   - New repositories may be onboarded
   - Team size and adoption may increase
   - Infrastructure complexity may change

Please use these predictions as a rough estimate and adjust based on your specific circumstances.

## Requirements

- Python 3.12 or higher
- GitHub Personal Access Token with `repo` and `read:org` permissions
- Git installed on the system

## Project Structure

```
.
├── .github/
│   └── workflows/
│       └── analyze-terraform-commits.yml  # GitHub Actions workflow
├── src/
│   ├── providers/           # Git provider implementations
│   │   ├── base.py         # Abstract base class for providers
│   │   └── github.py       # GitHub provider implementation
│   ├── analyzers/          # Analysis implementations
│   │   ├── terraform.py    # Terraform-specific analysis
│   │   └── usage_predictor.py  # Usage prediction logic
│   └── main.py            # Main script
├── tests/
│   └── test_analysis.py   # Test script for local development
├── requirements.txt       # Python dependencies
├── .gitignore           # Git ignore rules
└── README.md           # This file
```

## Rate Limits

The script automatically handles GitHub API rate limits by:
- Using GitHub's search API to efficiently find repositories
- Cloning repositories locally for commit analysis
- Using Git commands for commit analysis instead of API calls
- Checking remaining API calls before each request
- Waiting when rate limits are reached
- Resuming automatically when the rate limit resets

Note: Personal Access Tokens have higher rate limits than the default `GITHUB_TOKEN`:
- 5,000 requests per hour for authenticated requests
- 30 requests per minute for the Search API

## Adding New Providers

To add support for a new Git provider:

1. Create a new provider class in `src/providers/` that inherits from `GitProvider`
2. Implement all required methods from the base class
3. Update the main script to support the new provider
4. Add provider-specific dependencies to `requirements.txt` 