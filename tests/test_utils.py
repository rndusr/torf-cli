from torfcli import _utils


def test_bytes2string__rounding():
    assert _utils.bytes2string(1.455*2**30) == '1.46 GiB'
    assert _utils.bytes2string(1.454*2**30) == '1.45 GiB'

def test_bytes2string__trailing_zeroes():
    assert _utils.bytes2string(1.5*2**30, trailing_zeros=True) == '1.50 GiB'
    assert _utils.bytes2string(1.5*2**30, trailing_zeros=False) == '1.5 GiB'

    assert _utils.bytes2string(1*2**30, trailing_zeros=True) == '1.00 GiB'
    assert _utils.bytes2string(1*2**30, trailing_zeros=False) == '1 GiB'

    assert _utils.bytes2string(10*2**30, trailing_zeros=True) == '10.00 GiB'
    assert _utils.bytes2string(10*2**30, trailing_zeros=False) == '10 GiB'
