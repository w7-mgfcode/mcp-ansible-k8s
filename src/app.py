"""Streamlit web application for MCP Ansible-K8s playbook generation."""

import os
from pathlib import Path

import streamlit as st
from streamlit_ace import st_ace  # type: ignore[import-untyped]

from src.engine import generate_playbook, generate_readme, validate_playbook_yaml
from src.utils import (
    create_zip_bundle,
    delete_playbook,
    list_saved_playbooks,
    load_playbook,
    save_playbook,
)

# Page configuration
st.set_page_config(
    page_title="MCP Ansible-K8s Studio",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Data directory
DATA_DIR = Path("data")


def initialize_session_state() -> None:
    """Initialize Streamlit session state variables."""
    if "current_playbook" not in st.session_state:
        st.session_state.current_playbook = ""
    if "validation_result" not in st.session_state:
        st.session_state.validation_result = None
    if "gemini_api_key" not in st.session_state:
        st.session_state.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
    if "claude_api_key" not in st.session_state:
        st.session_state.claude_api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if "last_description" not in st.session_state:
        st.session_state.last_description = ""


def create_sidebar() -> None:
    """Create sidebar with API keys and playbook library."""
    st.sidebar.title("⚙️ Configuration")

    # API Keys Section
    st.sidebar.subheader("🔑 API Keys")
    st.sidebar.caption("Enter your LLM provider API keys")

    st.session_state.gemini_api_key = st.sidebar.text_input(
        "Gemini API Key",
        value=st.session_state.gemini_api_key,
        type="password",
        help="Get your key from https://ai.google.dev/",
    )

    st.session_state.claude_api_key = st.sidebar.text_input(
        "Claude API Key",
        value=st.session_state.claude_api_key,
        type="password",
        help="Get your key from https://console.anthropic.com/",
    )

    # Playbook Library Section
    st.sidebar.divider()
    st.sidebar.subheader("📚 Playbook Library")

    playbooks = list_saved_playbooks(DATA_DIR)

    if playbooks:
        st.sidebar.caption(f"{len(playbooks)} saved playbook(s)")

        # Create selection list with timestamps
        playbook_options = {
            f"{p.created_at.strftime('%Y-%m-%d %H:%M')} - {p.description}": p.filename
            for p in playbooks
        }

        selected_display = st.sidebar.selectbox(
            "Select playbook", options=list(playbook_options.keys()), label_visibility="collapsed"
        )

        if selected_display:
            selected_filename = playbook_options[selected_display]

            col1, col2 = st.sidebar.columns(2)

            with col1:
                if st.button("📂 Load", use_container_width=True):
                    try:
                        content = load_playbook(selected_filename, DATA_DIR)
                        st.session_state.current_playbook = content
                        st.success("Loaded successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error loading: {e}")

            with col2:
                if st.button("🗑️ Delete", use_container_width=True):
                    if delete_playbook(selected_filename, DATA_DIR):
                        st.success("Deleted successfully!")
                        st.rerun()
                    else:
                        st.error("Delete failed")
    else:
        st.sidebar.info("No saved playbooks yet. Generate one in the AI tab!")


def create_generator_tab() -> None:
    """Create the AI Generator tab."""
    st.header("🤖 AI Playbook Generator")
    st.caption("Generate Ansible Kubernetes playbooks from natural language")

    # LLM Provider Selection
    col1, col2 = st.columns([3, 1])

    with col1:
        description = st.text_area(
            "Describe your desired Kubernetes deployment:",
            value=st.session_state.last_description,
            placeholder="Example: Deploy HA Nginx with 3 replicas and a LoadBalancer service on port 80",
            height=120,
            help="Describe what you want to deploy in plain English",
        )

    with col2:
        llm_provider = st.radio(
            "LLM Provider", options=["gemini", "claude"], index=0, help="Choose your AI provider"
        )

        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.3,
            step=0.1,
            help="Lower = more consistent, Higher = more creative",
        )

    # Get appropriate API key
    api_key = (
        st.session_state.gemini_api_key
        if llm_provider == "gemini"
        else st.session_state.claude_api_key
    )

    # Generate button
    if st.button("🚀 Generate Playbook", type="primary", use_container_width=True):
        if not api_key:
            st.error(f"❌ Please set {llm_provider.upper()} API key in the sidebar first!")
            return

        if not description.strip():
            st.warning("Please enter a description of what you want to deploy")
            return

        # Save description for next time
        st.session_state.last_description = description

        with st.spinner("🤖 Generating playbook with AI..."):
            result = generate_playbook(
                description=description,
                llm_provider=llm_provider,
                api_key=api_key,
                temperature=temperature,
            )

        if result.success:
            st.success(
                f"✓ Generated successfully with {result.model_used} ({result.tokens_used} tokens)"
            )
            st.session_state.current_playbook = result.playbook_yaml
            st.session_state.validation_result = result.validation_result
        else:
            st.error(f"✗ Generation failed: {result.error_message}")
            if result.validation_result:
                with st.expander("View validation errors"):
                    for error in result.validation_result.errors:
                        st.code(error)

    # Display generated playbook
    if st.session_state.current_playbook:
        st.divider()
        st.subheader("📝 Generated Playbook")

        # Display in read-only ace editor
        st_ace(
            value=st.session_state.current_playbook,
            language="yaml",
            theme="monokai",
            height=400,
            readonly=True,
            show_gutter=True,
            show_print_margin=False,
        )

        # Action buttons
        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 Save to Library", use_container_width=True):
                try:
                    desc = st.session_state.last_description or "Playbook"
                    filepath = save_playbook(st.session_state.current_playbook, desc, DATA_DIR)
                    st.success(f"Saved as {filepath.name}")
                except Exception as e:
                    st.error(f"Error saving: {e}")

        with col2:
            if st.button("✏️ Edit in Visual Editor", use_container_width=True):
                st.session_state.editor_tab_switch = True
                st.rerun()


