"""
Core Compliance Checker Implementation
"""
import os
import uuid
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.integrations.git_client import GitClient
from src.integrations.ollama_client import OllamaClient
from src.core.analyzer import SpecAnalyzer
from src.core.report_generator import ReportGenerator

logger = logging.getLogger(__name__)

class ComplianceChecker:
    """Main compliance checker orchestrator"""
    
    def __init__(self):
        self.git_client = GitClient()
        self.ollama_client = OllamaClient()
        self.analyzer = SpecAnalyzer(self.ollama_client)
        self.report_generator = ReportGenerator()
        
        # Track active checks
        self.active_checks: Dict[str, dict] = {}
        self.check_results: Dict[str, dict] = {}
        
    def check_ollama_health(self) -> dict:
        """Check if Ollama is healthy"""
        return self.ollama_client.health_check()
    
    def start_check(self, repository_url: str, branch: str = 'main',
                   spec_files: Optional[List[str]] = None,
                   target_paths: Optional[List[str]] = None,
                   options: dict = None) -> dict:
        """
        Start a compliance check
        
        Args:
            repository_url: URL of repository to check
            branch: Branch to check
            spec_files: List of spec files to check against
            target_paths: Paths to analyze in repository
            options: Additional options
            
        Returns:
            Dict with check_id and status
        """
        check_id = f"chk_{uuid.uuid4().hex[:12]}"
        
        # Extract repository name
        repo_name = repository_url.rstrip('/').split('/')[-1].replace('.git', '')
        
        check_info = {
            'check_id': check_id,
            'status': 'started',
            'repository': repo_name,
            'repository_url': repository_url,
            'branch': branch,
            'spec_files': spec_files,
            'target_paths': target_paths,
            'options': options or {},
            'started_at': datetime.utcnow().isoformat() + 'Z',
            'estimated_completion': (datetime.utcnow() + timedelta(minutes=5)).isoformat() + 'Z',
            'progress': 0,
            'message': 'Compliance check started successfully'
        }
        
        self.active_checks[check_id] = check_info
        
        # Start check in background thread
        thread = threading.Thread(
            target=self._run_check,
            args=(check_id, repository_url, branch, spec_files, target_paths, options or {})
        )
        thread.daemon = True
        thread.start()
        
        return check_info
    
    def _run_check(self, check_id: str, repository_url: str, branch: str,
                   spec_files: Optional[List[str]], target_paths: Optional[List[str]],
                   options: dict):
        """Run the actual compliance check (in background)"""
        try:
            logger.info(f"Starting compliance check {check_id} for {repository_url}")
            
            # Update progress
            self._update_progress(check_id, 10, "Cloning repository...")
            
            # Clone repository
            git_token = os.getenv('GIT_TOKEN')
            repo_path = self.git_client.clone_repository(repository_url, branch, git_token)
            
            # Update progress
            self._update_progress(check_id, 30, "Loading specifications...")
            
            # Load spec files
            spec_content = self._load_specs(repo_path, spec_files)
            
            # Update progress
            self._update_progress(check_id, 50, "Analyzing code...")
            
            # Analyze compliance
            issues = self.analyzer.analyze_compliance(
                repo_path=repo_path,
                spec_content=spec_content,
                target_paths=target_paths,
                options=options
            )
            
            # Update progress
            self._update_progress(check_id, 80, "Generating report...")
            
            # Generate TODO.md
            todo_content = self.report_generator.generate_todo(
                repository_url=repository_url,
                branch=branch,
                issues=issues
            )
            
            # Save TODO.md to spec repository
            spec_repo_url = os.getenv('SPEC_REPO_URL')
            if spec_repo_url:
                self._commit_todo(check_id, todo_content, repository_url, branch)
            
            # Update progress
            self._update_progress(check_id, 100, "Check completed")
            
            # Store results
            result = {
                'check_id': check_id,
                'status': 'completed',
                'repository': self.active_checks[check_id]['repository'],
                'branch': branch,
                'started_at': self.active_checks[check_id]['started_at'],
                'completed_at': datetime.utcnow().isoformat() + 'Z',
                'progress': 100,
                'results': {
                    'total_issues': len(issues),
                    'critical': len([i for i in issues if i['severity'] == 'critical']),
                    'high': len([i for i in issues if i['severity'] == 'high']),
                    'medium': len([i for i in issues if i['severity'] == 'medium']),
                    'low': len([i for i in issues if i['severity'] == 'low']),
                    'files_analyzed': len(set(i.get('file', '') for i in issues)),
                    'specs_checked': len(spec_content),
                    'todo_file_url': f"{spec_repo_url}/blob/main/TODO.md" if spec_repo_url else None
                }
            }
            
            self.check_results[check_id] = {
                'result': result,
                'todo_content': todo_content
            }
            self.active_checks[check_id].update(result)
            
            # Cleanup
            self.git_client.cleanup_workspace(repo_path)
            
            logger.info(f"Completed compliance check {check_id}")
            
        except Exception as e:
            logger.error(f"Compliance check {check_id} failed: {e}")
            self.active_checks[check_id].update({
                'status': 'failed',
                'completed_at': datetime.utcnow().isoformat() + 'Z',
                'error': str(e)
            })
    
    def _update_progress(self, check_id: str, progress: int, message: str):
        """Update check progress"""
        if check_id in self.active_checks:
            self.active_checks[check_id]['progress'] = progress
            self.active_checks[check_id]['message'] = message
    
    def _load_specs(self, repo_path: str, spec_files: Optional[List[str]]) -> List[dict]:
        """Load specification files"""
        spec_dir = os.path.join(repo_path, 'spec')
        specs = []
        
        if not os.path.exists(spec_dir):
            logger.warning(f"No spec directory found in {repo_path}")
            return specs
        
        # If specific files specified, load those
        if spec_files:
            for spec_file in spec_files:
                spec_path = os.path.join(repo_path, spec_file)
                if os.path.exists(spec_path):
                    with open(spec_path, 'r') as f:
                        specs.append({
                            'file': spec_file,
                            'content': f.read()
                        })
        else:
            # Load all .md files in spec directory
            for filename in os.listdir(spec_dir):
                if filename.endswith('.md'):
                    spec_path = os.path.join(spec_dir, filename)
                    with open(spec_path, 'r') as f:
                        specs.append({
                            'file': f'spec/{filename}',
                            'content': f.read()
                        })
        
        return specs
    
    def _commit_todo(self, check_id: str, todo_content: str, 
                     repository_url: str, branch: str):
        """Commit TODO.md to spec repository"""
        try:
            spec_repo_url = os.getenv('SPEC_REPO_URL')
            git_token = os.getenv('GIT_TOKEN')
            
            self.git_client.commit_todo_file(
                spec_repo_url=spec_repo_url,
                todo_content=todo_content,
                check_info={
                    'check_id': check_id,
                    'repository_url': repository_url,
                    'branch': branch,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                },
                token=git_token
            )
            
        except Exception as e:
            logger.error(f"Failed to commit TODO.md: {e}")
    
    def get_check_status(self, check_id: str) -> Optional[dict]:
        """Get current status of a check"""
        return self.active_checks.get(check_id)
    
    def get_todo_content(self, check_id: str) -> str:
        """Get TODO.md content for a check"""
        result = self.check_results.get(check_id)
        if result:
            return result.get('todo_content', '')
        return ''
    
    def delete_check(self, check_id: str):
        """Delete a check and its data"""
        if check_id in self.active_checks:
            del self.active_checks[check_id]
        if check_id in self.check_results:
            del self.check_results[check_id]
