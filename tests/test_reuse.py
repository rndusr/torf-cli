import datetime
import os
import pathlib
import random
import re

import pytest
import torf

from torfcli import run


@pytest.fixture
def create_existing_torrent(tmp_path):
    torrents_path = tmp_path / 'torrents'
    torrents_path.mkdir(exist_ok=True)
    contents_path = tmp_path / 'contents'
    contents_path.mkdir(exist_ok=True)

    kwargs_base = {
        'trackers': ['http://some.tracker'],
        'webseeds': ['http://some.webseed'],
        'private': bool(random.randint(0, 1)),
        'source': 'ASDF',
        'randomize_infohash': False,
        'comment': 'Original Comment',
        'created_by': 'Original Creator',
        'creation_date': datetime.datetime.fromisoformat('1975-05-23'),
    }

    def create_torrent(*files, **kwargs):
        # Generate content
        if len(files) == 1:
            name = files[0][0]
            content = files[0][1]
            content_path = contents_path / name
            content_path.write_bytes(content)
        else:
            name = files[0][0].split('/')[0]
            content_path = contents_path / name
            content_path.mkdir()
            for file, data in files:
                assert file.startswith(name)
                (content_path / file).parent.mkdir(parents=True, exist_ok=True)
                (content_path / file).write_bytes(data)

        # Generate Torrent arguments
        kw = {**kwargs_base, **kwargs}
        for _ in range(random.randint(0, 5)):
            del kw[random.choice(tuple(kw))]

        t = torf.Torrent(path=content_path, **kw)
        t.generate()
        torrent_file = torrents_path / f'{name}.torrent'
        t.write(torrent_file)
        return torrent_file

    return create_torrent


@pytest.mark.parametrize('hr_enabled', (True, False), ids=('human_readable=True', 'human_readable=False'))
def test_finds_matching_torrent(hr_enabled, create_existing_torrent, regex, capsys,
                                human_readable, clear_ansi, assert_no_ctrl):
    existing_torrents = [
        create_existing_torrent(('foo1.jpg', b'just an image 1')),
        create_existing_torrent(('foo2.jpg', b'just an image 2')),
        create_existing_torrent(('foo3.jpg', b'just an image 3')),
        create_existing_torrent(
            ('bar/this.mp4', b'just a video'),
            ('bar/that.txt', b'just a text'),
            ('bar/baz/oh.pdf', b'a subdirectory!'),
        ),
        create_existing_torrent(
            ('baz/hello.mp4', b'just a video'),
            ('baz/yo.txt', b'just a text'),
        ),
    ]

    existing_torrents_path = pathlib.Path(os.path.commonpath(existing_torrents))
    existing_contents_path = existing_torrents_path.parent / 'contents'

    # Copy matching torrent with different piece sizes
    for piece_size in (4, 2, 8):
        t = torf.Torrent.read(existing_torrents_path / 'foo2.jpg.torrent')
        piece_size_max = t.piece_size_max
        t.piece_size_max = 16 * 1048576
        t.piece_size = piece_size * 1048576
        t.piece_size_max = piece_size_max
        t.write(existing_torrents_path / f'foo2.{piece_size}.jpg.torrent')
    os.unlink(existing_torrents_path / 'foo2.jpg.torrent')

    content_path = existing_contents_path / 'foo2.jpg'
    exp_reused_torrent = existing_torrents_path / 'foo2.2.jpg.torrent'
    exp_torrent = content_path.name + '.torrent'

    with human_readable(hr_enabled):
        run([str(content_path), '--reuse', str(existing_torrents_path), '--max-piece-size', '2'])
    cap = capsys.readouterr()
    assert cap.err == ''
    if hr_enabled:
        assert cap.out == regex(rf'Verifying  {exp_reused_torrent}', flags=re.MULTILINE)
        assert clear_ansi(cap.out) == regex(rf'^\s*Reused  {exp_reused_torrent}$', flags=re.MULTILINE)
        assert clear_ansi(cap.out) != regex(r'^\s+Progress\s+', flags=re.MULTILINE)
        assert clear_ansi(cap.out) == regex(rf'^\s*Torrent  {exp_torrent}$', flags=re.MULTILINE)
    else:
        assert_no_ctrl(cap.out)
        assert cap.out == regex(r'^Reuse\t'
                                rf'{existing_torrents_path}{os.sep}(?:foo[\d\.]+\.jpg|bar|baz)\.torrent\t'
                                r'\d+\.\d+\t\d+\t\d+$',
                                flags=re.MULTILINE)
        assert cap.out == regex(rf'^Verifying\t{exp_reused_torrent}$', flags=re.MULTILINE)
        assert cap.out == regex(rf'^Reused\t{exp_reused_torrent}$', flags=re.MULTILINE)
        assert cap.out != regex(r'^Progress\t', flags=re.MULTILINE)
        assert cap.out == regex(rf'^Torrent\t{exp_torrent}$', flags=re.MULTILINE)


