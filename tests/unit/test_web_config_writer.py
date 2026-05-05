from pathlib import Path
import yaml
import pytest

from web.config_writer import update_location


def test_update_location_changes_only_location(tmp_path):
    config_file = tmp_path / "search.yaml"
    config_file.write_text(
        "search:\n"
        "  location: 'Denver, CO'\n"
        "  remote: true\n"
        "  keywords: []\n"
    )

    update_location("Austin, TX", config_path=config_file)

    result = yaml.safe_load(config_file.read_text())
    assert result["search"]["location"] == "Austin, TX"
    assert result["search"]["remote"] is True
    assert result["search"]["keywords"] == []


def test_update_location_overwrites_previous_value(tmp_path):
    config_file = tmp_path / "search.yaml"
    config_file.write_text("search:\n  location: 'Denver, CO'\n")

    update_location("Seattle, WA", config_path=config_file)
    update_location("Chicago, IL", config_path=config_file)

    result = yaml.safe_load(config_file.read_text())
    assert result["search"]["location"] == "Chicago, IL"
