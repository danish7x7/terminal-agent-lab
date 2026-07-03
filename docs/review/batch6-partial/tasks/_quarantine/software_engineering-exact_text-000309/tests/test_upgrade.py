import os
from pathlib import Path


def read(p):
    return Path(p).read_text()


def test_mathutils_upgraded():
    # mathutils: current=1.2.0, latest=1.3.0 -> upgrade
    expected = read('/tests/expected_mathutils.c')
    got = read('/output/mathutils.c')
    assert got == expected, f'mathutils.c mismatch:\nGOT:\n{got}\nEXPECTED:\n{expected}'


def test_strhelper_unchanged():
    # strhelper: current=2.0.0, latest=2.0.0 -> no upgrade (same version)
    original = read('/src/strhelper.c')
    got = read('/output/strhelper.c')
    assert got == original, f'strhelper.c should be unchanged\nGOT:\n{got}\nORIGINAL:\n{original}'


def test_netio_upgraded():
    # netio: current=0.9.3, latest=1.0.0 -> upgrade (major bump)
    expected = read('/tests/expected_netio.c')
    got = read('/output/netio.c')
    assert got == expected, f'netio.c mismatch:\nGOT:\n{got}\nEXPECTED:\n{expected}'
