from types import SimpleNamespace

import pytest

from torfcli import _utils


def test_bytes2string__rounding():
    assert _utils.bytes2string(1.455 * 2**30) == '1.46 GiB'
    assert _utils.bytes2string(1.454 * 2**30) == '1.45 GiB'

def test_bytes2string__trailing_zeroes():
    assert _utils.bytes2string(1.5 * 2**30, trailing_zeros=True) == '1.50 GiB'
    assert _utils.bytes2string(1.5 * 2**30, trailing_zeros=False) == '1.5 GiB'

    assert _utils.bytes2string(1 * 2**30, trailing_zeros=True) == '1.00 GiB'
    assert _utils.bytes2string(1 * 2**30, trailing_zeros=False) == '1 GiB'

    assert _utils.bytes2string(10 * 2**30, trailing_zeros=True) == '10.00 GiB'
    assert _utils.bytes2string(10 * 2**30, trailing_zeros=False) == '10 GiB'


@pytest.mark.parametrize(
    argnames='torrent, cfg, exp_return_value',
    argvalues=(
        (None, {'out': 'user-given.torrent'}, 'user-given.torrent'),
        (SimpleNamespace(name='foo'), {'out': ''}, 'foo.torrent'),
        (SimpleNamespace(name='foo'), {'out': '', 'profile': ['this']}, 'foo.this.torrent'),
        (SimpleNamespace(name='foo'), {'out': '', 'profile': ['this', 'that']}, 'foo.this.that.torrent'),
    ),
    ids=lambda v: repr(v),
)
def test_get_torrent_filepath(torrent, cfg, exp_return_value):
    return_value = _utils.get_torrent_filepath(torrent, cfg)
    assert return_value == exp_return_value
