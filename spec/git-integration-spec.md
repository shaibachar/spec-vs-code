# Git Integration Specification

## Overview

This specification defines how the service integrates with Git repositories for reading code and writing compliance results.

## Requirements

### Read Access Requirements

1. **RR-1**: Service SHALL support public repositories without authentication
2. **RR-2**: Service SHALL support private repositories with token authentication
3. **RR-3**: Service SHALL support GitHub, GitLab, and Bitbucket
4. **RR-4**: Service SHALL clone repositories to temporary workspace
5. **RR-5**: Service SHALL support specific branch checkout
6. **RR-6**: Service SHALL handle large repositories efficiently
7. **RR-7**: Service SHALL clean up temporary repositories after use

### Write Access Requirements

1. **WR-1**: Service SHALL commit TODO.md to spec repository
2. **WR-2**: Service SHALL create commits with descriptive messages
3. **WR-3**: Service SHALL handle merge conflicts gracefully
4. **WR-4**: Service SHALL support branch-based workflows
5. **WR-5**: Service SHALL sign commits (if configured)

## Git Client Configuration

### Authentication Methods

1. **Personal Access Token (PAT)**
   - Used for HTTPS cloning
   - Stored as environment variable
   - Supports GitHub, GitLab, Bitbucket
   
   ```bash
   git clone https://<token>@github.com/user/repo.git
   ```

2. **SSH Keys** (Optional)
   - Used for SSH cloning
   - Keys mounted as Docker volume
   - More secure for production
   
   ```bash
   git clone git@github.com:user/repo.git
   ```

3. **OAuth (Future)**
   - User-delegated access
   - Better for multi-user scenarios

### Clone Configuration

```python
{
    "depth": 1,  # Shallow clone by default
    "single_branch": True,
    "branch": "main",
    "sparse_checkout": False,  # Future: only checkout needed paths
    "submodules": False,
    "timeout": 300  # seconds
}
```

## Repository Operations

### 1. Clone Repository

**Purpose**: Download target repository for analysis

**Steps**:
1. Validate repository URL
2. Create temporary workspace directory
3. Execute git clone with authentication
4. Checkout specified branch
5. Verify clone success
6. Return workspace path

**Error Handling**:
- Invalid URL: Return error, don't proceed
- Authentication failure: Check token, return clear error
- Network timeout: Retry with exponential backoff (3 attempts)
- Large repo (>1GB): Warn but continue
- Clone failure: Clean up workspace, return error

**Example**:
```python
def clone_repository(repo_url: str, branch: str, token: str) -> str:
    """
    Clone repository to temporary workspace
    
    Args:
        repo_url: Git repository URL
        branch: Branch to checkout
        token: Authentication token
        
    Returns:
        Path to cloned repository
        
    Raises:
        GitCloneError: If clone fails
    """
    workspace = create_temp_workspace()
    
    # Add token to URL if provided
    if token:
        auth_url = inject_token(repo_url, token)
    else:
        auth_url = repo_url
    
    try:
        subprocess.run([
            'git', 'clone',
            '--depth', '1',
            '--branch', branch,
            '--single-branch',
            auth_url,
            workspace
        ], check=True, timeout=300)
        
        return workspace
    except Exception as e:
        cleanup_workspace(workspace)
        raise GitCloneError(f"Failed to clone {repo_url}: {e}")
```

### 2. Read Repository Files

**Purpose**: Access code files for analysis

**Operations**:
- List files matching patterns
- Read file contents
- Get file metadata (size, last modified)
- Build directory tree

**Optimizations**:
- Cache file contents
- Lazy loading for large files
- Ignore binary files
- Skip vendor/node_modules directories

### 3. Commit Results

**Purpose**: Write TODO.md to spec repository

**Steps**:
1. Clone or pull spec repository
2. Update or create TODO.md file
3. Stage changes
4. Create commit with message
5. Push to remote
6. Handle conflicts if any

**Commit Message Format**:
```
chore: Update compliance check results for <repo-name>

- Repository: <repo-url>
- Branch: <branch>
- Check ID: <check-id>
- Issues Found: <count>
- Timestamp: <timestamp>
```

