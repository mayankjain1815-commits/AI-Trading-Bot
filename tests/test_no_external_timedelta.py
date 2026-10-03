"""Regression test: the bot must not depend on the external `timedelta`
PyPI package. That package (timedelta==2020.12.3) has been removed from
PyPI, so `pip install -r requirements.txt` / `pip install timedelta` fails
on a fresh machine, and `from timedelta import Timedelta` in tradingbot.py
raises ModuleNotFoundError. The stdlib `datetime.timedelta` provides the
same functionality used by tradingbot.py (subtracting N days from a
datetime)."""

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _imported_top_level_modules():
    tree = ast.parse((REPO_ROOT / "tradingbot.py").read_text())
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".")[0])
    return modules


def test_tradingbot_does_not_import_external_timedelta_package():
    assert "timedelta" not in _imported_top_level_modules()


def test_requirements_does_not_pin_external_timedelta_package():
    lines = (REPO_ROOT / "requirements.txt").read_text().splitlines()
    assert not any(line.split("==")[0].strip().lower() == "timedelta" for line in lines)


def test_readme_does_not_instruct_installing_external_timedelta():
    readme = (REPO_ROOT / "README.md").read_text()
    assert "pip install lumibot timedelta" not in readme


def test_timedelta_day_subtraction_semantics():
    from datetime import datetime, timedelta

    today = datetime(2024, 1, 5, 12, 30)
    three_days_prior = today - timedelta(days=3)
    assert three_days_prior.strftime("%Y-%m-%d") == "2024-01-02"
