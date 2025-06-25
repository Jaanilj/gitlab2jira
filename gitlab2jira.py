#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests>=2.32.4",
#     "colorama>=0.4.6",
# ]
# ///


"""
GitLab MR to Jira Ticket CLI
A command-line tool to create Jira tickets from GitLab merge requests.
"""

import argparse
import json
import os
import re
import sys
from typing import Dict, Optional, List
import requests
from urllib.parse import urljoin
from colorama import init, Fore, Style

# TypeGuard compatibility for older Python versions
try:
    from typing import TypeGuard
except ImportError:
    # For Python < 3.10, create a simple TypeGuard that acts as a bool
    def TypeGuard(x):
        return bool

# Initialize colorama for cross-platform color support
init(autoreset=True)


class Colors:
    """Color constants and helper functions for CLI output."""

    # Status colors
    SUCCESS = Fore.GREEN
    ERROR = Fore.RED
    WARNING = Fore.YELLOW
    INFO = Fore.CYAN

    # Emphasis colors
    BOLD = Style.BRIGHT
    DIM = Style.DIM
    RESET = Style.RESET_ALL

    # Semantic colors
    HEADER = Fore.MAGENTA + Style.BRIGHT
    URL = Fore.BLUE + Style.BRIGHT
    COMMAND = Fore.WHITE + Style.BRIGHT

    @staticmethod
    def success(text: str) -> str:
        """Format text as success message."""
        return f"{Colors.SUCCESS}✅ {text}{Style.RESET_ALL}"

    @staticmethod
    def error(text: str) -> str:
        """Format text as error message."""
        return f"{Colors.ERROR}❌ {text}{Style.RESET_ALL}"

    @staticmethod
    def warning(text: str) -> str:
        """Format text as warning message."""
        return f"{Colors.WARNING}⚠️  {text}{Style.RESET_ALL}"

    @staticmethod
    def info(text: str) -> str:
        """Format text as info message."""
        return f"{Colors.INFO}ℹ️  {text}{Style.RESET_ALL}"

    @staticmethod
    def header(text: str) -> str:
        """Format text as header."""
        return f"{Colors.HEADER}{text}{Style.RESET_ALL}"

    @staticmethod
    def url(text: str) -> str:
        """Format text as URL."""
        return f"{Colors.URL}🔗 {text}{Style.RESET_ALL}"

    @staticmethod
    def command(text: str) -> str:
        """Format text as command."""
        return f"{Colors.COMMAND}{text}{Style.RESET_ALL}"

    @staticmethod
    def bold(text: str) -> str:
        """Format text as bold."""
        return f"{Colors.BOLD}{text}{Style.RESET_ALL}"

    @staticmethod
    def section_divider(title: str) -> str:
        """Create a section divider with title."""
        divider = "─" * 60
        return f"{Colors.HEADER}{divider}\n{title}\n{divider}{Style.RESET_ALL}"


def confirm_creation() -> bool:
    """Ask user for confirmation to create the Jira ticket."""
    while True:
        try:
            response = input(f"\n{Colors.INFO}Create this Jira ticket? (y/n): {Style.RESET_ALL}").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print(Colors.warning("Please enter 'y' for yes or 'n' for no"))
        except KeyboardInterrupt:
            print(f"\n{Colors.warning('Operation cancelled by user')}")
            return False
        except EOFError:
            print(f"\n{Colors.warning('Operation cancelled')}")
            return False


