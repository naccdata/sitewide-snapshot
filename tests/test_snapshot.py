from unittest.mock import MagicMock, patch

from fw_gear_sitewide_snapshot.snapshot import snapshot

from .snapshot_assets import (FAKE_BATCH_NAME, FAKE_DATE, FAKE_GROUP, FAKE_KEY,
                              FAKE_PROJECT_ID, FAKE_PROJECT_LABEL,
                              FAKE_RESPONSE, FAKE_SNAPSHOT_ID, mock_client,
                              mock_project, mock_sdk_client)


@patch("fw_client.FWClient")
@patch("flywheel.Client")
def test_trigger_snapshots_on_filter(
    patch_client, patch_sdk_client, mock_client, mock_sdk_client, mock_project
):
    """Test finding projects with a filter"""
    patch_client.return_value = mock_client
    patch_sdk_client.return_value = mock_sdk_client

    snapshotter = snapshot.Snapshotter(api_key=FAKE_KEY)
    snapshotter.sdk_client = mock_sdk_client
    snapshotter.make_snapshot_on_project = MagicMock()

    test_filter = "label=Test Project"
    snapshotter.trigger_snapshots_on_filter(test_filter)
    print(mock_sdk_client.projects.find.call_args_list)
    mock_sdk_client.projects.iter_find.assert_called_with(test_filter)
    snapshotter.make_snapshot_on_project.assert_called_with(mock_project)


@patch("fw_client.FWClient")
@patch("flywheel.Client")
def test_make_snapshot_on_project(
    patch_client, patch_sdk_client, mock_client, mock_sdk_client, mock_project
):
    patch_client.return_value = mock_client
    patch_sdk_client.return_value = mock_sdk_client

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


@patch("fw_client.FWClient")
@patch("flywheel.Client")
def test_make_snapshot_on_id(
    patch_client, patch_sdk_client, mock_client, mock_sdk_client
):
    patch_client.return_value = mock_client
    patch_sdk_client.return_value = mock_sdk_client

    with patch(
        "fw_gear_sitewide_snapshot.snapshot.snapshot_utils.make_snapshot"
    ) as util_mock:
        util_mock.return_value = FAKE_RESPONSE
        snapshotter = snapshot.Snapshotter(api_key=FAKE_KEY)
        snapshotter.sdk_client = mock_sdk_client
        snapshotter.snapshot_client = mock_client
        snapshotter.log_snapshot = MagicMock()
        response = snapshotter.make_snapshot_on_id(FAKE_PROJECT_ID)

        assert snapshot.snapshot_utils.make_snapshot.call_count == 1
        snapshot.snapshot_utils.make_snapshot.assert_called_with(
            mock_client, FAKE_PROJECT_ID
        )
        snapshotter.log_snapshot.assert_called_with(FAKE_RESPONSE)
        assert response == FAKE_RESPONSE


@patch("fw_client.FWClient")
@patch("flywheel.Client")
def test_log_snapshot(patch_client, patch_sdk_client, mock_client, mock_sdk_client):
    patch_client.return_value = mock_client
    patch_sdk_client.return_value = mock_sdk_client

    snapshotter = snapshot.Snapshotter(api_key=FAKE_KEY)
    snapshotter.sdk_client = mock_sdk_client
    snapshotter.snapshot_client = mock_client
    snapshotter.batch_name = FAKE_BATCH_NAME
    record = snapshot.snapshot_utils.SnapshotRecord(**FAKE_RESPONSE)
    snapshotter.log_snapshot(FAKE_RESPONSE)
    assert snapshotter.snapshots == [record]
    snapshotter.sdk_client.get_project.assert_called_with(FAKE_PROJECT_ID)
