"""
Demo script to test MCP Ansible-K8s playbook generation.

This script demonstrates the server's capability to generate validated
Ansible Kubernetes playbooks from natural language descriptions.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Settings
from src.llm_engine import GenerationRequest, create_llm_engine
from src.prompts import load_system_prompt
from src.validator import PlaybookValidator


def test_playbook_generation(description: str) -> None:
    """
    Test playbook generation for a given description.

    Args:
        description: Natural language description of deployment
    """
    print(f"\n{'=' * 80}")
    print(f"Testing: {description}")
    print(f"{'=' * 80}\n")

    # Initialize components
    settings = Settings()
    settings.validate_api_keys()

    llm_engine = create_llm_engine(settings)
    validator = PlaybookValidator(timeout=settings.docker_validation_timeout)
    system_prompt = load_system_prompt()

    # Generate playbook
    print("🤖 Generating playbook...")
    request = GenerationRequest(
        user_prompt=description,
        system_prompt=system_prompt,
        max_tokens=4096,
        temperature=0.3,
    )

    response = llm_engine.generate(request)
    playbook = response.content

    print(f"✓ Generated with {response.model}")
    if response.usage_tokens:
        print(f"  Tokens used: {response.usage_tokens}")

    # Validate playbook
    print("\n🔍 Validating playbook...")
    validation = validator.validate(playbook)

    if validation.is_valid:
        print("✓ Validation passed!")
    else:
        print("✗ Validation failed:")
        for error in validation.errors:
            print(f"  - {error}")

    # Display playbook
    print("\n📝 Generated Playbook:")
    print("-" * 80)
    print(playbook)
    print("-" * 80)


def main() -> None:
    """Run test generation examples."""
    print("\n" + "=" * 80)
    print("MCP Ansible-K8s Playbook Generation Test")
    print("=" * 80)

    # Test cases
    test_cases = [
        "Deploy Lonhorn via helm with 2 replicas",
    ]

    for test_case in test_cases:
        try:
            test_playbook_generation(test_case)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 80)
    print("Test Complete!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
