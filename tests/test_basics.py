from torfcli._main import run
from torfcli._errors import CLIError
import pytest


def test_no_arguments():
    with pytest.raises(CLIError,
                       match=r'^Missing PATH or --in \(see `torf -h`\)$'):
        run([])


def test_help(capsys):
    for arg in ('--help', '-h'):
        run([arg])
        cap = capsys.readouterr()
        from torfcli._vars import HELP_TEXT
        assert cap.out == HELP_TEXT + '\n'


def test_version(capsys):
    run(['--version'])
    cap = capsys.readouterr()
    from torfcli._vars import VERSION_TEXT
    assert cap.out == VERSION_TEXT + '\n'
