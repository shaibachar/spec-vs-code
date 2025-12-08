"""
Spec Analyzer - Uses Ollama to analyze code against specifications
"""
import os
import re
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class SpecAnalyzer:
    """Analyzes code compliance against specifications using Ollama"""
    
    def __init__(self, ollama_client):
        self.ollama_client = ollama_client
    
    def analyze_compliance(self, repo_path: str, spec_content: List[dict],
                          target_paths: Optional[List[str]] = None,
                          options: dict = None) -> List[dict]:
        """
        Analyze repository for spec compliance
        
        Args:
            repo_path: Path to cloned repository
            spec_content: List of spec files with content
            target_paths: Specific paths to analyze
            options: Analysis options
            
        Returns:
            List of compliance issues found
        """
        issues = []
        options = options or {}
        
        logger.info(f"Analyzing {len(spec_content)} spec files")
        
        # Get code files to analyze
        code_files = self._get_code_files(repo_path, target_paths)
        
        logger.info(f"Analyzing {len(code_files)} code files")
        
        # For each spec, check compliance
        for spec in spec_content:
            spec_issues = self._analyze_spec(spec, code_files, repo_path, options)
            issues.extend(spec_issues)
        
        # Sort by severity
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        issues.sort(key=lambda x: severity_order.get(x['severity'], 99))
        
        return issues
    
    def _get_code_files(self, repo_path: str, target_paths: Optional[List[str]]) -> List[str]:
        """Get list of code files to analyze"""
        code_files = []
        
        # Common code file extensions
        code_extensions = {
            '.py', '.js', '.ts', '.java', '.go', '.rb', '.php', '.cs',
            '.cpp', '.c', '.h', '.hpp', '.rs', '.kt', '.swift', '.m'
        }
        
        # Directories to skip
        skip_dirs = {
            '.git', 'node_modules', 'vendor', 'venv', 'env', '__pycache__',
            'build', 'dist', 'target', '.pytest_cache', 'coverage'
        }
        
        # If target paths specified, only scan those
        scan_paths = target_paths if target_paths else [repo_path]
        
        for scan_path in scan_paths:
            full_path = os.path.join(repo_path, scan_path) if not os.path.isabs(scan_path) else scan_path
            
            if os.path.isfile(full_path):
                code_files.append(full_path)
            elif os.path.isdir(full_path):
                for root, dirs, files in os.walk(full_path):
                    # Skip unwanted directories
                    dirs[:] = [d for d in dirs if d not in skip_dirs]
                    
                    for file in files:
                        ext = os.path.splitext(file)[1]
                        if ext in code_extensions:
                            code_files.append(os.path.join(root, file))
        
        return code_files
    
    def _analyze_spec(self, spec: dict, code_files: List[str], 
                     repo_path: str, options: dict) -> List[dict]:
        """Analyze code files against a single spec"""
        issues = []
        
        spec_file = spec['file']
        spec_content = spec['content']
        
        # Extract requirements from spec
        requirements = self._extract_requirements(spec_content)
        
        logger.info(f"Checking {len(requirements)} requirements from {spec_file}")
        
        # For demonstration, create sample issues
        # In production, this would use Ollama to analyze each requirement
        if not requirements:
            # No explicit requirements found, do basic analysis
            issues.append({
                'severity': 'low',
                'type': 'documentation',
                'title': f'No explicit requirements found in {spec_file}',
                'spec_file': spec_file,
                'description': 'The specification file does not contain clearly marked requirements',
                'suggestion': 'Add explicit requirements using markers like FR-1, NFR-1, or SHALL statements'
            })
        else:
            # Check each requirement
            for req in requirements[:5]:  # Limit for demo
                # In production: Use Ollama to check if requirement is implemented
                # For now, create placeholder issue
                issue = self._check_requirement_with_ollama(req, code_files, spec_file, repo_path)
                if issue:
                    issues.append(issue)
        
        return issues
    
    def _extract_requirements(self, spec_content: str) -> List[dict]:
        """Extract requirements from spec content"""
        requirements = []
        
        # Look for numbered requirements (FR-1, NFR-1, etc.)
        req_pattern = r'((?:FR|NFR|SR)-\d+):?\s*(.+?)(?=\n|$)'
        
        for match in re.finditer(req_pattern, spec_content):
            requirements.append({
                'id': match.group(1),
                'text': match.group(2).strip()
            })
        
        # Also look for SHALL statements
        shall_pattern = r'(?:The service|Service|System)\s+SHALL\s+(.+?)(?=\n|$)'
        
        for i, match in enumerate(re.finditer(shall_pattern, spec_content, re.IGNORECASE)):
            requirements.append({
                'id': f'REQ-{i+1}',
                'text': match.group(0).strip()
            })
        
        return requirements
    
    def _check_requirement_with_ollama(self, requirement: dict, code_files: List[str],
                                      spec_file: str, repo_path: str) -> Optional[dict]:
        """
        Use Ollama to check if a requirement is implemented
        
        This is a simplified version. In production, this would:
        1. Build context from relevant code files
        2. Create detailed prompt for Ollama
        3. Parse Ollama response
        4. Return structured issue if non-compliant
        """
        try:
            # For demo: Create a sample issue for some requirements
            req_text = requirement['text'].lower()
            
            # Simple heuristic: If requirement mentions "authentication" or "security"
            # and we don't find related code, flag it
            if 'authentication' in req_text or 'auth' in req_text:
                # Check if any code file mentions auth
                has_auth = False
                for f in code_files[:10]:
                    if not os.path.exists(f):
                        continue
                    try:
                        with open(f, 'r', encoding='utf-8', errors='ignore') as file:
                            content = file.read(10000)  # Read max 10KB per file
                            if 'auth' in content.lower():
                                has_auth = True
                                break
                    except Exception:
                        continue
                
                if not has_auth:
                    return {
                        'severity': 'high',
                        'type': 'missing_implementation',
                        'title': f'Requirement {requirement["id"]} may not be implemented',
                        'spec_file': spec_file,
                        'requirement_id': requirement['id'],
                        'requirement_text': requirement['text'],
                        'description': 'No evidence of authentication implementation found in code',
                        'suggestion': 'Implement authentication as specified in the requirement',
                        'files_checked': len(code_files)
                    }
            
            # Could add more heuristics or use Ollama for real analysis
            return None
            
        except Exception as e:
            logger.error(f"Error checking requirement {requirement['id']}: {e}")
            return None
