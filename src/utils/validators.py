"""
Request validators
"""
import re

def validate_check_request(data: dict) -> str:
    """
    Validate compliance check request
    
    Args:
        data: Request data dictionary
        
    Returns:
        Error message if invalid, empty string if valid
    """
    if not data:
        return "Request body is required"
    
    # Check required fields
    if 'repository_url' not in data:
        return "Field 'repository_url' is required"
    
    repo_url = data['repository_url']
    
    # Validate URL format
    if not validate_git_url(repo_url):
        return "Invalid repository URL format"
    
    # Validate branch name if provided
    if 'branch' in data:
        branch = data['branch']
        if not isinstance(branch, str) or not branch.strip():
            return "Branch must be a non-empty string"
    
    # Validate spec_files if provided
    if 'spec_files' in data:
        spec_files = data['spec_files']
        if not isinstance(spec_files, list):
            return "spec_files must be an array"
        
        for spec_file in spec_files:
            if not isinstance(spec_file, str):
                return "All spec_files entries must be strings"
    
    # Validate target_paths if provided
    if 'target_paths' in data:
        target_paths = data['target_paths']
        if not isinstance(target_paths, list):
            return "target_paths must be an array"
        
        for path in target_paths:
            if not isinstance(path, str):
                return "All target_paths entries must be strings"
    
    # Validate options if provided
    if 'options' in data:
        options = data['options']
        if not isinstance(options, dict):
            return "options must be an object"
    
    return ""

def validate_git_url(url: str) -> bool:
    """
    Validate Git repository URL
    
    Args:
        url: Repository URL
        
    Returns:
        True if valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    # Check for common Git URL patterns (more flexible)
    patterns = [
        # HTTPS with .git
        r'^https?://[\w\-\.]+(:\d+)?/[\w\-\./@]+\.git$',
        # HTTPS without .git (allows more characters in repo name)
        r'^https?://[\w\-\.]+(:\d+)?/[\w\-\./@]+$',
        # SSH with .git
        r'^git@[\w\-\.]+:[\w\-\./@]+\.git$',
        # SSH without .git
        r'^git@[\w\-\.]+:[\w\-\./@]+$',
        # Git protocol
        r'^git://[\w\-\.]+(:\d+)?/[\w\-\./@]+\.git$',
    ]
    
    for pattern in patterns:
        if re.match(pattern, url):
            return True
    
    return False
