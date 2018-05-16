from torfcli._cli import run, CLIError
import pytest
import os
import torf
from datetime import (datetime, date, time)
import errno


### Basic creation modes

def test_default_torrent_filepath(capsys, mock_content, autoremove):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with autoremove(exp_torrent_filepath):
        run([content_path])

        t = torf.Torrent.read(exp_torrent_filepath)
        assert t.name == 'My Torrent'
        assert len(tuple(t.files)) == 3
        assert t.creation_date == datetime.combine(date.today(), time(0, 0, 0))
        assert t.created_by.startswith('torf/')

        cap = capsys.readouterr()
        assert 'Torrent File\t%s' % exp_torrent_filename in cap.out
        assert 'Name\tMy Torrent' in cap.out
        assert 'File Count\t3' in cap.out
        assert 'Info Hash' in cap.out
        assert 'Created By\ttorf' in cap.out


def test_user_given_torrent_filepath(capsys, mock_content, autoremove):
    content_path = str(mock_content)
    exp_torrent_filename = 'foo.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with autoremove(exp_torrent_filepath):
        run([content_path, '--out', exp_torrent_filename])

        t = torf.Torrent.read(exp_torrent_filepath)
        assert t.name == 'My Torrent'
        assert len(tuple(t.files)) == 3
        assert t.creation_date == datetime.combine(date.today(), time(0, 0, 0))
        assert t.created_by.startswith('torf/')

        cap = capsys.readouterr()
        assert 'Torrent File\t%s' % exp_torrent_filename in cap.out
        assert 'Name\tMy Torrent' in cap.out
        assert 'File Count\t3' in cap.out
        assert 'Info Hash' in cap.out
        assert 'Created By\ttorf' in cap.out


def test_create_only_magnet_link(capsys, mock_content):
    content_path = str(mock_content)
    run([content_path, '--magnet'])

    unexp_torrent_filename = os.path.basename(content_path) + '.torrent'
    unexp_torrent_filepath = os.path.join(os.getcwd(), unexp_torrent_filename)
    assert not os.path.exists(unexp_torrent_filepath)

    cap = capsys.readouterr()
    assert 'Magnet URI\t' in cap.out
    assert 'Torrent File\t' not in cap.out

    assert 'Name\tMy Torrent' in cap.out
    assert 'File Count\t3' in cap.out
    assert 'Info Hash' in cap.out
    assert 'Created By\ttorf' in cap.out


def test_create_torrent_file_and_magnet_link(capsys, mock_content, autoremove):
    content_path = str(mock_content)
    exp_torrent_filename = 'foo.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with autoremove(exp_torrent_filepath):
        run([content_path, '--out', exp_torrent_filename, '--magnet'])

        t = torf.Torrent.read(exp_torrent_filepath)
        assert t.name == 'My Torrent'
        assert len(tuple(t.files)) == 3
        assert t.creation_date == datetime.combine(date.today(), time(0, 0, 0))
        assert t.created_by.startswith('torf/')

        cap = capsys.readouterr()
        assert 'Magnet URI\t' in cap.out
        assert 'Torrent File\t%s' % exp_torrent_filename in cap.out
        assert 'Name\tMy Torrent' in cap.out
        assert 'File Count\t3' in cap.out
        assert 'Info Hash' in cap.out
        assert 'Created By\ttorf' in cap.out


### Error cases

def test_content_path_doesnt_exist(capsys):
    with pytest.raises(CLIError, match=r'torf: /path/doesnt/exist: No such file or directory') as exc_info:
        run(['/path/doesnt/exist'])
    assert exc_info.value.errno == errno.ENOENT


def test_torrent_filepath_exists(capsys, mock_content, autoremove):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with autoremove(exp_torrent_filepath):
        with open(exp_torrent_filepath, 'wb') as f:
            f.write(b'<torrent data>')

        with pytest.raises(CLIError, match=r'torf: %s: File exists' % exp_torrent_filepath) as exc_info:
            run([content_path, '--out', exp_torrent_filepath])
        assert exc_info.value.errno == errno.EEXIST