class Config:
    """Configuration manager for API credentials and settings."""

    def __init__(self, config_file: str = "~/.gitlab-jira-cli.json"):
        self.config_file = os.path.expanduser(config_file)
        self.config = self.load_config()

    def load_config(self) -> Dict:
        """Load configuration from file or environment variables."""
        config = {}

        # Try to load from config file
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(Colors.warning(f"Could not load config file: {e}"))

        # Override with environment variables if present
        env_config = {
            'gitlab': {
                'url': os.getenv('GITLAB_URL'),
                'token': os.getenv('GITLAB_TOKEN')
            },
            'jira': {
                'url': os.getenv('JIRA_URL'),
                'username': os.getenv('JIRA_USERNAME'),
                'api_token': os.getenv('JIRA_API_TOKEN'),
                'project_key': os.getenv('JIRA_PROJECT_KEY')
            },
            'defaults': {
                'issue_type': os.getenv('JIRA_ISSUE_TYPE'),
                'priority': os.getenv('JIRA_PRIORITY'),
                'auto_assign_me': os.getenv('AUTO_ASSIGN_ME', '').lower() in ['true', '1', 'yes', 'on'] if os.getenv('AUTO_ASSIGN_ME') else None
            }
        }

        # Merge configurations
        for section, values in env_config.items():
            if section not in config:
                config[section] = {}
            for key, value in values.items():
                if value is not None:
                    config[section][key] = value

        return config

    def save_config(self):
        """Save current configuration to file."""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(Colors.success(f"Configuration saved to {self.config_file}"))
        except IOError as e:
            print(Colors.error(f"Error saving configuration: {e}"))

    def setup_interactive(self):
        """Interactive setup for configuration."""
        print(Colors.header("Setting up GitLab to Jira CLI configuration..."))

        # GitLab configuration
        print(Colors.section_divider("GitLab Configuration"))
        gitlab_url = input(f"{Colors.INFO}GitLab URL (e.g., https://gitlab.com): {Style.RESET_ALL}").strip()
        gitlab_token = input(f"{Colors.INFO}GitLab Personal Access Token: {Style.RESET_ALL}").strip()

        # Jira configuration
        print(Colors.section_divider("Jira Configuration"))
        jira_url = input(f"{Colors.INFO}Jira URL (e.g., https://yourcompany.atlassian.net): {Style.RESET_ALL}").strip()
        jira_username = input(f"{Colors.INFO}Jira Username/Email: {Style.RESET_ALL}").strip()
        jira_token = input(f"{Colors.INFO}Jira API Token: {Style.RESET_ALL}").strip()
        jira_project = input(f"{Colors.INFO}Default Jira Project Key: {Style.RESET_ALL}").strip()

        # Default settings
        print(Colors.section_divider("Default Settings"))
        default_issue_type = input(f"{Colors.INFO}Default Issue Type (default: Task): {Style.RESET_ALL}").strip() or "Task"
        default_labels = input(f"{Colors.INFO}Default Labels (comma-separated, optional): {Style.RESET_ALL}").strip()
        default_components = input(f"{Colors.INFO}Default Components (comma-separated, optional): {Style.RESET_ALL}").strip()
        default_priority = input(f"{Colors.INFO}Default Priority (optional): {Style.RESET_ALL}").strip()
        auto_assign_me = input(f"{Colors.INFO}Auto-assign tickets to yourself? (y/n, default: n): {Style.RESET_ALL}").strip().lower() in ['y', 'yes']

        self.config = {
            'gitlab': {
                'url': gitlab_url,
                'token': gitlab_token
            },
            'jira': {
                'url': jira_url,
                'username': jira_username,
                'api_token': jira_token,
                'project_key': jira_project
            },
            'defaults': {
                'issue_type': default_issue_type,
                'labels': [l.strip() for l in default_labels.split(',') if l.strip()] if default_labels else [],
                'components': [c.strip() for c in default_components.split(',') if c.strip()] if default_components else [],
                'priority': default_priority if default_priority else None,
                'auto_assign_me': auto_assign_me
            },
            'project_mappings': {}
        }

        # Ask about project mappings
        print(Colors.section_divider("Project Mappings (Optional)"))
        print(Colors.info("You can map GitLab projects to specific Jira projects."))
        print(Colors.info("This allows different GitLab projects to create tickets in different Jira projects."))

        while True:
            add_mapping = input(f"\n{Colors.INFO}Add a project mapping? (y/n): {Style.RESET_ALL}").strip().lower()
            if add_mapping != 'y':
                break

            gitlab_project = input(f"{Colors.INFO}GitLab project path (e.g., 'namespace/project'): {Style.RESET_ALL}").strip()
            jira_project_key = input(f"{Colors.INFO}Jira project key for '{gitlab_project}': {Style.RESET_ALL}").strip()

            if gitlab_project and jira_project_key:
                self.config['project_mappings'][gitlab_project] = {
                    'jira_project_key': jira_project_key
                }
                print(Colors.success(f"Added mapping: {gitlab_project} → {jira_project_key}"))

        self.save_config()

    def get_jira_project_for_gitlab_project(self, gitlab_project_path: str) -> str:
        """Get the appropriate Jira project key for a GitLab project."""
        # Check project mappings first
        if 'project_mappings' in self.config and gitlab_project_path in self.config['project_mappings']:
            return self.config['project_mappings'][gitlab_project_path]['jira_project_key']

        # Fall back to default
        return self.config.get('jira', {}).get('project_key', '')

    def get_default_settings(self) -> Dict:
        """Get default settings from config."""
        return self.config.get('defaults', {
            'issue_type': 'Task',
            'labels': [],
            'components': [],
            'priority': None,
            'auto_assign_me': False
        })


