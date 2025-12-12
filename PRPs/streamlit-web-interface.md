name: "Streamlit Web Interface: Interactive Playbook Studio"
description: |

## Purpose
Extend the existing MCP Ansible-K8s server with a comprehensive Streamlit web dashboard that provides a visual interface for playbook generation, editing, validation, and management. This transforms the CLI-only tool into a full-featured web application accessible to non-technical users.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, examples, and caveats
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix
3. **Information Dense**: Use keywords and patterns from the codebase
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Be sure to follow all rules in CLAUDE.md

---

## Goal
Build a production-ready Streamlit web application that:
- Provides visual interface for AI playbook generation
- Enables interactive YAML editing with syntax highlighting
- Manages playbook library with persistent storage
- Validates playbooks in real-time with visual feedback
- Supports API key management through UI
- Generates AI-powered README documentation
- Shares core logic between MCP server and web app

## Why
- **Business value**: Makes the tool accessible to non-technical DevOps teams
- **User experience**: Visual editing prevents YAML syntax errors
- **Workflow efficiency**: Persistent library + download bundles streamline deployment
- **Accessibility**: No CLI knowledge required, just a web browser

## What
A Streamlit web application with:

**Tab 1: AI Generator**
- Text input for natural language prompts
- LLM provider selection (Gemini/Claude)
- Generate button triggering playbook creation
- Results displayed in syntax-highlighted editor

**Tab 2: Visual Editor**
- `streamlit-ace` editor with YAML syntax highlighting
- Live validation feedback sidebar
- Save to library button
- Download as ZIP (playbook + AI README)

**Sidebar**
- API key input fields (masked)
- Saved playbooks library (list + load)
- Settings (validation timeout, model selection)

**Backend Architecture**
- Refactor `src/server.py` → `src/engine.py` (shared logic)
- Keep MCP server in `src/server.py` (uses engine)
- Add `src/app.py` (Streamlit app uses engine)
- Docker Compose orchestration

### Success Criteria
- [ ] Streamlit app runs and connects to shared engine
- [ ] AI generation tab creates playbooks from prompts
- [ ] Visual editor shows YAML with syntax highlighting
- [ ] Live validation displays lint errors in sidebar
- [ ] Playbooks save to persistent Docker volume
- [ ] ZIP download includes playbook + AI README
- [ ] API keys can be set via UI (session state)
- [ ] Docker Compose starts both web app and MCP server
- [ ] All tests pass for new components

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window

# Streamlit
- url: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state
  why: Session state for API keys and playbook data management
  critical: Session state persists across reruns but not widget states

- url: https://docs.streamlit.io/deploy/tutorials/docker
  why: Official Streamlit Docker deployment guide

- url: https://github.com/okld/streamlit-ace
  why: Ace editor component for syntax-highlighted YAML editing
  critical: Install with pip install streamlit-ace

- url: https://pypi.org/project/streamlit-ace/
  why: Package documentation and usage examples

# Docker & Persistence
- url: https://docs.docker.com/engine/storage/volumes/
  why: Docker volumes for persistent playbook storage

- url: https://www.rockyourcode.com/run-streamlit-with-docker-and-docker-compose/
  why: Docker Compose patterns for Streamlit apps

- url: https://geekchamp.com/use-volumes-in-docker-compose-to-manage-persistent-data/
  why: Volume management in Docker Compose

# Python Libraries
- url: https://docs.python.org/3/library/zipfile.html
  why: Creating ZIP bundles (playbook + README)

# Existing Codebase
- file: src/server.py
  why: Current MCP server implementation to refactor into engine
  lines: 126 lines, contains generation and validation logic

- file: src/llm_engine.py
  why: LLM abstraction pattern to reuse in web app

- file: src/validator.py
  why: Docker validation to integrate with live editor

- file: src/config.py
  why: Settings pattern to extend for UI key management