### Options

def test_yes_option(capsys, mock_content, autoremove):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with autoremove(exp_torrent_filepath):
        with open(exp_torrent_filepath, 'wb') as f:
            f.write(b'<some file content>')
        assert os.path.exists(exp_torrent_filepath)

        run([content_path, '--out', exp_torrent_filename, '--yes'])

        t = torf.Torrent.read(exp_torrent_filepath)
        assert t.name == 'My Torrent'

        cap = capsys.readouterr()
        assert ('Torrent File\t%s' % exp_torrent_filename) in cap.out


def test_single_exclude(capsys, mock_content, autoremove):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with autoremove(exp_torrent_filepath):
        run([content_path, '--exclude', '*.jpg'])

        t = torf.Torrent.read(exp_torrent_filepath)
        assert len(tuple(t.files)) == 2

        cap = capsys.readouterr()
        assert 'Exclude\t*.jpg' in cap.out
        assert 'File Count\t2' in cap.out


def test_multiple_excludes(capsys, mock_content, autoremove):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with autoremove(exp_torrent_filepath):
        run([content_path, '--exclude', '*.jpg', '--exclude', '*.txt'])

        t = torf.Torrent.read(exp_torrent_filepath)
        assert len(tuple(t.files)) == 1

        cap = capsys.readouterr()
        assert 'Exclude\t*.jpg\t*.txt' in cap.out
        assert 'File Count\t1' in cap.out


def test_exclude_everything(capsys, mock_content, autoremove):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with autoremove(exp_torrent_filepath):
        with pytest.raises(CLIError, match=r'torf: %s: Empty directory' % content_path) as exc_info:
            run([content_path, '--exclude', '*'])
        assert exc_info.value.errno == errno.ENODATA


def test_noexclude_option(capsys, mock_content, autoremove):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with autoremove(exp_torrent_filepath):
        run([content_path, '--exclude', '*.jpg', '--noexclude'])

        t = torf.Torrent.read(exp_torrent_filepath)
        assert len(tuple(t.files)) == 3

        cap = capsys.readouterr()
        assert 'Exclude\t' not in cap.out
        assert 'File Count\t3' in cap.out


def test_name_option(capsys, mock_content, autoremove):
    content_path = str(mock_content)
    name = 'Your Torrent'
    exp_torrent_filename = '%s.torrent' % name
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)
    wrong_torrent_filename = os.path.basename(content_path) + '.torrent'

    with autoremove(exp_torrent_filename, wrong_torrent_filename):
        run([content_path, '--name', name])

        t = torf.Torrent.read(exp_torrent_filepath)
        assert t.name == 'Your Torrent'

        cap = capsys.readouterr()
        assert 'Torrent File\tYour Torrent.torrent' in cap.out


def test_private_option(capsys, mock_content, autoremove):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with autoremove(exp_torrent_filepath):
        run([content_path, '--private'])

        t = torf.Torrent.read(exp_torrent_filepath)
        assert t.private == True

        cap = capsys.readouterr()
        assert 'Private\tyes' in cap.out


def test_noprivate_option(capsys, mock_content, autoremove):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with autoremove(exp_torrent_filepath):
        run([content_path, '--private', '--noprivate'])

        t = torf.Torrent.read(exp_torrent_filepath)
        assert t.private == False

        cap = capsys.readouterr()
        assert 'Private\tno' in cap.out


def test_xseed_option(capsys, mock_content, autoremove):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with autoremove(exp_torrent_filepath):
        run([content_path])
        cap = capsys.readouterr()
        hash_line_1 = [line for line in cap.out.split('\n')
                       if 'Info Hash' in line][0]
        hash_1 = torf.Torrent.read(exp_torrent_filepath).infohash

    with autoremove(exp_torrent_filepath):
        run([content_path, '--xseed'])
        cap = capsys.readouterr()
        hash_line_2 = [line for line in cap.out.split('\n')
                       if 'Info Hash' in line][0]
        hash_2 = torf.Torrent.read(exp_torrent_filepath).infohash

    assert hash_line_1 != hash_line_2
    assert hash_1 != hash_2


