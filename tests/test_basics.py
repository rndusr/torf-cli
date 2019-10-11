from torfcli._main import run
from torfcli._errors import CLIError
from torfcli import _vars
import pytest


def test_no_arguments():
    with pytest.raises(CLIError,
                       match=('^Not sure what to do '
                              fr'\(see USAGE in `{_vars.__appname__} -h`\)$')):
        run([])


def test_help(capsys):
    for arg in ('--help', '-h'):
        run([arg])
        cap = capsys.readouterr()
        from torfcli._config import HELP_TEXT
        assert cap.out == HELP_TEXT + '\n'


def test_version(capsys):
    run(['--version'])
    cap = capsys.readouterr()
    from torfcli._config import VERSION_TEXT
    assert cap.out == VERSION_TEXT + '\n'
