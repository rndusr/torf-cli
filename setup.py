from setuptools import setup, find_packages

with open('torfcli/_vars.py') as f:
    exec(f.read())

try:
    long_description = open('README.rst').read()
except OSError:
    long_description = ''

setup(
    name               = 'torf-cli',
    version            = __version__,

    author             = 'Random User',
    author_email       = 'rndusr@posteo.de',
    license            = 'GPLv3+',
    description        = __description__,
    long_description   = long_description,
    keywords           = 'bittorrent torrent magnet file cli',
    url                = __url__,

    packages           = find_packages(),
    python_requires    = '>=3.6',
    install_requires   = ['torf>=2.0.0', 'pyxdg'],

    entry_points       = { 'console_scripts': [ 'torf = torfcli:run' ] },
    data_files         = [('share/man/man1', ['docs/torf.1'])],

    classifiers        = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3.6'
    ]
)