class GitLabAPI:
    """GitLab API client."""

    def __init__(self, url: str, token: str):
        self.url = url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        })

    def get_merge_request(self, project_id: str, mr_iid: str) -> Optional[Dict]:
        """Get merge request details."""
        endpoint = f"/api/v4/projects/{project_id}/merge_requests/{mr_iid}"
        url = urljoin(self.url, endpoint)

        try:
            response = self.session.get(url)
            if is_valid_response(response):
                return response.json()
            else:
                print(Colors.error(f"Error fetching GitLab MR: Invalid response (status: {response.status_code})"))
                return None
        except requests.RequestException as e:
            print(Colors.error(f"Error fetching GitLab MR: {e}"))
            return None

    def get_project_details(self, project_id: str) -> Optional[Dict]:
        """Get project details including numeric project ID."""
        endpoint = f"/api/v4/projects/{project_id}"
        url = urljoin(self.url, endpoint)

        try:
            response = self.session.get(url)
            if is_valid_response(response):
                return response.json()
            else:
                print(Colors.error(f"Error fetching GitLab project details: Invalid response (status: {response.status_code})"))
                return None
        except requests.RequestException as e:
            print(Colors.error(f"Error fetching GitLab project details: {e}"))
            return None

    def update_merge_request_title(self, project_id: str, mr_iid: str, new_title: str) -> bool:
        """Update merge request title."""
        endpoint = f"/api/v4/projects/{project_id}/merge_requests/{mr_iid}"
        url = urljoin(self.url, endpoint)

        payload = {"title": new_title}

        try:
            response = self.session.put(url, json=payload)
            if is_valid_response(response):
                return True
            else:
                print(Colors.error(f"Error updating GitLab MR title: Invalid response (status: {response.status_code})"))
                if response.text:
                    print(f"Response: {response.text}")
                return False
        except requests.RequestException as e:
            print(Colors.error(f"Error updating GitLab MR title: {e}"))
            if hasattr(e, 'response') and e.response is not None and hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return False

def is_valid_response(response: Optional[requests.Response]) -> TypeGuard[requests.Response]:
    """Check if the response is valid (status code 200-299) and not empty."""
    return response is not None and response.status_code >= 200 and response.status_code < 300 and response.text.strip() != ""

class JiraAPI:
    """Jira API client."""

    def __init__(self, url: str, username: str, api_token: str):
        self.url = url.rstrip('/')
        self.session = requests.Session()
        self.session.auth = (username, api_token)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def create_ticket(self, project_key: str, issue_type: str, summary: str,
                     description_content: Dict, labels: Optional[List[str]] = None,
                     components: Optional[List[str]] = None, priority: Optional[str] = None,
                     assignee: Optional[str] = None) -> Optional[Dict]:
        """Create a Jira ticket with structured content."""
        endpoint = "/rest/api/3/issue"
        url = urljoin(self.url, endpoint)

        # Build the issue payload
        fields = {
            "project": {"key": project_key},
            "summary": summary,
            "description": description_content,
            "issuetype": {"name": issue_type}
        }

        # Add optional fields
        if labels:
            fields["labels"] = labels

        if components:
            fields["components"] = [{"name": comp} for comp in components]

        if priority:
            fields["priority"] = {"name": priority}

        if assignee:
            fields["assignee"] = {"name": assignee}

        payload = {"fields": fields}

        try:
            response = self.session.post(url, json=payload)
            if is_valid_response(response):
                return response.json()
            else:
                print(Colors.error(f"Error creating Jira ticket: Invalid response (status: {response.status_code})"))
                if response.text:
                    print(f"Response: {response.text}")
                return None
        except requests.RequestException as e:
            print(Colors.error(f"Error creating Jira ticket: {e}"))
            if hasattr(e, 'response') and e.response is not None and hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None

    def transition_ticket(self, ticket_key: str, transition_name: str) -> bool:
        """Transition a Jira ticket to a specific status."""
        # First get available transitions
        transitions_endpoint = f"/rest/api/3/issue/{ticket_key}/transitions"
        transitions_url = urljoin(self.url, transitions_endpoint)

        try:
            response = self.session.get(transitions_url)
            if not is_valid_response(response):
                print(Colors.error(f"Error fetching transitions: Invalid response (status: {response.status_code})"))
                return False

            transitions = response.json().get('transitions', [])

            # Find the transition ID for "In Progress"
            transition_id = None
            for transition in transitions:
                if transition['name'].lower() == transition_name.lower():
                    transition_id = transition['id']
                    break

            if not transition_id:
                print(Colors.warning(f"Could not find '{transition_name}' transition for ticket {ticket_key}"))
                return False

            # Execute the transition
            transition_endpoint = f"/rest/api/3/issue/{ticket_key}/transitions"
            transition_url = urljoin(self.url, transition_endpoint)

            payload = {
                "transition": {
                    "id": transition_id
                }
            }

            response = self.session.post(transition_url, json=payload)
            if is_valid_response(response):
                return True
            else:
                print(Colors.error(f"Error executing transition: Invalid response (status: {response.status_code})"))
                if response.text:
                    print(f"Response: {response.text}")
                return False

        except requests.RequestException as e:
            print(Colors.error(f"Error transitioning Jira ticket: {e}"))
            if hasattr(e, 'response') and e.response is not None and hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return False

    def get_project_components(self, project_key: str) -> Optional[List[Dict]]:
        """Get available components for a Jira project."""
        endpoint = f"/rest/api/3/project/{project_key}/components"
        url = urljoin(self.url, endpoint)

        try:
            response = self.session.get(url)
            if is_valid_response(response):
                return response.json()
            else:
                print(Colors.error(f"Error fetching Jira project components: Invalid response (status: {response.status_code})"))
                if response.text:
                    print(f"Response: {response.text}")
                return None
        except requests.RequestException as e:
            print(Colors.error(f"Error fetching Jira project components: {e}"))
            if is_valid_response(e.response):
                print(f"Response: {e.response.text}")
            return None


