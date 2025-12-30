from pathlib import Path
import tomllib


def test_watsonx_settings_defaults_present():
    config_path = Path("src/cuga/configurations/models/settings.watsonx.toml")
    assert config_path.exists(), "Watsonx settings file must exist"

    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    model = data.get("model", {})

    assert model.get("id") == "ibm/granite-3-3-8b-instruct"
    assert model.get("decoding_method") == "greedy"
    assert model.get("max_new_tokens") == 512
    assert model.get("min_new_tokens") == 1
