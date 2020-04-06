from torfcli import run
from torfcli import _errors as err
from torfcli import _vars

import pytest
from unittest.mock import patch
import os
from datetime import datetime
import errno
import re


def test_nonexisting_torrent_file(capsys):
    nonexising_path = '/no/such/file'
    with patch('sys.exit') as mock_exit:
        run(['-i', nonexising_path])
    mock_exit.assert_called_once_with(err.Code.READ)
    cap = capsys.readouterr()
    assert cap.err == f'{_vars.__appname__}: {nonexising_path}: No such file or directory\n'


def test_insufficient_permissions(capsys, create_torrent):
    with create_torrent() as torrent_file:
        os.chmod(torrent_file, 0o000)
        with patch('sys.exit') as mock_exit:
            run(['-i', torrent_file])
        mock_exit.assert_called_once_with(err.Code.READ)
        cap = capsys.readouterr()
        assert cap.err == f'{_vars.__appname__}: {torrent_file}: Permission denied\n'

def test_magnet(capsys, create_torrent, human_readable, clear_ansi, regex):
    with create_torrent(name='foo') as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex(r'^\s*Magnet  magnet:\?xt=urn:btih:[0-9a-z]{40}', flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert cap.out == regex(r'^Magnet\tmagnet:\?xt=urn:btih:[0-9a-z]{40}', flags=re.MULTILINE)


def test_name(capsys, create_torrent, human_readable, clear_ansi, regex):
    with create_torrent(name='foo') as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex(r'^\s*Name  foo$', flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert cap.out == regex(r'^Name\tfoo$', flags=re.MULTILINE)


def test_info_hash(capsys, create_torrent, human_readable, clear_ansi, regex):
    with create_torrent() as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex(r'^\s*Info Hash  [0-9a-z]{40}$', flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert cap.out == regex(r'^Info Hash\t[0-9a-z]{40}$', flags=re.MULTILINE)


def test_size(capsys, create_torrent, human_readable, clear_ansi, regex):
    with create_torrent() as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex(r'^\s*Size  [0-9]+ [KMGT]?i?B$', flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert cap.out == regex(r'^Size\t[0-9]+$', flags=re.MULTILINE)


def test_piece_size(capsys, create_torrent, human_readable, clear_ansi, regex):
    with create_torrent() as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex(r'^\s*Piece Size  [0-9]+ [KMGT]?i?B$', flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert cap.out == regex(r'^Piece Size\t[0-9]+$', flags=re.MULTILINE)


def test_piece_count(capsys, create_torrent, human_readable, clear_ansi, regex):
    with create_torrent() as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex(r'^\s*Piece Count  [0-9]+$', flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert cap.out == regex(r'^Piece Count\t[0-9]+$', flags=re.MULTILINE)


def test_single_line_comment(capsys, create_torrent, human_readable, clear_ansi, regex):
    with create_torrent(comment='This is my torrent.') as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex(r'^\s*Comment  This is my torrent\.$', flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert cap.out == regex(r'^Comment\tThis is my torrent\.$', flags=re.MULTILINE)

def test_multiline_comment(capsys, create_torrent, human_readable, clear_ansi, regex):
    comment = 'This is my torrent.\nShare it!'
    with create_torrent(comment=comment) as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex(r'^(\s*)Comment  This is my torrent\.\n'
                                                r'\1         Share it!$', flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert cap.out == regex(r'^Comment\tThis is my torrent\.\tShare it!$', flags=re.MULTILINE)


def test_creation_date(capsys, create_torrent, human_readable, clear_ansi, regex):
    date = datetime(2000, 5, 10, 0, 30, 45)
    with create_torrent(creation_date=date) as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex(r'^\s*Created  2000-05-10 00:30:45$', flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            exp_timestamp = int(date.timestamp())
            assert cap.out == regex(rf'^Created\t{exp_timestamp}$', flags=re.MULTILINE)


def test_created_by(capsys, create_torrent, human_readable, clear_ansi, regex):
    with create_torrent(created_by='foo') as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex(r'^\s*Created By  foo$', flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert cap.out == regex(r'^Created By\tfoo$', flags=re.MULTILINE)


def test_private(capsys, create_torrent, human_readable, clear_ansi, regex):
    with create_torrent(private=True) as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex(r'^\s*Private  yes$', flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert cap.out == regex(r'^Private\tyes$', flags=re.MULTILINE)

    with create_torrent(private=False) as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex(r'^\s*Private  no', flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert cap.out == regex(r'^Private\tno', flags=re.MULTILINE)


def test_trackers___single_tracker_per_tier(capsys, create_torrent, human_readable, clear_ansi, regex):
    trackers = ['http://tracker1.1', 'http://tracker2.1']
    with create_torrent(trackers=trackers) as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex(rf'^(\s*)Trackers  {trackers[0]}\n'
                                                rf'\1          {trackers[1]}$', flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            exp_trackers = '\t'.join(trackers)
            assert cap.out == regex(rf'^Trackers\t{exp_trackers}$', flags=re.MULTILINE)

def test_trackers___multiple_trackers_per_tier(capsys, create_torrent, human_readable, clear_ansi, regex):
    trackers = ['http://tracker1.1',
                ['http://tracker2.1', 'http://tracker2.2'],
                ['http://tracker3.1']]
    with create_torrent(trackers=trackers) as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex(r'^(\s*)Trackers  Tier 1: http://tracker1.1\n'
                                                rf'\1          Tier 2: http://tracker2.1\n'
                                                rf'\1                  http://tracker2.2\n'
                                                rf'\1          Tier 3: http://tracker3.1$', flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            exp_trackers = '\t'.join(('http://tracker1.1', 'http://tracker2.1',
                                      'http://tracker2.2', 'http://tracker3.1'))
            assert cap.out == regex(rf'^Trackers\t{exp_trackers}$', flags=re.MULTILINE)


def test_webseeds(capsys, create_torrent, human_readable, clear_ansi, regex):
    webseeds = ['http://webseed1', 'http://webseed2']
    with create_torrent(webseeds=webseeds) as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex((rf'^(\s*)Webseeds  {webseeds[0]}\n'
                                                 rf'\1          {webseeds[1]}$'), flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            exp_webseeds = '\t'.join(webseeds)
            assert cap.out == regex(rf'^Webseeds\t{exp_webseeds}$', flags=re.MULTILINE)


def test_httpseeds(capsys, create_torrent, human_readable, clear_ansi, regex):
    httpseeds = ['http://httpseed1', 'http://httpseed2']
    with create_torrent(httpseeds=httpseeds) as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex((rf'^(\s*)HTTP Seeds  {httpseeds[0]}\n'
                                                 rf'\1            {httpseeds[1]}$'), flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            exp_httpseeds = '\t'.join(httpseeds)
            assert cap.out == regex(rf'^HTTP Seeds\t{exp_httpseeds}$', flags=re.MULTILINE)


def test_file_tree_and_file_count(capsys, create_torrent, human_readable, tmpdir, clear_ansi, regex):
    root = tmpdir.mkdir('root')
    subdir1 = root.mkdir('subdir1')
    file1 = subdir1.join('file1') ; file1.write('data')
    subdir10 = subdir1.mkdir('subsubdir1.0')
    file2 = subdir10.join('file2') ; file2.write('data')
    subdir100 = subdir10.mkdir('subsubdir1.0.0')
    file3 = subdir100.join('file3') ; file3.write('data')

    subdir2 = root.mkdir('subdir2')
    file4 = subdir2.join('file4') ; file4.write('data')

    with create_torrent(path=str(root)) as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert clear_ansi(cap.out) == regex(r'^\s*File Count  4$', flags=re.MULTILINE)
            assert clear_ansi(cap.out) == regex(r'^(\s*)      Files  root\n'
                                                r'\1             ├─subdir1\n'
                                                r'\1             │ ├─file1 \[4 B\]\n'
                                                r'\1             │ └─subsubdir1.0\n'
                                                r'\1             │   ├─file2 \[4 B\]\n'
                                                r'\1             │   └─subsubdir1.0.0\n'
                                                r'\1             │     └─file3 \[4 B\]\n'
                                                r'\1             └─subdir2\n'
                                                r'\1               └─file4 \[4 B\]$', flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert cap.out == regex(r'^File Count\t4$', flags=re.MULTILINE)
            exp_files = '\t'.join(('root/subdir1/file1',
	                           'root/subdir1/subsubdir1.0/file2',
	                           'root/subdir1/subsubdir1.0/subsubdir1.0.0/file3',
	                           'root/subdir2/file4'))
            assert cap.out == regex(rf'^Files\t{exp_files}$', flags=re.MULTILINE)
