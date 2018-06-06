from torfcli._main import run
from torfcli._errors import ConfigError
import pytest
import textwrap


def test_unknown_profile(cfgfile, mock_content, mock_create_mode):
    cfgfile.write(textwrap.dedent('''
    [foo]
    comment = Foo!
    '''))
    with pytest.raises(ConfigError, match=rf'^{str(cfgfile)}: No such profile: bar$'):
        run([str(mock_content), '--profile', 'bar'])
    assert mock_create_mode.call_args is None


def test_profile_option(cfgfile, mock_content, mock_create_mode):
    cfgfile.write(textwrap.dedent('''
    xseed
    date = 2000-01-02
    [foo]
    comment = Foo!
    '''))
    run([str(mock_content)])
    cfg = mock_create_mode.call_args[0][0]
    assert cfg['xseed'] == True
    assert cfg['date'] == '2000-01-02'
    assert cfg['comment'] == ''

    run([str(mock_content), '--profile', 'foo'])
    cfg = mock_create_mode.call_args[0][0]
    assert cfg['xseed'] == True
    assert cfg['date'] == '2000-01-02'
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
    cfg = mock_create_mode.call_args[0][0]
    assert cfg['comment'] == 'Bar'
    assert cfg['private'] == True
    assert cfg['yes'] == True
    assert cfg['xseed'] == False

    run([str(mock_content), '--profile', 'bar', '--profile', 'foo'])
    cfg = mock_create_mode.call_args[0][0]
    assert cfg['comment'] == 'Foo'
    assert cfg['private'] == True
    assert cfg['yes'] == True
    assert cfg['xseed'] == False

    run([str(mock_content), '--profile', 'bar', '--profile', 'baz'])
    cfg = mock_create_mode.call_args[0][0]
    assert cfg['comment'] == 'Baz'
    assert cfg['private'] == False
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
    cfg = mock_create_mode.call_args[0][0]
    assert cfg['webseed'] == ['https://foo', 'https://bar']
    assert cfg['nowebseed'] == False

    run([str(mock_content), '--profile', 'bar', '--profile', 'foo'])
    cfg = mock_create_mode.call_args[0][0]
    assert cfg['webseed'] == ['https://bar', 'https://foo']
    assert cfg['nowebseed'] == False

    run([str(mock_content), '--profile', 'bar', '--profile', 'baz'])
    cfg = mock_create_mode.call_args[0][0]
    assert cfg['webseed'] == ['https://bar', 'https://baz']
    assert cfg['nowebseed'] == True

    run([str(mock_content), '--profile', 'bar', '--profile', 'baz', '--profile', 'foo'])
    cfg = mock_create_mode.call_args[0][0]
    assert cfg['webseed'] == ['https://bar', 'https://baz', 'https://foo']
    assert cfg['nowebseed'] == True


# def test_referencing_profile_in_profile(cfgfile, mock_content, mock_create_mode):
#     cfgfile.write(textwrap.dedent('''
#     [foo]
#     webseed = https://foo
#     profile = bar
#     [bar]
#     profile = baz
#     webseed = https://bar
#     [baz]
#     nowebseed
#     webseed = https://baz
#     '''))
#     run([str(mock_content), '--profile', 'foo'])
#     cfg = mock_create_mode.call_args[0][0]
#     assert cfg['webseed'] == ['https://baz', 'https://bar']


# def test_circular_reference(cfgfile, mock_content, mock_create_mode):
#     cfgfile.write(textwrap.dedent('''
#     [foo]
#     profile = bar
#     [bar]
#     profile = baz
#     [baz]
#     profile = foo
#     '''))
#     with pytest.raises(MainError, match=r'^--profile: foo: Circular reference: bar -> baz -> foo$'):
#         run([str(mock_content), '--profile', 'foo'])


# def test_self_reference(cfgfile, mock_content, mock_create_mode):
#     cfgfile.write(textwrap.dedent('''
#     [foo]
#     profile = foo
#     '''))
#     with pytest.raises(MainError, match=r'^--profile: foo: Circular reference: foo$'):
#         run([str(mock_content), '--profile', 'foo'])
