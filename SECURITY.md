# Security Policy

## Supported Versions

We actively support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in EKS Cluster Validator, please help us by reporting it responsibly.

### How to Report

**Please DO NOT report security vulnerabilities through public GitHub issues.**

Instead, please report security vulnerabilities by emailing:

- **<security@techize.com>** (if this is a real email) or
- Create a [private security advisory](https://github.com/techize/eks-cluster-validator/security/advisories/new) on GitHub

### What to Include

When reporting a security vulnerability, please include:

1. A clear description of the vulnerability
2. Steps to reproduce the issue
3. Potential impact and severity
4. Any suggested fixes or mitigations
5. Your contact information for follow-up

### Our Response Process

1. **Acknowledgment**: We will acknowledge receipt of your report within 48 hours
2. **Investigation**: We will investigate the issue and provide regular updates
3. **Fix Development**: If confirmed, we will develop and test a fix
4. **Disclosure**: We will coordinate disclosure with you
5. **Release**: We will release the fix and security advisory

### Security Best Practices

When using EKS Cluster Validator:

1. **Credentials**: Never commit AWS credentials to version control
2. **Permissions**: Use the principle of least privilege for IAM roles
3. **Network**: Run validation in secure network environments
4. **Updates**: Keep the tool and dependencies updated
5. **Logs**: Be cautious with log output containing sensitive information

### Known Security Considerations

- The tool requires AWS credentials with read access to EKS, EC2, and other services
- Configuration files may contain sensitive information
- Log files may contain cluster information
- Network traffic to AWS APIs should be monitored

## Contact

For security-related questions or concerns:

- Email: <security@techize.com>
- GitHub Security Advisories: [Create Private Advisory](https://github.com/techize/eks-cluster-validator/security/advisories/new)
