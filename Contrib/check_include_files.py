#! /usr/bin/env python
# coding: ascii

"""\
Check include files in a ReST documentation project.

This script verifies that all ReST source files reside within or
below a given ``startdir``. Files that match the pattern "*.rst"
are considered to be source files. The ReST sources are scanned
for ``.. include::`` and ``.. literalinclude::`` directives
and checking continues with included files. The contents of
"literally included" files is not searched for further includes.
Docutils special "<...>" syntax is considered illegal.

Processing stops at the first illegal file.

Since this script only scans the ReST sources on a textual basis
for patterns that look like include directives it may find "false hits".
This will happen for example when an include directive is part of a
codeblock. In the case of "false hits" this script will still try
to follow those include files. Most probably such a file does not
exist. This is not treated as an error by this script.

Exitcodes::

  0 = success
  1 = some error occurred
  2 = wrong parameters
  3 = illegal includes detected

(check_include_files.py, mb, 2013-07-23, 2013-07-26)

"""

__version__ = "0.2.0"
__history__ = ""
__copyright__ = """\

Copyright (c), 2013-2099, Martin Bless  <martin@mbless.de>

All Rights Reserved.

Permission to use, copy, modify, and distribute this software and its
documentation for any purpose and without fee or royalty is hereby
granted, provided that the above copyright notice appears in all copies
and that both that copyright notice and this permission notice appear
in supporting documentation or portions thereof, including
modifications, that you make.

THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO
THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS, IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL,
INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING
FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION
WITH THE USE OR PERFORMANCE OF THIS SOFTWARE!
"""

import os
import sys
import re

ospj = os.path.join
ospe = os.path.exists

checkedfiles = []
checkedincludefiles = []
illegalfiles = []
forbiddenfiles = []
forbiddenfilesparents = []
notreadablefiles = []

# PATHPARTS = splitpath(startdir)
# N_PARTS = len(PATHPARTS)


def normalizepath(p):
    return os.path.normcase(os.path.realpath(p))


def splitpath(p):
    """Split a path to a list of its parts

    Example::

        input : 'D:/Repositories/Demo/Documentation/Index.rst'
        result: ['D:/','Repositories','Demo','Documentation','Index.rst']

    """
    result = []
    left, right = os.path.split(p)
    while True:
        if right:
            result.insert(0, right)
            if left:
                left, right = os.path.split(left)
                continue
        if left:
            result.insert(0, left)
        break
    return result


def processRstFile(filepath, parents=None, recurse=1):
    """Check a ReST source file.

    Check whether filepath is within or below ``startdir``.
    Process include directives.

    """
    ok = False
    restfile = normalizepath(filepath)
    if parents is None:
        parents = []
    if restfile in checkedfiles:
        ok = True
        return ok, parents
    else:
        parts = splitpath(restfile)
        if not parts[:N_PARTS] == PATHPARTS:
            forbiddenfiles.append(restfile)
            forbiddenfilesparents.append(parents)
            ok = False
            return ok, parents
        else:
            checkedfiles.append(restfile)
            ok = True
    if ok and recurse:
        strdata = None
        if ospe(restfile):
            f1 = file(restfile)
            strdata = f1.read()
            f1.close()
        elif ospe(restfile.decode("utf-8", "replace")):
            f1 = file(restfile.decode("utf-8", "replace"))
            strdata = f1.read()
            f1.close()
        else:
            if not restfile in notreadablefiles:
                notreadablefiles.append(restfile)

        if 1 and ok and strdata and "look for ``.. include::`` directives":
            # '\n .. include:: abc.txt \n\n  .. include:: abc.txt'
            filenames = re.findall(
                "^\s*\.\.\s+include::\s*(\S+)\s*$", strdata, flags=+re.MULTILINE
            )
            for filename in filenames:
                if filename[0] == "<":
                    parents.append(restfile)
                    forbiddenfiles.append(filename)
                    forbiddenfilesparents.append(parents)
                    ok = False
                    return ok, parents
                if os.path.isabs(filename):
                    restfile2 = filename
                else:
                    restfile2 = ospj(os.path.dirname(restfile), filename)
                restfile2 = normalizepath(restfile2)
                if not restfile2 in checkedincludefiles:
                    checkedincludefiles.append(restfile2)
                    parents.append(restfile)
                    ok, parents = processRstFile(restfile2, parents, recurse=1)
                    if not ok:
                        break
                    else:
                        parents.pop()
        if 1 and ok and strdata and "look for ``.. literalinclude::`` directives":
            # '\n .. literalinclude:: code.js \n\n  .. literalinclude:: code.php'
            filenames = re.findall(
                "^\s*\.\.\s+literalinclude::\s*(\S+)\s*$", strdata, flags=+re.MULTILINE
            )
            for filename in filenames:
                if filename[0] == "<":
                    parents.append(restfile)
                    forbiddenfiles.append(filename)
                    forbiddenfilesparents.append(parents)
                    ok = False
                    return ok, parents
                if os.path.isabs(filename):
                    restfile2 = filename
                else:
                    restfile2 = ospj(os.path.dirname(restfile), filename)
                restfile2 = normalizepath(restfile2)
                if not restfile2 in checkedincludefiles:
                    checkedincludefiles.append(restfile2)
                    parents.append(restfile)
                    ok, parents = processRstFile(restfile2, parents, recurse=0)
                    if not ok:
                        break
                    else:
                        parents.pop()

    return ok, parents


