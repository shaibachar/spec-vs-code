# Ollama Integration Specification

## Overview

This specification defines how the service integrates with Ollama (local LLM server) to perform AI-powered code analysis for spec compliance checking.

## Requirements

### Functional Requirements

1. **FR-1**: Service SHALL communicate with Ollama via HTTP API
2. **FR-2**: Service SHALL use code-specialized models (e.g., CodeLlama)
3. **FR-3**: Service SHALL handle Ollama responses with structured prompts
4. **FR-4**: Service SHALL gracefully handle Ollama unavailability
5. **FR-5**: Service SHALL support multiple concurrent Ollama requests
6. **FR-6**: Service SHALL implement timeout and retry logic
7. **FR-7**: Service SHALL cache similar analysis results

### Non-Functional Requirements

1. **NFR-1**: Ollama requests SHALL complete within 30 seconds
2. **NFR-2**: Service SHALL handle model loading delays
3. **NFR-3**: Service SHALL optimize token usage for cost efficiency
4. **NFR-4**: Service SHALL provide fallback when Ollama unavailable

## Ollama Architecture

### Deployment

Ollama runs as a separate Docker container in the same Docker Compose stack:

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    environment:
      - OLLAMA_MODELS=/root/.ollama/models
```

### Communication

```
┌─────────────────────┐         HTTP API          ┌─────────────────┐
│  Compliance Service │ ────────────────────────► │  Ollama Server  │
│                     │                            │                 │
│  - Analysis Engine  │ ◄────────────────────────  │  - Model Engine │
│  - Prompt Builder   │      JSON Response         │  - CodeLlama    │
└─────────────────────┘                            └─────────────────┘
```

## API Integration

### Ollama HTTP API

**Base URL**: `http://ollama:11434/api`

### 1. Generate Completion

**Endpoint**: `POST /api/generate`

**Request**:
```json
{
  "model": "codellama",
  "prompt": "Analyze this code for compliance...",
  "stream": false,
  "options": {
    "temperature": 0.1,
    "top_p": 0.9,
    "top_k": 40
  }
}
```

**Response**:
```json
{
  "model": "codellama",
  "created_at": "2025-12-08T04:09:29Z",
  "response": "Based on the analysis...",
  "done": true,
  "context": [...],
  "total_duration": 5000000000,
  "load_duration": 2000000000,
  "prompt_eval_count": 100,
  "eval_count": 200
}
```

### 2. Chat Completion (Alternative)

**Endpoint**: `POST /api/chat`

**Request**:
```json
{
  "model": "codellama",
  "messages": [
    {
      "role": "system",
      "content": "You are a code compliance checker..."
    },
    {
      "role": "user",
      "content": "Check if this code implements the spec..."
    }
  ],
  "stream": false
}
```

## Model Selection

### Primary Model: CodeLlama

- **Purpose**: Code understanding and analysis
- **Size**: 7B, 13B, or 34B parameters
- **Advantages**: 
  - Trained specifically for code
  - Understands multiple programming languages
  - Good at code explanation and analysis
- **Recommended**: `codellama:7b-instruct` for balance of speed/quality

### Alternative Models

1. **DeepSeek Coder**: Excellent code understanding
2. **Llama 2**: General purpose, good reasoning
3. **Mistral**: Fast, good quality for simple checks

### Model Loading

```python
def ensure_model_loaded(model_name: str):
    """Ensure model is pulled and loaded"""
    try:
        # Check if model exists
        response = requests.get(f"{OLLAMA_HOST}/api/tags")
        models = [m['name'] for m in response.json()['models']]
        
        if model_name not in models:
            # Pull model
            requests.post(f"{OLLAMA_HOST}/api/pull", 
                         json={"name": model_name})
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {e}")
        raise
```

## Prompt Engineering

### Prompt Structure

All prompts follow this structure:

```
[System Context]
You are an expert code compliance checker. Your task is to analyze code 
against specifications and identify compliance issues.

[Task Description]
Analyze the following code to determine if it complies with the specification.

[Specification]
<spec content>

[Code]
<code content>

[Instructions]
Provide your analysis in the following JSON format:
{
  "compliant": boolean,
  "confidence": number (0-100),
  "issues": [
    {
      "severity": "critical|high|medium|low",
      "type": "missing|incorrect|security|design",
      "description": "...",
      "location": "file:line",
      "suggestion": "..."
    }
  ],
  "summary": "..."
}
```

### Prompt Templates

#### 1. Requirement Compliance Check

```python
REQUIREMENT_CHECK_PROMPT = """
You are a code compliance analyzer. Analyze if the code implements the requirement correctly.

SPECIFICATION REQUIREMENT:
{requirement_text}

CODE IMPLEMENTATION:
{code_snippet}

Analyze the code and respond in JSON format:
{{
  "implemented": true/false,
  "correctness": "fully_compliant|partially_compliant|non_compliant",
  "confidence": 0-100,
  "issues": [
    {{
      "severity": "critical|high|medium|low",
      "description": "Issue description",
      "line": line_number,
      "suggestion": "How to fix"
    }}
  ],
  "explanation": "Brief explanation of your analysis"
}}

Focus on:
1. Functional correctness
2. Edge case handling
3. Error handling
4. Security implications
5. Performance considerations
"""
```

#### 2. API Contract Validation

```python
API_VALIDATION_PROMPT = """
You are an API compliance validator. Compare the API specification with implementation.

API SPECIFICATION:
{api_spec}

API IMPLEMENTATION:
{api_code}

Validate and respond in JSON format:
{{
  "compliant": true/false,
  "mismatches": [
    {{
      "aspect": "endpoint|method|parameters|response|auth",
      "expected": "...",
      "actual": "...",
      "severity": "critical|high|medium|low",
      "impact": "Description of impact"
    }}
  ],
  "summary": "Overall compliance status"
}}

Check:
1. Endpoint paths match
2. HTTP methods match
3. Request parameters (required, optional, types)
4. Response format and status codes
5. Authentication requirements
6. Error responses
"""
```

