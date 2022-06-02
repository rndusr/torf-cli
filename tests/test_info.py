import os
import re
from datetime import datetime
from unittest.mock import patch

from torfcli import _errors as err
from torfcli import _vars, run


def test_nonexisting_torrent_file(capsys):
    nonexising_path = '/no/such/file'
    with patch('sys.exit') as mock_exit:
        run(['-i', nonexising_path])
    mock_exit.assert_called_once_with(err.Code.READ)
    cap = capsys.readouterr()
    assert cap.err == f'{_vars.__appname__}: {nonexising_path}: No such file or directory\n'
    assert cap.out == ''


def test_insufficient_permissions(capsys, create_torrent):
    with create_torrent() as torrent_file:
        os.chmod(torrent_file, 0o000)
        with patch('sys.exit') as mock_exit:
            run(['-i', torrent_file])
        mock_exit.assert_called_once_with(err.Code.READ)
        cap = capsys.readouterr()
        assert cap.err == f'{_vars.__appname__}: {torrent_file}: Permission denied\n'
        assert cap.out == ''


def test_magnet(capsys, create_torrent, human_readable, clear_ansi, regex):
    with create_torrent(name='foo') as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex(r'^\s*Magnet  magnet:\?xt=urn:btih:[0-9a-z]{40}', flags=re.MULTILINE)
            assert cap.err == ''

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert cap.out == regex(r'^Magnet\tmagnet:\?xt=urn:btih:[0-9a-z]{40}', flags=re.MULTILINE)
            assert cap.err == ''


def test_nomagnet(capsys, create_torrent, human_readable, clear_ansi, regex):
    with create_torrent(name='foo') as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file, '--nomagnet'])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) != regex(r'^\s*Magnet', flags=re.MULTILINE)
            assert cap.err == ''

        with human_readable(False):
            run(['-i', torrent_file, '--nomagnet'])
            cap = capsys.readouterr()
            assert cap.out != regex(r'^Magnet', flags=re.MULTILINE)
            assert cap.err == ''


def test_name(capsys, create_torrent, human_readable, clear_ansi, regex):
    with create_torrent(name='foo') as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex(r'^\s*Name  foo$', flags=re.MULTILINE)
            assert cap.err == ''

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert cap.out == regex(r'^Name\tfoo$', flags=re.MULTILINE)
            assert cap.err == ''


def test_info_hash(capsys, create_torrent, human_readable, clear_ansi, regex):
    with create_torrent() as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex(r'^\s*Info Hash  [0-9a-z]{40}$', flags=re.MULTILINE)
            assert cap.err == ''

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert cap.out == regex(r'^Info Hash\t[0-9a-z]{40}$', flags=re.MULTILINE)
            assert cap.err == ''


def test_size(capsys, create_torrent, human_readable, clear_ansi, regex):
    with create_torrent() as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex(r'^\s*Size  [0-9]+ [KMGT]?i?B$', flags=re.MULTILINE)
            assert cap.err == ''

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert cap.out == regex(r'^Size\t[0-9]+$', flags=re.MULTILINE)
            assert cap.err == ''


def test_piece_size(capsys, create_torrent, human_readable, clear_ansi, regex):
    with create_torrent() as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex(r'^\s*Piece Size  [0-9]+ [KMGT]?i?B$', flags=re.MULTILINE)
            assert cap.err == ''

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert cap.out == regex(r'^Piece Size\t[0-9]+$', flags=re.MULTILINE)
            assert cap.err == ''


def test_piece_count(capsys, create_torrent, human_readable, clear_ansi, regex):
    with create_torrent() as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex(r'^\s*Piece Count  [0-9]+$', flags=re.MULTILINE)
            assert cap.err == ''

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert cap.out == regex(r'^Piece Count\t[0-9]+$', flags=re.MULTILINE)
            assert cap.err == ''


def test_single_line_comment(capsys, create_torrent, human_readable, clear_ansi, regex):
    with create_torrent(comment='This is my torrent.') as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex(r'^\s*Comment  This is my torrent\.$', flags=re.MULTILINE)
            assert cap.err == ''

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert cap.out == regex(r'^Comment\tThis is my torrent\.$', flags=re.MULTILINE)
            assert cap.err == ''

def test_multiline_comment(capsys, create_torrent, human_readable, clear_ansi, regex):
    comment = 'This is my torrent.\nShare it!'
    with create_torrent(comment=comment) as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex(r'^(\s*)Comment  This is my torrent\.\n'
                                                r'\1         Share it!$', flags=re.MULTILINE)
            assert cap.err == ''

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert cap.out == regex(r'^Comment\tThis is my torrent\.\tShare it!$', flags=re.MULTILINE)
            assert cap.err == ''