**Example**:
```python
def commit_todo_file(spec_repo_url: str, todo_content: str, 
                     check_info: dict, token: str):
    """
    Commit TODO.md to spec repository
    
    Args:
        spec_repo_url: URL of spec repository
        todo_content: Content of TODO.md file
        check_info: Metadata about the check
        token: Git authentication token
    """
    workspace = clone_or_pull_spec_repo(spec_repo_url, token)
    
    # Write TODO.md
    todo_path = os.path.join(workspace, 'TODO.md')
    with open(todo_path, 'w') as f:
        f.write(todo_content)
    
    # Commit and push
    git_add(workspace, 'TODO.md')
    commit_message = format_commit_message(check_info)
    git_commit(workspace, commit_message)
    git_push(workspace, token)
    
    cleanup_workspace(workspace)
```

### 4. Cleanup

**Purpose**: Remove temporary repositories

**Steps**:
1. Verify workspace is temporary (safety check)
2. Remove .git directory
3. Remove all files
4. Remove workspace directory

**Safety**:
- Only delete paths under `/tmp/spec-checker/`
- Verify path contains random UUID
- Never delete system directories

## Workspace Management

### Directory Structure

```
/tmp/spec-checker/
├── repos/                    # Cloned repositories
│   ├── <check-id-1>/
│   │   └── <repo-name>/     # Target repo
│   └── <check-id-2>/
│       └── <repo-name>/
└── spec-repos/              # Spec repository clones
    ├── <spec-repo-id>/
    └── ...
```

### Workspace Lifecycle

1. **Creation**: Generate UUID, create directory
2. **Usage**: Clone repo, analyze files
3. **Cleanup**: Remove after check completes or on error
4. **Timeout**: Auto-cleanup workspaces older than 1 hour

### Resource Limits

- **Max concurrent clones**: 5
- **Max workspace size**: 2GB per workspace
- **Max total disk usage**: 10GB
- **Workspace retention**: 1 hour after completion

## Security Considerations

### Token Security

1. **Storage**: Tokens stored in environment variables only
2. **Logging**: Never log tokens or authenticated URLs
3. **Memory**: Clear tokens from memory after use
4. **Transmission**: Only use HTTPS for git operations

### Repository Access

1. **Validation**: Verify repository URLs before cloning
2. **Sandboxing**: Run git commands in isolated environment
3. **Permissions**: Service runs as non-root user
4. **Network**: Limit egress to git providers only

### Data Protection

1. **Isolation**: Each check uses separate workspace
2. **Cleanup**: Securely delete repositories after use
3. **No persistence**: Never store repository code long-term
4. **Encryption**: Encrypt workspace if on shared storage

## Git Provider Support

### GitHub

- **Authentication**: Personal Access Token (classic or fine-grained)
- **URL format**: `https://github.com/user/repo.git`
- **Required scopes**: `repo` (for private repos)
- **API rate limits**: Respect GitHub API limits

### GitLab

- **Authentication**: Personal Access Token or Deploy Token
- **URL format**: `https://gitlab.com/user/repo.git`
- **Required scopes**: `read_repository`, `write_repository`
- **API rate limits**: Respect GitLab API limits

### Bitbucket

- **Authentication**: App Password
- **URL format**: `https://bitbucket.org/user/repo.git`
- **Required scopes**: `repository:read`, `repository:write`

## Error Handling

### Common Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failed | Invalid token | Check token validity and scopes |
| Repository not found | Wrong URL or no access | Verify URL and permissions |
| Clone timeout | Large repo or slow network | Increase timeout or use shallow clone |
| Disk quota exceeded | Too many workspaces | Clean up old workspaces |
| Merge conflict | Concurrent TODO updates | Implement conflict resolution |
| Push rejected | Non-fast-forward | Pull and retry |

### Retry Logic

- **Network errors**: Retry 3 times with exponential backoff
- **Rate limits**: Wait and retry after specified time
- **Transient errors**: Retry twice
- **Fatal errors**: Fail immediately, clean up

## Performance Optimization

### Shallow Clones

Use `--depth 1` for faster clones when full history isn't needed.

### Sparse Checkout (Future)

Only checkout specific directories:
```bash
git sparse-checkout set src/ lib/
```

### Parallel Operations

Clone multiple repositories in parallel with thread pool.

### Caching (Future)

Cache frequently accessed repositories to avoid re-cloning.