def create_jira_document(mr_url: str, mr_data: Dict, processed_description: Optional[str] = None) -> Dict:
    """Create a structured Jira document with proper formatting."""

    # Parse the processed description using markdown converter
    original_description = processed_description or "No description provided"

    content = []

    # Header with link to MR
    content.append({
        "type": "paragraph",
        "content": [
            {
                "type": "text",
                "text": "Created from "
            },
            {
                "type": "text",
                "text": "GitLab Merge Request",
                "marks": [
                    {
                        "type": "link",
                        "attrs": {
                            "href": mr_url
                        }
                    }
                ]
            },
            {
                "type": "text",
                "text": ":"
            }
        ]
    })

    # Add a divider
    content.append({"type": "rule"})

    # Convert and add markdown content
    if original_description.strip() != "No description provided":
        markdown_content = convert_markdown_to_jira(original_description)
        content.extend(markdown_content)

        # Add another divider before MR details if we have content
        if markdown_content:
            content.append({"type": "rule"})

    # MR Details panel
    mr_details_content = []

    # Panel heading
    mr_details_content.append({
        "type": "heading",
        "attrs": {"level": 3},
        "content": [
            {
                "type": "text",
                "text": "MR Details"
            }
        ]
    })

    # Panel content with MR details
    detail_content = []

    # Author
    detail_content.extend([
        {
            "type": "text",
            "text": "Author: "
        },
        {
            "type": "text",
            "text": mr_data['author']['name'],
            "marks": [{"type": "strong"}]
        },
        {"type": "hardBreak"}
    ])

    # Source branch
    detail_content.extend([
        {
            "type": "text",
            "text": "Source Branch: "
        },
        {
            "type": "text",
            "text": mr_data['source_branch'],
            "marks": [{"type": "code"}]
        },
        {"type": "hardBreak"}
    ])

    # Target branch
    detail_content.extend([
        {
            "type": "text",
            "text": "Target Branch: "
        },
        {
            "type": "text",
            "text": mr_data['target_branch'],
            "marks": [{"type": "code"}]
        },
        {"type": "hardBreak"}
    ])

    # State
    detail_content.extend([
        {
            "type": "text",
            "text": "State: "
        },
        {
            "type": "text",
            "text": mr_data['state'],
            "marks": [{"type": "strong"}]
        },
        {"type": "hardBreak"}
    ])

    # Created date
    detail_content.extend([
        {
            "type": "text",
            "text": "Created: "
        },
        {
            "type": "text",
            "text": mr_data['created_at'],
            "marks": [{"type": "strong"}]
        }
    ])

    mr_details_content.append({
        "type": "paragraph",
        "content": detail_content
    })

    # Add the panel
    content.append({
        "type": "panel",
        "attrs": {"panelType": "info"},
        "content": mr_details_content
    })

    return {
        "type": "doc",
        "version": 1,
        "content": content
    }