def create_editor_tab() -> None:
    """Create the Visual Editor tab."""
    st.header("✏️ Visual Playbook Editor")
    st.caption("Edit and validate Ansible playbooks with syntax highlighting")

    # Editor
    edited_content = st_ace(
        value=st.session_state.current_playbook,
        language="yaml",
        theme="monokai",
        height=400,
        key="yaml_editor",
        show_gutter=True,
        show_print_margin=False,
        wrap=True,
    )

    # Update session state if editor changed
    if edited_content != st.session_state.current_playbook:
        st.session_state.current_playbook = edited_content

    # File upload
    st.divider()
    uploaded_file = st.file_uploader(
        "📤 Or upload an existing playbook",
        type=["yml", "yaml"],
        help="Upload a YAML playbook file to validate or edit",
    )

    if uploaded_file is not None:
        content = uploaded_file.read().decode("utf-8")
        st.session_state.current_playbook = content
        st.success(f"Loaded {uploaded_file.name}")
        st.rerun()

    # Action buttons
    st.divider()
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("✅ Validate", use_container_width=True, type="primary"):
            if st.session_state.current_playbook:
                with st.spinner("Validating playbook..."):
                    result = validate_playbook_yaml(st.session_state.current_playbook)
                    st.session_state.validation_result = result

                if result.is_valid:
                    st.success("✓ Playbook is valid!")
                else:
                    st.error("✗ Validation failed - see details below")
            else:
                st.warning("No playbook to validate")

    with col2:
        if st.button("💾 Save", use_container_width=True):
            if st.session_state.current_playbook:
                desc = st.text_input("Description:", value="My Playbook", key="save_desc")
                try:
                    filepath = save_playbook(st.session_state.current_playbook, desc, DATA_DIR)
                    st.success(f"Saved as {filepath.name}")
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("No playbook to save")

    with col3:
        # Download ZIP with README
        if st.button("📦 Download Bundle", use_container_width=True):
            if st.session_state.current_playbook:
                # Get API key for README generation
                llm_provider = "gemini" if st.session_state.gemini_api_key else "claude"
                api_key = st.session_state.gemini_api_key or st.session_state.claude_api_key

                if api_key:
                    with st.spinner("Generating README..."):
                        readme = generate_readme(
                            st.session_state.current_playbook, llm_provider, api_key
                        )
                        zip_bytes = create_zip_bundle(
                            st.session_state.current_playbook,
                            readme,
                            "deployment-playbook",
                        )

                    st.download_button(
                        label="⬇️ Download ZIP",
                        data=zip_bytes,
                        file_name="ansible-k8s-playbook.zip",
                        mime="application/zip",
                        use_container_width=True,
                    )
                else:
                    st.warning("API key needed for README generation")
            else:
                st.warning("No playbook to download")

    with col4:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.current_playbook = ""
            st.session_state.validation_result = None
            st.rerun()

    # Validation Results
    if st.session_state.validation_result:
        st.divider()
        st.subheader("🔍 Validation Results")

        result = st.session_state.validation_result

        if result.is_valid:
            st.success("✓ Playbook passed all validation checks!")

            with st.expander("📄 Lint Output"):
                st.code(result.lint_output or "(no output)")

            with st.expander("📄 Syntax Check Output"):
                st.code(result.syntax_check_output or "(no output)")
        else:
            st.error("✗ Validation Failed")

            for idx, error in enumerate(result.errors, 1):
                with st.expander(f"Error {idx}", expanded=True):
                    st.code(error, language="text")

        if result.warnings:
            st.warning("⚠️ Warnings")
            for warning in result.warnings:
                st.code(warning, language="text")


def main() -> None:
    """Main Streamlit application entry point."""
    # Initialize session state
    initialize_session_state()

    # Title
    st.title("🚀 MCP Ansible-K8s Studio")
    st.caption("AI-Powered Kubernetes Playbook Generation & Validation")

    # Create sidebar
    create_sidebar()

    # Create tabs
    tab1, tab2 = st.tabs(["🤖 AI Generator", "✏️ Visual Editor"])

    with tab1:
        create_generator_tab()

    with tab2:
        create_editor_tab()

    # Footer
    st.divider()
    st.caption(
        "💡 **Tip**: Generate playbooks with AI, edit visually, and download as a bundle with documentation!"
    )


if __name__ == "__main__":
    main()
