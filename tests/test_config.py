from torfcli._cli import run, CLIError
import pytest
import os
import textwrap


def test_default_configfile_doesnt_exist(cfgfile, mock_content, mock_create_mode):
    run([str(mock_content)])
    assert mock_create_mode.call_count == 1


def test_config_unreadable(cfgfile, mock_content):
    cfgfile.write('something')
    os.chmod(cfgfile, 0o000)
    with pytest.raises(CLIError,
                       match=f"^torf: {str(cfgfile)}: Permission denied$"):
        run([str(mock_content)])


def test_nondefault_configfile_path(tmpdir, mock_content, mock_create_mode):
    cfgfile = tmpdir.join('special_config')
    cfgfile.write(textwrap.dedent('''
    comment = asdf
    '''))
    run(['--config', str(cfgfile), str(mock_content)])
    mock_create_mode_args = mock_create_mode.call_args[0][0]
    assert mock_create_mode_args['comment'] == 'asdf'


def test_nondefault_nonexisting_configfile_path(tmpdir, mock_content, mock_create_mode):
    cfgfile = tmpdir.join('wrong_special_config')
    with pytest.raises(CLIError,
                       match=f"^torf: {str(cfgfile)}: No such file or directory$"):
        run(['--config', str(cfgfile), str(mock_content)])


def test_cli_args_take_precedence(cfgfile, mock_content, mock_create_mode):
    cfgfile.write(textwrap.dedent('''
    xseed
    comment = Generic description
    date = 1970-01-01
    [foo]
    date = 2000-01-01 15:00
    tracker = http://asdf
    '''))
    run([str(mock_content), '--noxseed', '-f', 'foo', '--date', '2001-02-03 04:05'])
    mock_create_mode_args = mock_create_mode.call_args[0][0]
    assert mock_create_mode_args['xseed'] == True
    assert mock_create_mode_args['noxseed'] == True
    assert mock_create_mode_args['comment'] == 'Generic description'
    assert mock_create_mode_args['date'] == '2001-02-03 04:05'
    assert mock_create_mode_args['tracker'] == ['http://asdf']


def test_invalid_boolean_name_globally(cfgfile, mock_content):
    cfgfile.write(textwrap.dedent('''
    foo
    '''))
    with pytest.raises(CLIError,
                       match=f"^torf: {str(cfgfile)}: 'foo': Invalid argument$"):
        run([str(mock_content)])


def test_invalid_boolean_name_in_profile(cfgfile, mock_content):
    cfgfile.write(textwrap.dedent('''
    [foo]
    bar
    '''))
    with pytest.raises(CLIError,
                       match=f"^torf: {str(cfgfile)}: 'bar': Invalid argument$"):
        run([str(mock_content)])


def test_invalid_assignment_name_globally(cfgfile, mock_content):
    cfgfile.write(textwrap.dedent('''
    foo = 123
    '''))
    with pytest.raises(CLIError,
                       match=f"^torf: {str(cfgfile)}: 'foo': Invalid argument$"):
        run([str(mock_content)])


def test_invalid_assignment_name_in_profile(cfgfile, mock_content):
    cfgfile.write(textwrap.dedent('''
    [foo]
    bar = 123
    '''))
    with pytest.raises(CLIError,
                       match=f"^torf: {str(cfgfile)}: 'bar': Invalid argument$"):
        run([str(mock_content)])


def test_assigning_to_boolean_argument_globally(cfgfile, mock_content):
    cfgfile.write(textwrap.dedent('''
    private = something
    '''))
    with pytest.raises(CLIError,
                       match=f"^torf: {str(cfgfile)}: private = something: Assignment to option$"):
        run([str(mock_content)])


def test_assigning_to_boolean_argument_in_profile(cfgfile, mock_content):
    cfgfile.write(textwrap.dedent('''
    [foo]
    private = something
    '''))
    with pytest.raises(CLIError,
                       match=f"^torf: {str(cfgfile)}: private = something: Assignment to option$"):
        run([str(mock_content)])


def test_comments(cfgfile, mock_content, mock_create_mode):
    cfgfile.write(textwrap.dedent('''
    # This is a mock config file
    date = 1970-01-01
    # The next line is empty

    # A boolean value works like this
    private
    # And here's comment
    comment=A comment
    '''))
    run([str(mock_content), '-o', 'test.torrent'])
    mock_create_mode_args = mock_create_mode.call_args[0][0]
    assert mock_create_mode_args['date'] == '1970-01-01'
    assert mock_create_mode_args['private'] == True
    assert mock_create_mode_args['comment'] == 'A comment'


