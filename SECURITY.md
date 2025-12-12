# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Security Model & Trust Boundaries

### Docker Socket Access

**⚠️ IMPORTANT: Docker Socket Security Implications**

The current implementation (v0.2.0) mounts the Docker socket (`/var/run/docker.sock`) into both the `web` and `mcp` services for playbook validation purposes. This design decision has significant security implications:

**Risk Level:** 🟡 **MEDIUM** (for trusted environments)
**Risk Level:** 🔴 **HIGH** (for untrusted/public deployments)

#### What This Means

Mounting the Docker socket grants services:
- ✅ Ability to spawn validation containers (required functionality)
- ⚠️ Root-level control over the host Docker daemon
- ⚠️ Potential to access other containers on the host
- ⚠️ Ability to mount arbitrary host filesystems
- ⚠️ Escape to host system (if exploited)

#### Current Mitigations

1. **Input Sanitization**: All user input is sanitized before validation
   - Filenames: Regex sanitization prevents path traversal
   - YAML content: Validated before Docker execution
   - No user input directly passed to shell commands

2. **Read-Only Mounts**: Source code mounted read-only (`:ro`)

3. **Isolated Network**: Services run on dedicated Docker network

4. **Documentation**: Security warnings in docker-compose.yml

5. **Principle of Least Privilege**: Containers run as non-root where possible

#### Safe Usage Guidelines

**✅ SAFE FOR:**
- Local development environments
- Internal/corporate networks with trusted users
- Single-user deployments
- Testing and demonstration

**❌ NOT RECOMMENDED FOR:**
- Public-facing deployments
- Multi-tenant environments
- Untrusted user access
- Production without additional hardening

#### Deployment Recommendations

**For Development/Testing:**
```bash
# Current docker-compose.yml is acceptable
docker-compose up
```

**For Production:**

1. **Restrict Network Access:**
   ```yaml
   # Add to docker-compose.yml
   services:
     web:
       networks:
         - mcp-network
       ports:
         - "127.0.0.1:8501:8501"  # Bind to localhost only
   ```

2. **Use Firewall Rules:**
   ```bash
   # Allow only specific IPs
   sudo ufw allow from 10.0.0.0/8 to any port 8501
   ```

3. **Add Authentication:**
   - Deploy behind reverse proxy (nginx, traefik)
   - Implement OAuth/SSO (e.g., Auth0, Okta)
   - Use VPN for access control

4. **Monitor Container Activity:**
   ```bash
   # Enable Docker audit logging
   docker events --filter 'container=mcp-ansible-web' --format '{{json .}}'
   ```

### Future Architecture (v0.3.0+)

**Planned Security Enhancement:**

We plan to eliminate Docker socket mounts from web/mcp services by implementing a dedicated **Validator API Service**:

```yaml
services:
  validator-api:
    # Only this service has Docker socket access
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    ports:
      - "8000:8000"  # Internal API

  web:
    # No socket mount needed
    environment:
      - VALIDATOR_API_URL=http://validator-api:8000
```

**Benefits:**
- ✅ Single point of Docker access (easier to audit)
- ✅ Rate limiting and authentication at API layer
- ✅ Centralized validation logging
- ✅ Ability to run web service without elevated privileges

**Tracking Issue:** [#TBD - Create after merge]

---

## API Key Security

### Storage

**✅ Secure:**
- API keys stored in session state (memory only)
- Not persisted to disk or database
- Cleared when browser session ends

**✅ Transmission:**
- Keys passed as function parameters (not global state)
- Not logged or written to files

**⚠️ Environment Variables:**
- Keys in `.env` file must be protected (chmod 600)
- Never commit `.env` to version control (in .gitignore)

### Best Practices

1. **Use Environment Variables for Server:**
   ```bash
   # .env (chmod 600)
   GEMINI_API_KEY=your_key_here
   ```

2. **Use UI Input for Development:**
   - Enter keys in Streamlit sidebar
   - Session-specific (not shared across users)

3. **Rotate Keys Regularly:**
   - Rotate API keys every 90 days
   - Use separate keys for dev/staging/prod

4. **Monitor Usage:**
   - Check LLM provider dashboards for unusual activity
   - Set spending limits on API accounts

---

## Reporting a Vulnerability

If you discover a security vulnerability, please **DO NOT** open a public issue.

Instead, please report it privately:

**Email:** [security@yourdomain.com]
**GitHub Security Advisory:** https://github.com/w7-mgfcode/mcp-ansible-k8s/security/advisories/new

**Response Time:**
- Acknowledgment: Within 24 hours
- Initial assessment: Within 3 business days
- Fix timeline: Depends on severity (critical issues addressed immediately)

### Disclosure Policy

We follow **responsible disclosure**:
1. Security issue reported privately
2. We confirm and develop a fix
3. Fix released and deployed
4. Public disclosure after 90 days (or sooner if agreed)

---

## Security Best Practices for Users

### Production Deployment Checklist

- [ ] Deploy behind authentication (OAuth, VPN, etc.)
- [ ] Restrict network access (firewall, localhost binding)
- [ ] Use separate API keys for prod (not shared with dev)
- [ ] Enable Docker audit logging
- [ ] Regularly update dependencies (Streamlit, Python packages)
- [ ] Monitor API usage and costs
- [ ] Review generated playbooks before deployment
- [ ] Keep validator image updated (ansible-lint versions)

### Development Checklist

- [ ] Never commit `.env` files
- [ ] Use `chmod 600` for files containing secrets
- [ ] Rotate API keys if accidentally exposed
- [ ] Review Streamlit session state before sharing screens
- [ ] Use `.gitignore` to prevent secret commits

---

## Known Limitations (v0.2.0)

1. **Docker Socket Access** (see above)
2. **No Built-in Authentication** (use reverse proxy)
3. **Session-based API Keys** (not encrypted at rest in memory)
4. **No Rate Limiting** (on LLM API calls from UI)

These limitations are acceptable for:
- Development environments
- Single-user deployments
- Trusted internal networks

For production use, additional hardening is required.

---

## Version History

### v0.2.0 (Current)
- Added Streamlit web interface
- Documented Docker socket security implications
- Added input sanitization for path traversal prevention

### v0.1.0
- Initial MCP server release
- Docker-based validation
- Gemini and Claude support

---

**Last Updated:** 2025-12-12
**Next Security Review:** v0.3.0 (Validator API Service implementation)
