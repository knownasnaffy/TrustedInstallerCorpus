"""Tests for lib.url_utils.split_url — T1.1 Trusted Installer Corpus."""

import pytest

from lib.url_utils import split_url


class TestSplitUrl:
    """split_url(url) -> (domain, path)."""

    def test_basic_path(self) -> None:
        assert split_url("https://bun.sh/install") == ("bun.sh", "/install")

    def test_bare_domain_rustup(self) -> None:
        assert split_url("https://sh.rustup.rs") == ("sh.rustup.rs", "/")

    def test_bare_domain_docker(self) -> None:
        assert split_url("https://get.docker.com") == ("get.docker.com", "/")

    def test_deep_path(self) -> None:
        url = "https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh"
        assert split_url(url) == (
            "raw.githubusercontent.com",
            "/nvm-sh/nvm/v0.39.0/install.sh",
        )

    def test_query_string_preserved(self) -> None:
        assert split_url("https://example.com/install?v=2") == (
            "example.com",
            "/install?v=2",
        )

    def test_trailing_slash(self) -> None:
        assert split_url("https://example.com/install/") == (
            "example.com",
            "/install/",
        )

    def test_fragment_preserved(self) -> None:
        assert split_url("https://example.com/install#section") == (
            "example.com",
            "/install#section",
        )

    def test_port_in_domain(self) -> None:
        assert split_url("https://example.com:8080/install") == (
            "example.com:8080",
            "/install",
        )

    def test_http_scheme(self) -> None:
        assert split_url("http://install.pi-hole.net") == (
            "install.pi-hole.net",
            "/",
        )
