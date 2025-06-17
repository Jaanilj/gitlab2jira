# Contributing to GitLab to Jira CLI

Thank you for your interest in contributing to GitLab to Jira CLI! This document provides guidelines and information for contributors.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful and constructive in all interactions.

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When creating a bug report, please include:

- **Clear title and description**
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Environment details** (OS, Python version, etc.)
- **Configuration** (sanitized, without sensitive tokens)
- **Log output** or error messages

### Suggesting Features

Feature requests are welcome! Please provide:

- **Clear description** of the feature
- **Use case** and motivation
- **Possible implementation** approach (if you have ideas)
- **Examples** of how it would work

### Pull Requests

1. **Fork** the repository
2. **Create a branch** from `main` for your feature/fix
3. **Make your changes** following the coding standards
4. **Test your changes** thoroughly
5. **Update documentation** if needed
6. **Submit a pull request**

#### Branch Naming

Use descriptive branch names:
- `feature/add-bulk-processing`
- `fix/authentication-error`
- `docs/update-readme`

#### Commit Messages

Follow conventional commit format:
- `feat: add support for custom fields`
- `fix: resolve authentication timeout issue`
- `docs: update installation instructions`
- `refactor: improve error handling`

## Development Setup

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- Git

### Local Development

1. **Clone your fork**:
   ```bash
   git clone https://github.com/yourusername/gitlab2jira.git
   cd gitlab2jira
   ```

2. **Install dependencies**:
   ```bash
   # Using uv (recommended)
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -r requirements.txt
   
   # Or using pip
   pip install -r requirements.txt
   ```

3. **Make the script executable**:
   ```bash
   chmod +x gitlab2jira.py
   ```

4. **Test your setup**:
   ```bash
   ./gitlab2jira.py --help
   ```

### Testing

Before submitting changes:

1. **Test with dry-run mode**:
   ```bash
   ./gitlab2jira.py "https://gitlab.com/test/repo/-/merge_requests/1" --dry-run
   ```

2. **Test configuration setup**:
   ```bash
   ./gitlab2jira.py --setup
   ```

3. **Test with different options**:
   ```bash
   ./gitlab2jira.py "https://gitlab.com/test/repo/-/merge_requests/1" \
     --project "TEST" --issue-type "Bug" --dry-run
   ```

4. **Test edge cases**:
   - Invalid URLs
   - Missing configuration
   - Network errors
   - Invalid credentials

### Code Style

- Follow **PEP 8** Python style guidelines
- Use **type hints** where appropriate
- Add **docstrings** for functions and classes
- Keep **line length** under 100 characters
- Use **meaningful variable names**

### Documentation

When making changes that affect users:

- Update the **README.md**
- Update **CHANGELOG.md**
- Add **docstrings** to new functions
- Update **command-line help text**

## Architecture Overview

### Main Components

1. **Configuration Management** (`Config` class)
   - Handles loading/saving configuration
   - Manages environment variables
   - Interactive setup wizard

2. **GitLab API Client** (`GitLabAPI` class)
   - Fetches merge request data
   - Updates MR titles
   - Handles GitLab authentication

3. **Jira API Client** (`JiraAPI` class)
   - Creates tickets with ADF formatting
   - Handles workflow transitions
   - Manages Jira authentication

4. **Markdown Conversion**
   - Converts GitLab markdown to Jira ADF
   - Handles various formatting elements
   - Preserves structure and links

5. **CLI Interface**
   - Argument parsing
   - Command execution
   - Error handling and user feedback

### Key Functions

- `parse_mr_url()`: Extracts project and MR ID from GitLab URLs
- `convert_markdown_to_jira()`: Converts markdown to Jira ADF format
- `create_jira_document()`: Builds structured Jira ticket content
- `main()`: Main CLI entry point

## Common Development Tasks

### Adding New CLI Options

1. Add argument to `argparse` setup in `main()`
2. Update help text and documentation
3. Handle the new option in the logic
4. Test with various combinations

### Extending Markdown Conversion

1. Add new conversion logic to `convert_markdown_to_jira()`
2. Update `create_jira_document()` if needed
3. Test with various markdown inputs
4. Update documentation with supported formats

### Adding New Configuration Options

1. Update `Config` class initialization
2. Add to interactive setup in `setup_interactive()`
3. Update configuration file schema
4. Document in README.md

## Release Process

1. **Update version** in `pyproject.toml` and `setup.py`
2. **Update CHANGELOG.md** with new features and fixes
3. **Test thoroughly** with real GitLab and Jira instances
4. **Create release PR** with all changes
5. **Tag release** after merging
6. **Create GitHub release** with changelog notes

## Getting Help

If you need help with development:

1. **Check existing issues** for similar questions
2. **Read the documentation** thoroughly
3. **Create a discussion** or issue for questions
4. **Join community discussions** if available

## Recognition

Contributors will be recognized in:
- **README.md** contributors section
- **Release notes** for significant contributions
- **Special thanks** in documentation

Thank you for contributing to making GitLab to Jira CLI better for everyone!
