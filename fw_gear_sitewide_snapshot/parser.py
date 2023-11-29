"""Parser module to parse gear config.json."""
from typing import Tuple

import utils
from flywheel_gear_toolkit import GearToolkitContext


# This function mainly parses gear_context's config.json file and returns relevant
# inputs and options.
def parse_config(
    gear_context: GearToolkitContext,
) -> Tuple[str, str]:
    """[Summary]

    Returns:
        [type]: [description]
    """

    project_filter = gear_context.config.get("project filter")
    batch_name = gear_context.config.get("snapshot batch name")
    retry_failed = gear_context.get_input_path("retry failed")
    api_key = utils.get_api_key(gear_context.config_json)
    output_path = gear_context.output_dir
    save_file_out = output_path / "snapshot_report.csv"

    return debug, project_filter, batch_name, retry_failed, api_key, save_file_out
