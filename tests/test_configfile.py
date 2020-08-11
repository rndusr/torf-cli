import datetime
import os
import textwrap
from unittest.mock import patch

from torfcli import _errors, _vars, run


def test_default_configfile_doesnt_exist(cfgfile, mock_content, mock_create_mode):
    run([str(mock_content)])
    cfg = mock_create_mode.call_args[0][1]
    assert cfg['PATH'] == str(mock_content)


def test_custom_configfile_doesnt_exist(capsys, tmp_path, mock_content, mock_create_mode):
    cfgfile = tmp_path / 'wrong_special_config'
    with patch('sys.exit') as mock_exit:
        run(['--config', str(cfgfile), str(mock_content)])
    mock_exit.assert_called_once_with(_errors.Code.CONFIG)
    cap = capsys.readouterr()
    assert cap.out == ''
    assert cap.err == f'{_vars.__appname__}: {cfgfile}: No such file or directory\n'
    assert mock_create_mode.call_args is None


def test_config_unreadable(capsys, cfgfile, mock_content, mock_create_mode):
    cfgfile.write_text('something')
    import os
    os.chmod(cfgfile, 0o000)
    with patch('sys.exit') as mock_exit:
        run([str(mock_content)])
    mock_exit.assert_called_once_with(_errors.Code.CONFIG)
    cap = capsys.readouterr()
    assert cap.out == ''
    assert cap.err == f'{_vars.__appname__}: {cfgfile}: Permission denied\n'
    assert mock_create_mode.call_args is None


def test_custom_configfile(tmp_path, mock_content, mock_create_mode):
    cfgfile = tmp_path / 'special_config'
    cfgfile.write_text(textwrap.dedent('''
    comment = asdf
    '''))
    run(['--config', str(cfgfile), str(mock_content)])
    cfg = mock_create_mode.call_args[0][1]
    assert cfg['comment'] == 'asdf'


def test_noconfig_option(cfgfile, mock_content, mock_create_mode):
    cfgfile.write_text(textwrap.dedent('''
    private
    comment = Nobody shall see this!
    '''))
    run([str(mock_content), '--noconfig'])
    cfg = mock_create_mode.call_args[0][1]
    assert cfg['private'] is None
    assert cfg['comment'] is None


def test_cli_args_take_precedence(cfgfile, mock_content, mock_create_mode):
    cfgfile.write_text(textwrap.dedent('''
    xseed
    comment = Generic description
    date = 1970-01-01
    '''))
    run([str(mock_content), '--noxseed', '--date', '2001-02-03 04:05'])
    cfg = mock_create_mode.call_args[0][1]
    assert cfg['noxseed'] is True
    assert cfg['xseed'] is True
    assert cfg['comment'] == 'Generic description'
    assert cfg['date'] == datetime.datetime(2001, 2, 3, 4, 5)


def test_adding_to_list_via_cli(cfgfile, mock_content, mock_create_mode):
    cfgfile.write_text(textwrap.dedent('''
    tracker = https://foo
    tracker = https://bar
    '''))
    run([str(mock_content), '--tracker', 'https://baz'])
    cfg = mock_create_mode.call_args[0][1]
    assert cfg['tracker'] == ['https://foo', 'https://bar', 'https://baz']


def test_invalid_option_name(capsys, cfgfile, mock_content, mock_create_mode):
    cfgfile.write_text(textwrap.dedent('''
    foo = 123
    '''))
    with patch('sys.exit') as mock_exit:
        run([])
    mock_exit.assert_called_once_with(_errors.Code.CONFIG)
    cap = capsys.readouterr()
    assert cap.out == ''
    assert cap.err == f'{_vars.__appname__}: {cfgfile}: Unrecognized arguments: --foo\n'
    assert mock_create_mode.call_args is None


def test_invalid_boolean_name(capsys, cfgfile, mock_content, mock_create_mode):
    cfgfile.write_text(textwrap.dedent('''
    foo
    '''))
    with patch('sys.exit') as mock_exit:
        run([])
    mock_exit.assert_called_once_with(_errors.Code.CONFIG)
    cap = capsys.readouterr()
    assert cap.out == ''
    assert cap.err == f'{_vars.__appname__}: {cfgfile}: Unrecognized arguments: --foo\n'
    assert mock_create_mode.call_args is None


