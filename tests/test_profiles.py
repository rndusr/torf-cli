from torfcli import run
from torfcli import _errors as err
from torfcli import _vars

import pytest
from unittest.mock import patch
import textwrap
import datetime


def test_unknown_profile(capsys, cfgfile, mock_content, mock_create_mode):
    cfgfile.write(textwrap.dedent('''
    [foo]
    comment = Foo!
    '''))
    with patch('sys.exit') as mock_exit:
        run([str(mock_content), '--profile', 'bar'])
    mock_exit.assert_called_once_with(err.Code.CONFIG)
    cap = capsys.readouterr()
    assert cap.err == f'{_vars.__appname__}: {cfgfile}: No such profile: bar\n'
    assert mock_create_mode.call_args is None


def test_profile_option(cfgfile, mock_content, mock_create_mode):
    cfgfile.write(textwrap.dedent('''
    xseed
    date = 2000-01-02
    [foo]
    comment = Foo!
    '''))
    run([str(mock_content)])
    cfg = mock_create_mode.call_args[0][1]
    assert cfg['xseed'] == True
    assert cfg['date'] == datetime.datetime(2000, 1, 2)
    assert cfg['comment'] == None

    run([str(mock_content), '--profile', 'foo'])
    cfg = mock_create_mode.call_args[0][1]
    assert cfg['xseed'] == True
    assert cfg['date'] == datetime.datetime(2000, 1, 2)
    assert cfg['comment'] == 'Foo!'


def test_overloading_values(cfgfile, mock_content, mock_create_mode):
    cfgfile.write(textwrap.dedent('''
    [foo]
    comment = Foo
    private

    [bar]
    comment = Bar
    yes

    [baz]
    comment = Baz
    xseed
    '''))
    run([str(mock_content), '--profile', 'foo', '--profile', 'bar'])
    cfg = mock_create_mode.call_args[0][1]
    assert cfg['comment'] == 'Bar'
    assert cfg['private'] == True
    assert cfg['yes'] == True
    assert cfg['xseed'] == False

    run([str(mock_content), '--profile', 'bar', '--profile', 'foo'])
    cfg = mock_create_mode.call_args[0][1]
    assert cfg['comment'] == 'Foo'
    assert cfg['private'] == True
    assert cfg['yes'] == True
    assert cfg['xseed'] == False

    run([str(mock_content), '--profile', 'bar', '--profile', 'baz'])
    cfg = mock_create_mode.call_args[0][1]
    assert cfg['comment'] == 'Baz'
    assert cfg['private'] == None
    assert cfg['yes'] == True
    assert cfg['xseed'] == True


def test_list_value(cfgfile, mock_content, mock_create_mode):
    cfgfile.write(textwrap.dedent('''
    [foo]
    webseed = https://foo
    [bar]
    webseed = https://bar
    [baz]
    nowebseed
    webseed = https://baz
    '''))
    run([str(mock_content), '--profile', 'foo', '--profile', 'bar'])
    cfg = mock_create_mode.call_args[0][1]
    assert cfg['webseed'] == ['https://foo', 'https://bar']
    assert cfg['nowebseed'] == False

    run([str(mock_content), '--profile', 'bar', '--profile', 'foo'])
    cfg = mock_create_mode.call_args[0][1]
    assert cfg['webseed'] == ['https://bar', 'https://foo']
    assert cfg['nowebseed'] == False

    run([str(mock_content), '--profile', 'bar', '--profile', 'baz'])
    cfg = mock_create_mode.call_args[0][1]
    assert cfg['webseed'] == ['https://bar', 'https://baz']
    assert cfg['nowebseed'] == True

    run([str(mock_content), '--profile', 'bar', '--profile', 'baz', '--profile', 'foo'])
    cfg = mock_create_mode.call_args[0][1]
    assert cfg['webseed'] == ['https://bar', 'https://baz', 'https://foo']
    assert cfg['nowebseed'] == True


def test_illegal_configfile_arguments(capsys, cfgfile, mock_content, mock_create_mode):
    for arg in ('config', 'profile'):
        cfgfile.write(textwrap.dedent(f'''
        [foo]
        {arg} = foo
        '''))

        with patch('sys.exit') as mock_exit:
            run(['--config', str(cfgfile), str(mock_content)])
        mock_exit.assert_called_once_with(err.Code.CONFIG)
        cap = capsys.readouterr()
        assert cap.err == f'{_vars.__appname__}: {cfgfile}: Not allowed in config file: {arg}\n'
        assert mock_create_mode.call_args is None


    for arg in ('noconfig', 'help', 'version'):
        cfgfile.write(textwrap.dedent(f'''
        [foo]
        {arg}
        '''))
        with patch('sys.exit') as mock_exit:
            run(['--config', str(cfgfile), str(mock_content)])
        mock_exit.assert_called_once_with(err.Code.CONFIG)
        cap = capsys.readouterr()
        assert cap.err == f'{_vars.__appname__}: {cfgfile}: Not allowed in config file: {arg}\n'
        assert mock_create_mode.call_args is None
