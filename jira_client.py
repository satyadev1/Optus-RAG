#!/usr/bin/env python3
"""
Jira Client - Retrieve user details and tickets
"""

import os
import json
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class JiraClient:
    def __init__(self):
        self.jira_url = os.getenv("JIRA_URL")
        self.jira_email = os.getenv("JIRA_EMAIL")
        self.jira_token = os.getenv("JIRA_API_TOKEN")

        if not all([self.jira_url, self.jira_email, self.jira_token]):
            raise ValueError("Missing Jira credentials in .env file")

        self.auth = HTTPBasicAuth(self.jira_email, self.jira_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def get_current_user(self):
        """Get current user details"""
        url = f"{self.jira_url}/rest/api/3/myself"

        try:
            response = requests.get(url, auth=self.auth, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching user details: {e}")
            return None

    def get_user_issues(self, max_results=50):
        """Get issues assigned to or reported by current user with ALL details"""
        # Search for issues assigned to current user
        jql = f'assignee = currentUser() OR reporter = currentUser() ORDER BY updated DESC'

        url = f"{self.jira_url}/rest/api/3/search/jql"
        data = {
            'jql': jql,
            'maxResults': max_results,
            'fields': '*all',  # Get all available fields
            'expand': 'changelog,renderedFields,names,schema,transitions,operations'
        }

        try:
            response = requests.post(url, json=data, auth=self.auth, headers=self.headers)
            response.raise_for_status()
            result = response.json()

            # Fetch additional details for each issue
            for issue in result.get('issues', []):
                key = issue.get('key')

                # Fetch comments
                try:
                    comments_url = f"{self.jira_url}/rest/api/3/issue/{key}/comment"
                    comments_response = requests.get(comments_url, auth=self.auth, headers=self.headers)
                    if comments_response.status_code == 200:
                        issue['all_comments'] = comments_response.json()
                except:
                    pass

                # Fetch watchers
                try:
                    watchers_url = f"{self.jira_url}/rest/api/3/issue/{key}/watchers"
                    watchers_response = requests.get(watchers_url, auth=self.auth, headers=self.headers)
                    if watchers_response.status_code == 200:
                        issue['all_watchers'] = watchers_response.json()
                except:
                    pass

            return result
        except requests.exceptions.RequestException as e:
            print(f"Error fetching issues: {e}")
            try:
                print(f"Response: {response.text[:300]}")
            except:
                pass
            return None

    def get_worked_on_issues(self, max_results=50):
        """Get issues where user has logged work or added comments with ALL details"""
        jql = f'worklogAuthor = currentUser() OR commentedBy = currentUser() ORDER BY updated DESC'

        url = f"{self.jira_url}/rest/api/3/search/jql"
        data = {
            'jql': jql,
            'maxResults': max_results,
            'fields': '*all',  # Get all available fields
            'expand': 'changelog,renderedFields,names,schema,transitions,operations'
        }

        try:
            response = requests.post(url, json=data, auth=self.auth, headers=self.headers)
            response.raise_for_status()
            result = response.json()

            # Fetch additional details for each issue
            for issue in result.get('issues', []):
                key = issue.get('key')

                # Fetch comments
                try:
                    comments_url = f"{self.jira_url}/rest/api/3/issue/{key}/comment"
                    comments_response = requests.get(comments_url, auth=self.auth, headers=self.headers)
                    if comments_response.status_code == 200:
                        issue['all_comments'] = comments_response.json()
                except:
                    pass

                # Fetch watchers
                try:
                    watchers_url = f"{self.jira_url}/rest/api/3/issue/{key}/watchers"
                    watchers_response = requests.get(watchers_url, auth=self.auth, headers=self.headers)
                    if watchers_response.status_code == 200:
                        issue['all_watchers'] = watchers_response.json()
                except:
                    pass

            return result
        except requests.exceptions.RequestException as e:
            print(f"Error fetching worked issues: {e}")
            try:
                print(f"Response: {response.text[:300]}")
            except:
                pass
            return None

    def display_user_info(self, user_data):
        """Display user information"""
        if not user_data:
            print("No user data available")
            return

        print("\n" + "="*70)
        print("CURRENT USER DETAILS")
        print("="*70)
        print(f"Account ID: {user_data.get('accountId', 'N/A')}")
        print(f"Email: {user_data.get('emailAddress', 'N/A')}")
        print(f"Display Name: {user_data.get('displayName', 'N/A')}")
        print(f"Active: {user_data.get('active', 'N/A')}")
        print(f"Account Type: {user_data.get('accountType', 'N/A')}")
        print(f"Timezone: {user_data.get('timeZone', 'N/A')}")
        print(f"Locale: {user_data.get('locale', 'N/A')}")
        print("="*70)

    def display_issues(self, issues_data, title="ISSUES"):
        """Display issues in a formatted table with detailed information"""
        if not issues_data or 'issues' not in issues_data:
            print(f"\nNo {title.lower()} found")
            return

        issues = issues_data['issues']
        total = issues_data.get('total', len(issues))

        print(f"\n{'='*70}")
        print(f"{title} (Showing {len(issues)} of {total})")
        print("="*70)

        for i, issue in enumerate(issues, 1):
            key = issue.get('key', 'N/A')
            fields = issue.get('fields', {})
            changelog = issue.get('changelog', {})

            summary = fields.get('summary', 'N/A')
            status = fields.get('status', {}).get('name', 'N/A')
            status_category = fields.get('status', {}).get('statusCategory', {}).get('name', 'N/A')
            priority = fields.get('priority', {}).get('name', 'N/A')
            issue_type = fields.get('issuetype', {}).get('name', 'N/A')
            project = fields.get('project', {}).get('key', 'N/A')

            assignee = fields.get('assignee')
            assignee_name = assignee.get('displayName', 'Unassigned') if assignee else 'Unassigned'

            reporter = fields.get('reporter')
            reporter_name = reporter.get('displayName', 'Unknown') if reporter else 'Unknown'

            created = fields.get('created', '')
            updated = fields.get('updated', '')

            # Count additional details
            comments_count = len(issue.get('all_comments', {}).get('comments', []))
            watchers_count = len(issue.get('all_watchers', {}).get('watchers', []))
            history_count = len(changelog.get('histories', []))
            attachments_count = len(fields.get('attachment', []))
            labels = fields.get('labels', [])
            components = [c.get('name') for c in fields.get('components', [])]

            # Parse and format dates
            try:
                created_date = datetime.fromisoformat(created.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                updated_date = datetime.fromisoformat(updated.replace('Z', '+00:00')).strftime('%Y-%m-%d')
            except:
                created_date = 'N/A'
                updated_date = 'N/A'

            print(f"\n{i}. [{key}] {summary}")
            print(f"   Project: {project} | Type: {issue_type} | Priority: {priority}")
            print(f"   Status: {status} ({status_category}) | Assignee: {assignee_name}")
            print(f"   Reporter: {reporter_name}")
            print(f"   Created: {created_date} | Updated: {updated_date}")

            # Display additional metadata
            if labels:
                print(f"   Labels: {', '.join(labels[:5])}")
            if components:
                print(f"   Components: {', '.join(components)}")

            print(f"   Activity: {comments_count} comments | {history_count} history items | {attachments_count} attachments | {watchers_count} watchers")
            print(f"   URL: {self.jira_url}/browse/{key}")

        print("="*70)

    def save_to_json(self, data, filename):
        """Save data to JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"\n✓ Data saved to {filename}")
        except Exception as e:
            print(f"\n✗ Error saving to {filename}: {e}")


def main():
    """Main execution"""
    print("="*70)
    print("JIRA USER & TICKETS RETRIEVAL")
    print("="*70)

    try:
        # Initialize client
        client = JiraClient()

        # Get current user
        print("\n[1/3] Fetching current user details...")
        user_data = client.get_current_user()
        if user_data:
            client.display_user_info(user_data)
            client.save_to_json(user_data, "jira_user.json")

        # Get assigned/reported issues
        print("\n[2/3] Fetching assigned/reported issues...")
        issues = client.get_user_issues(max_results=50)
        if issues:
            client.display_issues(issues, "YOUR ISSUES (Assigned/Reported)")
            client.save_to_json(issues, "jira_issues.json")

        # Get worked on issues
        print("\n[3/3] Fetching issues you've worked on...")
        worked_issues = client.get_worked_on_issues(max_results=50)
        if worked_issues:
            client.display_issues(worked_issues, "ISSUES YOU'VE WORKED ON")
            client.save_to_json(worked_issues, "jira_worked_issues.json")

        print("\n" + "="*70)
        print("✓ RETRIEVAL COMPLETED")
        print("="*70)

    except ValueError as e:
        print(f"\n✗ Configuration Error: {e}")
    except Exception as e:
        print(f"\n✗ Unexpected Error: {e}")


if __name__ == "__main__":
    main()
