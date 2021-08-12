from __future__ import absolute_import

import codecs
import datetime
import json
import os
import subprocess
import sys
import time

try:
    from io import StringIO
except ImportError:
    from cStringIO import StringIO

# Keeplist for PyCharm's `optimize imports`:
codecs, datetime, json, os, subprocess, sys, time, StringIO


__all__ = [
    "cmdline",
    "data2json",
    "deepget",
    "execute_cmdlist",
    "finder",
    "logstamp",
    "logstamp_finegrained",
    "make_snapshot_of_milestones",
    "msecs",
    "PY3",
    "readjson",
    "save_the_result",
    "StringIO",
    "ustr",
    "versiontuple",
    "writejson",
]

PY3 = sys.version_info[0] == 3


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
                if (
                    os.path.isfile(fpath)
                    and os.access(fpath, os.X_OK)
                    and file.startswith("run_")
                ):
                    yield (
                        depth,
                        dirpath,
                        root[dirpathlen:].strip(os.path.sep),
                        file,
                        fpath,
                    )

    return finder1


def deepget(dictionary, *keys, **kwargs):
    if "default" in kwargs:
        default = kwargs["default"]
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
    if paramsfile_name.startswith("params_"):
        dest = os.path.join(paramsfile_folder, "milestones_" + paramsfile_name[7:])
        shutil.copy(milestonesfile_abspath, dest)


def msecs(unixtime=None):
    "Return number of msec of current time as string."

    if unixtime is None:
        unixtime = time.time()
    # 1469006952.733832
    # return '1469006952733'
    return str(int(unixtime * 1000))


def logstamp(unixtime=None, fmt="%Y-%m-%d %H:%M"):
    "Return a timestamp suitable for logging like '2016-07-26 21:05'"

    if unixtime is None:
        unixtime = time.time()
    return datetime.datetime.fromtimestamp(unixtime).strftime(fmt)


def logstamp_finegrained(unixtime=None, fmt="%Y-%m-%d_%H-%M-%S_%f"):
    "Return fine grained timestamp like `2016-07-26_21-05-59_888999`."

    return logstamp(unixtime, fmt=fmt)


def readjson(fpath):
    result = None
    with codecs.open(fpath, "r", "utf-8", errors="replace") as f1:
        result = json.load(f1)
    return result


def writejson(data, fpath):
    with codecs.open(fpath, "w", "utf-8", errors="replace") as f2:
        json.dump(data, f2, sort_keys=True, indent=2, separators=(",", ": "))
    return


def data2json(data):
    return json.dumps(data, sort_keys=True, indent=2, separators=(",", ": "))


def versiontuple(v, n=12):
    filled = []
    for point in v.split("."):
        filled.append(point.zfill(n))
    return tuple(filled)


def save_the_result(
    result, resultfile, params, facts, milestones, exitcode, CONTINUE, reason
):
    tool_exitcodes_2 = milestones.get("tool_exitcodes_2", {})
    k = "%s/%s" % (params["toolrelpath"], params["toolname"])
    tool_exitcodes_2[k] = "%s,%s,%s" % (exitcode, CONTINUE, reason)
    result["MILESTONES"].append({"tool_exitcodes_2": tool_exitcodes_2})
    writejson(result, resultfile)
    return True


def ustr(s, encoding='utf-8', errors='strict'):
    result = s.decode(encoding, errors) if type(s) == bytes else s
    return result


def cmdline(cmd, cwd=None):
    if cwd is None:
        cwd = os.getcwd()
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, cwd=cwd
    )
    out, err = process.communicate()
    out = ustr(out, errors='replace')
    err = ustr(err, errors='replace')
    exitcode = process.returncode
    return exitcode, cmd, out, err


class ExecuteParams:
    toolname_pure = 'toolname_pure'
    workdir = 'workdir'
    xeq_name_cnt = 0


def execute_cmdlist(cmdlist, cwd=None, ns=object()):
    cmd = " ".join(cmdlist)
    cmd_multiline = " \\\n   ".join(cmdlist) + "\n"

    ns.xeq_name_cnt += 1
    filename_cmd = "xeq-%s-%d-%s.txt" % (ns.toolname_pure, ns.xeq_name_cnt, "cmd")
    filename_err = "xeq-%s-%d-%s.txt" % (ns.toolname_pure, ns.xeq_name_cnt, "err")
    filename_out = "xeq-%s-%d-%s.txt" % (ns.toolname_pure, ns.xeq_name_cnt, "out")

    with codecs.open(os.path.join(ns.workdir, filename_cmd), "w", "utf-8") as f2:
        f2.write(ustr(cmd_multiline))

    exitcode, cmd, out, err = cmdline(cmd, cwd=cwd)

    ns.loglist.append({"exitcode": exitcode, "cmd": cmd, "out": out, "err": err})

    with codecs.open(os.path.join(ns.workdir, filename_out), "w", "utf-8") as f2:
        f2.write(out)

    with codecs.open(os.path.join(ns.workdir, filename_err), "w", "utf-8") as f2:
        f2.write(err)

    return exitcode, cmd, out, err


