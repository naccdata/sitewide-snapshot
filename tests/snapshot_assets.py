import pytest
from mock import patch, MagicMock
import datetime
from ..fw_gear_sitewide_snapshot.fw_snapshot import snapshot_utils
import fw_client
import flywheel

FAKE_KEY = "latest.sse.flywheel.io:1234"
FAKE_PROJECT_ID = "123456789abc123456789abc"
FAKE_SNAPSHOT_ID = "snapshot_id"
FAKE_PROJECT_LABEL = "project label"
FAKE_GROUP = "group label"
FAKE_BATCH_NAME = "batch name"
FAKE_DATE = datetime.datetime.now()
FAKE_RESPONSE = {
    "_id": FAKE_SNAPSHOT_ID,
    "created": FAKE_DATE,
    "status": snapshot_utils.SnapshotState.pending,
    "parents": snapshot_utils.SnapshotParents(project=FAKE_PROJECT_ID),
    "group_label": FAKE_GROUP,
    "project_label": FAKE_PROJECT_LABEL,
    "batch_label": FAKE_BATCH_NAME,
    }

FAKE_RECORD = snapshot_utils.SnapshotRecord(**FAKE_RESPONSE)

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
