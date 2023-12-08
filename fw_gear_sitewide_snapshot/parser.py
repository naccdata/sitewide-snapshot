"""Parser module to parse gear config.json."""

import os

import utils
from flywheel_gear_toolkit import GearToolkitContext


# This function mainly parses gear_context's config.json file and returns relevant
# inputs and options.
def parse_config(
    gear_context: GearToolkitContext,
) -> (str, str, os.Pathlike, str, str):
    """Parses necessary items out of the context object

    Args:
        gear_context (GearToolkitContext): The gear context object
    Returns:
        project_filter (str): The project filter
        batch_name (str): The snapshot batch name
        retry_failed (os.Pathlike): Path of previous gear output report to retry failed snapshots on
        api_key (str): Flywheel API key
        save_file_out (str): Output path for the snapshot report

    """

    project_filter = gear_context.config.get("project filter")
    batch_name = gear_context.config.get("snapshot batch name")
    retry_failed = gear_context.get_input_path("retry failed")
    api_key = utils.get_api_key(gear_context.config_json)
    output_path = gear_context.output_dir
    save_file_out = output_path / "snapshot_report.csv"

    return project_filter, batch_name, retry_failed, api_key, save_file_out
