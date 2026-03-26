# BicameriS Security Documentation

## Overview

BicameriS implements multiple security layers to protect the system and its users. This document explains the available security features and how to configure them.

## Switchboard Security Features

The Switchboard controls all security-relevant features. Access via API or UI:

```bash
# Get all switches
GET /api/system/switches

# Toggle a switch
POST /api/system/switches/{feature}
{"state": true}
```

### Available Security Switches

| Switch | Default | Description |
|--------|---------|-------------|
| `strict_airgap_mode` | `false` | Disables all external MCP tools |
| `auto_scaffolding` | `false` | Auto-installs missing Python packages |
| `sandbox_docker` | `true` | Uses Docker for code execution |
| `trauma_filter` | `true` | Filters sensitive data from logs |
| `entropy_tracking` | `true` | Tracks hardware entropy |

## Security Modes

### 1. Strict Airgap Mode

When enabled (`strict_airgap_mode: true`):
- All MCP tool servers are disabled
- Network requests are blocked
- Only internal tools available (sandbox, memory)
- No web search functionality

**Use case**: Maximum isolation for sensitive operations.

### 2. Auto-Scaffolding

When enabled (`auto_scaffolding: true`):
- Missing Python packages are auto-installed
- Executed in sandbox environment only
- Dangerous packages blocked

**Warning**: Only enable in sandbox mode!

### 3. Docker Sandbox

The sandbox provides isolation for code execution:

- **With Docker**: Full container isolation
- **Without Docker**: Falls back to venv with process tree cleanup

### 4. Trauma Filter

When enabled (`trauma_filter: true`):
- Sensitive data is masked in logs
- Error messages are sanitized
- No stack traces exposed

## Configuration

### storage/config/security.json

```json
{
  "allowed_modules": ["numpy", "pandas", "requests"],
  "blocked_modules": ["os", "sys", "subprocess"],
  "max_execution_time": 30,
  "max_memory_mb": 512,
  "network_access": false,
  "file_system_access": "sandbox_only"
}
```

## API Security

### Authentication

Currently uses HTTP basic auth. Set credentials:

```bash
# Via environment
BASIC_AUTH_USER=admin
BASIC_AUTH_PASS=your_secure_password
```

### Rate Limiting

Not currently implemented. Consider adding:

```python
from fastapi import FastAPI
from slowapi import Limiter

limiter = Limiter(default_limits=["10/minute"])
```

## Best Practices

1. **Never run with `strict_airgap_mode: false` in production** unless you trust all MCP tools
2. **Keep `auto_scaffolding: false`** - Only enable for development
3. **Use Docker** for all code execution when available
4. **Monitor logs** - Check `storage/logs/` regularly
5. **Update models** - Keep GGUF models updated for security patches

## Incident Response

If you detect unauthorized access:

1. **Enable strict mode**:
   ```bash
   POST /api/system/switches/strict_airgap_mode
   {"state": true}
   ```

2. **Kill all incarnations**:
   ```bash
   POST /api/inference/guillotine_all
   ```

3. **Check logs**: Review `storage/logs/` for suspicious activity

4. **Restart**: Clean restart clears all state

## Vulnerability Reporting

Report security issues via GitHub Issues with `[SECURITY]` prefix.
