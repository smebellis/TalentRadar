from pathlib import Path

import yaml

_DEFAULT_CONFIG = Path(__file__).parent.parent / "config" / "search.yaml"


def update_location(location: str, config_path: Path = _DEFAULT_CONFIG) -> None:
    data = yaml.safe_load(config_path.read_text())
    data["search"]["location"] = location
    config_path.write_text(yaml.dump(data, default_flow_style=False))
