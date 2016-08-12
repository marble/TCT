from cStringIO import StringIO
import datetime
import json
import os
import time

def finder(dirpath):
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


if 0 and 'for example':

    for depth, toolchainroot, toolrelpath, toolname, toolabspath in finder(toolchainroot)():
        pass


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
    with file(fpath) as f1:
        result = json.load(f1)
    return result

def writejson(data, fpath):
    with file(fpath, 'w') as f2:
        json.dump(data, f2, sort_keys=True, indent=2, separators=(',', ': '))
    return

def data2json(data):
    io = StringIO()
    json.dump(data, io, sort_keys=True, indent=2, separators=(',', ': '))
    return io.getvalue()
