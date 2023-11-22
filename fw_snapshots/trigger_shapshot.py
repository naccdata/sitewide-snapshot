import datetime
from dataclasses import dataclass
import pandas as pd
from . import snapshot_utils

import flywheel
import fw_utils
from fw_client import FWClient
from typing import List, Union
import logging

log = logging.getLogger("TriggerSnapshots")

RECORD_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M"
VALID_ENDSTATES = ["complete", "failed"]


@dataclass
class SnapshotRecordItem:
    group_label: str
    project_label: str
    project_id: str
    snapshot_id: str
    timestamp: datetime.datetime
    collection_label: str
    status: str
    message: str

    def to_series(self):
        return pd.Series(
            {
                "group_label": self.group_label,
                "project_label": self.project_label,
                "project_id": self.project_id,
                "snapshot_id": self.snapshot_id,
                "timestamp": self.timestamp,
                "collection_label": self.collection_label,
                "status": self.status,
                "message": self.message,
            }
        )


class TriggerSnapshots:
    """A class for triggering snapshots on projects

    Params:
        client: a flywheel client
        dry_run: if True, don't actually trigger snapshots
    """

    def __init__(self, client: FWClient, dry_run = False, batch_name=""):
        self.client = client
        self.dry_run = dry_run
        self.batch_name = batch_name
        self.snapshots = []


    def trigger_snapshots_on_filter(
        self,
        project_filter,
    ) -> pd.DataFrame:
        """Trigger snapshots on projects matching a filter

        Args:
            project_filter: the filter to use

        Returns:
            a dataframe of snapshot records
        """
        projects = self.find_projects_with_filter(project_filter)
        for project in projects:
            log.debug(f"Triggering snapshot on project {project.get('label')}")
            _ = self.make_snapshot_on_project(project)

    def find_projects_with_filter(self, project_filter: str) -> List[flywheel.Project]:
        """Find projects with a filter

        Args:
            project_filter: the filter to use

        Returns:
            a list of projects
        """
        projects = self.client.get("/api/projects", params={"filter": project_filter})
        log.debug(f"found {len(projects)} projects")
        return projects

    def make_snapshot_on_project(
        self, project: Union[str, flywheel.Project, fw_utils.dicts.AttrDict]
    ) -> str:
        """Make a snapshot on a project

        Args:
            project: the project to make a snapshot on.  Can be a project ID, a project
                label, or a flywheel project object.

        Returns:
            the ID of the snapshot
        """
        if isinstance(project, str):
            if snapshot_utils.string_matches_id(project):
                project_id = project
            else:
                project = snapshot_utils.lookup_project(self.client, project)
                project_id = project.get("_id")
        else:
            project_id = project.get("_id")

        if not project_id:
            raise ValueError(f"no project ID found for project {project}")

        return self.make_snapshot_on_id(project_id)

    def make_snapshot_on_id(self, project_id: str) -> str:
        """Make a snapshot on a project given a project ID

        Args:
            project_id: the ID of the project

        Returns:
            the ID of the snapshot
        """
        snapshot_id = None
        if self.dry_run:
            snapshot_id = self.dryrun_snapshot(project_id)

        log.debug(f"creating snapshot on {project_id}")
        try:
            snapshot_id = snapshot_utils.make_snapshot(self.client, project_id)
            self.log_snapshot(project_id, snapshot_id)
        except Exception as e:
            self.log_snapshot(project_id, snapshot_id=snapshot_id, exception=e)

        return snapshot_id

    def dryrun_snapshot(self, project_id):
        log.debug(f"would create snapshot on {project_id}")
        record = self.make_snapshot_record(
            snapshot_id="snapshot_id",
            project_id=project_id,
            timestamp=datetime.datetime.now(),
            status="complete",
        )
        self.snapshots.append(record)
        return "<snapshot ID>"

    def log_snapshot(self, project_id, snapshot_id=None, exception=None):
        if exception:
            record = self.make_snapshot_record(
                snapshot_id="",
                project_id=project.get("_id"),
                project_label=project.get("label"),
                status="FAILED",
                timestamp=datetime.datetime.now(),
                message=str(exception),
            )
        else:
            record = self.make_snapshot_record(snapshot_id, project_id)
        self.snapshots.append(record)

    def make_snapshot_record(
        self,
        snapshot_id,
        project_id,
        project_label: str = None,
        group_label: str = None,
        timestamp: datetime.datetime = None,
        status: str = "",
        message: str = "",
    ) -> SnapshotRecordItem:
        """Make a SnapshotRecordItem object

        Args:
            snapshot_id: the ID of the snapshot
            project_id: the ID of the project
            project_label: the label of the project
            group_label: the label of the group
            timestamp: the timestamp of the snapshot
            status: the status of the snapshot
            message: a message associated with the snapshot

        Returns:
            a SnapshotRecordItem object
        """
        snapshot = snapshot_utils.get_snapshot(self.client, project_id, snapshot_id)

        if not snapshot_id:
            raise ValueError("no snapshot ID provided")
        if not project_id:
            raise ValueError("no project ID provided")
        project = None
        if not timestamp:
            timestamp = self.get_formatted_snapshot_timestamp(snapshot)
        if not project_label:
            project_label = project.get("label")
        if not group_label:
            if not project:
                project = self.client.get(f"/api/projects/{project_id}")
            group_label = project.parents.group
        if not status:
            status = snapshot.status

        return SnapshotRecordItem(
            group_label=group_label,
            project_label=project_label,
            project_id=project_id,
            snapshot_id=snapshot_id,
            timestamp=timestamp,
            collection_label=self.collection_label,
            status=status,
            message=message,
        )

    @staticmethod
    def get_formatted_snapshot_timestamp(snapshot):
        """Get a formatted timestamp from a snapshot"""
        timestamp_datetime = snapshot_utils.get_snapshot_created_datetime(snapshot)
        timestamp = datetime.strftime(timestamp_datetime, RECORD_TIMESTAMP_FORMAT)
        return timestamp

    def update_snapshots(self):
        """Fetches updates on the status of the snapshots in the snapshot list and updates them in place"""

        snapshots_to_update = [s for s in self.snapshots if s.status not in VALID_ENDSTATES]
        for snapshot in snapshots_to_update:
            snapshot_id = snapshot.snapshot_id
            project_id = snapshot.project_id
            refreshed_snapshot = snapshot_utils.get_snapshot(self.client, project_id, snapshot_id)
            snapshot.status = refreshed_snapshot.status

    def snapshots_are_finished(self):
        """Returns True if all snapshots are finished, False otherwise"""

        return all([s.status in VALID_ENDSTATES for s in self.snapshots])

    def save_snapshot_report(self, report_path):
        """Saves the snapshot report to a CSV file"""
        df = self.reports_to_df()
        df.to_csv(report_path, index=False)

    def reports_to_df(self):
        """Converts the snapshot reports to a dataframe"""
        return pd.DataFrame([s.to_series() for s in self.snapshots])

