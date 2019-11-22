from torfcli import _errors as err
import torf
import errno
import pytest

def test_CliError():
    for cls,args,kwargs in ((err.CliError, ('invalid argument: --foo',), {}),
                            (err.Error, ('invalid argument: --foo', err.Code.CLI), {}),
                            (err.Error, ('invalid argument: --foo',), {'code': err.Code.CLI})):
        print(f'>>> {cls.__name__}({args}, {kwargs})')
        with pytest.raises(err.CliError) as exc_info:
            raise cls(*args, **kwargs)
        assert exc_info.value.exit_code is err.Code.CLI
        assert str(exc_info.value) == 'invalid argument: --foo'


def test_ConfigError():
    for cls,args,kwargs in ((err.ConfigError, ('config error',), {}),
                            (err.Error, ('config error', err.Code.CONFIG), {}),
                            (err.Error, ('config error',), {'code': err.Code.CONFIG})):
        print(f'>>> {cls.__name__}({args}, {kwargs})')
        with pytest.raises(err.ConfigError) as exc_info:
            raise cls(*args, **kwargs)
        assert exc_info.value.exit_code is err.Code.CONFIG
        assert str(exc_info.value) == 'config error'


def test_ReadError():
    for cls,args,kwargs in ((err.ReadError, ('path/to/file: No such file or directory',), {}),
                            (err.Error, (torf.ReadError(errno.ENOENT, 'path/to/file'),), {}),
                            (err.Error, (torf.PathNotFoundError('path/to/file'),), {}),
                            (err.Error, ('path/to/file: No such file or directory', err.Code.READ), {}),
                            (err.Error, ('path/to/file: No such file or directory',), {'code': err.Code.READ})):
        print(f'>>> {cls.__name__}({args}, {kwargs})')
        with pytest.raises(err.ReadError) as exc_info:
            raise cls(*args, **kwargs)
        assert exc_info.value.exit_code is err.Code.READ
        assert str(exc_info.value) == 'path/to/file: No such file or directory'

    with pytest.raises(err.ReadError) as exc_info:
        raise err.Error(torf.PathEmptyError('path/to/file'))
    assert exc_info.value.exit_code is err.Code.READ
    assert str(exc_info.value) == 'path/to/file: Empty directory'


def test_WriteError():
    for cls,args,kwargs in ((err.WriteError, ('path/to/file: No space left on device',), {}),
                            (err.Error, (torf.WriteError(errno.ENOSPC, 'path/to/file'),), {}),
                            (err.Error, ('path/to/file: No space left on device', err.Code.WRITE), {}),
                            (err.Error, ('path/to/file: No space left on device',), {'code': err.Code.WRITE})):
        print(f'>>> {cls.__name__}({args}, {kwargs})')
        with pytest.raises(err.WriteError) as exc_info:
            raise cls(*args, **kwargs)
        assert exc_info.value.exit_code is err.Code.WRITE
        assert str(exc_info.value) == 'path/to/file: No space left on device'


def test_ParseError():
    for cls,args,kwargs in ((err.ParseError, ('parse error',), {}),
                            (err.Error, ('parse error', err.Code.PARSE), {}),
                            (err.Error, ('parse error',), {'code': err.Code.PARSE})):
        print(f'{cls.__name__}({args}, {kwargs})')
        with pytest.raises(err.ParseError) as exc_info:
            raise cls(*args, **kwargs)
        assert exc_info.value.exit_code is err.Code.PARSE
        assert str(exc_info.value) == 'parse error'

    with pytest.raises(err.ParseError) as exc_info:
        raise err.Error(torf.ParseError('path/to/file'))
    assert exc_info.value.exit_code is err.Code.PARSE
    assert str(exc_info.value) == 'path/to/file: Invalid torrent file format'

    with pytest.raises(err.ParseError) as exc_info:
        raise err.Error(torf.MetainfoError('missing pieces'))
    assert exc_info.value.exit_code is err.Code.PARSE
    assert str(exc_info.value) == 'Invalid metainfo: missing pieces'

    with pytest.raises(err.ParseError) as exc_info:
        raise err.Error(torf.URLError('htp://gugu'))
    assert exc_info.value.exit_code is err.Code.PARSE
    assert str(exc_info.value) == 'htp://gugu: Invalid URL'

    with pytest.raises(err.ParseError) as exc_info:
        raise err.Error(torf.PieceSizeError(123))
    assert exc_info.value.exit_code is err.Code.PARSE
    assert str(exc_info.value) == 'Piece size must be a power of 2: 123'


def test_VerifyError():
    for cls,args,kwargs in ((err.VerifyError, (), {'content': 'path/to/content', 'torrent': 'path/to/torrent'}),
                            (err.Error, ('path/to/content does not satisfy path/to/torrent', err.Code.VERIFY), {}),
                            (err.Error, ('path/to/content does not satisfy path/to/torrent',), {'code': err.Code.VERIFY})):
        print(f'{cls.__name__}({args}, {kwargs})')
        with pytest.raises(err.VerifyError) as exc_info:
            raise cls(*args, **kwargs)
        assert exc_info.value.exit_code is err.Code.VERIFY
        assert str(exc_info.value) == 'path/to/content does not satisfy path/to/torrent'

    with pytest.raises(err.VerifyError) as exc_info:
        raise err.Error(torf.VerifyNotDirectoryError('path/to/file'))
    assert exc_info.value.exit_code is err.Code.VERIFY
    assert str(exc_info.value) == 'path/to/file: Is a directory'

    with pytest.raises(err.VerifyError) as exc_info:
        raise err.Error(torf.VerifyIsDirectoryError('path/to/file'))
    assert exc_info.value.exit_code is err.Code.VERIFY
    assert str(exc_info.value) == 'path/to/file: Not a directory'

    with pytest.raises(err.VerifyError) as exc_info:
        raise err.Error(torf.VerifyFileSizeError('path/to/file', 123, 456))
    assert exc_info.value.exit_code is err.Code.VERIFY
    assert str(exc_info.value) == 'path/to/file: Too small: 123 instead of 456 bytes'
