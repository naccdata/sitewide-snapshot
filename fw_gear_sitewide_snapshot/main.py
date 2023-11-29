"""Main module."""

import logging
import os
from typing import Union
import pandas as pd
import time

from fw_client import FWClient
import utils
from .fw_snapshot import snapshot_utils, snapshot

log = logging.getLogger(__name__)
SNAPSHOT_TIMEOUT = 10 * 60  # ten min


def process_report_for_retry(report_path: os.PathLike, client: FWClient) -> pd.DataFrame:
    df = pd.read_csv(report_path)
    df = utils.refresh_nonfailed_snapshots(df, client)
    df = utils.filter_completed_and_failed_snapshots(df)
    projects_to_retry = df["project_id"].tolist()
    return projects_to_retry


def wait_for_snapshots(snapshotter: snapshot.Snapshotter):
    start = time.time()
    while time.time() - start < SNAPSHOT_TIMEOUT:
        snapshotter.update_snapshots()
        if snapshotter.is_finished():
            # Finished includes "complete" or "failed", just any end state.
            return 0
        time.sleep(10)
    # Timeout was reached before snapshots were finished
    return 1


def run(api_key: str, project_filter: str, batch_name: str, output_file_path: os.PathLike, retry_failed: Union[None, os.PathLike]) -> int:
    """[summary]

    Returns:
        [type]: [description]
    """

    snapshotter = snapshot.Snapshotter(api_key, batch_name)

    if retry_failed:
        projects_to_retry = process_report_for_retry(retry_failed, snapshotter.snapshot_client)
        snapshotter.trigger_snapshots_on_list(projects_to_retry)
    else:
        snapshotter.trigger_snapshots_on_filter(project_filter)

    return_state = wait_for_snapshots(snapshotter)
    snapshotter.save_snapshot_report(output_file_path)
    return return_state

