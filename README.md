# MCP Ansible-K8s Server

An AI-powered Model Context Protocol (MCP) server that generates production-ready Ansible Kubernetes playbooks from natural language descriptions.

## Features

- 🤖 **AI-Powered Generation**: Uses Google Gemini or Anthropic Claude to generate playbooks from natural language
- 🌐 **Web Interface**: Full-featured Streamlit dashboard with visual editor and playbook library
- 🔒 **Sandboxed Validation**: All generated playbooks are validated in isolated Docker containers
- ✅ **Best Practices Enforcement**: Ensures FQCN usage, idempotency, and prevents kubectl commands
- 💾 **Playbook Library**: Persistent storage and management of generated playbooks
- 📦 **Export Bundles**: Download playbooks with AI-generated documentation
- 🔄 **Smart Retry Logic**: Automatically retries generation with error feedback if validation fails
- 🎯 **MCP Protocol**: Standard interface for AI assistants and tools

## Architecture

```
┌─────────────┐
│   MCP       │
│   Client    │
└──────┬──────┘
       │
       │ MCP Protocol (stdio)
       │
┌──────▼──────┐
│ MCP Server  │
│             │
│ ┌─────────┐ │    ┌────────────┐
│ │ LLM     │◄├────┤ Gemini/    │
│ │ Engine  │ │    │ Claude API │
│ └────┬────┘ │    └────────────┘
│      │      │
│ ┌────▼────┐ │    ┌────────────┐
│ │ Validator│◄├────┤   Docker   │
│ │          │ │    │  Container │
│ └─────────┘ │    │  (ansible) │
│             │    └────────────┘
└─────────────┘
```

## Prerequisites

- **Python 3.11+**
- **Docker** (for playbook validation)
- **API Key** for either:
  - Google Gemini API: https://ai.google.dev/
  - Anthropic Claude API: https://console.anthropic.com/

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd mcp-ansible-k8s
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv_linux
source venv_linux/bin/activate  # On Linux/Mac
# or
venv_linux\Scripts\activate  # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Build Docker Validator Image

```bash
docker build -t mcp-ansible-validator:latest -f docker/Dockerfile.validator .
```

Verify the image works:

```bash
docker run --rm mcp-ansible-validator:latest ansible-lint --version
docker run --rm mcp-ansible-validator:latest ansible-playbook --version
```

### 5. Configure Environment

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` and set your configuration:

```bash
# Choose your LLM provider
LLM_PROVIDER=gemini  # or "claude"

# Add the appropriate API key
GEMINI_API_KEY=your_gemini_api_key_here
# or
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## Quick Start

### Option 1: Web Interface (Recommended)

Start the complete application with Docker Compose:

```bash
# Build and start all services
docker-compose up --build

# Access the web interface
open http://localhost:8501
```

The web interface provides:
- 🤖 **AI Generator Tab**: Generate playbooks from natural language prompts
- ✏️ **Visual Editor Tab**: Edit YAML with syntax highlighting and live validation
- 📚 **Playbook Library**: Save, load, and manage your playbooks
- 📦 **Export**: Download playbooks with AI-generated README documentation

### Option 2: MCP Server (For AI Agents)

### Running the MCP Server

```bash
source venv_linux/bin/activate
python -m src.server
```

The server runs on stdio transport and waits for MCP client connections.

### Testing with Example Script

Test the generation functionality directly:

```bash
source venv_linux/bin/activate
python examples/test_generation.py
```

This will generate and validate playbooks for example scenarios:
- Deploy Redis with 1 replica
- Deploy HA Nginx with 3 replicas

### Available MCP Tools

The server exposes two tools:

#### 1. `smart_generate_playbook`

Generates a validated Ansible Kubernetes playbook from natural language.

**Parameters:**
- `description` (string): Natural language description of desired deployment

**Example:**
```
"Deploy HA Nginx with 3 replicas and a LoadBalancer service on port 80"
```

**Returns:** Validated YAML playbook or error message

#### 2. `validate_playbook`

Validates an existing Ansible playbook.

**Parameters:**
- `yaml_content` (string): YAML content to validate

**Returns:** Validation results with pass/fail status

## Development

### Running Tests

```bash
source venv_linux/bin/activate

# Run all tests with coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_config.py -v

# Run with Docker tests (requires validator image)
pytest tests/ -v -m "not skipif"
```

### Code Quality

```bash
source venv_linux/bin/activate

# Format code
ruff format src/ tests/ examples/

# Check linting
ruff check src/ tests/ examples/ --fix

# Type checking
mypy src/ tests/ examples/
```

### Project Structure

