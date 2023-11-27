import datetime

import flywheel
import fw_client
import mock
import pytest
from mock import MagicMock, patch

from ..fw_gear_sitewide_snapshot.fw_snapshot import snapshot, snapshot_utils
from .snapshot_assets import (FAKE_BATCH_NAME, FAKE_DATE, FAKE_GROUP, FAKE_KEY,
                              FAKE_PROJECT_ID, FAKE_PROJECT_LABEL,
                              FAKE_RESPONSE, FAKE_SNAPSHOT_ID, mock_client,
                              mock_project, mock_sdk_client)


@pytest.fixture
def mock_client():
    return MagicMock(spec=fw_client.FWClient)

@pytest.fixture
def mock_project():
    return flywheel.Project(label=FAKE_PROJECT_LABEL, id=FAKE_PROJECT_ID, group=FAKE_GROUP)

@pytest.fixture
def mock_sdk_client(mock_project):
    sdk_client = MagicMock(spc=flywheel.Client)
    sdk_client.get_project.return_value = mock_project
    sdk_client.lookup.return_value = mock_project
    sdk_client.projects.find.return_value = [mock_project]
    return sdk_client


def test_trigger_snapshots_on_filter(mock_client, mock_sdk_client, mock_project):
    """Test finding projects with a filter"""
    snapshotter = snapshot.Snapshotter(api_key=FAKE_KEY)
    snapshotter.sdk_client = mock_sdk_client
    snapshotter.snapshot_client = mock_client
    snapshotter.make_snapshot_on_project = MagicMock()

    test_filter = "label=Test Project"
    snapshotter.trigger_snapshots_on_filter(test_filter)
    print(mock_sdk_client.projects.find.call_args_list)
    mock_sdk_client.projects.find.assert_called_with(test_filter)
    snapshotter.make_snapshot_on_project.assert_called_with(mock_project)


def test_make_snapshot_on_project(mock_client, mock_sdk_client, mock_project):
    snapshotter = snapshot.Snapshotter(api_key=FAKE_KEY)
    snapshotter.sdk_client = mock_sdk_client
    snapshotter.snapshot_client = mock_client
    snapshotter.make_snapshot_on_id = MagicMock()

    # Test on project string
    project = "lookup/path"
    snapshotter.make_snapshot_on_project(project)
    # lookup functions that should have been called
    snapshotter.sdk_client.lookup.assert_called_with(project)
    snapshotter.sdk_client.lookup.assert_called_once()

    # Other functions that should not have been called
    assert snapshotter.sdk_client.get_project.call_count == 0
    snapshotter.make_snapshot_on_id.assert_called_with(FAKE_PROJECT_ID)

    # final call to make_snapshot_on_id should always happen
    assert snapshotter.make_snapshot_on_id.call_count == 1

    # test on lookup string
    project = FAKE_PROJECT_ID
    snapshotter.make_snapshot_on_project(project)
    # Get project functions that should have been called
    snapshotter.sdk_client.get_project.assert_called_with(project)
    snapshotter.sdk_client.get_project.assert_called_once()
    # Lookup has still been called only once
    snapshotter.sdk_client.lookup.assert_called_once()

    # final call to make_snapshot_on_id should always happen
    assert snapshotter.make_snapshot_on_id.call_count == 2

    # test on project object
    project = mock_project
    snapshotter.make_snapshot_on_project(project)
    # no additional calls made
    snapshotter.sdk_client.get_project.assert_called_once()
    snapshotter.sdk_client.lookup.assert_called_once()

    assert snapshotter.make_snapshot_on_id.call_count == 3


def test_make_snapshot_on_id(mock_client, mock_sdk_client):
    snapshotter = snapshot.Snapshotter(api_key=FAKE_KEY)
    snapshotter.sdk_client = mock_sdk_client
    snapshotter.snapshot_client = mock_client
    snapshotter.log_snapshot = MagicMock()
    snapshot.snapshot_utils.make_snapshot = MagicMock(return_value=FAKE_RESPONSE)

    response = snapshotter.make_snapshot_on_id(FAKE_PROJECT_ID)

    assert snapshot.snapshot_utils.make_snapshot.call_count == 1
    snapshot.snapshot_utils.make_snapshot.assert_called_with(mock_client, FAKE_PROJECT_ID)
    snapshotter.log_snapshot.assert_called_with(FAKE_RESPONSE)
    assert response == FAKE_RESPONSE


def test_log_snapshot(mock_client, mock_sdk_client):
    snapshotter = snapshot.Snapshotter(api_key=FAKE_KEY)
    snapshotter.sdk_client = mock_sdk_client
    snapshotter.snapshot_client = mock_client
    snapshotter.batch_name = FAKE_BATCH_NAME
    record = snapshot.snapshot_utils.SnapshotRecord(**FAKE_RESPONSE)
    snapshotter.log_snapshot(FAKE_RESPONSE)
    assert snapshotter.snapshots == [record]
    snapshotter.sdk_client.get_project.assert_called_with(FAKE_PROJECT_ID)


