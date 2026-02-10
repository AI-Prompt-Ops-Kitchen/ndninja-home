# Standalone Developer Tools

Two independent Python tools for Docker debugging and prompt versioning:

## Docker Environment Debugger

Diagnose Python environment issues in Docker containers.

```bash
# Check container environment
python3 tools/docker_env_debugger.py mycontainer

# Check specific aspect
python3 tools/docker_env_debugger.py mycontainer --check python_version

# Output as JSON
python3 tools/docker_env_debugger.py mycontainer --json
```

Available checks:
- `python_version`: Python version in container
- `python_path`: Location of Python executable
- `installed_packages`: List of pip packages
- `environment_variables`: Python-related env vars
- `sys_path`: Python module search paths
- `venv_status`: Virtual environment status

### Usage in Code

```python
from tools.docker_env_debugger import DockerDebugger

debugger = DockerDebugger(container_id="mycontainer")
results = debugger.run_all_checks()
print(f"Passed: {results['passed']}/{results['total_checks']}")
```

## Prompt Versioning & Testing

Version and test prompts to prevent regression.

```bash
# Save new version
python3 tools/prompt_versioning.py save \
  --prompt-id keyword_extractor \
  --text "Extract keywords: " \
  --purpose keyword_extraction

# List versions
python3 tools/prompt_versioning.py list --prompt-id keyword_extractor

# Test version
python3 tools/prompt_versioning.py test \
  --prompt-id keyword_extractor \
  --version 1
```

### Usage in Code

```python
from tools.prompt_versioning import PromptVersionManager

pm = PromptVersionManager()

# Save version
version = pm.save_version(
    prompt_id="extractor",
    prompt_text="Extract: ",
    purpose="extraction"
)

# Create test cases
pm.create_test_case(
    prompt_id="extractor",
    test_name="basic_test",
    input_text="Test input",
    expected_output="test"
)

# Test version
results = pm.test_prompt_version(
    prompt_id="extractor",
    version=version
)

# Compare versions
comparison = pm.compare_versions(
    prompt_id="extractor",
    version1=1,
    version2=2
)

# Get regression report
report = pm.get_regression_report(prompt_id="extractor")
```

## Features

### Docker Debugger
- Python version detection
- Package inventory
- Environment variable inspection
- sys.path analysis
- Virtual environment detection
- JSON output for automation
- Container or local execution

### Prompt Versioning
- Version tracking with metadata
- Test case management
- Regression testing across versions
- Version comparison
- Version activation
- Test results storage
- CSV/JSON export

## Files

```
tools/
├── __init__.py
├── docker_env_debugger.py    # Docker diagnostics
└── prompt_versioning.py       # Prompt management
```

## Test Coverage

- 2/2 Docker Debugger tests
- 2/2 Prompt Versioning tests

**Total: 4/4 tests passing**
