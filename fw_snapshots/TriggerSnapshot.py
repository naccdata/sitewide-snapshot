import datetime

import pandas as pd
import snapshot_utils


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

    def __init__(self, client: FWClient):
        self.client = client
        self.dry_run = False

    def make_snapshot_on_project(
        self, project: Union[str, flywheel.Project, fw_client.dicts.AttrDict]
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
            raise ValueError(f"no project ID found on project")

        return self.make_snapshot_on_id(project_id)

    def make_snapshot_record(
        self,
        snapshot_id,
        project_id,
        project_label: str = None,
        group_label: str = None,
        timestamp: datetime.datetime = None,
        collection_label: str = None,
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
            collection_label: the label of the collection
            status: the status of the snapshot
            message: a message associated with the snapshot

        Returns:
            a SnapshotRecordItem object
        """
        if not snapshot_id:
            raise ValueError("no snapshot ID provided")
        if not project_id:
            raise ValueError("no project ID provided")
        project = None
        if not timestamp:
            timestamp = datetime.datetime.now()
        if not project_label:
            project = self.client.get(f"/api/projects/{project_id}")
            project_label = project.get("label")
        if not group_label:
            if not project:
                project = self.client.get(f"/api/projects/{project_id}")
            group_label = project.parents.group
        if not collection_label:
            collection_label = ""

        return SnapshotRecordItem(
            group_label=group_label,
            project_label=project_label,
            project_id=project_id,
            snapshot_id=snapshot_id,
            timestamp=timestamp,
            collection_label=collection_label,
            status=status,
            message=message,
        )

    def make_snapshot_on_id(self, project_id: str) -> str:
        """Make a snapshot on a project given a project ID

        Args:
            project_id: the ID of the project

        Returns:
            the ID of the snapshot
        """
        if self.dry_run:
            log.debug(f"would create snapshot on {project_id}")
            return "snapshot ID"

        log.debug(f"creating snapshot on {project_id}")
        snapshot_id = snapshot_utils.make_snapshot(self.client, project_id)
        return snapshot_id

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

    def trigger_snapshots_on_filter(
        self, project_filter, collection_name=None
    ) -> pd.DataFrame:
        """Trigger snapshots on projects matching a filter

        Args:
            project_filter: the filter to use
            collection_name: a name to give to this collection of snapshots

        Returns:
            a dataframe of snapshot records
        """
        if collection_name is None:
            collection_name = ""
        projects = self.find_projects_with_filter(project_filter)
        snapshot_report = pd.DataFrame(
            columns=SnapshotRecordItem.__dataclass_fields__.keys()
        )

        for project in projects:
            try:
                log.debug(f"Triggering snapshot on project {project.get('label')}")
                snapshot_id = self.make_snapshot_on_project(project)
                record = self.make_snapshot_record(
                    snapshot_id,
                    project.get("_id"),
                    project.get("label"),
                    collection_label=collection_name,
                    status="SUCCESS",
                )
            except Exception as e:
                record = self.make_snapshot_record(
                    "",
                    project.get("_id"),
                    project.get("label"),
                    collection_label=collection_name,
                    status="FAILED",
                    message=str(e),
                )

            snapshot_report = snapshot_report.append(
                record.to_series, ignore_index=True
            )

        return snapshot_report
