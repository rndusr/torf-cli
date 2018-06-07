from torfcli._main import run
from torfcli._errors import ConfigError
import pytest
import textwrap


def test_default_configfile_doesnt_exist(cfgfile, mock_content, mock_create_mode):
    run([str(mock_content)])
    cfg = mock_create_mode.call_args[0][0]
    assert cfg['PATH'] == str(mock_content)


def test_custom_configfile_doesnt_exist(tmpdir, mock_content, mock_create_mode):
    cfgfile = tmpdir.join('wrong_special_config')
    with pytest.raises(ConfigError, match=f"^{str(cfgfile)}: No such file or directory$"):
        run(['--config', str(cfgfile), str(mock_content)])
    assert mock_create_mode.call_args is None


def test_config_unreadable(cfgfile, mock_content, mock_create_mode):
    cfgfile.write('something')
    import os
    os.chmod(cfgfile, 0o000)
    with pytest.raises(ConfigError, match=f"^{str(cfgfile)}: Permission denied$"):
        run([str(mock_content)])
    assert mock_create_mode.call_args is None


def test_custom_configfile(tmpdir, mock_content, mock_create_mode):
    cfgfile = tmpdir.join('special_config')
    cfgfile.write(textwrap.dedent('''
    comment = asdf
    '''))
    run(['--config', str(cfgfile), str(mock_content)])
    cfg = mock_create_mode.call_args[0][0]
    assert cfg['comment'] == 'asdf'


def test_noconfig_option(cfgfile, mock_content, mock_create_mode):
    cfgfile.write(textwrap.dedent('''
    private
    comment = Nobody shall see this!
    '''))
    run([str(mock_content), '--noconfig'])
    cfg = mock_create_mode.call_args[0][0]
    assert cfg['private'] == False
    assert cfg['comment'] == ''


def test_cli_args_take_precedence(cfgfile, mock_content, mock_create_mode):
    cfgfile.write(textwrap.dedent('''
    xseed
    comment = Generic description
    date = 1970-01-01
    '''))
    run([str(mock_content), '--noxseed', '--date', '2001-02-03 04:05'])
    cfg = mock_create_mode.call_args[0][0]
    assert cfg['noxseed'] == True
    assert cfg['xseed'] == True
    assert cfg['comment'] == 'Generic description'
    assert cfg['date'] == '2001-02-03 04:05'


def test_adding_to_list_via_cli(cfgfile, mock_content, mock_create_mode):
    cfgfile.write(textwrap.dedent('''
    tracker = https://foo
    tracker = https://bar
    '''))
    run([str(mock_content), '--tracker', 'https://baz'])
    cfg = mock_create_mode.call_args[0][0]
    assert cfg['tracker'] == ['https://foo', 'https://bar', 'https://baz']


def test_invalid_option_name(cfgfile, mock_content, mock_create_mode):
    cfgfile.write(textwrap.dedent('''
    foo = 123
    '''))
    with pytest.raises(ConfigError, match=f"^{str(cfgfile)}: Unrecognized arguments: --foo"):
        run([str(mock_content)])
    assert mock_create_mode.call_args is None


def test_invalid_boolean_name(cfgfile, mock_content, mock_create_mode):
    cfgfile.write(textwrap.dedent('''
    foo
    '''))
    with pytest.raises(ConfigError, match=f"^{str(cfgfile)}: Unrecognized arguments: --foo$"):
        run([str(mock_content)])
    assert mock_create_mode.call_args is None


def test_illegal_configfile_arguments(cfgfile, mock_content, mock_create_mode):
    for arg in ('config', 'profile'):
        cfgfile.write(textwrap.dedent(f'''
        {arg} = foo
        '''))
        with pytest.raises(ConfigError, match=f'^{str(cfgfile)}: Not allowed in config file: {arg}$'):
            run(['--config', str(cfgfile), str(mock_content)])
        assert mock_create_mode.call_args is None

    for arg in ('noconfig', 'help', 'version'):
        cfgfile.write(textwrap.dedent(f'''
        {arg}
        '''))
        with pytest.raises(ConfigError, match=f'^{str(cfgfile)}: Not allowed in config file: {arg}$'):
            run(['--config', str(cfgfile), str(mock_content)])
        assert mock_create_mode.call_args is None