```

### Current Codebase Tree
```bash
.
├── src/
│   ├── __init__.py
│   ├── config.py          # Pydantic settings
│   ├── prompts.py         # System prompt loading
│   ├── llm_engine.py      # LLM abstraction (Gemini/Claude)
│   ├── validator.py       # Docker validation
│   └── server.py          # MCP server (to refactor)
│
├── examples/
│   ├── test_generation.py
│   └── prompts/
│       └── ansible_k8s_expert.txt
│
├── tests/
│   ├── test_config.py
│   ├── test_llm_engine.py
│   ├── test_validator.py
│   ├── test_server.py
│   └── fixtures/
│
├── docker/
│   └── Dockerfile.validator
│
└── [config files]
```

### Desired Codebase Tree with Files to be Added
```bash
.
├── src/
│   ├── __init__.py
│   ├── config.py          # Existing
│   ├── prompts.py         # Existing
│   ├── llm_engine.py      # Existing
│   ├── validator.py       # Existing
│   ├── engine.py          # NEW: Core business logic (refactored from server.py)
│   ├── server.py          # MODIFIED: MCP server (now uses engine)
│   ├── app.py             # NEW: Streamlit web application
│   └── utils.py           # NEW: Utilities (ZIP creation, README generation)
│
├── data/                  # NEW: Persistent playbook storage (Docker volume)
│   └── playbooks/         # Saved YAML files
│
├── static/                # NEW: Static assets for web app
│   └── logo.png           # Optional: App branding
│
├── docker/
│   ├── Dockerfile.validator    # Existing
│   ├── Dockerfile.web          # NEW: Web app container
│   └── Dockerfile.mcp          # NEW: MCP server container
│
├── docker-compose.yml     # NEW: Multi-service orchestration
│
├── tests/
│   ├── [existing tests]
│   ├── test_engine.py     # NEW: Engine logic tests
│   ├── test_app.py        # NEW: Streamlit app tests
│   └── test_utils.py      # NEW: Utils tests
│
└── requirements-web.txt   # NEW: Web-specific dependencies
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: Streamlit
# - Session state persists across reruns but NOT widget states (buttons, file_uploader)
# - File uploader state is ephemeral - save uploaded content to session_state immediately
# - st.rerun() triggers full script re-execution from top
# - Use st.cache_data for expensive operations (not needed for our use case)
# - Port 8501 is Streamlit default

# CRITICAL: streamlit-ace
# - Install: pip install streamlit-ace
# - Language modes: "yaml", "python", "json"
# - Theme options: "monokai", "github", "twilight"
# - Returns edited content as string
# - Example: st_ace(value=yaml_content, language="yaml", theme="monokai")

# CRITICAL: Architecture Refactoring
# - Extract generation logic from server.py into engine.py
# - Engine should be stateless (no global LLM engine instance)
# - Both server.py and app.py import and use engine functions
# - Don't break existing MCP server functionality

# CRITICAL: Docker Compose
# - Use named volumes for persistence: volumes: - playbook-data:/app/data
# - Web service needs access to validator logic (mount src/)
# - MCP service runs on stdio (no exposed ports)
# - Web service exposes port 8501

# CRITICAL: API Key Management
# - Priority: 1) UI session state, 2) .env file, 3) raise error
# - Store in st.session_state["gemini_api_key"]
# - Mask in UI with type="password"
# - Pass to engine functions as parameters (don't rely on global Settings)

# CRITICAL: File Management
# - Save playbooks to data/playbooks/{timestamp}_{name}.yml
# - Use pathlib.Path for cross-platform paths
# - Validate filename to prevent directory traversal
# - List saved playbooks from filesystem, not database

# CRITICAL: README Generation
# - Use LLM to generate README from playbook YAML
# - Prompt: "Explain this Ansible K8s playbook in markdown README format"
# - Include setup instructions, what it deploys, and usage

# CRITICAL: ZIP Bundle
# - Use zipfile.ZipFile in memory (BytesIO)
# - Include: playbook.yml, README.md
# - Use st.download_button with MIME type "application/zip"
```

## Implementation Blueprint

### Data Models and Structure

```python
# src/engine.py - Core business logic (refactored)
from pydantic import BaseModel

class PlaybookGenerationRequest(BaseModel):
    """Request to generate a playbook."""
    description: str
    llm_provider: str  # "gemini" or "claude"
    api_key: str
    max_retries: int = 2
    temperature: float = 0.3

class PlaybookGenerationResult(BaseModel):
    """Result of playbook generation."""
    success: bool
    playbook_yaml: str
    validation_result: ValidationResult | None = None
    error_message: str | None = None
    model_used: str | None = None
    tokens_used: int | None = None

