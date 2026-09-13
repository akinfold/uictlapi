import json

import pytest

from uictlapi import cli


def test_parse_kv_basic():
    res = cli._parse_kv(("a=1", "b: 2", "flag"))
    assert res == {"a": "1", "b": "2", "flag": ""}


def test_parse_auth_direct_and_file(tmp_path):
    assert cli._parse_auth("user:pass@host") == ("user", "pass", "host")
    p = tmp_path / "auth.txt"
    p.write_text("foo:bar@192.0.2.1\n")
    assert cli._parse_auth("@" + str(p)) == ("foo", "bar", "192.0.2.1")


def test_parse_auth_user_pass_uses_url_host(tmp_path):
    assert cli._parse_auth("user:secret", default_host="192.0.2.1") == (
        "user",
        "secret",
        "192.0.2.1",
    )
    p = tmp_path / "creds.txt"
    p.write_text("admin:s3cret\n")
    assert cli._parse_auth("@" + str(p), default_host="unifi.example") == (
        "admin",
        "s3cret",
        "unifi.example",
    )


def test_parse_auth_two_line_file(tmp_path):
    p = tmp_path / "creds.txt"
    p.write_text("admin\np@ss:word\n")
    assert cli._parse_auth("@" + str(p), default_host="192.0.2.1") == (
        "admin",
        "p@ss:word",
        "192.0.2.1",
    )


def test_parse_auth_three_line_file_includes_host(tmp_path):
    p = tmp_path / "creds.txt"
    p.write_text("admin\np@ss:word\n192.0.2.1\n")
    assert cli._parse_auth("@" + str(p)) == ("admin", "p@ss:word", "192.0.2.1")


def test_parse_auth_password_may_contain_at():
    assert cli._parse_auth("user:p@ss@host.example") == ("user", "p@ss", "host.example")


def test_parse_auth_invalid():
    assert cli._parse_auth("invalidstring") is None
    assert cli._parse_auth("user:pass") is None  # no host and no default_host
    # Single-line value with '@' is always treated as user:pass@host (use three-line
    # file if the password itself contains '@').
    assert cli._parse_auth("user:p@ss", default_host="h") == ("user", "p", "ss")


def test_host_from_url():
    assert (
        cli._host_from_url("https://192.168.1.1/proxy/network/v2/api") == "192.168.1.1"
    )
    assert cli._host_from_url("https://example.test:8443/api") == "example.test:8443"
    assert cli._host_from_url("https://[2001:db8::1]:8443/api") == "[2001:db8::1]:8443"
    assert cli._host_from_url("https://user:secret@example.test/api") is None
    assert cli._host_from_url("https://example.test:not-a-port/api") is None
    assert cli._host_from_url("https://[2001:db8::1/api") is None
    assert cli._host_from_url("not-a-url") is None


@pytest.mark.parametrize(
    "url",
    [
        "https://[2001:db8::1]garbage/api",
        "https://example.test:0/api",
        "https://example.test\\@other.test/api",
        "https://example.test\t/api",
        "https://example%40.test/api",
        "https://[v1.example]/api",
        "https://exa!mple.test/api",
    ],
)
def test_parse_request_url_rejects_ambiguous_authorities(url):
    assert cli._parse_request_url(url) is None


def test_run_rejects_malformed_url_before_request(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "_request",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("must not send")),
    )

    with pytest.raises(SystemExit) as exited:
        cli._run(
            method="GET",
            url="https://user:secret@example.test:bad/api",
            header=(),
            params=(),
            data=(),
            json_text=None,
            auth=None,
            timeout=1.0,
            allow_redirects=True,
            verify=True,
            output=None,
            pretty=False,
            show_headers=False,
            status_only=False,
        )

    assert exited.value.code == 2
    assert "Invalid URL" in capsys.readouterr().err


def test_auth_host_matches_url():
    assert cli._auth_host_matches_url("192.168.1.1", "https://192.168.1.1/proxy/x")
    assert cli._auth_host_matches_url("Unifi.Example", "https://unifi.example/api")
    assert cli._auth_host_matches_url("example.test", "https://example.test:443/api")
    assert cli._auth_host_matches_url(
        "example.test:8443", "https://example.test:8443/api"
    )
    assert cli._auth_host_matches_url("[2001:db8::1]", "https://[2001:db8::1]/api")
    assert not cli._auth_host_matches_url("192.168.1.1", "https://192.168.1.2/proxy/x")
    assert not cli._auth_host_matches_url(
        "example.test", "https://example.test:8443/api"
    )
    assert not cli._auth_host_matches_url("example.test", "http://example.test/api")
    assert cli._auth_host_matches_url(
        "example.test", "http://example.test/api", allow_insecure_http=True
    )
    assert not cli._auth_host_matches_url("192.168.1.1", "not-a-url")


