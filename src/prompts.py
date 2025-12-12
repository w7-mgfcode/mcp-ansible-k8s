"""System prompt management for LLM interactions."""

from pathlib import Path


def load_system_prompt() -> str:
    """
    Load the Ansible K8s expert system prompt from file.

    Returns:
        System prompt string for LLM

    Raises:
        FileNotFoundError: If prompt file doesn't exist
        ValueError: If prompt doesn't contain critical keywords
    """
    prompt_path = Path(__file__).parent.parent / "examples" / "prompts" / "ansible_k8s_expert.txt"

    if not prompt_path.exists():
        raise FileNotFoundError(f"System prompt file not found: {prompt_path}")

    prompt = prompt_path.read_text(encoding="utf-8")

    # Validate that prompt contains critical enforcement keywords
    critical_keywords = [
        "kubernetes.core.k8s",
        "NEVER use kubectl",
        "FQCN",
        "state: present",
    ]

    missing_keywords = [kw for kw in critical_keywords if kw not in prompt]
    if missing_keywords:
        raise ValueError(f"System prompt missing critical keywords: {missing_keywords}")

    return prompt