# src/utils.py - Utility functions
from datetime import datetime
from pathlib import Path

class PlaybookMetadata(BaseModel):
    """Metadata for saved playbooks."""
    filename: str
    created_at: datetime
    description: str
    size_bytes: int
```

### List of Tasks to be Completed

```yaml
Task 1: Refactor Core Logic into Engine
EXTRACT from src/server.py:
  - Move smart_generate_playbook logic to new function in engine.py
  - Move validate_playbook logic to engine.py
  - Make engine stateless (accept Settings/keys as parameters)

CREATE src/engine.py:
  - Function: generate_playbook(request: PlaybookGenerationRequest) -> PlaybookGenerationResult
  - Function: validate_playbook_yaml(yaml_content: str, timeout: int) -> ValidationResult
  - Function: generate_readme(playbook_yaml: str, llm_provider: str, api_key: str) -> str
  - PATTERN: Pure functions, no global state
  - Keep validation retry logic

MODIFY src/server.py:
  - Import from engine
  - MCP tools become thin wrappers calling engine functions
  - Keep MCP-specific logic only

Task 2: Create Utility Functions
CREATE src/utils.py:
  - Function: save_playbook(yaml_content: str, description: str, data_dir: Path) -> Path
  - Function: list_saved_playbooks(data_dir: Path) -> list[PlaybookMetadata]
  - Function: load_playbook(filename: str, data_dir: Path) -> str
  - Function: create_zip_bundle(playbook_yaml: str, readme_md: str, filename: str) -> bytes
  - PATTERN: Use pathlib.Path for cross-platform compatibility
  - Validate filenames to prevent directory traversal

Task 3: Create Streamlit Web Application
CREATE src/app.py:
  - PATTERN: Streamlit multi-page layout with tabs
  - Initialize session_state for: api_keys, current_playbook, saved_playbooks
  - Sidebar: API key inputs, playbook library
  - Tab 1: AI Generator (prompt → generate → display in editor)
  - Tab 2: Visual Editor (streamlit-ace → validate button → results)
  - CRITICAL: Use st.session_state for all stateful data

Task 4: Implement AI Generator Tab
IN src/app.py - create_generator_tab():
  - Text area for user prompt
  - LLM provider selector (radio: Gemini/Claude)
  - Generate button with spinner
  - Call engine.generate_playbook with UI-provided keys
  - Display result in st_ace editor (read-only mode)
  - Show validation status and token usage
  - "Save to Library" button

Task 5: Implement Visual Editor Tab
IN src/app.py - create_editor_tab():
  - st_ace editor component (language="yaml", theme="monokai")
  - Load from library dropdown
  - Upload YAML file button
  - Validate button → calls engine.validate_playbook_yaml
  - Sidebar: Live validation results (✓/✗ with error details)
  - Save button → calls utils.save_playbook
  - Download ZIP button → generates README + creates bundle

Task 6: Implement Sidebar Components
IN src/app.py - create_sidebar():
  - st.text_input for GEMINI_API_KEY (type="password")
  - st.text_input for ANTHROPIC_API_KEY (type="password")
  - st.selectbox for saved playbooks (from utils.list_saved_playbooks)
  - Load playbook button → puts content in editor
  - Delete playbook button (with confirmation)

Task 7: Docker Compose Configuration
CREATE docker-compose.yml:
  - Service 1: web (Streamlit app on port 8501)
  - Service 2: mcp (MCP server on stdio)
  - Shared volume: playbook-data mounted to ./data
  - Environment variables from .env
  - Network: both services on same network

CREATE docker/Dockerfile.web:
  - Base: python:3.11-slim
  - Install: streamlit, streamlit-ace, requirements
  - WORKDIR /app
  - Copy src/ and data/
  - EXPOSE 8501
  - CMD: streamlit run src/app.py

Task 8: Update Dependencies
UPDATE requirements.txt:
  - Add: streamlit>=1.30.0
  - Add: streamlit-ace>=0.1.0

CREATE requirements-web.txt:
  - Include all requirements.txt dependencies
  - Add web-specific packages

