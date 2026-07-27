from types import SimpleNamespace
from unittest.mock import patch

from hermes_cli.main import cmd_version


def test_version_is_local_and_uses_deepagent_brand(capsys):
    with patch("hermes_cli.update.is_release_install", return_value=True), \
         patch("hermes_cli.update.get_current_version", return_value="0.9.0-alpha.1"), \
         patch("hermes_cli.update._get_deepagent_home", return_value="/tmp/deepagent"), \
         patch("hermes_cli.update.fetch_latest_version") as fetch:
        cmd_version(SimpleNamespace())

    output = capsys.readouterr().out
    assert "DeepAgent v0.9.0-alpha.1" in output
    assert "DeepSeek Agent" not in output
    fetch.assert_not_called()
