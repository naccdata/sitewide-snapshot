from fw_snapshots import TriggerSnapshot
import pytest
import fw_client
import flywheel
import mock
from mock import patch, MagicMock

@pytest.fixture
def mock_client():
    return MagicMock(spec=fw_client.FWClient)


def test_find_projects_with_filter(mock_client):
    """Test finding projects with a filter"""

    snapshotter = TriggerSnapshot.Snapshotter(client=mock_client)
    mock_client.get.return_value = [
        {"label": "Test Project", "id": "test_project_id"}
    ]
    projects = snapshotter.find_projects_with_filter("label=Test Project")
    assert len(projects) == 1
    assert projects[0]["label"] == "Test Project"