Task 9: Comprehensive Testing
CREATE tests/test_engine.py:
  - Test generate_playbook function
  - Test validate_playbook_yaml function
  - Test generate_readme function
  - Mock LLM calls
  - Verify retry logic still works

CREATE tests/test_utils.py:
  - Test save_playbook creates file correctly
  - Test list_saved_playbooks returns metadata
  - Test load_playbook reads content
  - Test create_zip_bundle creates valid ZIP
  - Test filename sanitization (security)

CREATE tests/test_app.py:
  - Test session state initialization
  - Test API key priority logic
  - Mock streamlit components
  - Test playbook library operations

Task 10: Documentation & Examples
UPDATE README.md:
  - Add "Web Interface" section
  - Docker Compose usage instructions
  - Screenshots or ASCII demo of UI
  - API key management guide

CREATE examples/web_complete/:
  - Directory for web interface examples
  - Sample docker-compose.yml
  - .env.example for web setup

Task 11: Integration & Validation
BUILD Docker images:
  - docker-compose build
  - Verify both services start

RUN integration test:
  - docker-compose up
  - Access http://localhost:8501
  - Test full workflow: Generate → Edit → Validate → Save → Download
```

### Per Task Pseudocode

```python
# Task 1: Refactor Core Logic into Engine
# src/engine.py

from src.config import Settings
from src.llm_engine import GenerationRequest, GenerationResponse, create_llm_engine
from src.validator import PlaybookValidator, ValidationResult
from src.prompts import load_system_prompt

def generate_playbook(
    description: str,
    llm_provider: str,
    api_key: str,
    max_retries: int = 2,
    temperature: float = 0.3,
    validation_timeout: int = 30
) -> PlaybookGenerationResult:
    """
    Generate and validate a playbook (stateless, reusable).

    This function can be called from both MCP server and Streamlit app.
    """
    # Create engine with provided credentials
    settings = Settings(
        llm_provider=llm_provider,
        gemini_api_key=api_key if llm_provider == "gemini" else None,
        claude_api_key=api_key if llm_provider == "claude" else None,
    )

    llm_engine = create_llm_engine(settings)
    validator = PlaybookValidator(timeout=validation_timeout)
    system_prompt = load_system_prompt()

    current_description = description

    for attempt in range(max_retries):
        # Generate
        request = GenerationRequest(
            user_prompt=current_description,
            system_prompt=system_prompt,
            max_tokens=4096,
            temperature=temperature,
        )

        response = llm_engine.generate(request)
        playbook_yaml = response.content

        # Validate
        validation = validator.validate(playbook_yaml)

        if validation.is_valid:
            return PlaybookGenerationResult(
                success=True,
                playbook_yaml=playbook_yaml,
                validation_result=validation,
                model_used=response.model,
                tokens_used=response.usage_tokens
            )

        # Retry with feedback
        if attempt < max_retries - 1:
            error_feedback = "\n".join(validation.errors)
            current_description += f"\n\nPrevious errors:\n{error_feedback}"

    # Failed
    return PlaybookGenerationResult(
        success=False,
        playbook_yaml="",
        validation_result=validation,
        error_message=f"Failed after {max_retries} attempts"
    )

def generate_readme(
    playbook_yaml: str,
    llm_provider: str,
    api_key: str
) -> str:
    """Generate README.md documentation for a playbook."""
    settings = Settings(
        llm_provider=llm_provider,
        gemini_api_key=api_key if llm_provider == "gemini" else None,
        claude_api_key=api_key if llm_provider == "claude" else None,
    )

    llm_engine = create_llm_engine(settings)

    readme_prompt = f"""Generate a comprehensive README.md in markdown format for this Ansible Kubernetes playbook.

Include:
1. Overview: What this playbook deploys
2. Prerequisites: Required tools and access
3. Usage: How to run the playbook
4. What Gets Created: List of K8s resources
5. Customization: How to modify for different environments

Playbook:
{playbook_yaml}
"""

    request = GenerationRequest(
        user_prompt=readme_prompt,
        system_prompt="You are a technical writer. Generate clear, professional documentation.",
        max_tokens=2048,
        temperature=0.5,
    )

    response = llm_engine.generate(request)
    return response.content


# Task 2: Utility Functions
# src/utils.py

