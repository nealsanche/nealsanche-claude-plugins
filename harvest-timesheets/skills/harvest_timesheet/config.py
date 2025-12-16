"""
Configuration management for Harvest timesheet automation.

Handles:
- .project.yaml creation and loading
- Harvest API credentials storage and retrieval
- Configuration validation
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


def create_project_config() -> Dict[str, Any]:
    """
    Interactive setup for .project.yaml configuration.

    Returns:
        Dict containing the project configuration
    """
    print("=== Harvest Project Setup ===\n")
    print("You'll need your Harvest Project ID and Task ID.")
    print("Find these in the Harvest web interface.\n")

    project_id = input("Enter Harvest Project ID: ").strip()
    if not project_id:
        raise ConfigurationError("Project ID is required")

    task_id = input("Enter Harvest Task ID: ").strip()
    if not task_id:
        raise ConfigurationError("Task ID is required")

    default_notes = input("Enter default notes (used when no commits found): ").strip()
    if not default_notes:
        default_notes = "Development work"

    future_notes = input("Enter notes for future days (e.g., Friday when submitting Thursday) [same as previous day]: ").strip()

    hours_input = input("Hours per day [8.0]: ").strip()
    hours_per_day = float(hours_input) if hours_input else 8.0

    config = {
        "harvest": {
            "project_id": project_id,
            "task_id": task_id,
            "default_notes": default_notes,
            "hours_per_day": hours_per_day
        }
    }

    # Add future_day_notes only if provided
    if future_notes:
        config["harvest"]["future_day_notes"] = future_notes

    # Save to .project.yaml
    config_path = Path(".project.yaml")
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(f"\n✓ Configuration saved to {config_path.absolute()}")
    print("\nTip: Add .project.yaml to .gitignore if it contains sensitive info")

    return config


def load_project_config() -> Dict[str, Any]:
    """
    Load and validate .project.yaml configuration.

    Returns:
        Dict containing the project configuration

    Raises:
        ConfigurationError: If config file not found or invalid
    """
    config_path = Path(".project.yaml")

    if not config_path.exists():
        raise ConfigurationError(
            ".project.yaml not found. Run project setup workflow first."
        )

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML in .project.yaml: {e}")

    # Validate required fields
    if "harvest" not in config:
        raise ConfigurationError("Missing 'harvest' section in .project.yaml")

    harvest = config["harvest"]
    required_fields = ["project_id", "task_id", "default_notes"]

    for field in required_fields:
        if field not in harvest:
            raise ConfigurationError(f"Missing required field: {field}")

    # Set default for hours_per_day if not present
    if "hours_per_day" not in harvest:
        harvest["hours_per_day"] = 8.0

    return config


def setup_harvest_auth() -> tuple[str, str]:
    """
    Interactive setup for Harvest API authentication.

    Returns:
        Tuple of (access_token, account_id)
    """
    print("=== Harvest Authentication Setup ===\n")
    print("You need a Harvest Personal Access Token.")
    print("Get one at: https://id.getharvest.com/developers\n")

    access_token = input("Enter Harvest Access Token: ").strip()
    if not access_token:
        raise ConfigurationError("Access token is required")

    account_id = input("Enter Harvest Account ID: ").strip()
    if not account_id:
        raise ConfigurationError("Account ID is required")

    # Ask how to store credentials
    print("\nHow would you like to store these credentials?")
    print("1. Environment variables (recommended)")
    print("2. .env file in current directory")
    print("3. Display only (you'll set them up manually)")

    choice = input("\nChoice (1-3): ").strip()

    if choice == "1":
        print("\nAdd these to your shell profile (~/.bashrc, ~/.zshrc, etc.):")
        print(f"export HARVEST_ACCESS_TOKEN='{access_token}'")
        print(f"export HARVEST_ACCOUNT_ID='{account_id}'")
        print("\nThen run: source ~/.bashrc  (or restart your terminal)")

    elif choice == "2":
        env_path = Path(".env")

        # Read existing .env if it exists
        existing_lines = []
        if env_path.exists():
            with open(env_path, "r") as f:
                existing_lines = [
                    line for line in f.readlines()
                    if not line.startswith("HARVEST_")
                ]

        # Write updated .env
        with open(env_path, "w") as f:
            f.writelines(existing_lines)
            f.write(f"\n# Harvest API credentials\n")
            f.write(f"HARVEST_ACCESS_TOKEN={access_token}\n")
            f.write(f"HARVEST_ACCOUNT_ID={account_id}\n")

        print(f"\n✓ Credentials saved to {env_path.absolute()}")
        print("⚠ Make sure .env is in your .gitignore!")

    else:
        print("\nHarvest credentials:")
        print(f"HARVEST_ACCESS_TOKEN={access_token}")
        print(f"HARVEST_ACCOUNT_ID={account_id}")

    return access_token, account_id


def get_harvest_credentials() -> tuple[str, str]:
    """
    Retrieve Harvest API credentials from environment.

    Checks:
    1. Environment variables directly
    2. .env file in current directory
    3. ~/.harvest/credentials file

    Returns:
        Tuple of (access_token, account_id)

    Raises:
        ConfigurationError: If credentials not found
    """
    # Load .env file if it exists
    load_dotenv()

    access_token = os.getenv("HARVEST_ACCESS_TOKEN")
    account_id = os.getenv("HARVEST_ACCOUNT_ID")

    # If not in environment, check ~/.harvest/credentials
    if not access_token or not account_id:
        harvest_dir = Path.home() / ".harvest"
        credentials_file = harvest_dir / "credentials"

        if credentials_file.exists():
            try:
                with open(credentials_file, "r") as f:
                    for line in f:
                        if line.startswith("HARVEST_ACCESS_TOKEN="):
                            access_token = line.split("=", 1)[1].strip()
                        elif line.startswith("HARVEST_ACCOUNT_ID="):
                            account_id = line.split("=", 1)[1].strip()
            except Exception as e:
                pass  # Fall through to error below

    if not access_token or not account_id:
        raise ConfigurationError(
            "Harvest credentials not found. Run authentication setup workflow.\n"
            "Set HARVEST_ACCESS_TOKEN and HARVEST_ACCOUNT_ID environment variables."
        )

    return access_token, account_id


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate project configuration structure.

    Args:
        config: Configuration dictionary to validate

    Returns:
        True if valid

    Raises:
        ConfigurationError: If validation fails
    """
    if "harvest" not in config:
        raise ConfigurationError("Missing 'harvest' section")

    harvest = config["harvest"]

    # Required fields
    if "project_id" not in harvest or not str(harvest["project_id"]).strip():
        raise ConfigurationError("project_id is required")

    if "task_id" not in harvest or not str(harvest["task_id"]).strip():
        raise ConfigurationError("task_id is required")

    if "default_notes" not in harvest or not harvest["default_notes"].strip():
        raise ConfigurationError("default_notes is required")

    # Optional but validated if present
    if "hours_per_day" in harvest:
        try:
            hours = float(harvest["hours_per_day"])
            if hours <= 0 or hours > 24:
                raise ConfigurationError("hours_per_day must be between 0 and 24")
        except (TypeError, ValueError):
            raise ConfigurationError("hours_per_day must be a number")

    # Validate time_off section if present
    if "time_off" in harvest:
        time_off = harvest["time_off"]

        if "project_id" not in time_off or not str(time_off["project_id"]).strip():
            raise ConfigurationError("time_off.project_id is required when time_off is configured")

        if "task_id" not in time_off or not str(time_off["task_id"]).strip():
            raise ConfigurationError("time_off.task_id is required when time_off is configured")

        # default_reason is optional, but validate if present
        if "default_reason" in time_off and not time_off["default_reason"].strip():
            raise ConfigurationError("time_off.default_reason cannot be empty if specified")

    return True
