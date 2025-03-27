import os
import time
import git
import subprocess
from datetime import datetime
from typing import List, Dict, Optional
from github import Github
from .base import GitProvider

class GitHubProvider(GitProvider):
    """GitHub provider implementation."""
    
    def __init__(self, token: str, owner_name: str, clone_dir: str = "temp_repos"):
        self.client = Github(token)
        self.owner_name = owner_name
        self.clone_dir = clone_dir
        self.token = token  # Store token for authentication
        os.makedirs(clone_dir, exist_ok=True)
        
        # Determine if owner is an organization or user
        try:
            self.owner = self.client.get_organization(owner_name)
            self.is_org = True
        except:
            self.owner = self.client.get_user(owner_name)
            self.is_org = False
    
    def get_repositories(self, sort: str = 'updated', direction: str = 'desc') -> List[Dict]:
        """Get list of repositories that contain Terraform files."""
        self.handle_rate_limit()
        
        # Search for repositories containing Terraform files
        query = f'{"org" if self.is_org else "user"}:{self.owner_name} language:hcl'
        repos = self.client.search_repositories(query=query, sort=sort, order=direction)
        
        return [{
            'name': repo.name,
            'updated_at': repo.updated_at,
            'clone_url': repo.clone_url,
            'default_branch': repo.default_branch,
            'private': repo.private
        } for repo in repos]
    
    def clone_repository(self, repo_name: str, repo_data: Dict) -> Optional[str]:
        """Clone a repository to local storage."""
        repo_path = os.path.join(self.clone_dir, repo_name)
        
        # Skip if already cloned
        if os.path.exists(repo_path):
            print(f"Repository {repo_name} already cloned, updating...")
            try:
                repo = git.Repo(repo_path)
                repo.remotes.origin.pull()
                return repo_path
            except Exception as e:
                print(f"Error updating repository {repo_name}: {str(e)}")
                return None
        
        # Clone repository
        try:
            print(f"Cloning repository {repo_name}...")
            # Use HTTPS with token for authentication
            clone_url = repo_data['clone_url']
            if repo_data['private']:
                # Insert token into clone URL for authentication
                clone_url = clone_url.replace('https://', f'https://{self.token}@')
            
            git.Repo.clone_from(clone_url, repo_path)
            return repo_path
        except Exception as e:
            print(f"Error cloning repository {repo_name}: {str(e)}")
            if "Authentication failed" in str(e):
                print("Authentication failed. Please check your GitHub token permissions.")
                print("Required permissions: repo (Full control of private repositories)")
            return None
    
    def get_commits(self, repo_path: str, start_date: Optional[datetime], end_date: datetime, branch: Optional[str] = None) -> List[Dict]:
        """Get commits from a local repository within the specified date range using Git commands."""
        try:
            # Format dates for git log command
            since_date = start_date.strftime("%Y-%m-%d") if start_date else "1970-01-01"
            until_date = end_date.strftime("%Y-%m-%d")
            
            # Construct git log command
            cmd = [
                'git', '-C', repo_path, 'log',
                '--all',
                f'--since={since_date}',
                f'--until={until_date}',
                '--pretty=format:%ad %H %s',
                '--date=format:%Y-%m-%d',
                '--name-only',
                '--', '*.tf', '*.tfvars'
            ]
            
            # Execute git log command
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error running git log: {result.stderr}")
                return []
            
            # Process the output
            commits = []
            current_commit = None
            current_files = []
            
            for line in result.stdout.splitlines():
                if not line.strip():
                    continue
                    
                # Check if this is a commit header (date, hash, message)
                parts = line.split(' ', 2)
                if len(parts) >= 3 and len(parts[1]) == 40:  # SHA-1 hash is 40 chars
                    if current_commit:
                        current_commit['files'] = current_files
                        commits.append(current_commit)
                        current_files = []
                    
                    current_commit = {
                        'date': datetime.strptime(parts[0], '%Y-%m-%d'),
                        'sha': parts[1],
                        'message': parts[2]
                    }
                else:
                    # This is a file name
                    if current_commit and line.strip():
                        current_files.append(line.strip())
            
            # Add the last commit
            if current_commit:
                current_commit['files'] = current_files
                commits.append(current_commit)
            
            return commits
            
        except Exception as e:
            print(f"Error getting commits: {str(e)}")
            return []
    
    def handle_rate_limit(self) -> None:
        """Handle GitHub API rate limits."""
        rate_limit = self.client.get_rate_limit()
        if rate_limit.core.remaining == 0:
            reset_time = rate_limit.core.reset
            wait_time = (reset_time - datetime.now()).total_seconds()
            if wait_time > 0:
                print(f"Rate limit reached. Waiting {wait_time:.2f} seconds...")
                time.sleep(wait_time)
    
    def get_commit_files(self, commit) -> List[str]:
        """Get list of files changed in a commit."""
        return commit['files']
    
    def get_commit_message(self, commit) -> str:
        """Get commit message."""
        return commit['message']
    
    def get_commit_date(self, commit) -> datetime:
        """Get commit date."""
        return commit['date']
    
    def get_commit_branch(self, commit) -> str:
        """Get commit branch name."""
        return commit.get('branch', 'unknown')
    
    def cleanup(self, repo_path: str) -> None:
        """Clean up cloned repository."""
        try:
            import shutil
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)
        except Exception as e:
            print(f"Warning: Could not clean up repository {repo_path}: {str(e)}")