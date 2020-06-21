from unittest.mock import patch

from torfcli import _errors, _vars, run


def test_no_arguments(capsys):
    with patch('sys.exit') as mock_exit:
        run([])
    mock_exit.assert_called_once_with(_errors.Code.CLI)
    cap = capsys.readouterr()
    assert cap.out == ''
    assert cap.err == (f'{_vars.__appname__}: Not sure what to do '
                       f'(see USAGE in `{_vars.__appname__} -h`)\n')


def test_help(capsys):
    for arg in ('--help', '-h'):
        with patch('sys.exit') as mock_exit:
            run([arg])
        mock_exit.assert_not_called()
        cap = capsys.readouterr()
        from torfcli._config import HELP_TEXT
        assert cap.out == HELP_TEXT + '\n'
        assert cap.err == ''


def test_version(capsys):
    with patch('sys.exit') as mock_exit:
        run(['--version'])
    mock_exit.assert_not_called()
    cap = capsys.readouterr()
    from torfcli._config import VERSION_TEXT
    assert cap.out == VERSION_TEXT + '\n'
    assert cap.err == ''