def test_run_refuses_auth_host_mismatch(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "_request",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("must not send")),
    )

    with pytest.raises(SystemExit) as exited:
        cli._run(
            method="GET",
            url="https://192.168.1.2/proxy/network/v2/api",
            header=(),
            params=(),
            data=(),
            json_text=None,
            auth="user:pass@192.168.1.1",
            timeout=1.0,
            allow_redirects=True,
            verify=False,
            allow_insecure_http=False,
            output=None,
            pretty=False,
            show_headers=False,
            status_only=False,
        )
    assert exited.value.code == 2
    err = capsys.readouterr().err
    assert "does not match URL authority" in err
    assert "Refusing to send credentials" in err


def test_run_preserves_scheme_and_nondefault_port(monkeypatch):
    captured = {}

    class FakeAuth:
        def __init__(self, username, password, authority, **kwargs):
            captured["constructor"] = (username, password, authority, kwargs)

        def is_controller_url(self, url):
            captured["matched_url"] = url
            return True

    def fake_request(**kwargs):
        captured["request_auth"] = kwargs["auth"]
        return _make_dummy_response()

    monkeypatch.setattr(cli, "UnifiControllerAuth", FakeAuth)
    monkeypatch.setattr(cli, "_request", fake_request)
    monkeypatch.setattr(cli, "_print_response", lambda *args, **kwargs: None)

    cli._run(
        method="GET",
        url="https://example.test:8443/api",
        header=(),
        params=(),
        data=(),
        json_text=None,
        auth="user:secret@example.test:8443",
        timeout=1.0,
        allow_redirects=True,
        verify=True,
        allow_insecure_http=False,
        output=None,
        pretty=False,
        show_headers=False,
        status_only=False,
    )

    username, password, authority, kwargs = captured["constructor"]
    assert (username, password, authority) == (
        "user",
        "secret",
        "example.test:8443",
    )
    assert kwargs == {"scheme": "https", "allow_insecure_http": False}
    assert captured["matched_url"] == "https://example.test:8443/api"
    assert isinstance(captured["request_auth"], FakeAuth)


def test_run_requires_explicit_opt_in_for_http_auth(monkeypatch, capsys):
    class FakeAuth:
        def __init__(self, username, password, authority, **kwargs):
            if kwargs["scheme"] == "http" and not kwargs["allow_insecure_http"]:
                raise ValueError("HTTP authentication is disabled")

    monkeypatch.setattr(cli, "UnifiControllerAuth", FakeAuth)
    monkeypatch.setattr(
        cli,
        "_request",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("must not send")),
    )

    with pytest.raises(SystemExit) as exited:
        cli._run(
            method="GET",
            url="http://example.test/api",
            header=(),
            params=(),
            data=(),
            json_text=None,
            auth="user:secret@example.test",
            timeout=1.0,
            allow_redirects=True,
            verify=True,
            allow_insecure_http=False,
            output=None,
            pretty=False,
            show_headers=False,
            status_only=False,
        )

    assert exited.value.code == 2
    assert "Invalid authentication target" in capsys.readouterr().err


def test_run_fails_closed_with_legacy_auth_dependency(monkeypatch, capsys):
    class LegacyAuth:
        def __init__(self, username, password, authority, **kwargs):
            if kwargs:
                raise TypeError("unexpected keyword argument 'scheme'")

    monkeypatch.setattr(cli, "UnifiControllerAuth", LegacyAuth)
    monkeypatch.setattr(
        cli,
        "_request",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("must not send")),
    )

    with pytest.raises(SystemExit) as exited:
        cli._run(
            method="GET",
            url="https://example.test/api",
            header=(),
            params=(),
            data=(),
            json_text=None,
            auth="user:synthetic-secret@example.test",
            timeout=1.0,
            allow_redirects=True,
            verify=True,
        )

    assert exited.value.code == 2
    assert "lacks the required exact-origin security API" in capsys.readouterr().err


def test_load_json_string_and_file_and_plain(tmp_path):
    assert cli._load_json('{"x":1}') == {"x": 1}
    p = tmp_path / "data.json"
    p.write_text('["a", 1]')
    assert cli._load_json("@" + str(p)) == ["a", 1]
    assert cli._load_json("not a json") == "not a json"


