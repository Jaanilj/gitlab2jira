# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-06-17

### Added
- Initial release of GitLab to Jira CLI tool
- Convert GitLab merge requests to Jira tickets
- Automatic markdown to Jira ADF (Atlassian Document Format) conversion
- Interactive configuration setup (`--setup` command)
- Support for multiple GitLab and Jira instances
- Project mapping functionality for routing different GitLab projects to different Jira projects
- Dry-run mode for testing without creating actual tickets
- Configurable default settings (issue types, labels, components, priorities)
- GitLab MR title updating with Jira ticket references
- Ticket workflow transition support
- Environment variable configuration support
- Comprehensive error handling and validation
- Command-line interface with extensive options
- Support for uv package manager with inline dependencies

### Features
- **GitLab Integration**: Fetch merge request details via GitLab API
- **Jira Integration**: Create tickets with rich formatting via Jira API v3
- **Markdown Conversion**: Convert GitLab Flavored Markdown to Jira ADF
- **Flexible Configuration**: JSON config file with environment variable overrides
- **Project Mappings**: Route different GitLab projects to specific Jira projects
- **Workflow Automation**: Optional MR title updates and ticket transitions
- **CLI Options**: Comprehensive command-line interface
- **Error Handling**: Robust error reporting and validation

### Dependencies
- Python 3.12+
- requests library
- Compatible with uv package manager

### Configuration
- Configuration file: `~/.gitlab-jira-cli.json`
- Environment variables support
- Interactive setup wizard
- Project-specific mappings

### Supported Platforms
- macOS
- Linux
- Windows (with Python 3.12+)

## [Unreleased]

### Planned Features
- Bulk processing of multiple merge requests
- Template system for custom ticket formats
- Integration with more GitLab events (issues, commits)
- Support for Jira custom fields
- Enhanced markdown conversion (tables, code blocks)
- Configuration validation and testing tools