def convert_markdown_to_jira(markdown_text: str) -> List[Dict]:
    """Convert markdown text to Jira document format."""
    if not markdown_text or markdown_text.strip() == "No description provided":
        return []

    lines = markdown_text.split('\n')
    content = []
    current_list_items = []

    def flush_list():
        """Flush any pending list items."""
        nonlocal current_list_items
        if current_list_items:
            content.append({
                "type": "bulletList",
                "content": [
                    {
                        "type": "listItem",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": item_content
                            }
                        ]
                    }
                    for item_content in current_list_items
                ]
            })
            current_list_items = []

    def parse_inline_formatting(text: str) -> List[Dict]:
        """Parse inline formatting like bold, italic, links, and code."""
        result = []
        pos = 0

        while pos < len(text):
            # Find the next markdown element
            patterns = [
                (r'\*\*(.*?)\*\*', 'strong'),     # **bold**
                (r'\*(.*?)\*', 'em'),             # *italic*
                (r'`(.*?)`', 'code'),             # `code`
                (r'\[(.*?)\]\((.*?)\)', 'link'),  # [text](url)
            ]

            earliest_match = None
            earliest_pos = len(text)

            for pattern, mark_type in patterns:
                match = re.search(pattern, text[pos:])
                if match and match.start() + pos < earliest_pos:
                    earliest_pos = match.start() + pos
                    earliest_match = (match, mark_type, pos)

            if earliest_match:
                match, mark_type, offset = earliest_match
                actual_pos = earliest_pos

                # Add text before the match
                if actual_pos > pos:
                    plain_text = text[pos:actual_pos]
                    if plain_text:
                        result.append({
                            "type": "text",
                            "text": plain_text
                        })

                # Add the formatted text
                if mark_type == 'link':
                    # Special handling for links
                    link_text = match.group(1)
                    link_url = match.group(2)
                    result.append({
                        "type": "text",
                        "text": link_text,
                        "marks": [
                            {
                                "type": "link",
                                "attrs": {
                                    "href": link_url
                                }
                            }
                        ]
                    })
                else:
                    # Regular formatting marks
                    inner_text = match.group(1)
                    result.append({
                        "type": "text",
                        "text": inner_text,
                        "marks": [{"type": mark_type}]
                    })

                pos = actual_pos + len(match.group(0))
            else:
                # No more matches, add remaining text
                remaining_text = text[pos:]
                if remaining_text:
                    result.append({
                        "type": "text",
                        "text": remaining_text
                    })
                break

        return result if result else [{"type": "text", "text": text}]

    for line in lines:
        line = line.rstrip()

        # Empty line - flush any pending list and add paragraph break if needed
        if not line:
            flush_list()
            # Don't add empty paragraphs, just continue
            continue

        # Headings
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if heading_match:
            flush_list()
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2)
            content.append({
                "type": "heading",
                "attrs": {"level": min(level, 6)},  # Jira supports levels 1-6
                "content": parse_inline_formatting(heading_text)
            })
            continue

        # Lists (bullet points)
        list_match = re.match(r'^[\s]*[-*+]\s+(.+)$', line)
        if list_match:
            item_text = list_match.group(1)
            current_list_items.append(parse_inline_formatting(item_text))
            continue

        # Regular paragraph
        flush_list()
        if line.strip():
            content.append({
                "type": "paragraph",
                "content": parse_inline_formatting(line)
            })

    # Flush any remaining list items
    flush_list()

    return content


def process_gitlab_description(description: str, gitlab_url: str, numeric_project_id: int, image_handling: str) -> str:
    """Process GitLab description to handle images and formatting for Jira."""
    if not description:
        return description

    # Convert relative image URLs to absolute GitLab URLs
    # Pattern: ![alt text](/uploads/hash/filename.ext){optional attributes}
    image_pattern = r'!\[([^\]]*)\]\((/uploads/[^)]+)\)(\{[^}]*\})?'

    def replace_image(match):
        alt_text = match.group(1) or "image"
        relative_path = match.group(2)
        # Note: attributes (match.group(3)) like {width=60%} are captured but not used
        # since they don't translate well to Jira format

        # Convert to absolute URL using GitLab's project ID format for images
        # GitLab stores images under: https://gitlab.com/-/project/{numeric_project_id}/uploads/{hash}/{filename}
        absolute_url = f"{gitlab_url.rstrip('/')}/-/project/{numeric_project_id}{relative_path}"

        if image_handling == "strip":
            return f"[Image: {alt_text} - see original MR]"
        elif image_handling == "jira-syntax":
            # Jira's image syntax (may not work for external URLs depending on Jira config)
            return f"!{absolute_url}!"
        else:  # "links"
            # Convert to a link with emoji indicator
            return f"🖼️ **{alt_text}**: {absolute_url}"

    # Replace images
    processed_description = re.sub(image_pattern, replace_image, description)

    return processed_description