def test_request_uses_json_and_auth(monkeypatch):
    captured = {}

    def fake_request(method, url, **kwargs):
        captured["method"] = method
        captured["url"] = url
        captured["kwargs"] = kwargs

        class Dummy:
            pass

        return Dummy()

    monkeypatch.setattr(cli.requests, "request", fake_request)

    auth = object()

    cli._request(
        method="POST",
        url="http://example.test",
        headers={"H": "v"},
        params={"q": "1"},
        data=[],
        json_body={"a": 1},
        auth=auth,
        timeout=5,
        allow_redirects=True,
        verify=False,
    )

    assert captured["method"] == "POST"
    assert captured["url"] == "http://example.test"
    assert captured["kwargs"]["json"] == {"a": 1}
    assert "data" not in captured["kwargs"]
    assert captured["kwargs"]["auth"] is auth


def test_request_data_file_and_multiple(monkeypatch, tmp_path):
    calls = []

    def fake_request(method, url, **kwargs):
        calls.append(kwargs)

        class Dummy:
            pass

        return Dummy()

    monkeypatch.setattr(cli.requests, "request", fake_request)

    f = tmp_path / "bin.dat"
    f.write_bytes(b"binarycontent")

    # single data file -> bytes body
    cli._request(
        method="PUT",
        url="http://x.test",
        headers={},
        params={},
        data=[f"@{f}"],
        json_body=None,
        auth=None,
        timeout=None,
        allow_redirects=True,
        verify=True,
    )
    assert calls[0]["data"] == b"binarycontent"

    # multiple data entries -> dict
    calls.clear()
    cli._request(
        method="PUT",
        url="http://x.test",
        headers={},
        params={},
        data=["k=1", "v:2"],
        json_body=None,
        auth=None,
        timeout=None,
        allow_redirects=True,
        verify=True,
    )
    assert calls[0]["data"] == {"k": "1", "v": "2"}


def _make_dummy_response(status=200, content=b'{"ok":true}', headers=None, reason="OK"):
    class Raw:
        version = "1.1"

    class DummyResp:
        def __init__(self):
            self.status_code = status
            self.reason = reason
            self.headers = headers or {"Content-Type": "application/json"}
            self.content = content
            self.raw = Raw()

        def json(self):
            return json.loads(self.content.decode("utf-8"))

        @property
        def text(self):
            try:
                return self.content.decode("utf-8")
            except Exception:
                return None

    return DummyResp()


def test_print_response_pretty_and_headers(capsys):
    r = _make_dummy_response()
    cli._print_response(
        r, show_headers=True, pretty=True, output=None, status_only=False
    )
    out = capsys.readouterr().out
    assert "HTTP/" in out
    assert '"ok": true' in out


def test_print_response_output_and_status_only(tmp_path, capsys):
    r = _make_dummy_response(
        content=b"binarydata", headers={"Content-Type": "application/octet-stream"}
    )
    out_file = tmp_path / "out.bin"
    cli._print_response(
        r, show_headers=False, pretty=False, output=str(out_file), status_only=False
    )
    assert out_file.read_bytes() == b"binarydata"

    # status_only prints only status code
    cli._print_response(
        _make_dummy_response(status=404, content=b""),
        show_headers=False,
        pretty=False,
        output=None,
        status_only=True,
    )
    out = capsys.readouterr().out
    assert "404" in out


def test_cli_version():
    from click.testing import CliRunner
    from uictlapi import __version__
    from uictlapi.cli import cli as cli_group

    result = CliRunner().invoke(cli_group, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_cli_help_describes_credentials_and_exit_codes():
    from click.testing import CliRunner
    from uictlapi.cli import cli as cli_group

    result = CliRunner().invoke(cli_group, ["--help"])
    assert result.exit_code == 0
    assert "username, password, host" in result.output
    assert "must match the request URL" in result.output
    assert "--ca-bundle PATH" in result.output
    assert "--allow-insecure-http" in result.output
    assert "Exit codes:" in result.output
    assert "uictlapi get -a @auth" in result.output


def test_cli_secure_defaults_and_negative_flags(monkeypatch):
    from click.testing import CliRunner
    from uictlapi.cli import cli as cli_group

    calls = []

    def fake_request(**kwargs):
        calls.append(kwargs)
        return _make_dummy_response()

    monkeypatch.setattr(cli, "_request", fake_request)
    monkeypatch.setattr(cli, "_print_response", lambda *args, **kwargs: None)

    runner = CliRunner()
    result = runner.invoke(cli_group, ["get", "https://example.test/api"])
    assert result.exit_code == 0
    assert calls[-1]["verify"] is True
    assert calls[-1]["allow_redirects"] is True

    result = runner.invoke(
        cli_group,
        [
            "get",
            "--no-verify",
            "--no-allow-redirects",
            "--no-pretty",
            "https://example.test/api",
        ],
    )
    assert result.exit_code == 0
    assert calls[-1]["verify"] is False
    assert calls[-1]["allow_redirects"] is False
