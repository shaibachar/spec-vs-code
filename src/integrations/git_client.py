"""
Git Client Integration
"""
import os
import shutil
import logging
import subprocess
import uuid
from typing import Optional

logger = logging.getLogger(__name__)

class GitClient:
    """Handles Git operations for repository cloning and committing"""
    
    def __init__(self):
        self.workspace_base = "/tmp/spec-checker"
        os.makedirs(self.workspace_base, exist_ok=True)
    
    def clone_repository(self, repo_url: str, branch: str = 'main', 
                        token: Optional[str] = None) -> str:
        """
        Clone a Git repository
        
        Args:
            repo_url: Repository URL
            branch: Branch to checkout
            token: Authentication token (optional)
            
        Returns:
            Path to cloned repository
        """
        # Create workspace
        workspace_id = uuid.uuid4().hex
        workspace = os.path.join(self.workspace_base, 'repos', workspace_id)
        os.makedirs(workspace, exist_ok=True)
        
        # Add token to URL if provided
        if token and 'https://' in repo_url:
            # Insert token into URL
            auth_url = repo_url.replace('https://', f'https://{token}@')
        else:
            auth_url = repo_url
        
        try:
            logger.info(f"Cloning {repo_url} (branch: {branch})")
            
            # Clone repository
            subprocess.run([
                'git', 'clone',
                '--depth', '1',
                '--branch', branch,
                '--single-branch',
                auth_url,
                workspace
            ], check=True, timeout=300, capture_output=True, text=True)
            
            logger.info(f"Successfully cloned repository to {workspace}")
            return workspace
            
        except subprocess.TimeoutExpired:
            self.cleanup_workspace(workspace)
            raise Exception(f"Clone operation timed out after 300 seconds")
        except subprocess.CalledProcessError as e:
            self.cleanup_workspace(workspace)
            error_msg = e.stderr if e.stderr else str(e)
            # Don't log token if it's in the error
            safe_error = error_msg.replace(token, '***') if token else error_msg
            raise Exception(f"Failed to clone repository: {safe_error}")
    
    def commit_todo_file(self, spec_repo_url: str, todo_content: str,
                        check_info: dict, token: Optional[str] = None):
        """
        Commit TODO.md to spec repository
        
        Args:
            spec_repo_url: URL of spec repository
            todo_content: Content of TODO.md
            check_info: Information about the check
            token: Git authentication token
        """
        workspace_id = uuid.uuid4().hex
        workspace = os.path.join(self.workspace_base, 'spec-repos', workspace_id)
        
        try:
            # Clone or pull spec repo
            if token and 'https://' in spec_repo_url:
                auth_url = spec_repo_url.replace('https://', f'https://{token}@')
            else:
                auth_url = spec_repo_url
            
            # Clone the spec repo
            subprocess.run([
                'git', 'clone',
                auth_url,
                workspace
            ], check=True, timeout=60, capture_output=True)
            
            # Write TODO.md
            todo_path = os.path.join(workspace, 'TODO.md')
            with open(todo_path, 'w') as f:
                f.write(todo_content)
            
            # Configure git user
            git_user = os.getenv('GIT_USER_NAME', 'Spec Checker Bot')
            git_email = os.getenv('GIT_USER_EMAIL', 'spec-checker@example.com')
            
            subprocess.run(['git', 'config', 'user.name', git_user], 
                         cwd=workspace, check=True)
            subprocess.run(['git', 'config', 'user.email', git_email], 
                         cwd=workspace, check=True)
            
            # Stage changes
            subprocess.run(['git', 'add', 'TODO.md'], cwd=workspace, check=True)
            
            # Create commit message
            commit_msg = (
                f"chore: Update compliance check results for {check_info.get('repository_url', 'repository')}\n\n"
                f"- Check ID: {check_info['check_id']}\n"
                f"- Branch: {check_info.get('branch', 'main')}\n"
                f"- Timestamp: {check_info['timestamp']}"
            )
            
            # Commit
            subprocess.run(['git', 'commit', '-m', commit_msg], 
                         cwd=workspace, check=True, capture_output=True)
            
            # Push
            subprocess.run(['git', 'push'], cwd=workspace, check=True, 
                         timeout=60, capture_output=True)
            
            logger.info(f"Successfully committed TODO.md to {spec_repo_url}")
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            safe_error = error_msg.replace(token, '***') if token else error_msg
            logger.error(f"Failed to commit TODO.md: {safe_error}")
            raise Exception(f"Failed to commit TODO.md: {safe_error}")
        finally:
            self.cleanup_workspace(workspace)
    
    def cleanup_workspace(self, workspace: str):
        """
        Clean up a temporary workspace
        
        Args:
            workspace: Path to workspace
        """
        try:
            # Safety check: only delete under workspace_base
            if workspace.startswith(self.workspace_base) and os.path.exists(workspace):
                shutil.rmtree(workspace)
                logger.info(f"Cleaned up workspace: {workspace}")
        except Exception as e:
            logger.error(f"Failed to cleanup workspace {workspace}: {e}")
