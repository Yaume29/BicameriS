# BicameriS Installation Guide

## Prerequisites

### Required
- **Python 3.10+** (3.11 recommended)
- **uv** or pip package manager
- **16GB RAM** minimum (32GB recommended)
- **50GB free disk space**

### Optional (for full features)
- **Docker** (for sandbox execution)
- **CUDA 12.x** + **GPU with 8GB VRAM** (for local inference)
- **LM Studio** or similar GGUF server

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/Yaume29/BicameriS.git
cd BicameriS
```

### 2. Install dependencies
```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

### 3. Download GGUF models

Place your GGUF models in a directory. Recommended models:

| Model | Quantization | VRAM | Link |
|-------|--------------|------|------|
| Qwen2.5-14B | Q4_K_M | 8GB | [HuggingFace](https://huggingface.co/Qwen/Qwen2.5-14B-Instruct-GGUF) |
| Gemma-3-12B | Q4_K_M | 8GB | [HuggingFace](https://huggingface.co/google/gemma-3-12b-it-qat-gguf) |

### 4. Configure the application

Edit `storage/config/config.yaml`:
```yaml
models:
  left_hemisphere:
    name: "Qwen2.5-14B"
    path: "C:/Models/qwen2.5-14b-q4_k_m.gguf"
    
  right_hemisphere:
    name: "Gemma-3-12B"  
    path: "C:/Models/gemma-3-12b-q4_k_m.gguf"

server:
  host: "0.0.0.0"
  port: 8000
```

### 5. Run the server

```bash
# Development
python -m server.main

# Or with uvicorn
uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Access the UI

Open http://localhost:8000 in your browser.

## Environment Variables

Create `.env` file:
```env
# API Keys (optional)
OPENAI_API_KEY=sk-...

# Model paths
LEFT_MODEL_PATH=C:/Models/qwen.gguf
RIGHT_MODEL_PATH=C:/Models/gemma.gguf

# Server
HOST=0.0.0.0
PORT=8000
```

## Troubleshooting

### "ZMQ unavailable" error
Install pyzmq:
```bash
pip install pyzmq
```

### Docker not available
The sandbox will fall back to venv mode. Install Python 3.11 in a venv for best isolation.

### VRAM issues
Reduce quantization or use smaller models. The system auto-detects available VRAM.

### Port already in use
Change port in config or kill existing process:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <pid> /F
```

## Security Notes

- `strict_airgap_mode`: Disables external MCP tools
- `auto_scaffolding`: Auto-installs missing Python packages (sandbox only)
- Default: Both disabled for safety

## Next Steps

See [config.example.yaml](config.example.yaml) for configuration examples.
See [docs/security.md](docs/security.md) for security details.
