from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional

class GitProvider(ABC):
    """Abstract base class for Git providers."""
    
    @abstractmethod
    def get_repositories(self) -> List[Dict]:
        """Get list of repositories available to the user."""
        pass
    
    @abstractmethod
    def get_commits(self, repo_name: str, start_date: datetime, end_date: datetime, branch: Optional[str] = None) -> List[Dict]:
        """Get commits from a repository within the specified date range."""
        pass
    
    @abstractmethod
    def handle_rate_limit(self) -> None:
        """Handle provider-specific rate limits."""
        pass
    
    @abstractmethod
    def get_commit_files(self, commit) -> List[str]:
        """Get list of files changed in a commit."""
        pass
    
    @abstractmethod
    def get_commit_message(self, commit) -> str:
        """Get commit message."""
        pass
    
    @abstractmethod
    def get_commit_date(self, commit) -> datetime:
        """Get commit date."""
        pass
    
    @abstractmethod
    def get_commit_branch(self, commit) -> str:
        """Get commit branch name."""
        pass 