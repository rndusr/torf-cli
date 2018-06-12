% TORF(1)

# NAME

torf - Command line tool to create, display and edit torrents

# SYNOPSIS

__torf__ [_PATH_] [_OPTIONS_]

# DESCRIPTION

torf can create new torrents, display information about existing torrents, and
edit torrents (e.g. to remove a comment or change the tracker) without
re-hashing the content.

Create: __torf__ [_PATH_] [_OPTIONS_] [__-o__ _TORRENT_]

Display: __torf__ __-i__ [_TORRENT_]

Edit: __torf__ __-i__ [_TORRENT_] [_OPTIONS_] __-o__ _TORRENT_

# OPTIONS

Options that start with __--no__ take precedence.

_PATH_
:   The path to the torrent's content.

__--exclude__, __-e__ _EXCLUDE_
:   Exclude files from _PATH_ that match the pattern _EXCLUDE_.  This option may
    be given multiple times.  It is ignored if _PATH_ is not a directory.  See
    __EXCLUDING FILES__.

__--in__, __-i__ _TORRENT_
:   Read metainfo from _TORRENT_.

__--out__, __-o__ _TORRENT_
:   Write torrent to _TORRENT_.

    Default: _NAME_**.torrent**

__--magnet__, __-m__
:   Create magnet link.

__--name__, __-n__ _NAME_
:   Destination file or directory when the torrent is downloaded.

    Default: Basename of _PATH_

__--tracker__, __-t__ _URL_
:   The announce URL of a tracker.  This option may be given multiple times.

__--notracker__, __-T__
:   Remove any trackers in edit mode or hide them in display mode.

__--webseed__, __-w__ _URL_
:   A webseed URL (BEP19).  This option may be given multiple times.

__--nowebseed__, __-W__
:   Remove any webseeds in edit mode or hide them in display mode.

__--private__, __-p__
:   Tell clients to use tracker(s) exclusively for peer discovery.

__--noprivate__, __-P__
:   Allow clients to use DHT and PEX for peer discovery.

__--comment__, __-c__ _COMMENT_
:   A comment that is stored in the torrent file.

__--nocomment__, __-C__
:   Remove an existing comment in edit mode or hide it in display mode.

__--date__, __-d__ _DATE_
:   The creation date as _YYYY_**-**_MM_**-**_DD_[ _HH_**:**_MM_[**:**_SS_]]
    __now__ for local time or __today__ for local time at midnight.

    Default: __today__

__--nodate__, __-D__
:   Remove an existing creation date in edit mode or hide it in display mode.

__--xseed__, __-x__
:   Randomize the info hash to help with cross\-seeding.  This simply adds an
    __entropy__ field to the __info__ section of the metainfo and sets it to a
    random integer.

__--noxseed__, __-X__
:   De-randomize a previously randomized info hash of an existing torrent.  This
    removes the __entropy__ field from the __info__ section of the metainfo.

__--nocreator__, __-R__
:   Remove the name of the application that create the torrent in edit mode,
    hide it in display mode or don't add it in create mode.

__--yes__, __-y__
:   Answer all yes/no prompts with "yes".  At the moment, all this does is
    overwrite _TORRENT_ without asking.

__--config__, __-f__ _FILE_
:   Read command line arguments from configuration FILE.  See
    __CONFIGURATION FILE__.

    Default: *$XDG_CONFIG_HOME*__/torf/config__

__--noconfig__, __-F__
:   Do not use any configuration file.

__--profile__, __-z__ PROFILE
:   Use predefined arguments specified in _PROFILE_.  This option may be given
    multiple times.  See __CONFIGURATION FILE__.

__--human__, __-u__
:   Display information in human-readable output even if stdout is not a TTY.
    See __PIPING OUTPUT__.

__--nohuman__, __-U__
:   Display information in machine-readable output even if stdout is a TTY.  See
    __PIPING OUTPUT__.

__--help__, __-h__
:   Display a short help text and exit.

__--version__, __-V__
:   Display the version number and exit.


# EXAMPLES

Create "foo.torrent" with two trackers and don't store the creation date:

    torf path/to/foo
         -t http://example.org:6881/announce
         -t http://example.com:6881/announce
         --nodate

Read "foo.torrent" and print its metainfo:

    torf -i foo.torrent

Print only the name:

    torf -i foo.torrent | grep '^Name' | cut -f2

Change the comment and remove the date from foo.torrent, write the
result to bar.torrent:

    torf -i foo.torrent -c 'New comment' -D -o bar.torrent

# EXCLUDING FILES

The **--exclude** option takes a pattern that is matched against each file path
beneath _PATH_.  Files that match are not included in the torrent.  Matching is
case-insensitive.

Each file path starts with the basename of _PATH_, e.g. if _PATH_ is
"/home/foo/bar", each file path starts with "bar/".

A file path matches if any of its directories or its file name match, e.g. the
pattern "foo" matches the paths "foo/bar/baz", "bar/foo/baz" and "bar/baz/foo".

A pattern must describe the full directory or file name, e.g. the pattern "bar"
does not match the path "foo/barr", but the patterns "bar?" and "bar*" match.

Empty directories and empty files are automatically excluded.

Patterns support these wildcard characters:

| | |
| -----: | :------------------------------- |
|      * | matches everything               |
|      ? | matches any single character     |
|  [SEQ] | matches any character in SEQ     |
| [!SEQ] | matches any character not in SEQ |

# CONFIGURATION FILE

Configuration files list command line options with all leading "-" characters
removed.  If an option takes a parameter, "=" is used as a separator.  Spaces
before and after the "=" are ignored.  The parameter may be quoted with single
or double quotes to preserve leading and/or trailing spaces.  Lines that start
with "#" are ignored.

All of the options listed in the __OPTIONS__ section are allowed except for
*PATH*, __config__, __noconfig__, __profile__, __help__ and __version__.

## Profiles
A profile is a set of options bound to a name that is given to the __--profile__
option.  In the configuration file it is specified as "[_PROFILE NAME_]"
followed by a list of options.  Profiles inherit any options specified globally
at the top of the file, but they can overload them.

## Example

This is an example configuration file with some global custom defaults and the
two profiles "foo" and "bar":

    yes
    nodate
    exclude = *.txt

    [foo]
    tracker = https://foo1/announce
    tracker = https://foo2/announce
    private

    [bar]
    tracker = https://bar/announce
    comment = I love bar.
    xseed

With this configuration file, these arguments are always used:

    --yes
    --nodate
    --exclude '*.txt'

If "--profile foo" is given, it also adds these arguments:

    --tracker https://foo1/announce
    --tracker https://foo2/announce
    --private

If "--profile foo" is given, it also adds these arguments:

    --tracker https://bar/announce
    --comment 'I love bar.'
    --xseed

# PIPING OUTPUT

If stdout is not a TTY (i.e. when output is piped) or if the __--nohuman__
option is provided, the output format is slightly different:

- Leading spaces are removed from each line.

- The delimiter between label and value as well as between multiple values (files,
trackers, etc) is a tab character ("\\t" or ASCII code 0x9).

- Numbers are not formatted (seconds for time deltas, UNIX timestamps for
  timestamps, raw bytes for sizes, etc).

# EXIT STATUS

torf returns zero on success and non-zero on failure.  You can lookup error
codes in the output of __errno -l__.

# REPORTING BUGS

Bug reports, feature requests and poems about hedgehogs are welcome on the
[issue tracker](https://github.com/rndusr/torf-cli/issues).
