"""Module to handle users."""
from typing import NamedTuple
from .api import WWW_BASE_URL


class User(NamedTuple):
    """A user."""

    name: str
    login: str

    def display_name(self):
        """Name to include in displays."""
        return f"{self.name} ({self.login})" if self.name else self.login

    def profile_url(self):
        """User profile url."""
        return f"{WWW_BASE_URL}/people/{self.login}" if self.login else ""


def get_user_from_json(record):
    """Get User from JSON record.

	Parameters
	----------
	record: dict
		A JSON record from /v1/users or other endpoints including user
		records.

	Returns
	-------
	User
		A User object from the JSON record.
	"""
    name = record["name"]
    login = record["login"]

    return User(name, login)