def interactive_component_selection(jira: 'JiraAPI', project_key: str, default_components: Optional[List[str]] = None) -> List[str]:
    """Interactive component selection for Jira ticket creation."""
    print(f"\n{Colors.info(f'Fetching available components for project {project_key}...')}")

    # Get available components
    components_data = jira.get_project_components(project_key)
    if not components_data:
        print(Colors.error("Could not fetch project components. Using defaults if any."))
        return default_components or []

    if not components_data:
        print(Colors.info("No components available in this project."))
        return []

    print(Colors.section_divider(f"Component Selection for {project_key}"))
    print(Colors.bold("Available components:"))

    # Display available components in a compact format
    for i, component in enumerate(components_data, 1):
        print(f"  {Colors.command(f'{i:2d}.')} {component['name']}")

    # Show current defaults
    if default_components:
        defaults_str = ', '.join(default_components)
        print(f"\n{Colors.info(f'Default components from config: {defaults_str}')}")

    selection_msg = 'Select components by entering numbers separated by spaces (e.g., "1 3 5")'
    print(f"\n{Colors.info(selection_msg)}")
    print(Colors.info('Press Enter with no input to use defaults, or "none" for no components'))

    while True:
        try:
            selection = input("Your selection: ").strip()

            if not selection:
                # Use defaults
                selected_components = default_components or []
                break
            elif selection.lower() == 'none':
                # No components
                selected_components = []
                break
            else:
                # Parse selection
                indices = [int(x.strip()) for x in selection.split()]
                selected_components = []

                for index in indices:
                    if 1 <= index <= len(components_data):
                        component_name = components_data[index - 1]['name']
                        selected_components.append(component_name)
                    else:
                        invalid_msg = f"Invalid selection: {index}. Please select numbers between 1 and {len(components_data)}"
                        print(Colors.error(invalid_msg))
                        raise ValueError("Invalid selection")

                break

        except (ValueError, IndexError):
            print(Colors.error("Invalid input. Please enter numbers separated by spaces, 'none', or press Enter for defaults."))
            continue

    if selected_components:
        components_str = ', '.join(selected_components)
        print(Colors.success(f"Selected components: {components_str}"))
    else:
        print(Colors.info("No components selected"))

    return selected_components


def validate_components(jira: 'JiraAPI', project_key: str, provided_components: List[str]) -> Optional[List[str]]:
    """Validate provided component names against actual Jira project components."""
    if not provided_components:
        return []

    print(Colors.info(f"Validating components for project {project_key}..."))

    # Get available components
    components_data = jira.get_project_components(project_key)
    if not components_data:
        print(Colors.error("Could not fetch project components for validation."))
        return provided_components  # Return as-is if we can't validate

    # Create a mapping of component names (case-insensitive) to actual names
    available_components = {comp['name'].lower(): comp['name'] for comp in components_data}

    validated_components = []
    invalid_components = []

    for component in provided_components:
        component_lower = component.lower()
        if component_lower in available_components:
            # Use the correct case from Jira
            validated_components.append(available_components[component_lower])
        else:
            invalid_components.append(component)

    if invalid_components:
        invalid_str = ', '.join(invalid_components)
        print(Colors.error(f"Invalid components found: {invalid_str}"))
        print(Colors.bold("Available components:"))
        for comp in components_data:
            print(f"  - {comp['name']}")

        # Ask user what to do
        print(f"\n{Colors.header('Choose an option:')}")
        print(f"{Colors.command('1.')} Continue with only valid components")
        print(f"{Colors.command('2.')} Use interactive component selection instead")
        print(f"{Colors.command('3.')} Exit and fix component names")

        while True:
            choice = input(f"{Colors.INFO}Your choice (1-3): {Style.RESET_ALL}").strip()
            if choice == "1":
                valid_str = ', '.join(validated_components)
                print(Colors.info(f"Continuing with valid components: {valid_str}"))
                return validated_components
            elif choice == "2":
                print(Colors.info("Switching to interactive component selection..."))
                return None  # Signal to use interactive selection
            elif choice == "3":
                print(Colors.info("Exiting. Please fix component names and try again."))
                sys.exit(1)
            else:
                print(Colors.error("Invalid choice. Please enter 1, 2, or 3."))

    if validated_components:
        valid_str = ', '.join(validated_components)
        print(Colors.success(f"All components validated: {valid_str}"))

    return validated_components


