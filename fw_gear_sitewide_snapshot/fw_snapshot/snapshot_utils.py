import re
from datetime import timezone
import datetime
from fw_client import FWClient
from fw_http_client.errors import NotFound
from pydantic import BaseModel, Field, root_validator, Extra
from enum import Enum
import logging
import pandas as pd

CONTAINER_ID_FORMAT = "^[0-9a-fA-F]{24}$"
SNAPSHOT_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%f%z"
RECORD_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M"
log=logging.getLogger("SnapshotUtils")

class SnapshotState(str, Enum):
    """The snapshot state"""

    pending = "pending"
    in_progress = "in_progress"
    complete = "complete"
    failed = "failed"

    def is_final(self) -> bool:
        """Helper that indicates whether or not this is a terminal state"""
        return self in (SnapshotState.complete, SnapshotState.failed)


class SnapshotParents(BaseModel):
    """Parent references for snapshots"""
    project: str


class SnapshotRecord(BaseModel):
    id: str = Field(alias="_id")
    created: datetime.datetime = datetime.datetime.now()
    status: SnapshotState = SnapshotState.pending
    parents: SnapshotParents = SnapshotParents(project="")
    group_label: str = ""
    project_label: str = ""
    batch_label: str = ""

    def update(self, client) -> None:
        """Updates the snapshot status"""
        snapshot = client.get(f"/snapshot/projects/{self.parents.project}/snapshots/{self.id}/detail")
        self.status = SnapshotState(snapshot.status)

    def is_final(self) -> bool:
        """Helper that indicates whether or not this is a terminal state"""
        return self.status.is_final()

    def format_timestamp(self):
        """Get a formatted timestamp from a snapshot"""
        return datetime.datetime.strftime(self.created, RECORD_TIMESTAMP_FORMAT)

    def to_series(self):
        return pd.Series(
            {
                "group_label": self.group_label,
                "project_label": self.project_label,
                "project_id": self.parents.project,
                "snapshot_id": self.id,
                "timestamp": self.format_timestamp(),
                "batch_label": self.batch_label,
                "status": self.status,
            }
        )

    @classmethod
    def from_series(cls, series: pd.Series):
        new_snapshot = cls(id=series["snapshot_id"],
                           created=datetime.datetime.strptime(series["timestamp"], RECORD_TIMESTAMP_FORMAT),
                           status=series["status"],
                           parents=SnapshotParents(project=series["project_id"]),
                           group_label=series["group_label"],
                           project_label=series["project_label"],
                           batch_label=series["batch_label"])
        return new_snapshot


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
    return client.post(f"/snapshot/projects/{project_id}/snapshots")


def get_snapshot(client: FWClient, project_id: str, snapshot_id: str) -> dict:
    """gets a snapshot from a project
    Args:
        client: a flywheel client
        project_id: the ID of the project to get the snapshot from
        snapshot_id: the ID of the snapshot to get
    Returns:
        the snapshot dict response from the flywheel API if found, None otherwise
    """
    endpoint = f"/snapshot/projects/{project_id}/snapshots/{snapshot_id}"
    try:
        response = client.get(endpoint)
    except NotFound:
        log.error(f"Unable to find snapshot {snapshot_id} on project {project_id}")
        response = None
    return response

