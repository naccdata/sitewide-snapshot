"""Main module."""

import logging
import os
from typing import Union
import pandas as pd

from fw_client import FWClient
import utils
from .fw_snapshot import snapshot_utils

log = logging.getLogger(__name__)


def process_report_for_retry(report_path: os.PathLike, client: FWClient) -> pd.DataFrame:
    df = pd.read_csv(report_path)
    df = utils.refresh_nonfailed_snapshots(df, client)
    df = utils.filter_completed_and_failed_snapshots(df)
    return df


def run_snapshot_on_filter():
    pass


def run_snapshot_on_df(df: pd.DataFrame, api_key):
    pass


def run(api_key: str, project_filter: str, batch_name: str, retry_failed: Union[None, os.PathLike]) -> int:
    """[summary]

    Returns:
        [type]: [description]
    """

    if retry_failed:
        client = utils.make_client(api_key)
        df_to_retry = process_report_for_retry(retry_failed, client)
        run_snapshot_on_df(df_to_retry)
        return 0

    run_snapshot_on_filter(api_key, project_filter, batch_name)
    return 0

