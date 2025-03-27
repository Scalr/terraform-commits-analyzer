from datetime import datetime
from typing import List, Dict, Optional
from ..providers.base import GitProvider

class TerraformAnalyzer:
    """Analyzer for Terraform-related commits."""
    
    def __init__(self, provider: GitProvider):
        self.provider = provider
        self.terraform_extensions = {'.tf', '.tfvars', '.tfvars.json'}
    
    def is_terraform_file(self, filename: str) -> bool:
        """Check if a file is a Terraform file."""
        return any(filename.endswith(ext) for ext in self.terraform_extensions)
    
    def is_skip_ci(self, commit) -> bool:
        """Check if commit message contains [skip ci]."""
        return '[skip ci]' in self.provider.get_commit_message(commit).lower()
    
    def analyze_repository(self, repo_name: str, start_date: datetime, end_date: datetime, commits: Optional[List[Dict]] = None) -> Dict:
        """Analyze Terraform commits in a repository."""
        if commits is None:
            commits = self.provider.get_commits(repo_name, start_date, end_date)
            
        terraform_commits = []
        
        for commit in commits:
            if self.is_skip_ci(commit):
                continue
                
            files = self.provider.get_commit_files(commit)
            terraform_files = [f for f in files if self.is_terraform_file(f)]
            
            if terraform_files:
                terraform_commits.append({
                    'date': self.provider.get_commit_date(commit),
                    'files': terraform_files,
                    'message': self.provider.get_commit_message(commit),
                    'branch': self.provider.get_commit_branch(commit)
                })
        
        return {
            'total_commits': len(terraform_commits),
            'commits': terraform_commits
        } 