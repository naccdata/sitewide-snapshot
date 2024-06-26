import logging
import os
from typing import List, Union

import flywheel
import fw_utils
import pandas as pd
from fw_client import FWClient

from . import snapshot_utils

log = logging.getLogger("TriggerSnapshots")


class Snapshotter:
    """A class for triggering snapshots on projects

    Params:
        api_key: a flywheel api key
    """

    def __init__(self, api_key: str, batch_name=""):
        self.snapshot_client = FWClient(
            api_key=api_key,
            client_name="Snapshotter",
            client_version="0.1",
        )
        self.sdk_client = flywheel.Client(api_key=api_key)
        self.batch_name = batch_name
        self.snapshots = []

    def trigger_snapshots_on_list(self, projects: List) -> pd.DataFrame:
        """Trigger snapshots on a list of project ids

        Args:
            projects: a list of project ids

        Returns:
            a dataframe of snapshot records
        """
        for project_id in projects:
            log.debug(f"Triggering snapshot on project {project_id} from list")
            _ = self.make_snapshot_on_id(project_id)

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
        if project_filter == "ALL":
            project_filter = ""
        projects = self.sdk_client.projects.iter_find(project_filter)
        for project in projects:
            log.debug(f"Filter triggered snapshot on project {project.get('label')}")
            _ = self.make_snapshot_on_project(project)

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
        # If a string is provided, it's an ID or a lookup path
        if isinstance(project, str):
            if snapshot_utils.string_matches_id(project):
                # Snapshots can be initiated on bogus project IDs as long as they're in the correct format.
                # Ensure the project exists here by getting it
                project = self.sdk_client.get_project(project)
            else:
                project = self.sdk_client.lookup(project)

        # Otherwise it's an sdk project object or a FWClient project object,
        # either way they should have the "_id" attribute
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
        response = snapshot_utils.make_snapshot(self.snapshot_client, project_id)
        self.log_snapshot(response)
        return response

    def log_snapshot(self, response: dict) -> None:
        """Logs a snapshot response and adds it to the snapshot list
        Args:
            response: the response from the flywheel API
        """

        record = snapshot_utils.SnapshotRecord(**response)

        project_id = record.parents.project
        project = self.sdk_client.get_project(project_id)

        record.project_label = project.label
        record.group_label = project.group
        record.batch_label = self.batch_name

        self.snapshots.append(record)

    def update_snapshots(self) -> None:
        """Fetches updates on the status of the snapshots in the snapshot list and updates them in place"""
        [s.update(self.snapshot_client) for s in self.snapshots if not s.is_final()]

    def is_finished(self) -> bool:
        """Returns True if all snapshots are finished, False otherwise"""
        return all([s.is_final() for s in self.snapshots])

    def save_snapshot_report(self, report_path: os.PathLike) -> None:
        """Saves the snapshot report to a CSV file"""
        df = self.reports_to_df()
        df.to_csv(report_path, index=False)

    def reports_to_df(self) -> pd.DataFrame:
        """Converts the snapshot reports to a dataframe"""
        return pd.DataFrame([s.to_series() for s in self.snapshots])
