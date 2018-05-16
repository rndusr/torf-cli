from torfcli._cli import run, CLIError
import pytest


def test_no_arguments():
    with pytest.raises(CLIError,
                       match=r'^torf: Missing PATH or --in argument \(see `torf -h`\)$'):
        run([])


def test_help(capsys):
    for arg in ('--help', '-h'):
        run([arg])
        cap = capsys.readouterr()
        from torfcli._cli import _HELP
        assert cap.out == _HELP + '\n'


def test_version(capsys):
    run(['--version'])
    cap = capsys.readouterr()
    from torfcli._cli import _VERSION_INFO
    assert cap.out == _VERSION_INFO + '\n'