def test_creation_date(capsys, create_torrent, human_readable, clear_ansi, regex):
    date = datetime(2000, 5, 10, 0, 30, 45)
    with create_torrent(creation_date=date) as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex(r'^\s*Created  2000-05-10 00:30:45$', flags=re.MULTILINE)
            assert cap.err == ''

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            exp_timestamp = int(date.timestamp())
            assert cap.out == regex(rf'^Created\t{exp_timestamp}$', flags=re.MULTILINE)
            assert cap.err == ''


def test_created_by(capsys, create_torrent, human_readable, clear_ansi, regex):
    with create_torrent(created_by='foo') as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex(r'^\s*Created By  foo$', flags=re.MULTILINE)
            assert cap.err == ''

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert cap.out == regex(r'^Created By\tfoo$', flags=re.MULTILINE)
            assert cap.err == ''


def test_private(capsys, create_torrent, human_readable, clear_ansi, regex):
    with create_torrent(private=True) as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex(r'^\s*Private  yes$', flags=re.MULTILINE)
            assert cap.err == ''

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert cap.out == regex(r'^Private\tyes$', flags=re.MULTILINE)
            assert cap.err == ''

    with create_torrent(private=False) as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex(r'^\s*Private  no', flags=re.MULTILINE)
            assert cap.err == ''

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert cap.out == regex(r'^Private\tno', flags=re.MULTILINE)
            assert cap.err == ''


def test_trackers___single_tracker_per_tier(capsys, create_torrent, human_readable, clear_ansi, regex):
    trackers = ['http://tracker1.1', 'http://tracker2.1']
    with create_torrent(trackers=trackers) as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex(rf'^(\s*)Trackers  Tier 1: {trackers[0]}\n'
                                                rf'\1          Tier 2: {trackers[1]}$', flags=re.MULTILINE)
            assert cap.err == ''

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            exp_trackers = '\t'.join(trackers)
            assert cap.out == regex(rf'^Trackers\t{exp_trackers}$', flags=re.MULTILINE)
            assert cap.err == ''

def test_trackers___multiple_trackers_per_tier(capsys, create_torrent, human_readable, clear_ansi, regex):
    trackers = ['http://tracker1.1',
                ['http://tracker2.1', 'http://tracker2.2'],
                ['http://tracker3.1']]
    with create_torrent(trackers=trackers) as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex(r'^(\s*)Trackers  Tier 1: http://tracker1.1\n'
                                                r'\1          Tier 2: http://tracker2.1\n'
                                                r'\1                  http://tracker2.2\n'
                                                r'\1          Tier 3: http://tracker3.1$', flags=re.MULTILINE)
            assert cap.err == ''

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            exp_trackers = '\t'.join(('http://tracker1.1', 'http://tracker2.1',
                                      'http://tracker2.2', 'http://tracker3.1'))
            assert cap.out == regex(rf'^Trackers\t{exp_trackers}$', flags=re.MULTILINE)
            assert cap.err == ''


def test_webseeds(capsys, create_torrent, human_readable, clear_ansi, regex):
    webseeds = ['http://webseed1', 'http://webseed2']
    with create_torrent(webseeds=webseeds) as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex((rf'^(\s*)Webseeds  {webseeds[0]}\n'
                                                 rf'\1          {webseeds[1]}$'), flags=re.MULTILINE)
            assert cap.err == ''

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            exp_webseeds = '\t'.join(webseeds)
            assert cap.out == regex(rf'^Webseeds\t{exp_webseeds}$', flags=re.MULTILINE)
            assert cap.err == ''


def test_httpseeds(capsys, create_torrent, human_readable, clear_ansi, regex):
    httpseeds = ['http://httpseed1', 'http://httpseed2']
    with create_torrent(httpseeds=httpseeds) as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex((rf'^(\s*)HTTP Seeds  {httpseeds[0]}\n'
                                                 rf'\1            {httpseeds[1]}$'), flags=re.MULTILINE)
            assert cap.err == ''

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            exp_httpseeds = '\t'.join(httpseeds)
            assert cap.out == regex(rf'^HTTP Seeds\t{exp_httpseeds}$', flags=re.MULTILINE)
            assert cap.err == ''