def test_noxseed_option(capsys, mock_content, autoremove):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with autoremove(exp_torrent_filepath):
        run([content_path, '--xseed', '--noxseed'])
        cap = capsys.readouterr()
        hash_line_1 = [line for line in cap.out.split('\n')
                       if 'Info Hash' in line][0]
        hash_1 = torf.Torrent.read(exp_torrent_filepath).infohash

    with autoremove(exp_torrent_filepath):
        run([content_path])
        cap = capsys.readouterr()
        hash_line_2 = [line for line in cap.out.split('\n')
                       if 'Info Hash' in line][0]
        hash_2 = torf.Torrent.read(exp_torrent_filepath).infohash

    assert hash_line_1 == hash_line_2
    assert hash_1 == hash_2


def test_default_date(capsys, mock_content, autoremove):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with autoremove(exp_torrent_filepath):
        run([content_path])

        t = torf.Torrent.read(exp_torrent_filepath)
        assert t.creation_date == datetime.combine(date.today(), time(0, 0, 0))

        cap = capsys.readouterr()
        assert 'Creation Date\t%s' % (date.today().isoformat() + ' 00:00:00') in cap.out


def test_date_now(capsys, mock_content, autoremove):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with autoremove(exp_torrent_filepath):
        date = datetime.today()
        run([content_path, '--date', 'now'])

        t = torf.Torrent.read(exp_torrent_filepath)
        assert t.creation_date == datetime.today().replace(microsecond=0)

        cap = capsys.readouterr()
        assert 'Creation Date\t%s' % date.isoformat(sep=' ', timespec='seconds') in cap.out


def test_user_given_date(capsys, mock_content, autoremove):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with autoremove(exp_torrent_filepath):
        run([content_path, '--date', '2000-01-02'])

        t = torf.Torrent.read(exp_torrent_filepath)
        assert t.creation_date == datetime.combine(date(2000, 1, 2), time(0, 0, 0))

        cap = capsys.readouterr()
        assert 'Creation Date\t%s' % (date(2000, 1, 2).isoformat() + ' 00:00:00') in cap.out


def test_user_given_date_and_time(capsys, mock_content, autoremove):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with autoremove(exp_torrent_filepath):
        run([content_path, '--date', '2000-01-02 03:04'])

        t = torf.Torrent.read(exp_torrent_filepath)
        assert t.creation_date == datetime(2000, 1, 2, 3, 4)

        cap = capsys.readouterr()
        assert 'Creation Date\t%s' % datetime(2000, 1, 2, 3, 4).isoformat(sep=' ', timespec='seconds') in cap.out


def test_user_given_date_and_time_with_seconds(capsys, mock_content, autoremove):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with autoremove(exp_torrent_filepath):
        run([content_path, '--date', '2000-01-02 03:04:05'])

        t = torf.Torrent.read(exp_torrent_filepath)
        assert t.creation_date == datetime(2000, 1, 2, 3, 4, 5)

        cap = capsys.readouterr()
        assert 'Creation Date\t%s' % datetime(2000, 1, 2, 3, 4, 5).isoformat(sep=' ', timespec='seconds') in cap.out


def test_invalid_date(capsys, mock_content, autoremove):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with autoremove(exp_torrent_filepath):
        with pytest.raises(CLIError, match=r'torf: foo: Invalid date') as exc_info:
            run([content_path, '--date', 'foo'])
        assert exc_info.value.errno == errno.EINVAL


def test_nodate_option(capsys, mock_content, autoremove):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with autoremove(exp_torrent_filepath):
        run([content_path, '--date', '2000-01-02 03:04:05', '--nodate'])

        t = torf.Torrent.read(exp_torrent_filepath)
        assert t.creation_date == None

        cap = capsys.readouterr()
        assert 'Creation Date\t' not in cap.out


def test_comment_option(capsys, mock_content, autoremove):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with autoremove(exp_torrent_filepath):
        run([content_path, '--comment', 'This is a comment.'])

        t = torf.Torrent.read(exp_torrent_filepath)
        assert t.comment == 'This is a comment.'

        cap = capsys.readouterr()
        assert 'Comment\tThis is a comment.' in cap.out


