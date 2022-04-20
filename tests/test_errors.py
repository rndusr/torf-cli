import errno

import pytest
import torf

from torfcli import _errors as err


def test_CliError():
    for cls,args,kwargs in ((err.CliError, ('invalid argument: --foo',), {}),
                            (err.Error, ('invalid argument: --foo', err.Code.CLI), {}),
                            (err.Error, ('invalid argument: --foo',), {'code': err.Code.CLI})):
        with pytest.raises(err.CliError) as exc_info:
            raise cls(*args, **kwargs)
        assert exc_info.value.exit_code is err.Code.CLI
        assert str(exc_info.value) == 'invalid argument: --foo'


def test_ConfigError():
    for cls,args,kwargs in ((err.ConfigError, ('config error',), {}),
                            (err.Error, ('config error', err.Code.CONFIG), {}),
                            (err.Error, ('config error',), {'code': err.Code.CONFIG})):
        with pytest.raises(err.ConfigError) as exc_info:
            raise cls(*args, **kwargs)
        assert exc_info.value.exit_code is err.Code.CONFIG
        assert str(exc_info.value) == 'config error'


def test_ReadError():
    for cls,args,kwargs in ((err.ReadError, ('path/to/file: No such file or directory',), {}),
                            (err.Error, (torf.ReadError(errno.ENOENT, 'path/to/file'),), {}),
                            (err.Error, (torf.PathError('path/to/file', msg='No such file or directory'),), {}),
                            (err.Error, ('path/to/file: No such file or directory', err.Code.READ), {}),
                            (err.Error, ('path/to/file: No such file or directory',), {'code': err.Code.READ})):
        with pytest.raises(err.ReadError) as exc_info:
            raise cls(*args, **kwargs)
        assert exc_info.value.exit_code is err.Code.READ
        assert str(exc_info.value) == 'path/to/file: No such file or directory'


def test_WriteError():
    for cls,args,kwargs in ((err.WriteError, ('path/to/file: No space left on device',), {}),
                            (err.Error, (torf.WriteError(errno.ENOSPC, 'path/to/file'),), {}),
                            (err.Error, ('path/to/file: No space left on device', err.Code.WRITE), {}),
                            (err.Error, ('path/to/file: No space left on device',), {'code': err.Code.WRITE})):
        with pytest.raises(err.WriteError) as exc_info:
            raise cls(*args, **kwargs)
        assert exc_info.value.exit_code is err.Code.WRITE
        assert str(exc_info.value) == 'path/to/file: No space left on device'


def test_VerifyError():
    for cls,args,kwargs in ((err.VerifyError, (), {'content': 'path/to/content', 'torrent': 'path/to/torrent'}),
                            (err.Error, ('path/to/content does not satisfy path/to/torrent', err.Code.VERIFY), {}),
                            (err.Error, ('path/to/content does not satisfy path/to/torrent',), {'code': err.Code.VERIFY})):
        with pytest.raises(err.VerifyError) as exc_info:
            raise cls(*args, **kwargs)
        assert exc_info.value.exit_code is err.Code.VERIFY
        assert str(exc_info.value) == 'path/to/content does not satisfy path/to/torrent'

    with pytest.raises(err.VerifyError) as exc_info:
        raise err.Error(torf.VerifyNotDirectoryError('path/to/file'))
    assert exc_info.value.exit_code is err.Code.VERIFY
    assert str(exc_info.value) == 'path/to/file: Not a directory'

    with pytest.raises(err.VerifyError) as exc_info:
        raise err.Error(torf.VerifyIsDirectoryError('path/to/file'))
    assert exc_info.value.exit_code is err.Code.VERIFY
    assert str(exc_info.value) == 'path/to/file: Is a directory'

    with pytest.raises(err.VerifyError) as exc_info:
        raise err.Error(torf.VerifyFileSizeError('path/to/file', 123, 456))
    assert exc_info.value.exit_code is err.Code.VERIFY
    assert str(exc_info.value) == 'path/to/file: Too small: 123 instead of 456 bytes'
