# Security Policy

## Supported Versions

We actively support the following versions of TTRPG Assistant with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | ✅ Yes             |
| 1.2.x   | ✅ Yes (until 2025-06-01) |
| 1.1.x   | ❌ No              |
| < 1.1   | ❌ No              |

## Security Considerations

### Data Handling
- **PDF Files**: The system processes PDF files which may contain potentially malicious content
- **User Input**: All user input is processed through search queries and configuration files
- **File System Access**: The application reads/writes to local file system for ChromaDB and cache storage
- **Network Access**: May make network requests for model downloads and Discord integration

### Built-in Security Measures

#### Input Validation
- PDF file size limits (configurable, default 100MB)
- Query length limitations
- File path sanitization
- Configuration schema validation

#### File System Security
- Sandboxed file access within configured directories
- No execution of user-provided code
- Safe PDF parsing with error handling

#### Network Security
- HTTPS-only model downloads
- Discord bot token validation
- No external API calls with user data

#### Data Privacy
- Local data storage only (ChromaDB)
- No telemetry by default (ChromaDB anonymized telemetry can be disabled)
- PDF content remains local to your system

### Configuration Security

#### Secure Configuration
```yaml
# Example secure config
chromadb:
  persist_directory: "./chroma_db"  # Relative path within project
  anonymized_telemetry: false       # Disable telemetry

pdf_processing:
  max_file_size_mb: 50             # Limit file sizes
  enable_adaptive_learning: true   # Safe ML features only

discord:
  token: "your-token-here"         # Keep tokens secure
```

#### Insecure Configurations to Avoid
- Absolute paths outside the project directory
- Overly large file size limits
- Storing Discord tokens in version control

## Reporting a Vulnerability

### Where to Report
Please report security vulnerabilities by:

1. **Email**: Send details to [security@example.com] (replace with actual email)
2. **GitHub Security Advisories**: Use GitHub's private security reporting
3. **Direct Message**: Contact maintainers directly for sensitive issues

### What to Include
Please include the following information:
- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact assessment
- Suggested mitigation (if any)
- Your contact information for follow-up

### Response Timeline
- **Initial Response**: Within 48 hours
- **Vulnerability Assessment**: Within 1 week
- **Security Fix**: Within 2-4 weeks (depending on severity)
- **Public Disclosure**: After fix is released and deployed

### Security Fix Process
1. **Triage**: Assess severity and impact
2. **Development**: Create fix in private repository
3. **Testing**: Validate fix doesn't break functionality
4. **Release**: Publish patched version
5. **Disclosure**: Public security advisory after fix deployment

## Security Best Practices for Users

### Installation Security
```bash
# Verify downloads
wget https://github.com/user/repo/releases/download/v2.0.0/ttrpg-assistant.tar.gz
# Check checksums if provided
sha256sum ttrpg-assistant.tar.gz

# Use virtual environments
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Runtime Security
- Run with minimal necessary permissions
- Keep dependencies updated
- Use strong Discord bot permissions (if using Discord integration)
- Regularly backup your ChromaDB data
- Monitor log files for suspicious activity

### PDF File Security
- Only process trusted PDF files
- Scan PDFs for malware before processing
- Be cautious with PDFs from unknown sources
- Monitor disk usage during processing

### Network Security
- Use HTTPS for all downloads
- Keep Discord bot tokens secret
- Don't expose the web UI to public internet without authentication
- Use firewall rules to restrict network access

### Configuration Security
```bash
# Secure file permissions
chmod 600 config/config.yaml
chmod 700 config/

# Don't commit sensitive data
echo "config/local_config.yaml" >> .gitignore
echo "*.secret" >> .gitignore
```

## Known Security Considerations

### PDF Processing
- **Risk**: Malicious PDF files could cause crashes or resource exhaustion
- **Mitigation**: File size limits, timeout handling, sandboxed processing

### File System Access
- **Risk**: Path traversal attacks through configuration
- **Mitigation**: Path sanitization, restricted base directories

### Model Downloads
- **Risk**: Man-in-the-middle attacks during model downloads
- **Mitigation**: HTTPS-only downloads, checksum verification (when available)

### ChromaDB Storage
- **Risk**: Unencrypted local storage of processed content
- **Mitigation**: File system permissions, consider disk encryption

### Discord Integration
- **Risk**: Bot token exposure or misuse
- **Mitigation**: Environment variables, secure token storage, minimal permissions

## Security Updates

### Automatic Updates
The application does not automatically update itself. Users should:
- Subscribe to GitHub releases
- Monitor the changelog for security fixes
- Update promptly when security releases are available

### Security Notifications
- Security advisories published on GitHub
- Critical issues announced in README
- Discord server notifications (if available)

## Compliance and Standards

### Privacy Compliance
- GDPR: Local processing only, no data transmission
- CCPA: No personal data collection by default
- General: Users control all data, can delete at any time

### Security Standards
- Follow OWASP guidelines for web applications
- Use secure coding practices
- Regular dependency vulnerability scanning
- Static analysis with bandit and other tools

## Contact Information

### Security Team
- Primary Contact: [security-email]
- GitHub: [@maintainer-username]
- Response Time: 48 hours maximum

### Community Security
- GitHub Issues: For non-sensitive security discussions
- Discord: #security channel (if available)
- Documentation: security section in docs/

---

**Note**: This is a community project. While we take security seriously, users should evaluate their own risk tolerance and implement additional security measures as needed for their specific use cases.