def test_optional_quotes(cfgfile, mock_content, mock_create_mode):
    for comment_cfg,comment_exp in ((' A comment ', 'A comment'),
                                    ("' A comment '", ' A comment '),
                                    ('" A comment "', ' A comment '),
                                    ('\' A comment "', '\' A comment "')):
        cfgfile.write(textwrap.dedent(f'''
        comment = {comment_cfg}
        '''))
        run([str(mock_content)])
        mock_create_mode_args = mock_create_mode.call_args[0][0]
        assert mock_create_mode_args['comment'] == comment_exp


def test_multiple_assignments_create_list(cfgfile, mock_content, mock_create_mode):
    cfgfile.write(textwrap.dedent('''
    tracker = http://1.test.local
    '''))
    run([str(mock_content)])
    mock_create_mode_args = mock_create_mode.call_args[0][0]
    assert mock_create_mode_args['tracker'] == ['http://1.test.local']

    cfgfile.write(textwrap.dedent('''
    tracker = http://1.test.local
    tracker = http://2.test.local
    '''))
    run([str(mock_content)])
    mock_create_mode_args = mock_create_mode.call_args[0][0]
    assert mock_create_mode_args['tracker'] == ['http://1.test.local', 'http://2.test.local']


def test_multiple_assignments_to_nonlist(cfgfile, mock_content, mock_create_mode):
    cfgfile.write(textwrap.dedent('''
    date = 1970
    date = 2000
    '''))
    with pytest.raises(CLIError,
                       match=f"^torf: {str(cfgfile)}: date = '1970', '2000': Multiple values not allowed$"):
        run([str(mock_content)])


def test_single_profile(cfgfile, mock_content, mock_create_mode):
    cfgfile.write(textwrap.dedent('''
    date = 1970-01-01
    comment = arf

    [foo]
    private
    tracker = http://some.tracker/foo
    nocomment

    [bar]
    date = 2000-01-01
    tracker = http://some.other.tracker/bar
    tracker = http://some.other.tracker/baz
    nocreator
    '''))
    run([str(mock_content)])
    mock_create_mode_args = mock_create_mode.call_args[0][0]
    assert mock_create_mode_args['date'] == '1970-01-01'
    assert mock_create_mode_args['tracker'] == []
    assert mock_create_mode_args['private'] == False
    assert mock_create_mode_args['comment'] == 'arf'
    assert mock_create_mode_args['nocomment'] == False

    run(['--profile', 'foo', str(mock_content)])
    mock_create_mode_args = mock_create_mode.call_args[0][0]
    assert mock_create_mode_args['date'] == '1970-01-01'
    assert mock_create_mode_args['tracker'] == ['http://some.tracker/foo']
    assert mock_create_mode_args['private'] == True
    assert mock_create_mode_args['comment'] == ''
    assert mock_create_mode_args['nocomment'] == True

    run(['--profile', 'bar', str(mock_content)])
    mock_create_mode_args = mock_create_mode.call_args[0][0]
    assert mock_create_mode_args['date'] == '2000-01-01'
    assert mock_create_mode_args['tracker'] == ['http://some.other.tracker/bar', 'http://some.other.tracker/baz']
    assert mock_create_mode_args['private'] == False
    assert mock_create_mode_args['comment'] == 'arf'
    assert mock_create_mode_args['nocomment'] == False
    assert mock_create_mode_args['nocreator'] == True


def test_multiple_profiles(cfgfile, mock_content, mock_create_mode):
    cfgfile.write(textwrap.dedent('''
    date = 1970-01-01
    comment = arf

    [foo]
    private
    nocomment

    [bar]
    date = 2000-01-01
    tracker = http://some.other.tracker/bar
    tracker = http://some.other.tracker/baz
    nocreator
    '''))
    run(['--profile', 'foo', '--profile', 'bar', str(mock_content)])
    mock_create_mode_args = mock_create_mode.call_args[0][0]
    assert mock_create_mode_args['date'] == '2000-01-01'
    assert mock_create_mode_args['tracker'] == ['http://some.other.tracker/bar', 'http://some.other.tracker/baz']
    assert mock_create_mode_args['private'] == True
    assert mock_create_mode_args['comment'] == ''
    assert mock_create_mode_args['nocomment'] == True
    assert mock_create_mode_args['nocreator'] == True

    run(['--profile', 'bar', '--profile', 'foo', str(mock_content)])
    mock_create_mode_args = mock_create_mode.call_args[0][0]
    assert mock_create_mode_args['date'] == '2000-01-01'
    assert mock_create_mode_args['tracker'] == ['http://some.other.tracker/bar', 'http://some.other.tracker/baz']
    assert mock_create_mode_args['private'] == True
    assert mock_create_mode_args['comment'] == ''
    assert mock_create_mode_args['nocomment'] == True
    assert mock_create_mode_args['nocreator'] == True


