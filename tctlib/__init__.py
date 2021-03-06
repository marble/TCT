from __future__ import absolute_import
from cStringIO import StringIO
import codecs
import datetime
import json
import os
import time

__all__ = [
    'data2json',
    'deepget',
    'finder',
    'logstamp',
    'logstamp_finegrained',
    'make_snapshot_of_milestones',
    'msecs',
    'readjson',
    'save_the_result',
    'versiontuple',
    'writejson',
]

def finder(dirpath):
    # Usage:
    # for depth, toolchainroot, toolrelpath, toolname, toolabspath in finder(toolchainroot)():
    #     pass
    #
    dirpathlen = len(dirpath)
    initialdepth = dirpath.count(os.path.sep)
    def finder1():
        for root, dirs, files in os.walk(dirpath):
            depth = root.count(os.path.sep) - initialdepth
            dirs.sort()
            files.sort()
            for file in files:
                fpath = os.path.join(root, file)
                if os.path.isfile(fpath) and os.access(fpath, os.X_OK) and file.startswith('run_'):
                    yield (depth, dirpath, root[dirpathlen:].strip(os.path.sep), file, fpath)
    return finder1

def deepget(dictionary, *keys, **kwargs):
    if 'default' in kwargs:
        default = kwargs['default']
    else:
        default = {}
    result = dictionary
    for k in keys:
        if k in result:
            result = result[k]
        else:
            result = default
            break
    return result


def make_snapshot_of_milestones(milestonesfile_abspath, paramsfile_abspath):
    import shutil

    paramsfile_folder, paramsfile_name = os.path.split(paramsfile_abspath)
    # do a rough check
    if paramsfile_name.startswith('params_'):
        dest = os.path.join(paramsfile_folder, 'milestones_' + paramsfile_name[7:])
        shutil.copy(milestonesfile_abspath, dest)


def msecs(unixtime=None):
    "Return number of msec of current time as string."

    if unixtime is None:
        unixtime = time.time()
    # 1469006952.733832
    # return '1469006952733'
    return str(int(unixtime * 1000))

def logstamp(unixtime=None, fmt='%Y-%m-%d %H:%M'):
    "Return a timestamp suitable for logging like '2016-07-26 21:05'"

    if unixtime is None:
        unixtime = time.time()
    return datetime.datetime.fromtimestamp(unixtime).strftime(fmt)

def logstamp_finegrained(unixtime=None, fmt='%Y-%m-%d_%H-%M-%S_%f'):
    "Return fine grained timestamp like `2016-07-26_21-05-59_888999`."

    return logstamp(unixtime, fmt=fmt)

def readjson(fpath):
    result = None
    with codecs.open(fpath, 'r', 'utf-8', errors='replace') as f1:
        result = json.load(f1)
    return result

def writejson(data, fpath):
    with codecs.open(fpath, 'w', 'utf-8', errors='replace') as f2:
        json.dump(data, f2, sort_keys=True, indent=2, separators=(',', ': '))
    return

def data2json(data):
    io = StringIO()
    json.dump(data, io, sort_keys=True, indent=2, separators=(',', ': '))
    return io.getvalue()

def versiontuple(v, n=12):
   filled = []
   for point in v.split("."):
      filled.append(point.zfill(n))
   return tuple(filled)

def save_the_result(result, resultfile, params, facts, milestones, exitcode,
                    CONTINUE, reason):
    tool_exitcodes_2 = milestones.get('tool_exitcodes_2', {})
    k = '%s/%s' % (params['toolrelpath'], params['toolname'])
    tool_exitcodes_2[k] = '%s,%s,%s' % (exitcode, CONTINUE, reason)
    result['MILESTONES'].append({'tool_exitcodes_2': tool_exitcodes_2})
    writejson(result, resultfile)
    return True
