# Service Specification

## Overview

The Spec Compliance Checker Service is a self-hosted Docker-based service that analyzes code repositories to ensure they comply with defined specifications. It leverages Ollama (local LLM) to perform intelligent code analysis and comparison.

## Requirements

### Functional Requirements

1. **FR-1**: The service SHALL run as a Docker container
2. **FR-2**: The service SHALL integrate with Ollama server for AI-powered analysis
3. **FR-3**: The service SHALL have read access to Git repositories
4. **FR-4**: The service SHALL compare code implementation against spec files
5. **FR-5**: The service SHALL generate TODO.md files with compliance findings
6. **FR-6**: The service SHALL expose a REST API for triggering compliance checks
7. **FR-7**: The service SHALL support multiple repository checks
8. **FR-8**: The service SHALL persist compliance check results

### Non-Functional Requirements

1. **NFR-1**: The service SHALL be deployable on any Docker-compatible host
2. **NFR-2**: The service SHALL handle repositories up to 1GB in size
3. **NFR-3**: The service SHALL complete compliance checks within reasonable time (< 10 minutes for typical repos)
4. **NFR-4**: The service SHALL support concurrent compliance checks (minimum 3 simultaneous)
5. **NFR-5**: The service SHALL provide detailed logging for troubleshooting
6. **NFR-6**: The service SHALL be secure and not expose sensitive repository data

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Environment                        │
│                                                              │
│  ┌──────────────────┐         ┌─────────────────────┐      │
│  │  Spec Compliance │         │   Ollama Server     │      │
│  │     Service      │◄────────┤   (LLM Engine)      │      │
│  │                  │         │                     │      │
│  └────────┬─────────┘         └─────────────────────┘      │
│           │                                                  │
│           │                                                  │
│  ┌────────▼─────────┐         ┌─────────────────────┐      │
│  │   Git Client     │         │   Results Storage   │      │
│  │   Integration    │         │   (TODO.md files)   │      │
│  └──────────────────┘         └─────────────────────┘      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
         ▲                                    │
         │                                    │
         │ Git Access                         ▼
    ┌────┴──────┐                     ┌──────────────┐
    │   Target  │                     │  Spec Repo   │
    │   Repos   │                     │  (Output)    │
    └───────────┘                     └──────────────┘
```

### Component Descriptions

1. **Spec Compliance Service**: Main application handling API requests and orchestrating checks
2. **Ollama Server**: Local LLM server for AI-powered code analysis
3. **Git Client Integration**: Module for cloning and reading repositories
4. **Results Storage**: Module for generating and storing TODO.md files

## Deployment

### Docker Deployment

The service is deployed using Docker Compose with two containers:
- Service container (Python-based application)
- Ollama container (LLM server)

### Environment Variables

- `OLLAMA_HOST`: URL of Ollama server (default: http://ollama:11434)
- `OLLAMA_MODEL`: Model to use for analysis (default: codellama)
- `GIT_TOKEN`: GitHub/GitLab access token for private repos (optional)
- `SPEC_REPO_URL`: URL of the spec repository where results are committed
- `SERVICE_PORT`: Port to expose API (default: 8080)
- `LOG_LEVEL`: Logging level (default: INFO)

## Workflow

1. API receives compliance check request with repository URL
2. Service clones the target repository
3. Service reads spec files from spec/ folder
4. Service uses Ollama to analyze code against specs
5. Service generates TODO.md with compliance findings
6. Service commits TODO.md to spec repository
7. Service returns check results via API

## Security Considerations

1. Service runs with minimal permissions
2. Git tokens are stored securely as environment variables
3. Service does not expose repository content externally
4. All API endpoints require authentication (API key)
5. Docker network isolation between components

## Scalability

- Stateless design allows horizontal scaling
- Each instance handles independent compliance checks
- Ollama can be shared across instances or run per-instance
- Results are stored in Git (distributed version control)
