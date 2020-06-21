import os
from unittest.mock import patch

import pytest

from torfcli import _errors as err
from torfcli import _vars, run


@pytest.mark.parametrize('hr_enabled', (True, False), ids=('human_readable=True', 'human_readable=False'))
def test_creating_prints_performance_summary_on_success(tmp_path, human_readable, hr_enabled, capsys, clear_ansi, regex):
    content_path = tmp_path / 'foo'
    content_path.write_text('bar')

    with human_readable(hr_enabled):
        run([str(content_path)])

    cap = capsys.readouterr()
    if hr_enabled:
        pattern = (r'\s*Progress  100.00 % \| \d+:\d{2}:\d{2} total \| \s*\d+\.\d{2} [KMGT]iB/s\n'
                   r'\s*Info Hash  [0-9a-f]{40}\n'
                   r'\s*Magnet  magnet:\?xt=urn:btih:[0-9a-f]{40}&dn=foo&xl=3\n'
                   r'\s*Torrent  foo.torrent\n$')
        assert clear_ansi(cap.out) == regex(pattern), clear_ansi(cap.out)
    else:
        pattern = (r'\nProgress\t100\.000\t\d+\t\d+\t\d+\t\d+\t\d+\t' + str(content_path) + '\n'
                   r'Info Hash\t[0-9a-f]{40}\n'
                   r'Magnet\tmagnet:\?xt=urn:btih:[0-9a-f]{40}&dn=foo&xl=3\n'
                   r'Torrent\tfoo.torrent\n$')
        assert cap.out == regex(pattern), cap.out


@pytest.mark.parametrize('hr_enabled', (True, False), ids=('human_readable=True', 'human_readable=False'))
def test_creating_keeps_progress_when_aborted(tmp_path, human_readable, hr_enabled, capsys, clear_ansi, monkeypatch, regex):
    content_path = tmp_path / 'foo'
    content_path.write_bytes(os.urandom(int(1e6)))

    import torfcli
    if hr_enabled:
        status_reporter_cls = torfcli._ui._HumanStatusReporter
    else:
        status_reporter_cls = torfcli._ui._MachineStatusReporter

    class MockStatusReporter(status_reporter_cls):
        def generate_callback(self, torrent, filepath, pieces_done, pieces_total):
            if pieces_done / pieces_total >= 0.5:
                raise KeyboardInterrupt()
            else:
                super().generate_callback(torrent, filepath, pieces_done, pieces_total)

    monkeypatch.setattr(torfcli._ui, status_reporter_cls.__name__, MockStatusReporter)
    monkeypatch.setattr(torfcli._main, 'PROGRESS_INTERVAL', 0)

    with human_readable(hr_enabled):
        with patch('sys.exit') as mock_exit:
            run([str(content_path)])
    mock_exit.assert_called_once_with(err.Code.ABORTED)
    cap = capsys.readouterr()
    assert cap.err == f'{_vars.__appname__}: Aborted\n'

    if hr_enabled:
        pattern = (r'\s*Progress  \d+:\d{2}:\d{2} elapsed \| \d+:\d{2}:\d{2} left \| '
                   r'\d+:\d{2}:\d{2} total \| ETA: \d{2}:\d{2}:\d{2}'
                   r'\d{1,2}\.\d{2} % ▕foo\s+▏ \s*\d+\.\d{2} [KMGT]iB/s\n\n$')
        assert clear_ansi(cap.out) == regex(pattern), clear_ansi(cap.out)
    else:
        pattern = (r'\nProgress\t\d+\.\d+\t\d+\t\d+\t\d+\t\d+\t\d+\t' + str(content_path) + '\n$')
        assert cap.out == regex(pattern), cap.out


@pytest.mark.parametrize('hr_enabled', (True, False), ids=('human_readable=True', 'human_readable=False'))
def test_verifying_prints_performance_summary_on_success(tmp_path, human_readable, hr_enabled, capsys, clear_ansi, regex):
    content_path = tmp_path / 'foo'
    content_path.write_text('bar')
    run([str(content_path)])

    with human_readable(hr_enabled):
        run([str(content_path), '-i', 'foo.torrent'])

    cap = capsys.readouterr()
    if hr_enabled:
        pattern = r'\s*Progress  100.00 % \| \d+:\d{2}:\d{2} total \| \s*\d+\.\d{2} [KMGT]iB/s\n$'
        assert clear_ansi(cap.out) == regex(pattern)
    else:
        pattern = rf'Progress\t100.000\t\d+\t\d+\t\d+\t\d+\t\d+\t{content_path}\n$'
        assert clear_ansi(cap.out) == regex(pattern)


@pytest.mark.parametrize('hr_enabled', (True, False), ids=('human_readable=True', 'human_readable=False'))
def test_verifying_keeps_progress_when_aborted(tmp_path, human_readable, hr_enabled, capsys, clear_ansi, monkeypatch, regex):
    content_path = tmp_path / 'foo'
    content_path.write_bytes(os.urandom(int(1e6)))
    run([str(content_path)])

    import torfcli
    if hr_enabled:
        status_reporter_cls = torfcli._ui._HumanStatusReporter
    else:
        status_reporter_cls = torfcli._ui._MachineStatusReporter

    class MockStatusReporter(status_reporter_cls):
        def verify_callback(self, torrent, filepath, pieces_done, pieces_total,
                            piece_index, piece_hash, exception):
            if pieces_done / pieces_total >= 0.5:
                raise KeyboardInterrupt()
            else:
                super().verify_callback(torrent, filepath, pieces_done, pieces_total,
                                        piece_index, piece_hash, exception)

    monkeypatch.setattr(torfcli._ui, status_reporter_cls.__name__, MockStatusReporter)
    monkeypatch.setattr(torfcli._main, 'PROGRESS_INTERVAL', 0)

    with human_readable(hr_enabled):
        with patch('sys.exit') as mock_exit:
            run([str(content_path), '-i', 'foo.torrent'])
    mock_exit.assert_called_once_with(err.Code.ABORTED)
    cap = capsys.readouterr()
    assert cap.err == f'{_vars.__appname__}: Aborted\n'

    if hr_enabled:
        pattern = (r'\s*Progress  \d+:\d{2}:\d{2} elapsed \| \d+:\d{2}:\d{2} left \| '
                   r'\d+:\d{2}:\d{2} total \| ETA: \d{2}:\d{2}:\d{2}'
                   r'\d{1,2}\.\d{2} % ▕foo\s+▏ \s*\d+\.\d{2} [KMGT]iB/s\n\n$')
        assert clear_ansi(cap.out) == regex(pattern), clear_ansi(cap.out)
    else:
        pattern = (r'\nProgress\t\d+\.\d+\t\d+\t\d+\t\d+\t\d+\t\d+\t' + str(content_path) + '\n$')
        assert cap.out == regex(pattern), cap.out