#### 3. Architecture Compliance

```python
ARCHITECTURE_PROMPT = """
You are a software architecture analyst. Verify if the codebase follows the specified architecture.

ARCHITECTURE SPECIFICATION:
{architecture_spec}

CODEBASE STRUCTURE:
{file_structure}

KEY FILES:
{key_files_content}

Analyze and respond in JSON format:
{{
  "compliant": true/false,
  "architecture_pattern": "Identified pattern",
  "deviations": [
    {{
      "component": "Component name",
      "expected": "Expected design",
      "actual": "Actual implementation",
      "severity": "critical|high|medium|low",
      "recommendation": "How to align"
    }}
  ],
  "summary": "Architecture compliance summary"
}}

Focus on:
1. Component separation
2. Dependency direction
3. Design patterns
4. Modularity
5. Scalability considerations
"""
```

### Response Parsing

```python
def parse_ollama_response(response: dict) -> ComplianceResult:
    """
    Parse Ollama JSON response into structured result
    
    Args:
        response: Raw Ollama API response
        
    Returns:
        ComplianceResult object
    """
    try:
        # Extract response text
        response_text = response['response']
        
        # Try to parse as JSON
        # Ollama might wrap JSON in markdown code blocks
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', 
                              response_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(1))
        else:
            # Try direct JSON parse
            data = json.loads(response_text)
        
        return ComplianceResult.from_dict(data)
    except Exception as e:
        logger.error(f"Failed to parse Ollama response: {e}")
        # Return fallback result
        return ComplianceResult(
            compliant=False,
            confidence=0,
            error="Failed to parse response"
        )
```

## Request Configuration

### Optimal Parameters

```python
OLLAMA_CONFIG = {
    "model": "codellama:7b-instruct",
    "options": {
        "temperature": 0.1,      # Low for consistent analysis
        "top_p": 0.9,            # Nucleus sampling
        "top_k": 40,             # Top-k sampling
        "num_predict": 2000,     # Max tokens to generate
        "stop": ["</analysis>"]  # Stop sequences
    },
    "timeout": 30,               # Request timeout (seconds)
    "max_retries": 3             # Retry attempts
}
```

### Temperature Settings

- **0.0 - 0.2**: Deterministic, consistent analysis (recommended)
- **0.3 - 0.5**: Slightly more creative, still reliable
- **0.6 - 1.0**: Creative but less consistent (not recommended)

## Error Handling

### Connection Errors

```python
def call_ollama_with_retry(prompt: str, max_retries: int = 3) -> dict:
    """Call Ollama with retry logic"""
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            raise OllamaUnavailableError("Ollama server unreachable")
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                continue
            raise OllamaTimeoutError("Ollama request timed out")
```

### Model Not Found

```python
def handle_model_error(error: dict):
    """Handle model-related errors"""
    if "model not found" in error.get("error", "").lower():
        # Attempt to pull model
        logger.info(f"Model not found, pulling {OLLAMA_MODEL}")
        pull_model(OLLAMA_MODEL)
        return "retry"
    return "fail"
```

### Response Quality Issues

- **Empty response**: Retry with simplified prompt
- **Malformed JSON**: Use regex extraction or fallback analysis
- **Contradictory results**: Run multiple checks and vote
- **Low confidence**: Flag for manual review

## Performance Optimization

### 1. Request Batching

Combine multiple small checks into single prompt:

```python
def batch_check(requirements: List[str], code_files: List[str]) -> List[Result]:
    """Batch multiple checks into one Ollama request"""
    prompt = build_batch_prompt(requirements, code_files)
    response = call_ollama(prompt)
    return parse_batch_response(response)
```

### 2. Response Caching

Cache Ollama responses for identical prompts:

```python
@lru_cache(maxsize=1000)
def cached_ollama_call(prompt_hash: str, prompt: str) -> dict:
    """Cache Ollama responses by prompt hash"""
    return call_ollama(prompt)
```

### 3. Parallel Requests

Use async requests for concurrent analysis:

```python
async def analyze_multiple(checks: List[Check]) -> List[Result]:
    """Analyze multiple items in parallel"""
    tasks = [analyze_async(check) for check in checks]
    return await asyncio.gather(*tasks)
```

## Monitoring and Metrics

### Key Metrics

- **Request latency**: Average time per Ollama request
- **Success rate**: Percentage of successful requests
- **Token usage**: Total tokens consumed
- **Cache hit rate**: Percentage of cached responses used
- **Model accuracy**: Manual validation of results

### Health Checks

```python
def check_ollama_health() -> dict:
    """Check Ollama server health"""
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        models = response.json().get('models', [])
        return {
            "status": "healthy",
            "models_loaded": len(models),
            "primary_model_available": OLLAMA_MODEL in [m['name'] for m in models]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

## Security Considerations

1. **Prompt Injection**: Sanitize user input before including in prompts
2. **Data Leakage**: Don't include sensitive data in prompts
3. **Resource Limits**: Set timeouts and token limits
4. **Model Integrity**: Verify model checksums
5. **Network Isolation**: Run Ollama in isolated network

## Future Enhancements

1. **Fine-tuning**: Train custom models on project-specific code
2. **Multi-model Ensemble**: Use multiple models and vote
3. **Streaming**: Use streaming responses for real-time feedback
4. **GPU Acceleration**: Use GPU for faster inference
5. **Model Versioning**: Support different model versions
