# -*- coding: utf-8 -*-

"""Utility functions."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import base64
import json
import os.path as op
import os
import sys
import subprocess

from traitlets.config import Config, PyFileConfigLoader
import numpy as np
from six import string_types, exec_
from six.moves import builtins

from ._types import _is_integer

PHY_USER_DIR = op.expanduser('~/.phy/')


#------------------------------------------------------------------------------
# JSON utility functions
#------------------------------------------------------------------------------

def _encode_qbytearray(arr):
    b = arr.toBase64().data()
    data_b64 = base64.b64encode(b).decode('utf8')
    return data_b64


def _decode_qbytearray(data_b64):
    from phy.gui.qt import QtCore
    encoded = base64.b64decode(data_b64)
    out = QtCore.QByteArray.fromBase64(encoded)
    return out


class _CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            obj_contiguous = np.ascontiguousarray(obj)
            data_b64 = base64.b64encode(obj_contiguous.data).decode('utf8')
            return dict(__ndarray__=data_b64,
                        dtype=str(obj.dtype),
                        shape=obj.shape)
        elif obj.__class__.__name__ == 'QByteArray':
            return {'__qbytearray__': _encode_qbytearray(obj)}
        elif isinstance(obj, np.generic):
            return np.asscalar(obj)
        return super(_CustomEncoder, self).default(obj)  # pragma: no cover


def _json_custom_hook(d):
    if isinstance(d, dict) and '__ndarray__' in d:
        data = base64.b64decode(d['__ndarray__'])
        return np.frombuffer(data, d['dtype']).reshape(d['shape'])
    elif isinstance(d, dict) and '__qbytearray__' in d:
        return _decode_qbytearray(d['__qbytearray__'])
    return d


def _intify_keys(d):
    assert isinstance(d, dict)
    out = {}
    for k, v in d.items():
        if isinstance(k, string_types) and k.isdigit():
            k = int(k)
        out[k] = v
    return out


def _stringify_keys(d):
    assert isinstance(d, dict)
    out = {}
    for k, v in d.items():
        if _is_integer(k):
            k = str(k)
        out[k] = v
    return out


def _load_json(path):
    path = op.realpath(op.expanduser(path))
    if not op.exists(path):
        raise IOError("The JSON file `{}` doesn't exist.".format(path))
    with open(path, 'r') as f:
        contents = f.read()
    if not contents:
        return {}
    out = json.loads(contents, object_hook=_json_custom_hook)
    return _intify_keys(out)


def _save_json(path, data):
    assert isinstance(data, dict)
    data = _stringify_keys(data)
    path = op.realpath(op.expanduser(path))
    with open(path, 'w') as f:
        json.dump(data, f, cls=_CustomEncoder, indent=2)


#------------------------------------------------------------------------------
# traitlets config
#------------------------------------------------------------------------------

def _load_config(path):
    if not op.exists(path):
        return {}
    path = op.realpath(path)
    dirpath, filename = op.split(path)
    config = PyFileConfigLoader(filename, dirpath).load_config()
    return config


def load_master_config():
    """Load a master Config file from `~/.phy/phy_config.py`."""
    c = Config()
    paths = [op.join(PHY_USER_DIR, 'phy_config.py')]
    for path in paths:
        c.update(_load_config(path))
    return c


#------------------------------------------------------------------------------
# Various Python utility functions
#------------------------------------------------------------------------------

def _read_python(path):
    path = op.realpath(op.expanduser(path))
    assert op.exists(path)
    with open(path, 'r') as f:
        contents = f.read()
    metadata = {}
    exec_(contents, {}, metadata)
    metadata = {k.lower(): v for (k, v) in metadata.items()}
    return metadata


def _is_interactive():  # pragma: no cover
    """Determine whether the user has requested interactive mode."""
    # The Python interpreter sets sys.flags correctly, so use them!
    if sys.flags.interactive:
        return True

    # IPython does not set sys.flags when -i is specified, so first
    # check it if it is already imported.
    if '__IPYTHON__' not in dir(builtins):
        return False

    # Then we check the application singleton and determine based on
    # a variable it sets.
    try:
        from IPython.config.application import Application as App
        return App.initialized() and App.instance().interact
    except (ImportError, AttributeError):
        return False


def _git_version():
    curdir = os.getcwd()
    filedir, _ = op.split(__file__)
    os.chdir(filedir)
    try:
        fnull = open(os.devnull, 'w')
        version = ('-git-' + subprocess.check_output(
                   ['git', 'describe', '--abbrev=8', '--dirty',
                    '--always', '--tags'],
                   stderr=fnull).strip().decode('ascii'))
        return version
    except (OSError, subprocess.CalledProcessError):  # pragma: no cover
        return ""
    finally:
        os.chdir(curdir)
