from torfcli._cli import run, CLIError
import pytest
import os
from datetime import datetime
import errno
import re


def test_nonexisting_torrent_file(capsys):
    nonexising_path = '/no/such/file'
    with pytest.raises(CLIError, match=r'torf: %s: No such file or directory' % nonexising_path) as exc_info:
        run(['-i', nonexising_path])
    assert exc_info.value.errno == errno.ENOENT


def test_insufficient_permissions(capsys, create_torrent):
    with create_torrent() as torrent_file:
        os.chmod(torrent_file, 0o000)
        with pytest.raises(CLIError, match=r'torf: %s: Permission denied' % torrent_file) as exc_info:
            run(['-i', torrent_file])
    assert exc_info.value.errno == errno.EACCES


def test_name(capsys, create_torrent, mock_tty):
    with create_torrent(name='foo') as torrent_file:
        with mock_tty(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^\s*Name  foo$', cap.out, flags=re.MULTILINE)

        with mock_tty(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^Name\tfoo$', cap.out, flags=re.MULTILINE)


def test_info_hash(capsys, create_torrent, mock_tty):
    with create_torrent() as torrent_file:
        with mock_tty(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^\s*Info Hash  [0-9a-z]{40}$', cap.out, flags=re.MULTILINE)

        with mock_tty(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^Info Hash\t[0-9a-z]{40}$', cap.out, flags=re.MULTILINE)


def test_size(capsys, create_torrent, mock_tty):
    with create_torrent() as torrent_file:
        with mock_tty(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^\s*Size  [0-9]+ [KMGT]?i?B$', cap.out, flags=re.MULTILINE)

        with mock_tty(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^Size\t[0-9]+$', cap.out, flags=re.MULTILINE)


def test_piece_size(capsys, create_torrent, mock_tty):
    with create_torrent() as torrent_file:
        with mock_tty(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^\s*Piece Size  [0-9]+ [KMGT]?i?B$', cap.out, flags=re.MULTILINE)

        with mock_tty(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^Piece Size\t[0-9]+$', cap.out, flags=re.MULTILINE)


def test_piece_count(capsys, create_torrent, mock_tty):
    with create_torrent() as torrent_file:
        with mock_tty(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^\s*Piece Count  [0-9]+$', cap.out, flags=re.MULTILINE)

        with mock_tty(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^Piece Count\t[0-9]+$', cap.out, flags=re.MULTILINE)


def test_single_line_comment(capsys, create_torrent, mock_tty):
    with create_torrent(comment='This is my torrent.') as torrent_file:
        with mock_tty(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^\s*Comment  This is my torrent\.$', cap.out, flags=re.MULTILINE)

        with mock_tty(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^Comment\tThis is my torrent\.$', cap.out, flags=re.MULTILINE)

def test_multiline_comment(capsys, create_torrent, mock_tty):
    comment = 'This is my torrent.\nShare it!'
    with create_torrent(comment=comment) as torrent_file:
        with mock_tty(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^(\s*)Comment  This is my torrent\.\n\1         Share it!$', cap.out, flags=re.MULTILINE)

        with mock_tty(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^Comment\tThis is my torrent\.\tShare it!$', cap.out, flags=re.MULTILINE)


def test_creation_date(capsys, create_torrent, mock_tty):
    date = datetime(2000, 5, 10, 0, 30, 45)
    with create_torrent(creation_date=date) as torrent_file:
        with mock_tty(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^\s*Creation Date  2000-05-10 00:30:45$', cap.out, flags=re.MULTILINE)

        with mock_tty(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^Creation Date\t2000-05-10 00:30:45$', cap.out, flags=re.MULTILINE)


def test_created_by(capsys, create_torrent, mock_tty):
    with create_torrent(created_by='foo') as torrent_file:
        with mock_tty(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^\s*Created By  foo$', cap.out, flags=re.MULTILINE)

        with mock_tty(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^Created By\tfoo$', cap.out, flags=re.MULTILINE)


def test_private(capsys, create_torrent, mock_tty):
    with create_torrent(private=True) as torrent_file:
        with mock_tty(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^\s*Private  yes$', cap.out, flags=re.MULTILINE)

        with mock_tty(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^Private\tyes$', cap.out, flags=re.MULTILINE)

    with create_torrent(private=False) as torrent_file:
        with mock_tty(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^\s*Private  no', cap.out, flags=re.MULTILINE)

        with mock_tty(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^Private\tno', cap.out, flags=re.MULTILINE)


def test_trackers___single_tracker_per_tier(capsys, create_torrent, mock_tty):
    trackers = ['http://tracker1.1', 'http://tracker2.1']
    with create_torrent(trackers=trackers) as torrent_file:
        with mock_tty(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(f'^(\s*)Trackers  {trackers[0]}\n\\1          {trackers[1]}$', cap.out, flags=re.MULTILINE)

        with mock_tty(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^Trackers\t%s$' % '\t'.join(trackers), cap.out, flags=re.MULTILINE)

def test_trackers___multiple_trackers_per_tier(capsys, create_torrent, mock_tty):
    trackers = ['http://tracker1.1',
                ['http://tracker2.1', 'http://tracker2.2'],
                ['http://tracker3.1']]
    with create_torrent(trackers=trackers) as torrent_file:
        with mock_tty(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            exp_trackers = '''
     Trackers  Tier 1: http://tracker1.1
               Tier 2: http://tracker2.1
                       http://tracker2.2
               Tier 3: http://tracker3.1'''
            assert exp_trackers in cap.out

        exp_trackers = ('http://tracker1.1\thttp://tracker2.1\t'
                        'http://tracker2.2\thttp://tracker3.1')
        with mock_tty(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^Trackers\t%s$' % exp_trackers, cap.out, flags=re.MULTILINE)


def test_webseeds(capsys, create_torrent, mock_tty):
    webseeds = ['http://webseed1', 'http://webseed2']
    with create_torrent(webseeds=webseeds) as torrent_file:
        with mock_tty(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(f'^(\s*)Webseeds  {webseeds[0]}\n\\1          {webseeds[1]}$', cap.out, flags=re.MULTILINE)

        with mock_tty(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^Webseeds\t%s$' % '\t'.join(webseeds), cap.out, flags=re.MULTILINE)


def test_httpseeds(capsys, create_torrent, mock_tty):
    httpseeds = ['http://httpseed1', 'http://httpseed2']
    with create_torrent(httpseeds=httpseeds) as torrent_file:
        with mock_tty(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            print(cap.out)
            assert re.search(f'^(\s*)HTTP Seeds  {httpseeds[0]}\n\\1            {httpseeds[1]}$', cap.out, flags=re.MULTILINE)

        with mock_tty(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            print(cap.out)
            assert re.search(r'^HTTP Seeds\t%s$' % '\t'.join(httpseeds), cap.out, flags=re.MULTILINE)


def test_httpseeds(capsys, create_torrent, mock_tty):
    httpseeds = ['http://httpseed1', 'http://httpseed2']
    with create_torrent(httpseeds=httpseeds) as torrent_file:
        with mock_tty(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            print(cap.out)
            assert re.search(f'^(\s*)HTTP Seeds  {httpseeds[0]}\n\\1            {httpseeds[1]}$', cap.out, flags=re.MULTILINE)

        with mock_tty(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            print(cap.out)
            assert re.search(r'^HTTP Seeds\t%s$' % '\t'.join(httpseeds), cap.out, flags=re.MULTILINE)


def test_file_tree_and_file_count(capsys, create_torrent, mock_tty, tmpdir):
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
        with mock_tty(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            print(cap.out)
            assert re.search(f'^(\s*)File Count  4$', cap.out, flags=re.MULTILINE)
            filetree = '''
        Files  root
               ├─subdir1
               │ ├─file1
               │ └─subsubdir1.0
               │   ├─file2
               │   └─subsubdir1.0.0
               │     └─file3
               └─subdir2
                 └─file4
'''.strip()
            assert filetree in cap.out

        with mock_tty(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(f'^(\s*)File Count  4$', cap.out, flags=re.MULTILINE)
            files = ('root/subdir1/file1',
	             'root/subdir1/subsubdir1.0/file2',
	             'root/subdir1/subsubdir1.0/subsubdir1.0.0/file3',
	             'root/subdir2/file4')
            assert re.search(r'^Files\t%s$' % '\t'.join(files), cap.out, flags=re.MULTILINE)