def test_nocomment_option(capsys, mock_content, autoremove):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with autoremove(exp_torrent_filepath):
        run([content_path, '--comment', 'This is a comment.', '--nocomment'])

        t = torf.Torrent.read(exp_torrent_filepath)
        assert t.comment is None

        cap = capsys.readouterr()
        assert 'Comment\t' not in cap.out


def test_nocreator_option(capsys, mock_content, autoremove):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with autoremove(exp_torrent_filepath):
        run([content_path, '--nocreator'])

        t = torf.Torrent.read(exp_torrent_filepath)
        assert t.created_by is None

        cap = capsys.readouterr()
        assert 'Created By\t' not in cap.out


def test_single_tracker(capsys, mock_content, autoremove):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with autoremove(exp_torrent_filepath):
        run([content_path, '--tracker', 'https://mytracker.example.org'])

        t = torf.Torrent.read(exp_torrent_filepath)
        assert t.trackers == [['https://mytracker.example.org']]

        cap = capsys.readouterr()
        assert 'Tracker\thttps://mytracker.example.org' in cap.out


def test_multiple_trackers(capsys, mock_content, autoremove):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with autoremove(exp_torrent_filepath):
        run([content_path,
             '--tracker', 'https://tracker1.example.org/foo',
             '--tracker', 'https://tracker2.example.org/bar/',
             '--tracker', 'https://tracker3.example.org/baz'])

        t = torf.Torrent.read(exp_torrent_filepath)
        assert t.trackers == [['https://tracker1.example.org/foo'],
                              ['https://tracker2.example.org/bar/'],
                              ['https://tracker3.example.org/baz']]

        cap = capsys.readouterr()
        assert 'Trackers\thttps://tracker1.example.org/foo' in cap.out
        assert '\thttps://tracker2.example.org/bar/' in cap.out
        assert '\thttps://tracker3.example.org/baz' in cap.out


def test_notracker_option(capsys, mock_content, autoremove):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with autoremove(exp_torrent_filepath):
        run([content_path, '--tracker', 'https://mytracker.example.org', '--notracker'])

        t = torf.Torrent.read(exp_torrent_filepath)
        assert t.trackers == None

        cap = capsys.readouterr()
        assert 'Tracker\t' not in cap.out


def test_single_webseed(capsys, mock_content, autoremove):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with autoremove(exp_torrent_filepath):
        run([content_path, '--webseed', 'https://mywebseed.example.org/foo'])

        t = torf.Torrent.read(exp_torrent_filepath)
        assert t.webseeds == ['https://mywebseed.example.org/foo']

        cap = capsys.readouterr()
        assert 'Webseed\thttps://mywebseed.example.org/foo' in cap.out


def test_multiple_webseeds(capsys, mock_content, autoremove):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with autoremove(exp_torrent_filepath):
        run([content_path,
             '--webseed', 'https://webseed1.example.org/foo',
             '--webseed', 'https://webseed2.example.org/bar/',
             '--webseed', 'https://webseed3.example.org/baz'])

        t = torf.Torrent.read(exp_torrent_filepath)
        assert t.webseeds == ['https://webseed1.example.org/foo',
                              'https://webseed2.example.org/bar/',
                              'https://webseed3.example.org/baz']

        cap = capsys.readouterr()
        assert 'Webseeds\thttps://webseed1.example.org/foo' in cap.out
        assert '\thttps://webseed2.example.org/bar/' in cap.out
        assert '\thttps://webseed3.example.org/baz' in cap.out


def test_nowebseed_option(capsys, mock_content, autoremove):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with autoremove(exp_torrent_filepath):
        run([content_path, '--webseed', 'https://mywebseed.example.org/foo', '--nowebseed'])

        t = torf.Torrent.read(exp_torrent_filepath)
        assert t.webseeds == None

        cap = capsys.readouterr()
        assert 'Webseed\t' not in cap.out
