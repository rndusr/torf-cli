from torfcli._main import run
from torfcli import _errors as err
import pytest
import os
from datetime import datetime
import errno
import re


def test_nonexisting_torrent_file(capsys):
    nonexising_path = '/no/such/file'
    with pytest.raises(err.ReadError, match=rf'^{nonexising_path}: No such file or directory$') as exc_info:
        run(['-i', nonexising_path])


def test_insufficient_permissions(capsys, create_torrent):
    with create_torrent() as torrent_file:
        os.chmod(torrent_file, 0o000)
        with pytest.raises(err.ReadError, match=rf'^{torrent_file}: Permission denied$') as exc_info:
            run(['-i', torrent_file])


def test_magnet(capsys, create_torrent, human_readable, clear_ansi):
    with create_torrent(name='foo') as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^\s*Magnet  magnet:\?xt=urn:btih:[0-9a-z]{40}', clear_ansi(cap.out), flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^Magnet\tmagnet:\?xt=urn:btih:[0-9a-z]{40}', cap.out, flags=re.MULTILINE)


def test_name(capsys, create_torrent, human_readable, clear_ansi):
    with create_torrent(name='foo') as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^\s*Name  foo$', clear_ansi(cap.out), flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^Name\tfoo$', cap.out, flags=re.MULTILINE)


def test_info_hash(capsys, create_torrent, human_readable, clear_ansi):
    with create_torrent() as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^\s*Info Hash  [0-9a-z]{40}$', clear_ansi(cap.out), flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^Info Hash\t[0-9a-z]{40}$', cap.out, flags=re.MULTILINE)


def test_size(capsys, create_torrent, human_readable, clear_ansi):
    with create_torrent() as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^\s*Size  [0-9]+ [KMGT]?i?B$', clear_ansi(cap.out), flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^Size\t[0-9]+$', cap.out, flags=re.MULTILINE)


def test_piece_size(capsys, create_torrent, human_readable, clear_ansi):
    with create_torrent() as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^\s*Piece Size  [0-9]+ [KMGT]?i?B$', clear_ansi(cap.out), flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^Piece Size\t[0-9]+$', cap.out, flags=re.MULTILINE)


def test_piece_count(capsys, create_torrent, human_readable, clear_ansi):
    with create_torrent() as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^\s*Piece Count  [0-9]+$', clear_ansi(cap.out), flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^Piece Count\t[0-9]+$', cap.out, flags=re.MULTILINE)


def test_single_line_comment(capsys, create_torrent, human_readable, clear_ansi):
    with create_torrent(comment='This is my torrent.') as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^\s*Comment  This is my torrent\.$', clear_ansi(cap.out), flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^Comment\tThis is my torrent\.$', cap.out, flags=re.MULTILINE)

def test_multiline_comment(capsys, create_torrent, human_readable, clear_ansi):
    comment = 'This is my torrent.\nShare it!'
    with create_torrent(comment=comment) as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^(\s*)Comment  This is my torrent\.\n\1         Share it!$', clear_ansi(cap.out), flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^Comment\tThis is my torrent\.\tShare it!$', cap.out, flags=re.MULTILINE)


def test_creation_date(capsys, create_torrent, human_readable, clear_ansi):
    date = datetime(2000, 5, 10, 0, 30, 45)
    with create_torrent(creation_date=date) as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^\s*Created  2000-05-10 00:30:45$', clear_ansi(cap.out), flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^Created\t2000-05-10 00:30:45$', cap.out, flags=re.MULTILINE)


def test_created_by(capsys, create_torrent, human_readable, clear_ansi):
    with create_torrent(created_by='foo') as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^\s*Created By  foo$', clear_ansi(cap.out), flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^Created By\tfoo$', cap.out, flags=re.MULTILINE)


def test_private(capsys, create_torrent, human_readable, clear_ansi):
    with create_torrent(private=True) as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^\s*Private  yes$', clear_ansi(cap.out), flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^Private\tyes$', cap.out, flags=re.MULTILINE)

    with create_torrent(private=False) as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^\s*Private  no', clear_ansi(cap.out), flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^Private\tno', cap.out, flags=re.MULTILINE)


def test_trackers___single_tracker_per_tier(capsys, create_torrent, human_readable, clear_ansi):
    trackers = ['http://tracker1.1', 'http://tracker2.1']
    with create_torrent(trackers=trackers) as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(rf'^(\s*)Trackers  {trackers[0]}\n\1          {trackers[1]}$', clear_ansi(cap.out), flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            tab = '\t'
            assert re.search(rf'^Trackers\t{tab.join(trackers)}$', cap.out, flags=re.MULTILINE)

def test_trackers___multiple_trackers_per_tier(capsys, create_torrent, human_readable, clear_ansi):
    trackers = ['http://tracker1.1',
                ['http://tracker2.1', 'http://tracker2.2'],
                ['http://tracker3.1']]
    with create_torrent(trackers=trackers) as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            exp_trackers = '''
   Trackers  Tier 1: http://tracker1.1
             Tier 2: http://tracker2.1
                     http://tracker2.2
             Tier 3: http://tracker3.1'''
            assert exp_trackers in clear_ansi(cap.out)

        exp_trackers = ('http://tracker1.1\thttp://tracker2.1\t'
                        'http://tracker2.2\thttp://tracker3.1')
        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(rf'^Trackers\t{exp_trackers}$', cap.out, flags=re.MULTILINE)


def test_webseeds(capsys, create_torrent, human_readable, clear_ansi):
    webseeds = ['http://webseed1', 'http://webseed2']
    with create_torrent(webseeds=webseeds) as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(rf'^(\s*)Webseeds  {webseeds[0]}\n\1          {webseeds[1]}$', clear_ansi(cap.out), flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            tab = '\t'
            assert re.search(rf'^Webseeds\t{tab.join(webseeds)}$', cap.out, flags=re.MULTILINE)


def test_httpseeds(capsys, create_torrent, human_readable, clear_ansi):
    httpseeds = ['http://httpseed1', 'http://httpseed2']
    with create_torrent(httpseeds=httpseeds) as torrent_file:
        with human_readable(True):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(rf'^(\s*)HTTP Seeds  {httpseeds[0]}\n\1            {httpseeds[1]}$', clear_ansi(cap.out), flags=re.MULTILINE)

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            tab = '\t'
            assert re.search(rf'^HTTP Seeds\t{tab.join(httpseeds)}$', cap.out, flags=re.MULTILINE)


def test_file_tree_and_file_count(capsys, create_torrent, human_readable, tmpdir, clear_ansi):
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
            assert re.search(r'^\s*File Count  4$', clear_ansi(cap.out), flags=re.MULTILINE)
            filetree = '''
      Files  root
             ├─subdir1
             │ ├─file1 [4 B]
             │ └─subsubdir1.0
             │   ├─file2 [4 B]
             │   └─subsubdir1.0.0
             │     └─file3 [4 B]
             └─subdir2
               └─file4 [4 B]
'''.strip()
            assert filetree in cap.out

        with human_readable(False):
            run(['-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(r'^File Count\t4$', cap.out, flags=re.MULTILINE)
            files = ('root/subdir1/file1',
	             'root/subdir1/subsubdir1.0/file2',
	             'root/subdir1/subsubdir1.0/subsubdir1.0.0/file3',
	             'root/subdir2/file4')
            tab = '\t'
            assert re.search(rf'^Files\t{tab.join(files)}$', cap.out, flags=re.MULTILINE)
