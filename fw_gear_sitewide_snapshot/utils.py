from fw_client import FWClient
from .snapshot import snapshot_utils
import pandas as pd


def get_api_key(config: dict) -> str:
    """Returns api-key value if present in config.json."""
    for inp in config["inputs"].values():
        if inp["base"] == "api-key" and inp["key"]:
            api_key = inp["key"]
            return api_key
    raise ValueError("no api-key found in config.json")


def is_final(value: str):
    return snapshot_utils.SnapshotState(value).is_final()


def filter_completed_and_failed_snapshots(snapshots: pd.DataFrame) -> pd.DataFrame:
    snapshots = snapshots[~snapshots["status"].apply(is_final)]
    return snapshots


def refresh_nonfailed_snapshots(
    snapshots: pd.DataFrame, client: FWClient
) -> pd.DataFrame:
    rows_to_refresh = snapshots[~snapshots["status"].apply(is_final)].index
    for row_index in rows_to_refresh:
        snapshot = snapshots.loc[row_index]
        snapshot_record = snapshot_utils.SnapshotRecord.from_series(snapshot)
        snapshot_record.update(client)
        snapshots.loc[row_index, "status"] = snapshot_record.status
    return snapshots