def main(startdir):
    ok = True
    for path, dirs, files in os.walk(startdir):
        dirs.sort()
        files.sort()
        for fname in files:
            stem, ext = os.path.splitext(fname)
            if ext == ".rst":
                f1path = ospj(path, fname)
                ok, parents = processRstFile(f1path)
            if not ok:
                break
        if not ok:
            break
    return ok, parents


def removestartdir(fname):
    L = splitpath(fname)
    if L[:N_PARTS] == PATHPARTS:
        L = L[N_PARTS:]
        result = ospj(*L)
    else:
        result = fname
    return result


def printresult():
    print

    print "observed files:"
    print "==============="
    if checkedfiles:
        for f in checkedfiles:
            print removestartdir(f)
    else:
        print "None."
    print

    print "observed include files:"
    print "======================="
    if checkedincludefiles:
        for f in checkedincludefiles:
            print removestartdir(f)
    else:
        print "None."
    print

    print "include files that could not be read (= no error):"
    print "=================================================="
    if notreadablefiles:
        for f in notreadablefiles:
            print removestartdir(f)
    else:
        print "None."
    print

    print "forbidden include files:"
    print "========================"
    if forbiddenfilesparents:
        for i, parents in enumerate(forbiddenfilesparents):
            j = 0
            for j in range(len(parents)):
                if j == 0:
                    indent = ""
                else:
                    indent = ("    " * (j - 1)) + "|-- "
                fname = removestartdir(parents[j])
                print "%s%s" % (indent, fname)
            j += 1
            indent = ("    " * (j - 1)) + "|-- "
            fname = removestartdir(forbiddenfiles[i])
            print "%s%s" % (indent, fname)
    else:
        print "None."
    print


def get_argparse_args():
    """Get commandline args using module 'argparse'. Python >= 2.7 required."""

    class License(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            print __copyright__
            parser.exit()

    class History(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            print __history__
            parser.exit()

    class Info(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            print
            print __doc__
            parser.exit()

    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0], add_help=False
    )
    parser.add_argument(
        "--verbose",
        "-v",
        help="verbose - list filenames",
        dest="verbose",
        action="store_true",
    )
    parser.add_argument(
        "--help",
        "-h",
        action="help",
        default=argparse.SUPPRESS,
        help="show this help message and exit",
    )
    parser.add_argument(
        "--info", help="show information and exit", nargs=0, action=Info
    )
    parser.add_argument(
        "--version", help="show version and exit", action="version", version=__version__
    )
    parser.add_argument(
        "--license", help="show license and exit", nargs=0, action=License
    )
    # parser.add_argument('--history', help='show history', nargs=0, action=History)
    parser.add_argument("startdir")
    return parser.parse_args()


class Namespace(object):
    """Simple object for storing attributes."""

    def __init__(self, **kwargs):
        for name in kwargs:
            setattr(self, name, kwargs[name])


if __name__ == "__main__":
    # sys.argv = sys.argv[:1] + [r'D:\kannweg\TO_BE_DELETED_HACKS_XAVIER\Documentation', '-v']

    argparse_available = False
    try:
        import argparse

        argparse_available = True
    except ImportError:
        pass
    if not argparse_available:
        try:
            import local_argparse as argparse

            argparse_available = True
        except ImportError:
            pass
    if argparse_available:
        args = get_argparse_args()
    else:
        args = Namespace()
        args.startdir = ""
    if not args.startdir:
        msg = (
            "\nNote:\n"
            "   '%(prog)s'\n"
            "   needs module 'argparse' (Python >= 2.7) to handle commandline\n"
            "   parameters. It seems that 'argparse' is not available. Provide\n"
            "   module 'argparse' or hardcode parameters in the code instead (exitcode=2).\n"
            % {"prog": sys.argv[0]}
        )
        print msg
        sys.exit(2)
    if not os.path.isdir(args.startdir):
        print "argument is not a directory (exitcode=2)\n"
        sys.exit(2)

    startdir = normalizepath(args.startdir)
    PATHPARTS = splitpath(startdir)
    N_PARTS = len(PATHPARTS)
    ok, parents = main(startdir)
    if args.verbose:
        printresult()
    if ok:
        if args.verbose:
            print "exitcode=0"
        sys.exit(0)
    else:
        if args.verbose:
            print "exitcode=3"
        sys.exit(3)