def test_illegal_configfile_arguments(capsys, cfgfile, mock_content, mock_create_mode):
    for arg in ('config', 'noconfig', 'profile', 'help', 'version'):
        cfgfile.write_text(textwrap.dedent(f'''
        {arg} = foo
        '''))
        with patch('sys.exit') as mock_exit:
            run(['--config', str(cfgfile), str(mock_content)])
        mock_exit.assert_called_once_with(_errors.Code.CONFIG)
        cap = capsys.readouterr()
        assert cap.out == ''
        assert cap.err == f'{_vars.__appname__}: {cfgfile}: Not allowed in config file: {arg}\n'
        assert mock_create_mode.call_args is None

    for arg in ('config', 'noconfig', 'profile', 'help', 'version'):
        cfgfile.write_text(textwrap.dedent(f'''
        {arg}
        '''))
        with patch('sys.exit') as mock_exit:
            run(['--config', str(cfgfile), str(mock_content)])
        mock_exit.assert_called_once_with(_errors.Code.CONFIG)
        cap = capsys.readouterr()
        assert cap.out == ''
        assert cap.err == f'{_vars.__appname__}: {cfgfile}: Not allowed in config file: {arg}\n'
        assert mock_create_mode.call_args is None


def test_environment_variable_resolution(cfgfile, mock_content, mock_create_mode):
    cfgfile.write_text(textwrap.dedent('''
    tracker = https://$DOMAIN:$PORT${PATH}
    date = $DATE
    comment = $UNDEFINED
    '''))

    with patch.dict(os.environ, {'DOMAIN': 'tracker.example.org',
                                 'PORT': '123',
                                 'PATH': '/announce',
                                 'DATE': '1999-12-31'}):
        run([str(mock_content)])
        cfg = mock_create_mode.call_args[0][1]
        assert cfg['tracker'] == ['https://tracker.example.org:123/announce']
        assert cfg['date'] == datetime.datetime(1999, 12, 31, 0, 0)
        assert cfg['comment'] == '$UNDEFINED'


def test_environment_variable_resolution_in_profile(cfgfile, mock_content, mock_create_mode):
    cfgfile.write_text(textwrap.dedent('''
    [foo]
    tracker = https://$DOMAIN:${PORT}/$PATH
    date = $DATE
    comment = $UNDEFINED
    '''))

    with patch.dict(os.environ, {'DOMAIN': 'tracker.example.org',
                                 'PORT': '123',
                                 'PATH': 'announce',
                                 'DATE': '1999-12-31'}):
        run([str(mock_content), '--profile', 'foo'])
        cfg = mock_create_mode.call_args[0][1]
        assert cfg['tracker'] == ['https://tracker.example.org:123/announce']
        assert cfg['date'] == datetime.datetime(1999, 12, 31, 0, 0)
        assert cfg['comment'] == '$UNDEFINED'


def test_escaping_dollar(cfgfile, mock_content, mock_create_mode):
    cfgfile.write_text(textwrap.dedent('''
    [one]
    comment = \\$COMMENT
    [two]
    comment = \\\\$COMMENT
    [three]
    comment = \\\\\\$COMMENT
    [four]
    comment = \\\\\\\\$COMMENT
    [five]
    comment = \\\\\\\\\\$COMMENT
    [six]
    comment = \\\\\\\\\\\\$COMMENT
    [seven]
    comment = \\\\\\\\\\\\\\$COMMENT
    '''))

    with patch.dict(os.environ, {'COMMENT': 'The comment.'}):
        run([str(mock_content), '--profile', 'one'])
        cfg = mock_create_mode.call_args[0][1]
        assert cfg['comment'] == '$COMMENT'

    with patch.dict(os.environ, {'COMMENT': 'The comment.'}):
        run([str(mock_content), '--profile', 'two'])
        cfg = mock_create_mode.call_args[0][1]
        assert cfg['comment'] == '\\The comment.'

    with patch.dict(os.environ, {'COMMENT': 'The comment.'}):
        run([str(mock_content), '--profile', 'three'])
        cfg = mock_create_mode.call_args[0][1]
        assert cfg['comment'] == '\\$COMMENT'

    with patch.dict(os.environ, {'COMMENT': 'The comment.'}):
        run([str(mock_content), '--profile', 'four'])
        cfg = mock_create_mode.call_args[0][1]
        assert cfg['comment'] == '\\\\The comment.'

    with patch.dict(os.environ, {'COMMENT': 'The comment.'}):
        run([str(mock_content), '--profile', 'five'])
        cfg = mock_create_mode.call_args[0][1]
        assert cfg['comment'] == '\\\\$COMMENT'

    with patch.dict(os.environ, {'COMMENT': 'The comment.'}):
        run([str(mock_content), '--profile', 'six'])
        cfg = mock_create_mode.call_args[0][1]
        assert cfg['comment'] == '\\\\\\The comment.'

    with patch.dict(os.environ, {'COMMENT': 'The comment.'}):
        run([str(mock_content), '--profile', 'seven'])
        cfg = mock_create_mode.call_args[0][1]
        assert cfg['comment'] == '\\\\\\$COMMENT'
