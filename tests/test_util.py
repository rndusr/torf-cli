from torfcli import _util as util


def test_bytes2string__rounded_to_two_decimal_points():
    assert util.bytes2string(1.455*2**30) == '1.46 GiB'
    assert util.bytes2string(1.454*2**30) == '1.45 GiB'

def test_bytes2string__trailing_zeroes_after_point_are_removed():
    assert util.bytes2string(1.5*2**30) == '1.5 GiB'
    assert util.bytes2string(1*2**30) == '1 GiB'

def test_bytes2string__trailing_zeroes_before_point_are_preserved():
    assert util.bytes2string(10*2**30) == '10 GiB'
