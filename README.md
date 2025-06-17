# GitLab to Jira CLI

A command-line tool to create Jira tickets from GitLab merge requests with automatic markdown conversion and rich formatting.

## Features

- 🔗 **Easy Integration**: Convert GitLab merge requests to Jira tickets with a single command
- 📝 **Markdown Conversion**: Automatically converts GitLab markdown to Jira Document Format (ADF)
- ⚙️ **Flexible Configuration**: Support for multiple GitLab/Jira instances and project mappings
- 🎯 **Smart Defaults**: Pre-configured settings for issue types, labels, and priorities
- 🔄 **Workflow Integration**: Optional GitLab MR title updates with Jira ticket references
- 🧪 **Dry Run Mode**: Test your configuration without creating actual tickets

## Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- GitLab Personal Access Token with API access
- Jira API Token

## Installation

### Using uv (Recommended)

The script is designed to run with `uv` and includes all dependencies in the script header:

```bash
# Clone the repository
git clone https://github.com/yourusername/gitlab2jira.git
cd gitlab2jira

# Make the script executable
chmod +x gitlab2jira.py

# Run directly with uv (dependencies will be installed automatically)
./gitlab2jira.py --setup
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/gitlab2jira.git
cd gitlab2jira

# Install dependencies
pip install requests

# Run the setup
python gitlab2jira.py --setup
```

## Quick Start

1. **Setup Configuration**:
   ```bash
   ./gitlab2jira.py --setup
   ```
   This will guide you through setting up your GitLab and Jira credentials.

2. **Create a Jira Ticket from GitLab MR**:
   ```bash
   ./gitlab2jira.py "https://gitlab.com/namespace/project/-/merge_requests/123"
   ```

3. **Test with Dry Run**:
   ```bash
   ./gitlab2jira.py "https://gitlab.com/namespace/project/-/merge_requests/123" --dry-run
   ```

## Usage

### Basic Usage

```bash
./gitlab2jira.py <gitlab_mr_url> [options]
```

### Options

- `--setup`: Interactive configuration setup
- `--dry-run`: Preview the Jira ticket without creating it
- `--project PROJECT_KEY`: Override default Jira project
- `--issue-type TYPE`: Issue type (default: Task)
- `--labels LABEL1 LABEL2`: Add labels to the ticket
- `--components COMP1 COMP2`: Add components to the ticket
- `--priority PRIORITY`: Set ticket priority
- `--no-update-mr`: Don't update GitLab MR title with Jira ticket reference
- `--transition STATUS`: Transition ticket to specific status after creation

### Examples

**Create a bug ticket with high priority:**
```bash
./gitlab2jira.py "https://gitlab.com/project/repo/-/merge_requests/456" \
  --issue-type "Bug" \
  --priority "High" \
  --labels "urgent" "backend"
```

**Preview ticket creation:**
```bash
./gitlab2jira.py "https://gitlab.com/project/repo/-/merge_requests/789" \
  --dry-run \
  --components "Authentication" "API"
```

**Create ticket and transition to "In Progress":**
```bash
./gitlab2jira.py "https://gitlab.com/project/repo/-/merge_requests/123" \
  --transition "In Progress"
```

## Configuration

### Configuration File

The tool stores configuration in `~/.gitlab-jira-cli.json`:

```json
{
  "gitlab": {
    "url": "https://gitlab.com",
    "token": "glpat-xxxxxxxxxxxxxxxxxxxx"
  },
  "jira": {
    "url": "https://yourcompany.atlassian.net",
    "username": "your.email@company.com",
    "api_token": "ATATT3xFfGF0xxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "project_key": "DEV"
  },
  "defaults": {
    "issue_type": "Task",
    "labels": ["merge-request"],
    "components": [],
    "priority": null
  },
  "project_mappings": {
    "namespace/frontend-app": {
      "jira_project_key": "FRONT"
    },
    "namespace/backend-api": {
      "jira_project_key": "BACK"
    }
  }
}
```

### Environment Variables

You can also configure using environment variables:

```bash
export GITLAB_URL="https://gitlab.com"
export GITLAB_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxx"
export JIRA_URL="https://yourcompany.atlassian.net"
export JIRA_USERNAME="your.email@company.com"
export JIRA_API_TOKEN="ATATT3xFfGF0xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export JIRA_PROJECT_KEY="DEV"
```

### Project Mappings

Map different GitLab projects to different Jira projects:

```json
{
  "project_mappings": {
    "company/mobile-app": {
      "jira_project_key": "MOBILE"
    },
    "company/web-frontend": {
      "jira_project_key": "WEB"
    },
    "company/backend-services": {
      "jira_project_key": "BACKEND"
    }
  }
}
```

## Getting API Tokens

### GitLab Personal Access Token

1. Go to GitLab → User Settings → Access Tokens
2. Create a new token with `api` scope
3. Copy the token (starts with `glpat-`)

### Jira API Token

1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Create a new API token
3. Copy the token (starts with `ATATT`)

## Markdown to Jira Conversion

The tool automatically converts GitLab Flavored Markdown to Jira's Atlassian Document Format (ADF):

| Markdown | Jira Result |
|----------|-------------|
| `# Heading` | Large heading |
| `## Subheading` | Medium heading |
| `**bold**` | **Bold text** |
| `*italic*` | *Italic text* |
| `[link](url)` | Clickable link |
| `` `code` `` | Inline code |
| `- List item` | Bullet list |
| `1. Numbered` | Numbered list |

## Troubleshooting

### Common Issues

**"Invalid GitLab merge request URL format"**
- Ensure the URL follows the format: `https://gitlab.com/namespace/project/-/merge_requests/123`

**"Error: Missing configuration"**
- Run `./gitlab2jira.py --setup` to configure your credentials

**"GitLab API Error: 401 Unauthorized"**
- Check your GitLab token has `api` scope
- Verify the token hasn't expired

**"Jira API Error: 401 Unauthorized"**
- Verify your Jira credentials and API token
- Check if your Jira instance URL is correct

**"Permission denied"**
- Make sure the script is executable: `chmod +x gitlab2jira.py`

### Debug Mode

For troubleshooting, you can enable debug output by modifying the script or using dry-run mode to see what would be created.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions:

1. Check the [troubleshooting section](#troubleshooting)
2. Search existing [GitHub Issues](https://github.com/yourusername/gitlab2jira/issues)
3. Create a new issue with detailed information about your problem

## Changelog

### v1.0.0
- Initial release
- GitLab MR to Jira ticket conversion
- Markdown to ADF conversion
- Interactive configuration setup
- Dry-run mode
- Project mappings support