@pytest.mark.parametrize('hr_enabled', (True, False), ids=('human_readable=True', 'human_readable=False'))
def test_does_not_find_matching_torrent(hr_enabled, create_existing_torrent, regex, capsys,
                                        human_readable, clear_ansi, assert_no_ctrl, mock_content):
    existing_torrents = [
        create_existing_torrent(('foo1.jpg', b'just an image 1')),
        create_existing_torrent(('foo2.jpg', b'just an image 2')),
        create_existing_torrent(('foo3.jpg', b'just an image 3')),
        create_existing_torrent(
            ('bar/this.mp4', b'just a video'),
            ('bar/that.txt', b'just a text'),
            ('bar/baz/oh.pdf', b'a subdirectory!'),
        ),
        create_existing_torrent(
            ('baz/hello.mp4', b'just a video'),
            ('baz/yo.txt', b'just a text'),
        ),
    ]
    existing_torrents_path = pathlib.Path(os.path.commonpath(existing_torrents))
    exp_torrent = mock_content.name + '.torrent'

    with human_readable(hr_enabled):
        run([str(mock_content), '--reuse', str(existing_torrents_path)])
    cap = capsys.readouterr()
    assert cap.err == ''
    if hr_enabled:
        assert cap.out == regex(r'\s+Reuse\s+', flags=re.MULTILINE)
        assert cap.out != regex(r'\s+Verifying\s+', flags=re.MULTILINE)
        assert clear_ansi(cap.out) != regex(r'^\s+Reused\s+', flags=re.MULTILINE)
        assert clear_ansi(cap.out) == regex(r'^\s+Progress  100\.00 % \| \d+:\d+:\d+ total \| \d+.\d+ \w+/s$',
                                            flags=re.MULTILINE)
        assert clear_ansi(cap.out) == regex(rf'^\s*Torrent  {exp_torrent}$', flags=re.MULTILINE)
    else:
        assert_no_ctrl(cap.out)
        assert cap.out == regex(r'^Reuse\t', flags=re.MULTILINE)
        assert cap.out != regex(r'^Verifying\t$', flags=re.MULTILINE)
        assert cap.out != regex(r'^Reused\t$', flags=re.MULTILINE)
        assert cap.out == regex(rf'^Progress\t.*?/{mock_content.name}/', flags=re.MULTILINE)
        assert cap.out == regex(rf'^Torrent\t{exp_torrent}$', flags=re.MULTILINE)


@pytest.mark.parametrize('hr_enabled', (True, False), ids=('human_readable=True', 'human_readable=False'))
def test_noreuse_argument(hr_enabled, create_existing_torrent, regex, capsys,
                          human_readable, clear_ansi, assert_no_ctrl):
    existing_torrents = [
        create_existing_torrent(('foo1.jpg', b'just an image 1')),
        create_existing_torrent(('foo2.jpg', b'just an image 2')),
        create_existing_torrent(('foo3.jpg', b'just an image 3')),
        create_existing_torrent(
            ('bar/this.mp4', b'just a video'),
            ('bar/that.txt', b'just a text'),
            ('bar/baz/oh.pdf', b'a subdirectory!'),
        ),
        create_existing_torrent(
            ('baz/hello.mp4', b'just a video'),
            ('baz/yo.txt', b'just a text'),
        ),
    ]
    existing_torrents_path = pathlib.Path(os.path.commonpath(existing_torrents))
    existing_contents_path = existing_torrents_path.parent / 'contents'
    content_path = existing_contents_path / 'foo2.jpg'
    exp_torrent = content_path.name + '.torrent'

    with human_readable(hr_enabled):
        run([str(content_path), '--reuse', str(existing_torrents_path), '--noreuse'])
    cap = capsys.readouterr()
    assert cap.err == ''
    if hr_enabled:
        assert cap.out != regex(r'Reuse', flags=re.MULTILINE)
        assert cap.out != regex(r'Verifying', flags=re.MULTILINE)
        assert clear_ansi(cap.out) != regex(r'^\s*Reused', flags=re.MULTILINE)
        assert clear_ansi(cap.out) == regex(r'^\s+Progress\s+', flags=re.MULTILINE)
        assert clear_ansi(cap.out) == regex(rf'^\s*Torrent  {exp_torrent}$', flags=re.MULTILINE)
    else:
        assert_no_ctrl(cap.out)
        assert cap.out != regex(r'^Reuse\t', flags=re.MULTILINE)
        assert cap.out != regex(r'^Verifying\t', flags=re.MULTILINE)
        assert cap.out != regex(r'^Reused\t', flags=re.MULTILINE)
        assert cap.out == regex(r'^Progress\t', flags=re.MULTILINE)
        assert cap.out == regex(rf'^Torrent\t{exp_torrent}$', flags=re.MULTILINE)
