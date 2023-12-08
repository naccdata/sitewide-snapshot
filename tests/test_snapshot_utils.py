import datetime

import flywheel
import fw_client
import mock
import pytest
from mock import MagicMock, patch

from ..fw_gear_sitewide_snapshot.snapshot import snapshot_utils
from .snapshot_assets import (
    FAKE_BATCH_NAME,
    FAKE_DATE,
    FAKE_GROUP,
    FAKE_KEY,
    FAKE_PROJECT_ID,
    FAKE_PROJECT_LABEL,
    FAKE_RECORD,
    FAKE_RESPONSE,
    FAKE_SNAPSHOT_ID,
    mock_client,
    mock_project,
    mock_sdk_client,
)


def test_SnapshotRecord_update(mock_client):
    """Test updating a snapshot record"""

    fake_response = snapshot_utils.SnapshotRecord(**FAKE_RESPONSE)
    fake_response.status = snapshot_utils.SnapshotState.complete
    mock_client.get.return_value = fake_response

    update_response = snapshot_utils.SnapshotRecord(**FAKE_RESPONSE)
    assert update_response.status == snapshot_utils.SnapshotState.pending
    update_response.update(mock_client)
    assert update_response.status == snapshot_utils.SnapshotState.complete
    record = snapshot_utils.SnapshotRecord(**FAKE_RESPONSE)
    record.update(mock_client)
    mock_client.get.assert_called_with(
        f"/snapshot/projects/{FAKE_PROJECT_ID}/snapshots/{FAKE_SNAPSHOT_ID}/detail"
    )


def test_SnapshotRecord_is_final():
    """Test is_final method of SnapshotRecord"""
    record = snapshot_utils.SnapshotRecord(**FAKE_RESPONSE)

    assert record.status == snapshot_utils.SnapshotState.pending
    assert not record.is_final()
    assert record.status == snapshot_utils.SnapshotState.pending
    record.status = snapshot_utils.SnapshotState.in_progress
    assert not record.is_final()

    record.status = snapshot_utils.SnapshotState.complete
    assert record.is_final()
    record.status = snapshot_utils.SnapshotState.failed
    assert record.is_final()


def test_string_matches_id():
    """Test string_matches_id function"""
    assert snapshot_utils.string_matches_id(FAKE_PROJECT_ID)
    assert not snapshot_utils.string_matches_id("NOPE")


def test_make_snapshot(mock_client):
    """Test making a snapshot"""
    snapshot_utils.make_snapshot(client=mock_client, project_id=FAKE_PROJECT_ID)
    mock_client.post.assert_called_with(
        f"/snapshot/projects/{FAKE_PROJECT_ID}/snapshots"
    )


def test_get_snapshot(mock_client):
    """Test getting a snapshot"""
    mock_client.get.return_value = FAKE_RESPONSE
    response = snapshot_utils.get_snapshot(
        client=mock_client, project_id=FAKE_PROJECT_ID, snapshot_id=FAKE_SNAPSHOT_ID
    )
    mock_client.get.assert_called_with(
        f"/snapshot/projects/{FAKE_PROJECT_ID}/snapshots/{FAKE_SNAPSHOT_ID}"
    )

    assert response == FAKE_RESPONSE
