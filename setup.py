from setuptools import setup, find_packages

with open('torfcli/__vars__.py') as f:
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
    install_requires   = ['torf>=1.0rc5'],

    entry_points       = { 'console_scripts': [ 'torf = torfcli:run' ] },

    classifiers        = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3.6'
    ]
)
