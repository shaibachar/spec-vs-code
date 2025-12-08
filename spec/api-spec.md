# API Specification

## Overview

The Spec Compliance Checker Service exposes a REST API for triggering and managing compliance checks.

## Base URL

```
http://<host>:<port>/api/v1
```

Default port: 8080

## Authentication

All API endpoints require an API key passed in the header:

```
Authorization: Bearer <API_KEY>
```

## Endpoints

### 1. Health Check

Check if the service is running and healthy.

**Endpoint**: `GET /health`

**Authentication**: Not required

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-08T04:09:29Z",
  "ollama_status": "connected",
  "ollama_model": "codellama"
}
```

**Status Codes**:
- 200: Service is healthy
- 503: Service is unhealthy

---

### 2. Trigger Compliance Check

Start a compliance check for a repository.

**Endpoint**: `POST /compliance/check`

**Authentication**: Required

**Request Body**:
```json
{
  "repository_url": "https://github.com/username/repo.git",
  "branch": "main",
  "spec_files": ["spec/service-spec.md", "spec/api-spec.md"],
  "target_paths": ["src/", "lib/"],
  "options": {
    "deep_analysis": true,
    "include_suggestions": true,
    "severity_threshold": "medium"
  }
}
```

**Parameters**:
- `repository_url` (required): Git URL of the repository to check
- `branch` (optional): Branch to check (default: "main")
- `spec_files` (optional): Specific spec files to check against (default: all in spec/)
- `target_paths` (optional): Specific paths to analyze (default: entire repo)
- `options` (optional): Additional options for the check
  - `deep_analysis`: Use more detailed analysis (slower)
  - `include_suggestions`: Include fix suggestions in results
  - `severity_threshold`: Minimum severity to report (low, medium, high, critical)

**Response**:
```json
{
  "check_id": "chk_a1b2c3d4e5f6",
  "status": "started",
  "repository": "username/repo",
  "branch": "main",
  "estimated_completion": "2025-12-08T04:15:29Z",
  "message": "Compliance check started successfully"
}
```

**Status Codes**:
- 202: Check started successfully
- 400: Invalid request
- 401: Unauthorized
- 500: Internal server error

---

### 3. Get Check Status

Retrieve the status of a compliance check.

**Endpoint**: `GET /compliance/check/{check_id}`

**Authentication**: Required

**Response**:
```json
{
  "check_id": "chk_a1b2c3d4e5f6",
  "status": "completed",
  "repository": "username/repo",
  "branch": "main",
  "started_at": "2025-12-08T04:09:29Z",
  "completed_at": "2025-12-08T04:14:12Z",
  "progress": 100,
  "results": {
    "total_issues": 15,
    "critical": 2,
    "high": 5,
    "medium": 6,
    "low": 2,
    "files_analyzed": 42,
    "specs_checked": 3,
    "todo_file_url": "https://github.com/username/spec-repo/blob/main/TODO.md"
  }
}
```

**Status Values**:
- `pending`: Check is queued
- `started`: Check is in progress
- `completed`: Check finished successfully
- `failed`: Check failed with errors

**Status Codes**:
- 200: Success
- 401: Unauthorized
- 404: Check not found

---

### 4. List Compliance Checks

List all compliance checks with optional filtering.

**Endpoint**: `GET /compliance/checks`

**Authentication**: Required

**Query Parameters**:
- `status`: Filter by status (pending, started, completed, failed)
- `repository`: Filter by repository URL
- `limit`: Number of results (default: 20, max: 100)
- `offset`: Pagination offset (default: 0)

**Response**:
```json
{
  "total": 42,
  "limit": 20,
  "offset": 0,
  "checks": [
    {
      "check_id": "chk_a1b2c3d4e5f6",
      "status": "completed",
      "repository": "username/repo",
      "branch": "main",
      "started_at": "2025-12-08T04:09:29Z",
      "completed_at": "2025-12-08T04:14:12Z"
    }
  ]
}
```

**Status Codes**:
- 200: Success
- 401: Unauthorized

---

### 5. Get TODO Report

Retrieve the generated TODO.md content for a completed check.

**Endpoint**: `GET /compliance/check/{check_id}/todo`

**Authentication**: Required

**Response**:
```markdown
# TODO: Spec Compliance Issues

Generated: 2025-12-08T04:14:12Z
Repository: username/repo
Branch: main

## Critical Issues (2)

### 1. Missing Authentication in API Endpoint
- **File**: `src/api/users.py`
- **Spec**: `spec/api-spec.md` (Section 2: Authentication)
- **Issue**: The `/api/users` endpoint does not implement required authentication
- **Suggestion**: Add `@require_auth` decorator to the endpoint handler
...
```

**Status Codes**:
- 200: Success
- 401: Unauthorized
- 404: Check not found or not completed

---

### 6. Delete Check

Delete a compliance check and its results.

**Endpoint**: `DELETE /compliance/check/{check_id}`

**Authentication**: Required

**Response**:
```json
{
  "message": "Check deleted successfully",
  "check_id": "chk_a1b2c3d4e5f6"
}
```

**Status Codes**:
- 200: Success
- 401: Unauthorized
- 404: Check not found

---

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": "Additional context (optional)"
  }
}
```

**Common Error Codes**:
- `INVALID_REQUEST`: Malformed request
- `UNAUTHORIZED`: Missing or invalid authentication
- `NOT_FOUND`: Resource not found
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Server error
- `OLLAMA_UNAVAILABLE`: Ollama server not accessible
- `GIT_ACCESS_DENIED`: Cannot access repository

## Rate Limiting

- Rate limit: 60 requests per hour per API key
- Header: `X-RateLimit-Remaining: 45`
- When exceeded: 429 Too Many Requests

## Webhooks (Future)

Future versions may support webhooks for check completion notifications.