def test_file_tree_and_file_count(capsys, create_torrent, human_readable, tmp_path, clear_ansi, regex):
    root = tmp_path / 'root'
    (root / 'subdir1' / 'subdir1.0' / 'subdir1.0.0').mkdir(parents=True)
    (root / 'subdir2').mkdir(parents=True)
    (root / 'subdir1' / 'file1').write_text('data')
    (root / 'subdir1' / 'subdir1.0' / 'file2').write_text('data')
    (root / 'subdir1' / 'subdir1.0' / 'subdir1.0.0' / 'file3').write_text('data')
    (root / 'subdir2' / 'file4').write_text('data')

    with create_torrent(path=str(root)) as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex(r'^\s*File Count  4$', flags=re.MULTILINE)
            assert clear_ansi(cap.out) == regex(r'^(\s*)      Files  root\n'
                                                r'\1             ├─subdir1\n'
                                                r'\1             │ ├─file1 \[4 B\]\n'
                                                r'\1             │ └─subdir1.0\n'
                                                r'\1             │   ├─file2 \[4 B\]\n'
                                                r'\1             │   └─subdir1.0.0\n'
                                                r'\1             │     └─file3 \[4 B\]\n'
                                                r'\1             └─subdir2\n'
                                                r'\1               └─file4 \[4 B\]$', flags=re.MULTILINE)
            assert cap.err == ''

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert cap.out == regex(r'^File Count\t4$', flags=re.MULTILINE)
            exp_files = '\t'.join(('root/subdir1/file1',
                                   'root/subdir1/subdir1.0/file2',
                                   'root/subdir1/subdir1.0/subdir1.0.0/file3',
                                   'root/subdir2/file4'))
            assert cap.out == regex(rf'^Files\t{exp_files}$', flags=re.MULTILINE)
            assert cap.err == ''


def test_reading_magnet(capsys, human_readable, clear_ansi, regex):
    magnet = ('magnet:?xt=urn:btih:e167b1fbb42ea72f051f4f50432703308efb8fd1&dn=My+Torrent&xl=142631'
              '&tr=https%3A%2F%2Flocalhost%3A123%2Fannounce'
              '&xs=https%3A%2F%2Flocalhost%3A123%2FMy+Torrent.torrent'
              '&as=https%3A%2F%2Flocalhost%3A456%2FMy+Torrent.torrent'
              '&ws=https%3A%2F%2Flocalhost%2FMy+Torrent')

    with human_readable(True):
        run(['-i', magnet])
    cap = capsys.readouterr()
    assert clear_ansi(cap.out) == regex((r'^\s*Name  My Torrent\n'
                                         r'\s*Size  \d+\.\d+ [TMK]iB\n'
                                         r'\s*Tracker  https://localhost:123/announce\n'
                                         r'\s*Webseed  https://localhost/My\+Torrent\n'
                                         r'\s*File Count  \d+\n'
                                         r'\s*Files  My Torrent \[\d+\.\d+ [TMK]iB\]\n'
                                         r'\s*Magnet  magnet:\?xt=urn:btih:[0-9a-z]{40}.*?\n$'))
    assert cap.err == regex((rf'^{_vars.__appname__}: https://localhost:123/My\+Torrent.torrent: [\w\s]+\n'
                             rf'{_vars.__appname__}: https://localhost:456/My\+Torrent.torrent: [\w\s]+\n'
                             rf'{_vars.__appname__}: https://localhost/My\+Torrent.torrent: [\w\s]+\n'
                             rf'{_vars.__appname__}: https://localhost:123/file\?info_hash='
                             r'%E1g%B1%FB%B4\.%A7/%05%1FOPC%27%030%8E%FB%8F%D1: [\w\s]+\n$'))

    with human_readable(False):
        run(['-i', magnet])
    cap = capsys.readouterr()
    assert cap.out == regex((r'^Name\tMy Torrent\n'
                             r'Size\t\d+\n'
                             r'Tracker\thttps://localhost:123/announce\n'
                             r'Webseed\thttps://localhost/My\+Torrent\n'
                             r'File Count\t\d+\n'
                             r'Files\tMy Torrent\n'
                             r'Magnet\tmagnet:\?xt=urn:btih:[0-9a-z]{40}.*?\n$'))
    assert cap.err == regex((rf'^{_vars.__appname__}: https://localhost:123/My\+Torrent.torrent: [\w\s]+\n'
                             rf'{_vars.__appname__}: https://localhost:456/My\+Torrent.torrent: [\w\s]+\n'
                             rf'{_vars.__appname__}: https://localhost/My\+Torrent.torrent: [\w\s]+\n'
                             rf'{_vars.__appname__}: https://localhost:123/file\?info_hash='
                             r'%E1g%B1%FB%B4\.%A7/%05%1FOPC%27%030%8E%FB%8F%D1: [\w\s]+\n$'))

def test_reading_invalid_magnet(capsys):
    magnet = 'magnet:?xt=urn:btih:e167b1fbb42ea72f051f4f50432703308efb8fd1&xl=not_an_int'
    with patch('sys.exit') as mock_exit:
        run(['-i', magnet])
    mock_exit.assert_called_once_with(err.Code.READ)
    cap = capsys.readouterr()
    assert cap.err == f'{_vars.__appname__}: not_an_int: Invalid exact length ("xl")\n'
    assert cap.out == ''
