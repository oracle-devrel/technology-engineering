# Security Policy

## Reporting Security Vulnerabilities

We take security seriously and value the independent security research community.

**Please do NOT raise a GitHub Issue to report a security vulnerability.**

If you believe you have found a security vulnerability, please report it responsibly by sending an email to the project maintainers. Include:

- A description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Any suggested fixes (optional)

We ask that you:

- Give us reasonable time to respond before any public disclosure
- Do not access or modify other users' data without permission
- Act in good faith to avoid privacy violations and service disruptions

## Security Updates

Security updates will be released as soon as possible after a vulnerability is confirmed and a fix is available. We recommend always running the latest version of the application.

## Security Considerations

### Application Security

This application follows security best practices:

1. **No Cloud Credentials Stored**: The app never stores cloud provider credentials. All cloud authentication is handled by CI/CD pipelines via GitHub Secrets.

2. **GitHub Credentials Only**: User login is OAuth-first. `GITHUB_TOKEN` is an optional server-side fallback for catalog reads; it must not bypass user-scoped project authorization or create project repositories.

3. **GitOps Approval Gates**: All infrastructure changes go through Pull Request review before being applied.

4. **Audit Trail**: Complete change history is maintained in Git commits.

### Deployment Recommendations

- Run behind a reverse proxy (nginx, Caddy) with TLS
- Set a strong random `SESSION_SECRET` in production (the app warns at startup when the dev placeholder is in use)
- Restrict GitHub token permissions to only required repositories
- Enable branch protection rules on infrastructure repositories
- Regularly rotate credentials

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| Latest  | :white_check_mark: |
| Older   | :x:                |

We recommend always using the latest version for security updates.
