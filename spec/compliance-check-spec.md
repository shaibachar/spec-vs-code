# Compliance Check Specification

## Overview

This specification defines how the service performs compliance checking by comparing code implementation against specification documents.

## Compliance Check Process

### Phase 1: Initialization

1. **Repository Cloning**
   - Clone the target repository to a temporary workspace
   - Checkout the specified branch
   - Validate repository structure

2. **Spec Loading**
   - Load all spec files from the `spec/` folder
   - Parse spec files into structured format
   - Extract requirements, design constraints, and API contracts

3. **Scope Definition**
   - Identify code files to analyze based on target_paths
   - Map spec files to relevant code modules
   - Create analysis plan

### Phase 2: Code Analysis

1. **Static Code Analysis**
   - Parse code files to extract structure (functions, classes, imports)
   - Identify public APIs and interfaces
   - Extract documentation and comments
   - Build dependency graph

2. **Spec Parsing**
   - Extract requirements from spec files
   - Identify mandatory vs. optional requirements
   - Parse API contracts and signatures
   - Extract design constraints

3. **Ollama-Powered Analysis**
   - For each spec requirement, query Ollama to:
     - Determine if requirement is implemented
     - Identify which code files implement the requirement
     - Assess quality of implementation
     - Detect deviations from spec

### Phase 3: Comparison

1. **Requirement Coverage**
   - Map each requirement to implementing code
   - Identify unimplemented requirements (gaps)
   - Identify code not covered by specs (extra functionality)

2. **API Contract Validation**
   - Compare API signatures against spec
   - Validate request/response formats
   - Check authentication requirements
   - Verify error handling

3. **Design Constraint Validation**
   - Check architecture patterns match spec
   - Validate component interactions
   - Verify security requirements
   - Check performance considerations

### Phase 4: Issue Classification

Issues are classified by:

1. **Severity Levels**
   - **Critical**: Security vulnerabilities, data loss risks, spec violations that break functionality
   - **High**: Missing core requirements, incorrect API contracts, significant deviations
   - **Medium**: Partial implementations, minor API mismatches, missing error handling
   - **Low**: Documentation gaps, style inconsistencies, optional features not implemented

2. **Issue Types**
   - **Missing Implementation**: Spec requirement not implemented
   - **Incorrect Implementation**: Code doesn't match spec behavior
   - **API Mismatch**: API signature/contract differs from spec
   - **Security Gap**: Security requirement not met
   - **Design Deviation**: Architecture doesn't follow spec design
   - **Documentation Gap**: Missing or incorrect documentation

### Phase 5: Report Generation

1. **TODO.md Structure**
   ```markdown
   # TODO: Spec Compliance Issues
   
   Generated: [timestamp]
   Repository: [repo]
   Branch: [branch]
   Total Issues: [count]
   
   ## Summary
   - Critical: [count]
   - High: [count]
   - Medium: [count]
   - Low: [count]
   
   ## Critical Issues
   [List of critical issues with details]
   
   ## High Priority Issues
   [List of high priority issues]
   
   ## Medium Priority Issues
   [List of medium priority issues]
   
   ## Low Priority Issues
   [List of low priority issues]
   
   ## Recommendations
   [General recommendations for improvement]
   ```

2. **Issue Entry Format**
   ```markdown
   ### [N]. [Issue Title]
   - **Severity**: [Critical/High/Medium/Low]
   - **Type**: [Issue Type]
   - **Spec Reference**: [spec file] (Section [X])
   - **Files Affected**: [file1.py, file2.py]
   - **Description**: [Detailed description of the issue]
   - **Current State**: [What exists in code]
   - **Expected State**: [What spec requires]
   - **Suggestion**: [How to fix the issue]
   - **Example**: [Code example if applicable]
   ```

## Ollama Integration

### Model Selection

- Primary model: `codellama` (optimized for code analysis)
- Fallback model: `llama2` (general purpose)
- Model requirements: Minimum 7B parameters

### Prompting Strategy

1. **Requirement Analysis Prompt**
   ```
   Given this specification requirement:
   [spec requirement text]
   
   And this code implementation:
   [code snippet]
   
   Analyze if the code correctly implements the requirement.
   Consider:
   1. Functional correctness
   2. Edge cases
   3. Error handling
   4. Security implications
   
   Provide: compliance status, issues found, and suggestions.
   ```

2. **API Validation Prompt**
   ```
   Compare this API specification:
   [spec API definition]
   
   With this implementation:
   [code API definition]
   
   Check for:
   1. Endpoint path matches
   2. HTTP methods match
   3. Request parameters match
   4. Response format matches
   5. Authentication requirements
   6. Error responses
   
   Report any discrepancies.
   ```

3. **Design Pattern Prompt**
   ```
   The specification describes this architecture:
   [spec architecture description]
   
   Analyze this codebase structure:
   [file tree and component list]
   
   Determine if the implementation follows the specified architecture.
   Identify any significant deviations.
   ```

### Response Parsing

Ollama responses are parsed to extract:
- Compliance status (compliant/partial/non-compliant)
- Issues found (structured list)
- Severity assessment
- Suggested fixes
- Code examples

## Smart Analysis Features

### 1. Context-Aware Checking

- Understand code context and intent
- Consider design patterns and idioms
- Account for language-specific implementations
- Recognize equivalent implementations

### 2. Prioritization

- Focus on critical requirements first
- Identify high-impact issues
- Consider dependencies between issues
- Suggest implementation order

### 3. Learning from History

- Track common compliance issues
- Build patterns of non-compliance
- Suggest proactive checks
- Improve accuracy over time

## Configuration

### Analysis Options

```yaml
compliance_check:
  # Analysis depth
  depth: standard  # quick, standard, deep
  
  # Include/exclude patterns
  include_paths:
    - "src/**"
    - "lib/**"
  exclude_paths:
    - "**/*_test.py"
    - "**/vendor/**"
  
  # Severity threshold
  min_severity: medium  # low, medium, high, critical
  
  # Ollama settings
  ollama:
    model: codellama
    temperature: 0.1  # Lower for more consistent analysis
    max_tokens: 2000
    
  # Reporting
  report:
    include_suggestions: true
    include_examples: true
    max_issues_per_severity: 50
```

## Performance Considerations

- **Batch Processing**: Analyze multiple files in parallel
- **Caching**: Cache Ollama responses for similar code patterns
- **Incremental Analysis**: Only analyze changed files when possible
- **Timeout Limits**: Maximum 10 minutes per check
- **Resource Limits**: Maximum memory and CPU allocation

## Accuracy Goals

- **False Positive Rate**: < 20%
- **False Negative Rate**: < 10%
- **Critical Issue Detection**: > 95%
- **API Mismatch Detection**: > 90%