def parse_mr_url(mr_url: str) -> Optional[tuple]:
    """Parse GitLab MR URL to extract project ID and MR IID."""
    # Expected format: https://gitlab.com/namespace/project/-/merge_requests/123
    try:
        parts = mr_url.rstrip('/').split('/')
        mr_iid = parts[-1]

        # Find the project path (everything between domain and /-/merge_requests)
        mr_index = None
        for i, part in enumerate(parts):
            if part == '-' and i + 1 < len(parts) and parts[i + 1] == 'merge_requests':
                mr_index = i
                break

        if mr_index is None:
            return None

        # Get project path and encode it
        project_path = '/'.join(parts[3:mr_index])  # Skip https, empty, domain
        from urllib.parse import quote
        project_id = quote(project_path, safe='')

        return project_id, mr_iid, project_path
    except (IndexError, ValueError):
        return None


def main():
    parser = argparse.ArgumentParser(description="Create Jira tickets from GitLab merge requests")
    parser.add_argument("mr_url", nargs='?', help="GitLab merge request URL")
    parser.add_argument("--setup", action="store_true", help="Setup configuration interactively")
    parser.add_argument("--project", help="Jira project key (overrides config)")
    parser.add_argument("--issue-type", help="Jira issue type (default: from config or Task)")
    parser.add_argument("--labels", nargs="*", help="Jira labels to add")
    parser.add_argument("--components", nargs="*", help="Jira components to add (skips interactive selection if provided)")
    parser.add_argument("--priority", help="Jira priority (e.g., High, Medium, Low)")
    parser.add_argument("--image-handling", choices=["links", "jira-syntax", "strip"], default="jira-syntax",
                       help="How to handle images: 'links' (convert to links), 'jira-syntax' (use !url!), 'strip' (remove images)")
    parser.add_argument("--set-in-progress", action="store_true", help="Set Jira ticket to 'In Progress' status")
    parser.add_argument("--update-mr-title", action="store_true", help="Update MR title with Jira ticket key")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation and create ticket immediately")
    parser.add_argument("--no-preview", action="store_true", help="Skip preview and create ticket immediately (same as --yes)")

    args = parser.parse_args()

    # Load configuration
    config = Config()

    # Handle setup
    if args.setup:
        config.setup_interactive()
        return

    # Validate we have an MR URL
    if not args.mr_url:
        print(Colors.error("Please provide a GitLab merge request URL"))
        parser.print_help()
        sys.exit(1)

    # Validate configuration
    required_config = ['gitlab.url', 'gitlab.token', 'jira.url', 'jira.username', 'jira.api_token']
    for key in required_config:
        section, field = key.split('.')
        if section not in config.config or field not in config.config[section]:
            print(Colors.error(f"Missing configuration for {key}"))
            print(Colors.info("Run with --setup to configure, or set environment variables"))
            sys.exit(1)

    # Parse MR URL
    parsed = parse_mr_url(args.mr_url)
    if not parsed:
        print(Colors.error("Invalid GitLab merge request URL format"))
        sys.exit(1)

    project_id, mr_iid, project_path = parsed

    # Initialize API clients
    gitlab = GitLabAPI(config.config['gitlab']['url'], config.config['gitlab']['token'])
    jira = JiraAPI(config.config['jira']['url'],
                   config.config['jira']['username'],
                   config.config['jira']['api_token'])

    # Get MR details
    print(Colors.info(f"Fetching merge request details for {project_path}..."))
    mr_data = gitlab.get_merge_request(project_id, mr_iid)
    if not mr_data:
        print(Colors.error("Could not fetch merge request details"))
        sys.exit(1)

    # Get project details to get the numeric project ID needed for image URLs
    print(Colors.info("Fetching project details..."))
    project_data = gitlab.get_project_details(project_id)
    if not project_data:
        print(Colors.error("Could not fetch project details"))
        sys.exit(1)

    numeric_project_id = project_data['id']

    # Determine Jira project (command line arg > project mapping > default config)
    project_key = (args.project or
                   config.get_jira_project_for_gitlab_project(project_path) or
                   config.config.get('jira', {}).get('project_key'))

    if not project_key:
        print(Colors.error("No Jira project key found. Use --project, configure project mappings, or set default"))
        sys.exit(1)

    # Get default settings from config
    defaults = config.get_default_settings()

    # Prepare Jira ticket data with defaults
    issue_type = args.issue_type or defaults.get('issue_type', 'Task')
    priority = args.priority or defaults.get('priority')

    # Determine assignee based on auto_assign_me setting
    assignee = None
    if defaults.get('auto_assign_me', False):
        assignee = config.config.get('jira', {}).get('username')

    # Combine labels: defaults + command line args + auto-generated
    labels = defaults.get('labels', []).copy()
    if args.labels:
        labels.extend(args.labels)
    # labels.extend(['gitlab-mr', f"project-{mr_data['source_project_id']}"])

    # Handle components: validate provided components or use interactive selection
    components = defaults.get('components', []).copy()

    if args.components:
        # Validate provided components
        validated_components = validate_components(jira, project_key, args.components)
        if validated_components is None:
            # User chose to use interactive selection instead
            components = interactive_component_selection(jira, project_key, components)
        else:
            # Add validated components to defaults
            components.extend(validated_components)
    else:
        # No components provided via CLI, use interactive selection
        components = interactive_component_selection(jira, project_key, components)

    summary = mr_data['title']

    if not summary:
        print(Colors.error("Merge request has no title. Cannot create Jira ticket."))
        sys.exit(1)

    # Process the description to handle images and relative links
    processed_description = process_gitlab_description(
        mr_data.get('description', ''),
        config.config['gitlab']['url'],
        numeric_project_id,
        args.image_handling
    )

    # Create structured Jira document
    description_content = create_jira_document(args.mr_url, mr_data, processed_description)

    # Always show preview unless --yes or --no-preview is used
    skip_preview = args.yes or args.no_preview

    if not skip_preview:
        print(Colors.section_divider("PREVIEW: Jira ticket to be created"))
        print(f"{Colors.bold('Project:')} {Colors.command(project_key)}")
        print(f"{Colors.bold('Issue Type:')} {Colors.command(issue_type)}")
        print(f"{Colors.bold('Summary:')} {summary}")
        print(f"{Colors.bold('Description Preview:')} {processed_description[:200]}{'...' if len(processed_description) > 200 else ''}")
        print(f"{Colors.bold('Labels:')} {Colors.command(str(labels))}")
        if components:
            components_str = ', '.join(components)
            print(f"{Colors.bold('Components:')} {Colors.command(components_str)}")
        if priority:
            print(f"{Colors.bold('Priority:')} {Colors.command(priority)}")
        if assignee:
            print(f"{Colors.bold('Assignee:')} {Colors.command(assignee)}")
        print(f"{Colors.bold('GitLab Project:')} {Colors.command(project_path)}")
        if args.set_in_progress:
            print(Colors.info("Will set ticket to 'In Progress' status"))
        if args.update_mr_title:
            print(Colors.info("Will update MR title to include Jira ticket key"))

        # Ask for confirmation
        if not confirm_creation():
            print(Colors.warning("Ticket creation cancelled by user"))
            return

    # Create Jira ticket
    print(Colors.info(f"Creating Jira ticket in project {project_key}..."))
    result = jira.create_ticket(
        project_key=project_key,
        issue_type=issue_type,
        summary=summary,
        description_content=description_content,
        labels=labels,
        components=components if components else None,
        priority=priority,
        assignee=assignee
    )

    if result:
        ticket_key = result['key']
        ticket_url = f"{config.config['jira']['url']}/browse/{ticket_key}"
        print(Colors.success(f"Successfully created Jira ticket: {ticket_key}"))
        print(Colors.url(ticket_url))

        # Set ticket to In Progress if requested
        if args.set_in_progress:
            print(Colors.info(f"Setting ticket {ticket_key} to 'In Progress'..."))
            if jira.transition_ticket(ticket_key, "In Progress"):
                print(Colors.success(f"Successfully set {ticket_key} to 'In Progress'"))
            else:
                print(Colors.error(f"Failed to set {ticket_key} to 'In Progress'"))

        # Update MR title if requested
        if args.update_mr_title:
            original_title = mr_data['title']
            # Check if title already has a Jira ticket key
            if not original_title.startswith('[') or ']' not in original_title:
                new_title = f"[{ticket_key}] {original_title}"
                print(Colors.info(f"Updating MR title to: {new_title}"))
                if gitlab.update_merge_request_title(project_id, mr_iid, new_title):
                    print(Colors.success("Successfully updated MR title"))
                else:
                    print(Colors.error("Failed to update MR title"))
            else:
                print(Colors.warning("MR title already appears to have a ticket key, skipping update"))
    else:
        print(Colors.error("Failed to create Jira ticket"))
        sys.exit(1)


if __name__ == "__main__":
    main()
