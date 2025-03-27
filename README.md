# Terraform Commits Analysis

This tool analyzes Terraform-related commits across all repositories in a organization to provide insights into infrastructure changes and predict future usage.

## Features

- Analyzes commits affecting Terraform files (`.tf`, `.tfvars`, `.tfvars.json`)
- Excludes commits with `[skip ci]` in the message
- Provides monthly breakdown of Terraform commits
- Calculates average monthly usage
- Predicts future monthly and annual usage based on historical data
- Generates detailed JSON report with repository-specific information
- Efficiently analyzes commits using local Git operations
- Handles private repositories with proper authentication

## Setup

1. Fork or clone this repository
2. Set up the required secrets in your GitHub repository:
   - `GITHUB_TOKEN`: A GitHub token with `repo` scope (automatically provided by GitHub Actions)

## Usage

### GitHub Actions

The analysis can be triggered manually from the Actions tab in your GitHub repository:

1. Go to the "Actions" tab in your repository
2. Select the "Analyze Terraform Commits" workflow
3. Click "Run workflow" and optionally select a branch to analyze
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
   export GITHUB_TOKEN=your_github_token
   ```

3. Run the analysis:
   ```bash
   python tests/test_analysis.py
   ```

## Report Format

The generated report (`terraform_usage_report.json`) includes:

- Organization name
- Analysis period (last 12 months)
- Total number of Terraform commits
- Average monthly commits
- Monthly breakdown of commits
- Usage predictions for next month and year
- Repository-specific details

### Sample Output
```
==================================================
TOTAL ACROSS ALL REPOSITORIES
==================================================
Total repositories analyzed: X
Total Terraform commits: Y
Average monthly commits: Z
Predicted commits next month: A
Predicted commits next year: B

Monthly Breakdown:
- 2023-04: N commits
- 2023-05: M commits
...

Per-Repository Breakdown:
- repo1: X commits
- repo2: Y commits
...
```

## Requirements

- Python 3.12 or higher
- GitHub token with appropriate permissions
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

## Adding New Providers

To add support for a new Git provider:

1. Create a new provider class in `src/providers/` that inherits from `GitProvider`
2. Implement all required methods from the base class
3. Update the main script to support the new provider
4. Add provider-specific dependencies to `requirements.txt` 