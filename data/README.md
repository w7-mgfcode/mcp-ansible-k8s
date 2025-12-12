# Playbook Storage

This directory stores generated and saved playbooks.

## Structure

- `playbooks/` - Saved YAML playbooks with timestamp prefixes
- Format: `YYYYMMDD_HHMMSS_description.yml`

## Persistence

When running with Docker Compose, this directory is backed by a named Docker volume (`playbook-data`) ensuring playbooks persist across container restarts.
