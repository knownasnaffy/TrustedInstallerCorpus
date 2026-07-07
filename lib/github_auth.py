"""GitHub authentication via gh CLI."""

import subprocess


def get_token() -> str:
    """Return GitHub auth token from `gh auth token`.

    Raises:
        RuntimeError: gh CLI not installed or not authenticated.
    """
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        raise RuntimeError(
            "gh CLI not installed — install from https://cli.github.com/"
        )

    if result.returncode != 0:
        raise RuntimeError(
            f"gh CLI not authenticated — run `gh auth login` first (stderr: {result.stderr.strip()})"
        )

    return result.stdout.strip()