```
├── src/
│   ├── config.py           # Configuration management
│   ├── prompts.py          # System prompt loading
│   ├── llm_engine.py       # LLM abstraction (Gemini/Claude)
│   ├── validator.py        # Docker-based validation
│   └── server.py           # MCP server with tools
│
├── examples/
│   ├── prompts/
│   │   └── ansible_k8s_expert.txt  # System prompt
│   └── test_generation.py  # Demo script
│
├── tests/
│   ├── fixtures/           # Test playbooks
│   ├── test_config.py      # Config tests
│   ├── test_llm_engine.py  # LLM engine tests
│   ├── test_validator.py   # Validator tests
│   └── test_server.py      # Server tests
│
├── docker/
│   └── Dockerfile.validator # Validation environment
│
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Project metadata & tools config
└── .env.example            # Environment template
```

## How It Works

### 1. Generation Process

1. User provides natural language description
2. System prompt enforces best practices (FQCN, no kubectl)
3. LLM generates Ansible playbook YAML
4. Playbook is validated in Docker sandbox
5. If validation fails, retry with error feedback
6. Return validated playbook or error message

### 2. Validation Process

The validator runs two checks in an isolated Docker container:

1. **ansible-lint**: Checks for best practices, FQCN usage, style
2. **ansible-playbook --syntax-check**: Verifies YAML syntax and structure

### 3. System Prompt Engineering

The system prompt (`examples/prompts/ansible_k8s_expert.txt`) enforces:

- ✅ FQCN usage (e.g., `kubernetes.core.k8s` not `k8s`)
- ✅ Idempotency with `state: present/absent`
- ❌ No kubectl commands
- ✅ Proper YAML formatting
- ✅ Complete K8s resource definitions

## Web Interface Details

### Features

**AI Generator Tab:**
1. Enter natural language description (e.g., "Deploy Redis with 3 replicas")
2. Select LLM provider (Gemini or Claude)
3. Adjust temperature for creativity vs consistency
4. Click "Generate" to create validated playbook
5. Save to library or edit further

**Visual Editor Tab:**
1. Edit YAML with syntax highlighting (powered by Ace Editor)
2. Upload existing playbooks for validation
3. Click "Validate" for real-time lint + syntax checking
4. Save to persistent library
5. Download as ZIP bundle (includes AI-generated README)

**Sidebar:**
- 🔑 API key management (session-specific, not persisted)
- 📚 Playbook library with timestamps
- 📂 Load/delete saved playbooks

### Docker Compose Services

```yaml
services:
  web:       # Streamlit UI on port 8501
  mcp:       # MCP server (stdio transport)
  validator: # Ansible validation environment

volumes:
  playbook-data:  # Persistent playbook storage
```

### Persistent Storage

Playbooks are saved to a Docker volume (`playbook-data`) which persists across container restarts:

```bash
# List saved playbooks
docker exec mcp-ansible-web ls -la /app/data/playbooks

# Backup playbook library
docker run --rm -v mcp-ansible-k8s_playbook-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/playbooks-backup.tar.gz -C /data playbooks

# Restore playbook library
docker run --rm -v mcp-ansible-k8s_playbook-data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/playbooks-backup.tar.gz -C /data
```

## Troubleshooting

### Docker Issues

**Problem:** `docker: command not found`

**Solution:** Install Docker and ensure it's in your PATH

**Problem:** Permission denied when running Docker

**Solution:** Add your user to the docker group or use sudo

```bash
sudo usermod -aG docker $USER
# Log out and back in
```

### API Key Issues

**Problem:** `GEMINI_API_KEY not set` or `ANTHROPIC_API_KEY not set`

**Solution:** Ensure `.env` file exists and contains the correct API key for your selected provider

### Validation Timeout

**Problem:** Validation takes too long and times out

**Solution:** Increase timeout in `.env`:

```bash
DOCKER_VALIDATION_TIMEOUT=60  # Increase from default 30s
```

## Configuration

All configuration is managed via environment variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider to use ('gemini' or 'claude') | `gemini` |
| `GEMINI_API_KEY` | Google Gemini API key | - |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | - |
| `DOCKER_VALIDATION_TIMEOUT` | Validation timeout in seconds | `30` |
| `MCP_SERVER_NAME` | MCP server name | `mcp-ansible-k8s` |
| `MCP_SERVER_VERSION` | MCP server version | `0.1.0` |

## Contributing

1. Follow PEP8 style guidelines
2. Use type hints for all functions
3. Write comprehensive docstrings (Google style)
4. Add tests for new features
5. Ensure all tests pass before submitting
6. Run code quality tools (ruff, mypy)

## License

[Add your license here]

## Acknowledgments

- Built with [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- Uses [Google Gemini API](https://ai.google.dev/) and [Anthropic Claude API](https://www.anthropic.com/)
- Validates with [Ansible](https://www.ansible.com/) and [ansible-lint](https://ansible.readthedocs.io/projects/lint/)
