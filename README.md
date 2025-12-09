# Spec Compliance Checker Service

A self-hosted Docker service that uses AI (Ollama) to analyze code repositories and check compliance against specification documents. The service generates detailed TODO.md files highlighting gaps between specifications and implementation.

## Overview

This service provides automated spec compliance checking by:
- Analyzing code repositories against specification documents
- Using local LLM (Ollama with CodeLlama) for intelligent code analysis
- Generating detailed TODO.md files with compliance issues
- Committing results to a spec repository for tracking

## Features

- **AI-Powered Analysis**: Uses Ollama (CodeLlama) for intelligent code understanding
- **Docker-Based**: Easy deployment with Docker Compose
- **REST API**: Trigger checks and retrieve results via API
- **Git Integration**: Supports GitHub, GitLab, and Bitbucket repositories
- **Detailed Reports**: Generates comprehensive TODO.md with actionable items
- **Security-First**: Runs as non-root user, supports token-based authentication
- **Concurrent Checks**: Supports multiple simultaneous compliance checks

## Architecture

The service consists of two main components:

1. **Spec Compliance Service**: Python-based REST API service
2. **Ollama Server**: Local LLM server for code analysis

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Environment                        │
│                                                              │
│  ┌──────────────────┐         ┌─────────────────────┐      │
│  │  Spec Compliance │         │   Ollama Server     │      │
│  │     Service      │◄────────┤   (CodeLlama)       │      │
│  │   (Port 8080)    │         │   (Port 11434)      │      │
│  └────────┬─────────┘         └─────────────────────┘      │
│           │                                                  │
│           ▼                                                  │
│    Git Repositories ──► Code Analysis ──► TODO.md           │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Git repository access (public or with token for private repos)
- At least 8GB RAM (for Ollama model)
- 10GB disk space (for Docker images and models)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/shaibachar/spec-vs-code.git
   cd spec-vs-code
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and set your values
   ```

3. **Start the service**:
   ```bash
   docker-compose up -d
   ```

4. **Wait for Ollama to download the model** (first time only):
   ```bash
   docker-compose logs -f ollama-init
   ```

5. **Check service health**:
   ```bash
   curl http://localhost:8080/api/v1/health
   ```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Git Configuration
GIT_TOKEN=your_github_personal_access_token
SPEC_REPO_URL=https://github.com/your-org/your-spec-repo.git
GIT_USER_NAME=Spec Checker Bot
GIT_USER_EMAIL=spec-checker@example.com

# API Security
API_KEY=your_secure_api_key

# Ollama Configuration (defaults work with docker-compose)
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=codellama:7b-instruct

# Service Configuration
SERVICE_PORT=8080
LOG_LEVEL=INFO
MAX_CONCURRENT_CHECKS=3
```

### Getting a Git Token

**GitHub**:
1. Go to Settings → Developer Settings → Personal Access Tokens
2. Generate new token with `repo` scope
3. Copy the token to `GIT_TOKEN` in `.env`

**GitLab**:
1. Go to Preferences → Access Tokens
2. Create token with `read_repository` and `write_repository` scopes

**Bitbucket**:
1. Go to Personal Settings → App Passwords
2. Create app password with repository read/write permissions

## API Usage

### Authentication

All API endpoints (except `/health`) require an API key:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:8080/api/v1/...
```

### Trigger Compliance Check

```bash
curl -X POST http://localhost:8080/api/v1/compliance/check \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/username/repo.git",
    "branch": "main",
    "spec_files": ["spec/service-spec.md", "spec/api-spec.md"],
    "target_paths": ["src/", "lib/"],
    "options": {
      "deep_analysis": true,
      "include_suggestions": true
    }
  }'
```

Response:
```json
{
  "check_id": "chk_a1b2c3d4e5f6",
  "status": "started",
  "repository": "repo",
  "branch": "main",
  "estimated_completion": "2025-12-08T04:15:29Z"
}
```

### Get Check Status

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8080/api/v1/compliance/check/chk_a1b2c3d4e5f6
```

### Get TODO Report

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8080/api/v1/compliance/check/chk_a1b2c3d4e5f6/todo
```

## Specification Format

Place specification files in a `spec/` folder in your repository. Use Markdown format with clear requirements:

```markdown
# Service Specification

## Requirements

### Functional Requirements

1. **FR-1**: The service SHALL provide a REST API
2. **FR-2**: The service SHALL support authentication
3. **FR-3**: The service SHALL log all requests

## API Endpoints

### POST /api/users
- Creates a new user
- Requires authentication
- Returns 201 on success
```

## Output Format

The service generates `TODO.md` files with this structure:

```markdown
# TODO: Spec Compliance Issues

**Generated**: 2025-12-08 04:09:29 UTC
**Repository**: https://github.com/username/repo.git
**Branch**: main
**Total Issues**: 15

## Summary
- **Critical**: 2
- **High**: 5
- **Medium**: 6
- **Low**: 2

## Critical Issues (2)

### 1. Missing Authentication in API Endpoint
- **Severity**: Critical
- **Type**: Missing Implementation
- **Spec Reference**: spec/api-spec.md
- **Requirement**: FR-2
- **Description**: The /api/users endpoint does not implement authentication
- **Suggestion**: Add authentication middleware to the endpoint
```

## Development

### Project Structure

```
spec-vs-code/
├── spec/                   # Specification files
│   ├── README.md
│   ├── service-spec.md
│   ├── api-spec.md
│   ├── compliance-check-spec.md
│   ├── git-integration-spec.md
│   └── ollama-integration-spec.md
├── src/                    # Service source code
│   ├── main.py            # Application entry point
│   ├── api/               # REST API routes
│   ├── core/              # Core compliance checking logic
│   ├── integrations/      # Git and Ollama clients
│   └── utils/             # Utilities
├── config/                 # Configuration files
├── Dockerfile             # Service container definition
├── docker-compose.yml     # Docker Compose configuration
├── requirements.txt       # Python dependencies
└── .env.example          # Environment variable template
```

### Running Tests

```bash
# TODO: Add tests
python -m pytest tests/
```

### Local Development

Run the service locally without Docker:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OLLAMA_HOST=http://localhost:11434
export API_KEY=test-key

# Run Ollama separately (or via Docker)
docker run -d -p 11434:11434 ollama/ollama

# Start the service
python -m src.main
```

## Troubleshooting

### Ollama Connection Issues

If the service can't connect to Ollama:
1. Check Ollama container is running: `docker-compose ps`
2. Check Ollama health: `curl http://localhost:11434/api/tags`
3. Check logs: `docker-compose logs ollama`

### Model Not Found

If Ollama model is not available:
```bash
# Manually pull the model
docker-compose exec ollama ollama pull codellama:7b-instruct
```

### Git Clone Failures

- Verify `GIT_TOKEN` is set correctly
- Check repository URL is accessible
- Ensure token has required permissions

## Security Considerations

- Service runs as non-root user
- Git tokens are stored as environment variables (not in code)
- API requires authentication (API key)
- Docker network isolation between components
- Repository code is not persisted after analysis

## Performance

- **Typical check duration**: 2-5 minutes
- **Concurrent checks**: Up to 3 simultaneous (configurable)
- **Repository size limit**: 1GB (configurable)
- **Ollama memory usage**: ~4-8GB (depends on model size)

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

See [LICENSE](LICENSE) file for details.

## Support

For issues or questions:
- Open an issue on GitHub
- Check the spec files in `spec/` folder for detailed documentation
