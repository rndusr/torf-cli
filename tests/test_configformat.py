import textwrap

from torfcli._config import _readfile


def test_boolean_options(cfgfile):
    cfgfile.write_text(textwrap.dedent('''
    foo
    bar
    '''))
    cfg = _readfile(cfgfile)
    assert cfg == {'foo': True, 'bar': True}


def test_options_with_single_values(cfgfile):
    cfgfile.write_text(textwrap.dedent('''
    foo = 1
    bar = two
    '''))
    cfg = _readfile(cfgfile)
    assert cfg == {'foo': '1', 'bar': 'two'}


def test_options_with_empty_value(cfgfile):
    cfgfile.write_text(textwrap.dedent('''
    foo =
    '''))
    cfg = _readfile(cfgfile)
    assert cfg == {'foo': ''}


def test_options_with_list_values(cfgfile):
    cfgfile.write_text(textwrap.dedent('''
    foo = 1
    foo = 2
    foo = three
    '''))
    cfg = _readfile(cfgfile)
    assert cfg == {'foo': ['1', '2', 'three']}


def test_optional_quotes(cfgfile):
    for comment_cfg,comment_exp in ((' A comment ', 'A comment'),
                                    ("' A comment '", ' A comment '),
                                    ('" A comment "', ' A comment '),
                                    ('\' A comment "', '\' A comment "')):
        cfgfile.write_text(textwrap.dedent(f'''
        comment = {comment_cfg}
        '''))
        cfg = _readfile(cfgfile)
        assert cfg == {'comment': comment_exp}


def test_comments(cfgfile):
    cfgfile.write_text(textwrap.dedent('''
    # This is a config file
    date = 1970-01-01
    # The next line is empty

    # This is a boolean value
    private
    # And here's comment
    comment=A comment
    # Goodbye!
    '''))
    cfg = _readfile(cfgfile)
    assert cfg == {'date': '1970-01-01',
                   'private': True,
                   'comment': 'A comment'}


def test_sections(cfgfile):
    cfgfile.write_text(textwrap.dedent('''
    date = 1970-01-01
    x = 0

    [foo]
    x = 10
    date = never
    yup

    [bar]
    yup
    x = -100
    y = 25
    '''))
    cfg = _readfile(cfgfile)
    assert cfg == {'date': '1970-01-01',
                   'x': '0',
                   'foo': {'x': '10', 'date': 'never', 'yup': True},
                   'bar': {'x': '-100', 'y': '25', 'yup': True}}
