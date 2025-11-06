"""Pytest fixtures for scraping integration tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from infrastructure.config import Settings


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    """Provide test settings with temporary storage."""
    return Settings(
        storage={"base_path": str(tmp_path), "pretty_json": True},
        auth={
            "session_file_name": "test_session.json",
            "login_url": os.getenv("PJN_URL", "https://scw.pjn.gov.ar"),
        },
    )


@pytest.fixture
def pjn_credentials() -> tuple[str, str] | None:
    """Get PJN credentials from environment.

    Returns None if credentials are not available, which will cause
    tests requiring credentials to be skipped.
    """
    usuario = os.getenv("PJN_USUARIO")
    password = os.getenv("PJN_PASSWORD")

    if not usuario or not password:
        return None

    return (usuario, password)


@pytest.fixture
def pjn_login_url() -> str:
    """Get PJN login URL from environment."""
    return os.getenv("PJN_URL", "https://scw.pjn.gov.ar")


@pytest.fixture
def skip_if_no_credentials(pjn_credentials: tuple[str, str] | None):
    """Skip test if PJN credentials are not available."""
    if pjn_credentials is None:
        pytest.skip("PJN credentials not available. Set PJN_USUARIO and PJN_PASSWORD env vars.")
