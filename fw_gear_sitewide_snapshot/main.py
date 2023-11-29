"""Main module."""

import logging
import os
import time
from typing import Union

import pandas as pd
from . import utils
from fw_client import FWClient

from .fw_snapshot import snapshot

log = logging.getLogger(__name__)
SNAPSHOT_TIMEOUT = 10 * 60  # ten min


def process_report_for_retry(
    report_path: os.PathLike, client: FWClient
) -> pd.DataFrame:
    """Process a snapshot report to retry failed snapshots

    Args:
        report_path: path to a snapshot report
        client: A flywheel client object
    Returns:
        A list of project ids to retry
    """
    df = pd.read_csv(report_path)
    df = utils.refresh_nonfailed_snapshots(df, client)
    df = utils.filter_completed_and_failed_snapshots(df)
    projects_to_retry = df["project_id"].tolist()
    return projects_to_retry


def wait_for_snapshots(snapshotter: snapshot.Snapshotter) -> int:
    """Wait for snapshots to reach an end state, complete or failed

    Args:
        snapshotter: A snapshotter object with snapshots to wait on

    Returns:
        int: 0 if completed, 1 if timed out
    """
    start = time.time()
    while time.time() - start < SNAPSHOT_TIMEOUT:
        snapshotter.update_snapshots()
        if snapshotter.is_finished():
            # Finished includes "complete" or "failed", just any end state.
            return 0
        time.sleep(10)
    # Timeout was reached before snapshots were finished
    return 1


def run(
    api_key: str,
    project_filter: str,
    batch_name: str,
    output_file_path: os.PathLike,
    retry_failed: Union[None, os.PathLike],
) -> int:
    """
    Run the sitewide snapshot gear.

    Initiate a snapshot on a project filter if provided.  If a csv report from a previous
    gear run is provided, retry creating the snapshot for any failed snapshots in the report.

    Args:
        api_key: a flywheel instance api key
        project_filter: the project filter to use
        batch_name: the name of the snapshot batch
        output_file_path: the path to save the snapshot report to
        retry_failed: If set, the path to a snapshot report to retry failed snapshots

    Returns:
        0 if successful, 1 if not

    """

    snapshotter = snapshot.Snapshotter(api_key, batch_name)

    if retry_failed:
        projects_to_retry = process_report_for_retry(
            retry_failed, snapshotter.snapshot_client
        )
        if not projects_to_retry:
            log.info("No failed snapshots to retry")
            return 0

        snapshotter.trigger_snapshots_on_list(projects_to_retry)
    else:
        snapshotter.trigger_snapshots_on_filter(project_filter)

    return_state = wait_for_snapshots(snapshotter)
    snapshotter.save_snapshot_report(output_file_path)
    return return_state
