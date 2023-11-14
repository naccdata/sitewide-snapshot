import re

from fw_client import FWClient
from fw_http_client.errors import NotFound

CONTAINER_ID_FORMAT = "^[0-9a-fA-F]{24}$"


def string_matches_id(string: str) -> bool:
    """determines if a string matches the flywheel ID format
    Args:
        string: the string to check
    Returns:
        True if the string matches the flywheel ID format, False otherwise
    """
    return True if re.fullmatch(CONTAINER_ID_FORMAT, string) else False


def make_snapshot(client: FWClient, project_id: str) -> str:
    """makes a snapshot on a project
    Args:
        client: a flywheel client
        project_id: the ID of the project to make a snapshot on
    Returns:
        the ID of the snapshot
    """
    log.debug(f"creating snapshot on {project_id}")
    response = client.post(f"/snapshot/projects/{project_id}/snapshots")
    return response["_id"]


def lookup_project(client: FWClient, project_lookup_string: str) -> dict:
    """looks up a project by group/label hierarchy format
    Args:
        client: a flywheel client
        project_lookup_string: the string to lookup
    Returns:
        the project dict response from the flywheel API if found, None otherwise
    """
    endpoint = "/api/lookup"
    body = {"path": project_lookup_string.split("/")}
    try:
        response = client.post(endpoint, json=body)
    except NotFound:
        log.error(f"Unable to find project {project_lookup_string}")
        response = None
    return response
