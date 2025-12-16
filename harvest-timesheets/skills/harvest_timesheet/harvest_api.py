"""
Harvest API client for timesheet management.

Implements Harvest API v2 for:
- Authentication
- Time entry creation
- Time entry retrieval
- User information
"""

import requests
from typing import Dict, Any, List, Optional
from datetime import date


class HarvestAPIError(Exception):
    """Raised when Harvest API requests fail."""
    pass


class HarvestClient:
    """
    Client for interacting with Harvest API v2.

    Documentation: https://help.getharvest.com/api-v2/
    """

    BASE_URL = "https://api.harvestapp.com/v2"

    def __init__(self, access_token: str, account_id: str):
        """
        Initialize Harvest API client.

        Args:
            access_token: Harvest Personal Access Token
            account_id: Harvest Account ID
        """
        self.access_token = access_token
        self.account_id = account_id
        self.session = requests.Session()
        self.session.headers.update(self._get_headers())

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Harvest-Account-ID": self.account_id,
            "Content-Type": "application/json",
            "User-Agent": "Harvest-Timesheet-Automation/1.0"
        }

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response and raise errors if needed.

        Args:
            response: Response object from requests

        Returns:
            Parsed JSON response

        Raises:
            HarvestAPIError: If request failed
        """
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_msg = f"Harvest API error: {response.status_code}"

            try:
                error_data = response.json()
                if "error" in error_data:
                    error_msg += f" - {error_data['error']}"
                if "error_description" in error_data:
                    error_msg += f": {error_data['error_description']}"
            except Exception:
                error_msg += f" - {response.text}"

            raise HarvestAPIError(error_msg) from e
        except requests.exceptions.RequestException as e:
            raise HarvestAPIError(f"Network error: {e}") from e

    def authenticate(self) -> Dict[str, Any]:
        """
        Test authentication by retrieving current user info.

        Returns:
            User information dictionary

        Raises:
            HarvestAPIError: If authentication fails
        """
        return self.get_current_user()

    def get_current_user(self) -> Dict[str, Any]:
        """
        Get current authenticated user information.

        Returns:
            User information including ID, name, email

        Raises:
            HarvestAPIError: If request fails
        """
        response = self.session.get(f"{self.BASE_URL}/users/me")
        return self._handle_response(response)

    def create_time_entry(
        self,
        project_id: str,
        task_id: str,
        spent_date: date,
        hours: float,
        notes: str
    ) -> Dict[str, Any]:
        """
        Create a new time entry.

        Args:
            project_id: Harvest project ID
            task_id: Harvest task ID
            spent_date: Date the time was spent
            hours: Number of hours to log
            notes: Description of work done

        Returns:
            Created time entry data

        Raises:
            HarvestAPIError: If creation fails
        """
        data = {
            "project_id": int(project_id),
            "task_id": int(task_id),
            "spent_date": spent_date.strftime("%Y-%m-%d"),
            "hours": float(hours),
            "notes": notes
        }

        response = self.session.post(
            f"{self.BASE_URL}/time_entries",
            json=data
        )

        return self._handle_response(response)

    def get_time_entries(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve time entries with optional filters.

        Args:
            from_date: Start date for filtering (optional)
            to_date: End date for filtering (optional)
            project_id: Filter by project ID (optional)

        Returns:
            List of time entry dictionaries

        Raises:
            HarvestAPIError: If request fails
        """
        params = {}

        if from_date:
            params["from"] = from_date.strftime("%Y-%m-%d")
        if to_date:
            params["to"] = to_date.strftime("%Y-%m-%d")
        if project_id:
            params["project_id"] = project_id

        response = self.session.get(
            f"{self.BASE_URL}/time_entries",
            params=params
        )

        data = self._handle_response(response)
        return data.get("time_entries", [])

    def update_time_entry(
        self,
        entry_id: int,
        hours: Optional[float] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing time entry.

        Args:
            entry_id: ID of time entry to update
            hours: New hours value (optional)
            notes: New notes value (optional)

        Returns:
            Updated time entry data

        Raises:
            HarvestAPIError: If update fails
        """
        data = {}
        if hours is not None:
            data["hours"] = float(hours)
        if notes is not None:
            data["notes"] = notes

        response = self.session.patch(
            f"{self.BASE_URL}/time_entries/{entry_id}",
            json=data
        )

        return self._handle_response(response)

    def delete_time_entry(self, entry_id: int) -> None:
        """
        Delete a time entry.

        Args:
            entry_id: ID of time entry to delete

        Raises:
            HarvestAPIError: If deletion fails
        """
        response = self.session.delete(
            f"{self.BASE_URL}/time_entries/{entry_id}"
        )

        if response.status_code != 200:
            self._handle_response(response)

    def check_duplicate_entries(
        self,
        project_id: str,
        spent_date: date
    ) -> List[Dict[str, Any]]:
        """
        Check if time entries already exist for a project on a given date.

        Args:
            project_id: Harvest project ID
            spent_date: Date to check

        Returns:
            List of existing time entries for that project/date

        Raises:
            HarvestAPIError: If request fails
        """
        entries = self.get_time_entries(
            from_date=spent_date,
            to_date=spent_date,
            project_id=project_id
        )

        return entries

    def get_projects(self) -> List[Dict[str, Any]]:
        """
        Get list of projects accessible to current user.

        Returns:
            List of project dictionaries

        Raises:
            HarvestAPIError: If request fails
        """
        response = self.session.get(f"{self.BASE_URL}/projects")
        data = self._handle_response(response)
        return data.get("projects", [])

    def get_project_tasks(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get list of tasks for a specific project.

        Args:
            project_id: Harvest project ID

        Returns:
            List of task dictionaries

        Raises:
            HarvestAPIError: If request fails
        """
        response = self.session.get(
            f"{self.BASE_URL}/projects/{project_id}/task_assignments"
        )
        data = self._handle_response(response)
        return data.get("task_assignments", [])

    def get_timesheets(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get timesheets (weekly collections of time entries).

        Args:
            from_date: Start date for filtering (optional)
            to_date: End date for filtering (optional)

        Returns:
            List of timesheet dictionaries

        Raises:
            HarvestAPIError: If request fails
        """
        params = {}
        if from_date:
            params["from"] = from_date.strftime("%Y-%m-%d")
        if to_date:
            params["to"] = to_date.strftime("%Y-%m-%d")

        response = self.session.get(
            f"{self.BASE_URL}/time_sheets",
            params=params
        )
        data = self._handle_response(response)
        return data.get("time_sheets", [])

    def submit_timesheet(
        self,
        from_date: date,
        to_date: date
    ) -> Dict[str, Any]:
        """
        Submit a timesheet for approval.

        Args:
            from_date: Start date of timesheet week
            to_date: End date of timesheet week

        Returns:
            Timesheet data

        Raises:
            HarvestAPIError: If submission fails
        """
        data = {
            "start_date": from_date.strftime("%Y-%m-%d"),
            "end_date": to_date.strftime("%Y-%m-%d")
        }

        response = self.session.post(
            f"{self.BASE_URL}/time_sheets",
            json=data
        )

        return self._handle_response(response)


def test_authentication(access_token: str, account_id: str) -> bool:
    """
    Test if Harvest credentials are valid.

    Args:
        access_token: Harvest Personal Access Token
        account_id: Harvest Account ID

    Returns:
        True if authentication successful, False otherwise
    """
    try:
        client = HarvestClient(access_token, account_id)
        user = client.authenticate()

        print(f"✓ Authentication successful!")
        print(f"  User: {user.get('first_name')} {user.get('last_name')}")
        print(f"  Email: {user.get('email')}")

        return True

    except HarvestAPIError as e:
        print(f"✗ Authentication failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False
