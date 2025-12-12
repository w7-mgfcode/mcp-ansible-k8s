## FEATURE:

- **AI-Powered DevOps Factory:** An MCP server that uses Large Language Models (Gemini or Claude) to dynamically generate Ansible Kubernetes playbooks based on high-level user intent.
- **Sandboxed Validation:** A rigorous "Trust but Verify" architecture. The server generates code using an LLM, then immediately isolates it in a Docker container to run `ansible-lint` and `ansible-playbook --syntax-check` before returning it to the user.
- **Model Agnostic Generation:**
    - Supports **Google Gemini API** and **Anthropic Claude API** for the code generation step.
    - Uses a specialized system prompt within the server to enforce `kubernetes.core` best practices (FQCN, idempotency) during the generation phase.
- **Tools:**
    - `smart_generate_playbook`: Accepts a natural language description (e.g., "HA Nginx with 3 replicas and a LoadBalancer"), calls the configured LLM to draft the YAML, validates it, and returns the clean code.
    - `validate_playbook`: A utility tool to lint external YAML content.

## EXAMPLES:

In the `examples/` folder, we provide scripts to simulate the AI interaction and test the dual-LLM support.

- `examples/test_generation.py` - A script that simulates a user request ("Deploy Redis"), triggering the MCP server to call the configured backend API (Gemini/Claude), generate the file, lint it, and return the result.
- `examples/prompts/` - Contains the system prompts used by the MCP server to instruct the backend LLM on how to write perfect Ansible K8s modules.

## DOCUMENTATION:

- **Google Gemini API:** https://ai.google.dev/gemini-api/docs
- **Anthropic Claude API:** https://platform.claude.com/docs/en/api/overview
- **MCP Python SDK:** https://modelcontextprotocol.io/sdk/python
- **Ansible Kubernetes Collection:** https://docs.ansible.com/ansible/latest/collections/kubernetes/core/k8s_module.html

## OTHER CONSIDERATIONS:

- **API Key Management:** The server requires valid API keys (`GEMINI_API_KEY` or `ANTHROPIC_API_KEY`) loaded via `.env`.
- **Latency vs. Accuracy:** The `smart_generate` tool involves a network call to an LLM followed by a local subprocess call to `ansible-lint`. The timeout settings for the MCP client should be generous (30s+).
- **Prompt Engineering:** The internal system prompt is critical. It must explicitly forbid the use of `command: kubectl` and enforce the use of structured `kubernetes.core` modules.
- **Project Structure:**
    - `src/server.py`: Main entry point.
    - `src/llm_engine.py`: Handles the abstraction between Gemini and Claude APIs.
    - `Dockerfile`: Provides the execution environment for validation.