import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
import re

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal."""
    # Remove any path separators and dangerous characters
    filename = re.sub(r'[^\w\s-]', '', filename)
    filename = filename.replace(' ', '_')
    return filename[:100]  # Limit length

def save_playbook(
    yaml_content: str,
    description: str,
    data_dir: Path
) -> Path:
    """Save playbook to persistent storage."""
    # Create playbooks directory if it doesn't exist
    playbooks_dir = data_dir / "playbooks"
    playbooks_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_desc = sanitize_filename(description)
    filename = f"{timestamp}_{safe_desc}.yml"

    filepath = playbooks_dir / filename
    filepath.write_text(yaml_content, encoding="utf-8")

    return filepath

def list_saved_playbooks(data_dir: Path) -> list[PlaybookMetadata]:
    """List all saved playbooks with metadata."""
    playbooks_dir = data_dir / "playbooks"

    if not playbooks_dir.exists():
        return []

    playbooks = []
    for filepath in sorted(playbooks_dir.glob("*.yml"), reverse=True):
        stat = filepath.stat()
        playbooks.append(PlaybookMetadata(
            filename=filepath.name,
            created_at=datetime.fromtimestamp(stat.st_mtime),
            description=filepath.stem.split('_', 2)[-1] if '_' in filepath.stem else filepath.stem,
            size_bytes=stat.st_size
        ))

    return playbooks

def create_zip_bundle(
    playbook_yaml: str,
    readme_md: str,
    bundle_name: str
) -> bytes:
    """Create ZIP bundle containing playbook and README."""
    # Reason: Use BytesIO to create ZIP in memory without temp files
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("playbook.yml", playbook_yaml)
        zip_file.writestr("README.md", readme_md)

    zip_buffer.seek(0)
    return zip_buffer.getvalue()


# Task 3: Streamlit Application
# src/app.py

import streamlit as st
from streamlit_ace import st_ace
from pathlib import Path

from src.engine import generate_playbook, generate_readme, validate_playbook_yaml
from src.utils import save_playbook, list_saved_playbooks, load_playbook, create_zip_bundle

# Page config
st.set_page_config(
    page_title="MCP Ansible-K8s Studio",
    page_icon="🚀",
    layout="wide"
)

# Initialize session state
if "current_playbook" not in st.session_state:
    st.session_state.current_playbook = ""
if "validation_result" not in st.session_state:
    st.session_state.validation_result = None
if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
if "claude_api_key" not in st.session_state:
    st.session_state.claude_api_key = os.getenv("ANTHROPIC_API_KEY", "")

def create_sidebar():
    """Create sidebar with API keys and library."""
    st.sidebar.title("⚙️ Configuration")

    # API Keys
    st.sidebar.subheader("API Keys")
    st.session_state.gemini_api_key = st.sidebar.text_input(
        "Gemini API Key",
        value=st.session_state.gemini_api_key,
        type="password",
        help="Get key from https://ai.google.dev/"
    )
    st.session_state.claude_api_key = st.sidebar.text_input(
        "Claude API Key",
        value=st.session_state.claude_api_key,
        type="password",
        help="Get key from https://console.anthropic.com/"
    )

    # Playbook Library
    st.sidebar.divider()
    st.sidebar.subheader("📚 Saved Playbooks")

    data_dir = Path("data")
    playbooks = list_saved_playbooks(data_dir)

    if playbooks:
        selected = st.sidebar.selectbox(
            "Select playbook",
            options=[p.filename for p in playbooks],
            format_func=lambda f: f.replace('.yml', '')
        )

        if st.sidebar.button("Load Selected"):
            content = load_playbook(selected, data_dir)
            st.session_state.current_playbook = content
            st.rerun()
    else:
        st.sidebar.info("No saved playbooks yet")

def create_generator_tab():
    """Tab 1: AI Generator."""
    st.header("🤖 AI Playbook Generator")

    # Get API key based on provider
    llm_provider = st.radio(
        "LLM Provider",
        options=["gemini", "claude"],
        horizontal=True
    )

    api_key = (st.session_state.gemini_api_key if llm_provider == "gemini"
               else st.session_state.claude_api_key)

    if not api_key:
        st.error(f"Please set {llm_provider.upper()} API key in sidebar")
        return

    # User prompt
    description = st.text_area(
        "Describe your desired Kubernetes deployment:",
        placeholder="Deploy HA Nginx with 3 replicas and a LoadBalancer on port 80",
        height=100
    )

    if st.button("🚀 Generate Playbook", type="primary"):
        with st.spinner("Generating and validating playbook..."):
            result = generate_playbook(
                description=description,
                llm_provider=llm_provider,
                api_key=api_key,
            )

        if result.success:
            st.success(f"✓ Generated with {result.model_used} ({result.tokens_used} tokens)")
            st.session_state.current_playbook = result.playbook_yaml
            st.session_state.validation_result = result.validation_result
        else:
            st.error(f"✗ Generation failed: {result.error_message}")

    # Display current playbook
    if st.session_state.current_playbook:
        st.subheader("Generated Playbook")
        st_ace(
            value=st.session_state.current_playbook,
            language="yaml",
            theme="monokai",
            readonly=True,
            height=400
        )

# Main app
def main():
    st.title("🚀 MCP Ansible-K8s Studio")

    create_sidebar()

    tab1, tab2 = st.tabs(["🤖 AI Generator", "✏️ Visual Editor"])

    with tab1:
        create_generator_tab()

    with tab2:
        create_editor_tab()

if __name__ == "__main__":
    main()
```

### Integration Points

```yaml
ENVIRONMENT:
  - Docker Compose .env file:
      LLM_PROVIDER=gemini
      GEMINI_API_KEY=your_key_here
      ANTHROPIC_API_KEY=your_key_here
      DOCKER_VALIDATION_TIMEOUT=30

DOCKER_COMPOSE:
  services:
    web:
      build:
        context: .
        dockerfile: docker/Dockerfile.web
      ports:
        - "8501:8501"
      volumes:
        - playbook-data:/app/data
        - ./src:/app/src:ro
      environment:
        - GEMINI_API_KEY=${GEMINI_API_KEY}
        - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

    mcp:
      build:
        context: .
        dockerfile: docker/Dockerfile.mcp
      volumes:
        - playbook-data:/app/data
        - ./src:/app/src:ro
      stdin_open: true

  volumes:
    playbook-data:

DEPENDENCIES:
  - streamlit>=1.30.0 (web framework)
  - streamlit-ace>=0.1.0 (code editor component)
  - All existing requirements (mcp, google-genai, anthropic, etc.)

DATA_DIRECTORY:
  - location: ./data/playbooks/
  - structure: {timestamp}_{description}.yml
  - persistence: Docker volume
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# CRITICAL: Run in venv_linux - fix any errors before proceeding
source venv_linux/bin/activate

# Lint and format
ruff check src/ tests/ --fix
ruff format src/ tests/

# Type checking
mypy src/ tests/

# Expected: No errors. If errors, READ the error message and fix.
```

### Level 2: Unit Tests
```python
# tests/test_engine.py - Example test structure

def test_generate_playbook_success():
    """Test playbook generation with valid API key."""
    with patch('src.engine.create_llm_engine') as mock_llm_factory:
        mock_engine = Mock()
        mock_response = GenerationResponse(
            content="---\nvalid playbook",
            model="gemini-2.0-flash-001",
            usage_tokens=500
        )
        mock_engine.generate.return_value = mock_response
        mock_llm_factory.return_value = mock_engine

        with patch('src.engine.PlaybookValidator') as mock_validator_class:
            mock_validator = Mock()
            mock_validation = ValidationResult(
                is_valid=True,
                lint_output="passed",
                syntax_check_output="OK",
                errors=[],
                warnings=[]
            )
            mock_validator.validate.return_value = mock_validation
            mock_validator_class.return_value = mock_validator

            result = generate_playbook(
                description="Deploy Redis",
                llm_provider="gemini",
                api_key="test_key"
            )

            assert result.success
            assert "valid playbook" in result.playbook_yaml

# tests/test_utils.py

def test_save_playbook_creates_file(tmp_path):
    """Test playbook is saved with correct filename."""
    yaml_content = "---\ntest: playbook"

    filepath = save_playbook(yaml_content, "Test Deployment", tmp_path)

    assert filepath.exists()
    assert filepath.read_text() == yaml_content
    assert "test_deployment" in filepath.name.lower()

def test_create_zip_bundle():
    """Test ZIP bundle contains both files."""
    playbook = "---\ntest: playbook"
    readme = "# README\nTest"

    zip_bytes = create_zip_bundle(playbook, readme, "test-bundle")

    # Verify ZIP is valid
    with zipfile.ZipFile(BytesIO(zip_bytes)) as zf:
        assert "playbook.yml" in zf.namelist()
        assert "README.md" in zf.namelist()
        assert zf.read("playbook.yml").decode() == playbook
```

```bash
# Run tests iteratively until passing:
source venv_linux/bin/activate
pytest tests/ -v --cov=src --cov-report=term-missing

# Target: 80%+ code coverage
```

### Level 3: Integration Test
```bash
# Build Docker images
docker-compose build

# Start services
docker-compose up

# In browser, navigate to:
http://localhost:8501

# Test workflow:
# 1. Enter API key in sidebar
# 2. Tab 1: Enter "Deploy Redis" and click Generate
# 3. Verify playbook appears in editor
# 4. Tab 2: Edit playbook in visual editor
# 5. Click Validate - verify feedback appears
# 6. Click Save - verify appears in library
# 7. Click Download ZIP - verify both files in bundle

# Stop services
docker-compose down
```

## Final Validation Checklist
- [ ] Engine refactoring preserves MCP server functionality
- [ ] Streamlit app starts without errors
- [ ] AI Generator tab generates playbooks
- [ ] Visual editor displays YAML with syntax highlighting
- [ ] Live validation shows errors in sidebar
- [ ] Save to library persists playbooks in Docker volume
- [ ] Download ZIP includes playbook + README
- [ ] API keys work from UI (override .env)
- [ ] Saved playbooks list loads from filesystem
- [ ] Load playbook populates editor
- [ ] All unit tests pass
- [ ] Docker Compose orchestrates both services
- [ ] README updated with web interface docs

---

## Anti-Patterns to Avoid
- ❌ Don't put state in global variables - use st.session_state
- ❌ Don't validate on every keystroke - use button or debounce
- ❌ Don't break MCP server when refactoring to engine
- ❌ Don't hardcode data paths - use environment variables or config
- ❌ Don't skip filename sanitization - security vulnerability
- ❌ Don't forget to handle missing API keys gracefully
- ❌ Don't use st.cache_data for session-specific data
- ❌ Don't forget type hints in new code (per CLAUDE.md)
- ❌ Don't create files >500 lines - split app.py into modules if needed
- ❌ Don't commit .env with real API keys

## Research Sources

**Streamlit:**
- [Session State Documentation](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state)
- [Docker Deployment Guide](https://docs.streamlit.io/deploy/tutorials/docker)
- [Streamlit Ace GitHub](https://github.com/okld/streamlit-ace)
- [Streamlit Ace PyPI](https://pypi.org/project/streamlit-ace/)

**Docker & Persistence:**
- [Docker Volumes Documentation](https://docs.docker.com/engine/storage/volumes/)
- [Streamlit with Docker Compose](https://www.rockyourcode.com/run-streamlit-with-docker-and-docker-compose/)
- [Docker Compose Volume Management](https://geekchamp.com/use-volumes-in-docker-compose-to-manage-persistent-data/)

**Python Standard Library:**
- [Zipfile Documentation](https://docs.python.org/3/library/zipfile.html)

**Community Examples:**
- [Streamlit File Upload/Download Discussion](https://discuss.streamlit.io/t/download-upload-session-state/24141)
- [Using Session State with File Uploader](https://discuss.streamlit.io/t/using-session-state-with-file-uploader/6553)

## Confidence Score: 8/10

**High confidence due to:**
- Clear Streamlit documentation and patterns
- Existing engine logic well-tested and working
- Simple refactoring (extract functions, no algorithm changes)
- Standard Docker Compose patterns
- Well-defined file operations (save/load/zip)

**Minor uncertainty on:**
- streamlit-ace exact API (may need minor adjustments)
- Optimal UI/UX flow (may iterate based on usability)
- Docker Compose environment variable passing (standard but needs testing)

**Mitigation:**
- Validation loops catch issues early
- Streamlit's hot reload enables rapid iteration
- Engine tests ensure core logic remains intact after refactor