def test_unknown_profile(cfgfile, mock_content, mock_create_mode):
    cfgfile.write(textwrap.dedent('''
    [foo]

    [bar]
    '''))
    with pytest.raises(CLIError,
                       match=f"^torf: {str(cfgfile)}: 'baz': No such profile$"):
        run(['--profile', 'baz', str(mock_content)])


def test_referencing_profile_in_profile(cfgfile, mock_content, mock_create_mode):
    cfgfile.write(textwrap.dedent('''
    date = 1970-01-01

    [foo]
    profile = noimg

    [bar]
    profile = friendly
    profile = noimg

    [noimg]
    exclude = *.jpg
    exclude = *.png

    [friendly]
    comment = 'I like you.'
    '''))
    run(['--profile', 'foo', str(mock_content)])
    mock_create_mode_args = mock_create_mode.call_args[0][0]
    assert mock_create_mode_args['date'] == '1970-01-01'
    assert mock_create_mode_args['exclude'] == ['*.jpg', '*.png']
    assert mock_create_mode_args['comment'] == ''

    run(['--profile', 'bar', str(mock_content)])
    mock_create_mode_args = mock_create_mode.call_args[0][0]
    assert mock_create_mode_args['date'] == '1970-01-01'
    assert mock_create_mode_args['exclude'] == ['*.jpg', '*.png']
    assert mock_create_mode_args['comment'] == 'I like you.'


def test_adjusting_exclude_of_referenced_profile_in_profile(cfgfile, mock_content, mock_create_mode):
    cfgfile.write(textwrap.dedent('''
    [foo]
    profile = x
    exclude = *.txt

    [bar]
    profile = x
    noexclude
    exclude = *.txt

    [x]
    exclude = *.jpg
    '''))
    run(['--profile', 'foo', str(mock_content)])
    mock_create_mode_args = mock_create_mode.call_args[0][0]
    assert mock_create_mode_args['exclude'] == ['*.jpg', '*.txt']

    run(['--profile', 'bar', str(mock_content)])
    mock_create_mode_args = mock_create_mode.call_args[0][0]
    assert mock_create_mode_args['exclude'] == ['*.txt']


def test_adjusting_trackers_of_referenced_profile_in_profile(cfgfile, mock_content, mock_create_mode):
    cfgfile.write(textwrap.dedent('''
    [foo]
    profile = x
    tracker = http://additional.tracker

    [bar]
    profile = x
    notracker
    tracker = http://only.tracker

    [x]
    tracker = http://first.tracker
    tracker = http://second.tracker
    '''))
    run(['--profile', 'foo', str(mock_content)])
    mock_create_mode_args = mock_create_mode.call_args[0][0]
    assert mock_create_mode_args['tracker'] == ['http://first.tracker', 'http://second.tracker',
                                                'http://additional.tracker']

    run(['--profile', 'bar', str(mock_content)])
    mock_create_mode_args = mock_create_mode.call_args[0][0]
    assert mock_create_mode_args['tracker'] == ['http://only.tracker']


def test_adjusting_private_of_referenced_profile_in_profile(cfgfile, mock_content, mock_create_mode):
    cfgfile.write(textwrap.dedent('''
    [foo]
    profile = np
    private

    [bar]
    profile = p
    noprivate

    [p]
    private

    [np]
    noprivate
    '''))
    run(['--profile', 'foo', str(mock_content)])
    mock_create_mode_args = mock_create_mode.call_args[0][0]
    assert mock_create_mode_args['private'] == True
    assert mock_create_mode_args['noprivate'] == False

    run(['--profile', 'bar', str(mock_content)])
    mock_create_mode_args = mock_create_mode.call_args[0][0]
    assert mock_create_mode_args['private'] == False
    assert mock_create_mode_args['noprivate'] == True
