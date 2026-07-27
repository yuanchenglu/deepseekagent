import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "audit-python-licenses.py"
SPEC = importlib.util.spec_from_file_location("audit_python_licenses", SCRIPT)
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def test_canonical_name_matches_python_distribution_rules():
    assert AUDIT._canonical_name("Fal_Client") == "fal-client"
    assert AUDIT._canonical_name("edge.tts") == "edge-tts"


def test_license_text_recognizes_supported_runtime_licenses():
    assert AUDIT._license_from_text(
        "Apache License, Version 2.0"
    ) == "Apache-2.0"
    assert AUDIT._license_from_text(
        "Permission is hereby granted, free of charge, to any person"
    ) == "MIT"
    assert AUDIT._license_from_text(
        "GNU LESSER GENERAL PUBLIC LICENSE Version 3"
    ) == "LGPL-3.0-only"


def test_unknown_license_text_fails_recognition():
    assert AUDIT._license_from_text("private proprietary terms") is None
