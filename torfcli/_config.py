# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details
# http://www.gnu.org/licenses/gpl-3.0.txt

import re


class ConfigError(Exception):
    def __init__(self, name, value=None, msg=None):
        if value:
            if not msg:
                msg = 'Invalid value'
            super().__init__(f'{name} = {value}: {msg}')
        else:
            if not msg:
                msg = 'Invalid option'
            super().__init__(f'{name!r}: {msg}')


_re_bool = re.compile(r'^(\S+)$')
_re_assign = re.compile(r'^(\S+)\s*=\s*(.*)\s*$')

def read(filepath):
    """Read INI-style file into dictionary"""

    cfg = subcfg = {}
    with open(filepath, 'r') as f:
        for line in (l.strip() for l in f.readlines()):
            # Skip empty lines and comments
            if not line or line[0] == '#':
                continue

            # Start new profile
            if line[0] == '[' and line[-1] == ']':
                profile_name = line[1:-1]
                cfg[profile_name] = subcfg = {}
                continue

            # Boolean option
            bool_match = _re_bool.match(line)
            if bool_match:
                name = bool_match.group(1)
                subcfg[name] = True
                continue

            # Option takes a value
            assign_match = _re_assign.match(line)
            if assign_match:
                name = assign_match.group(1)
                value = assign_match.group(2).strip()
                if value[0] == value[-1] == '"' or value[0] == value[-1] == "'":
                    value = value[1:-1]

                # Multiple occurences of the same name turn its value into a list
                if name in subcfg:
                    if not isinstance(subcfg[name], list):
                        subcfg[name] = [subcfg[name]]
                    subcfg[name].append(value)
                else:
                    subcfg[name] = value

                continue

    return cfg


_invalid_options = ('config', 'noconfig')
def validate(cfgfile, defaults):
    """Return validated values from cfgfile"""

    for opt in _invalid_options:
        if opt in cfgfile:
            raise ConfigError(opt)

    result = {}
    for name,value_cfgfile in tuple(cfgfile.items()):
        # Dictionaries are profiles
        if isinstance(value_cfgfile, dict):
            result[name] = validate(value_cfgfile, defaults)
            continue

        # Non-profile names must be present in defaults
        if name not in defaults:
            raise ConfigError(name)

        # Do type checking or coercion
        value_default = defaults[name]
        if type(value_cfgfile) != type(value_default):
            if type(value_default) is list:
                # We expect a list but value is not - a list option has just one value
                result[name] = [value_cfgfile]
                continue
            elif type(value_cfgfile) is list:
                # We expect a non-list but value is a list
                raise ConfigError(name, value=', '.join((repr(item) for item in value_cfgfile)),
                                  msg='Multiple values not allowed')
            elif type(value_default) is bool:
                raise ConfigError(name, value_cfgfile, msg='Assignment to option')
            else:
                raise ConfigError(name, value_cfgfile)

        result[name] = value_cfgfile

    return result


def combine(cli, cfgfile, defaults):
    """Return combined values from CLI args, cfgfile and defaults"""

    result = {}
    for name in defaults:
        if name in cli:
            result[name] = cli[name]
        elif name in cfgfile:
            result[name] = cfgfile[name]
        else:
            result[name] = defaults[name]

    def apply_profile(profile):
        for name,value in profile.items():
            # CLI option takes precedence over config file
            if name not in cli or cli[name] == defaults[name]:
                if 'no'+name in defaults:
                    # Options that have a 'no*' counterpart reset it
                    result['no'+name] = False
                elif name.startswith('no') and name[2:] in defaults:
                    # 'no*' options reset their counterpart option to its default
                    result[name[2:]] = defaults[name[2:]]

                # Append to lists instead of overwriting the previous value
                if isinstance(result[name], list):
                    if isinstance(value, list):
                        value = result[name] + value
                    else:
                        value = result[name] + [value]

                result[name] = value
            elif name == 'profile':
                for profile_name in value:
                    if profile is cfgfile[profile_name]:
                        raise ConfigError(name='profile', value=profile_name,
                                          msg='Profile references itself')
                    else:
                        apply_profile(cfgfile[profile_name])
        return result

    # Update result with values from specified profile
    profile_names = cli.get('profile', ())
    for profile_name in profile_names:
        profile = cfgfile.get(profile_name)
        if profile is None:
            raise ConfigError(profile_name, msg='No such profile')
        else:
            apply_profile(cfgfile[profile_name])

    return result
