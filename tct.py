from __future__ import print_function
from __future__ import print_function
import click
import ConfigParser
import cStringIO as StringIO
import os
import shutil
import subprocess
import sys

from tctlib import finder, data2json, readjson, writejson, msecs, logstamp

PY3 = sys.version_info[0] == 3

if PY3:
    string_types = str,
else:
    string_types = basestring,

FACTS = {}
INITIAL_MILESTONES = {'dummy':'1'}
stats_exitcodes = {}
INITIAL_RESULT = {'FACTS':[], 'MILESTONES':[], 'loglist': []}

BUILTIN_CFG = """
[general]
email_admin = martin.bless@gmail.com
toolchains_home = /home/marble/Repositories/mbnas/mbgit/toolchains
temp_home = /home/marble/Repositories/mbnas/mbgit/tct/TEMPROOT_NOT_VERSIONED
# temp_home = /tmp/tct_uczkq9NVCc
"""

user_home = os.path.join(os.path.expanduser('~'))
tctconfig_file_user = os.path.join(user_home, '.tctconfig.cfg')

io = StringIO.StringIO(BUILTIN_CFG)
tctconfig = ConfigParser.RawConfigParser()
tctconfig.readfp(io)
tctconfig_files_successfully_read = tctconfig.read(['/etc/tctconfig.cfg',
                                                    tctconfig_file_user, 'tctconfig.cfg'])
tctconfig_user = ConfigParser.RawConfigParser()
result = tctconfig_user.read(tctconfig_file_user)

try:
    items = tctconfig.items('general')
except ConfigParser.NoSectionError:
    items = []
ctx = {}
for key, value in items:
    ctx[key] = value
CONTEXT_SETTINGS = {'default_map': ctx}
@click.group(context_settings=CONTEXT_SETTINGS)
@click.option('--toolchains-home', default='.',
              metavar='PATH', help='Root folder holding toolchains')
@click.option('--temp-home', default='/tmp/tct',
              metavar='PATH', help='Root folder for tempfiles')
@click.option('--config', '-c', nargs=2, multiple=True,
              metavar='KEY VALUE', help='Define or override config key-value pair (repeatable)')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose mode.')
@click.option('--dump-params', '-D', is_flag=True, help='Dump parameters and exit.')

@click.version_option('1.0')
def cli(toolchains_home, config, verbose, temp_home, dump_params):
    """tct, the toolchain tool, is a command line tool that travels a toolchain
    folder alphabetically and topdown and runs each tool it finds.

    Tools are executable files with a name starting with 'run_'.
    Files are run first. Then processing continues with the next (sub)folder.
    When a tool fails (exitcode != 0) processing stops for the current folder
    and its subfolders. It continues with the next folder in order.

    Use --help with the subcommands.
    """

    FACTS['argv0'] = sys.argv[0] if len(sys.argv) else ''
    FACTS['cmdline'] = ' '.join(sys.argv)
    FACTS['cwd'] = os.path.abspath(os.getcwd())
    FACTS['toolchains_home'] = os.path.abspath(os.path.normpath(toolchains_home))
    FACTS['verbose'] = verbose
    FACTS['temp_home'] = os.path.abspath(os.path.normpath(temp_home))
    FACTS['dump_params'] = dump_params
    FACTS['run_id'] = msecs()
    for key, value in config:
        FACTS[key] = value
    FACTS['binabspath'] = os.path.split(os.path.abspath(os.path.normpath(sys.argv[0])))[0]



def dump_params(facts):
    click.echo(data2json(facts))
    sys.exit()

def possibly_dump_params():
    if FACTS['dump_params']:
        dump_params(FACTS)


@cli.command()
def list():
    """List available toolchains."""

    possibly_dump_params()
    verbose = FACTS['verbose']
    if verbose:
        print("Toolchains in TOOLCHAINS_HOME ('%s'):" % FACTS['toolchains_home'])
    cnt = 0
    for top, dirs, files in os.walk(FACTS['toolchains_home']):
        dirs.sort()
        for item in dirs:
            if item.startswith('.'):
                continue
            cnt += 1
            print('  ', item)
        dirs[:] = []

    if verbose:
        if cnt == 0:
            print("   None.")



@cli.command()
@click.option('--dry-run', '-n', is_flag=True, help='Perform a trial run with no changes made.')
def clean(dry_run):
    """Clean the temp folder."""

    FACTS['clean_command'] = dict(dry_run=dry_run)
    possibly_dump_params()
    live_run = not dry_run
    verbose = FACTS['verbose']
    temp_home = FACTS['temp_home']

    if dry_run:
        click.echo("CLEAN will remove in '%s':" % temp_home)
        cnt = 0
        for top, dirs, files in os.walk(temp_home):
            dirs.sort()
            files.sort()
            dirs[:] = [d for d in dirs if not d in ['.', '..']]
            for d in dirs:
                cnt += 1
                click.echo('   rm -rf %s' % d)
            for f in files:
                cnt += 1
                click.echo('   rm -f %s' % f)
            dirs[:] = []
        if cnt == 0:
            click.echo('   Nothing.')

    if live_run:
        if verbose:
            click.echo("CLEAN is removing in '%s':" % temp_home)
        cnt = 0
        for top, dirs, files in os.walk(temp_home):
            dirs.sort()
            files.sort()
            dirs[:] = [d for d in dirs if not d in ['.', '..']]
            for d in dirs:
                cnt += 1
                if verbose:
                    click.echo('   rm -rf %s' % d)
                shutil.rmtree(os.path.join(top, d))
            for f in files:
                cnt += 1
                if verbose:
                    click.echo('   rm -f %s' % f)
                os.remove(os.path.join(top, f))
            dirs[:] = []
        if cnt == 0:
            if verbose:
                click.echo('   Nothing.')


@cli.command()
@click.argument('toolchain')
@click.option('--config', '-c', nargs=2, multiple=True,
              metavar='KEY VALUE', help='Define or override config key-value pair (repeatable)')
@click.option('--dry-run', '-n', is_flag=True, help='Perform a trial run with no changes made.')
def run(toolchain, config, dry_run):
    """Run a toolchain.

    TOOLCHAIN is the name of the toolchain to be run. It must either be the name of
    a subfolder in TOOLCHAINS_HOME or an absolute path to the toolchain folder.
    """

    FACTS['tc_name'] = toolchain
    FACTS['toolchain_folder'] = os.path.join(FACTS['toolchains_home'], toolchain)
    tempname = '%s-%s' % (FACTS['tc_name'], FACTS['run_id'])
    workdir_home = os.path.join(FACTS['temp_home'], tempname)
    factsfile = os.path.join(workdir_home, 'facts.json')
    milestonesfile = os.path.join(workdir_home, 'milestones.json')
    binabspath = FACTS['binabspath']

    # add parameters to facts so we can check these with --dry-run
    FACTS['run_command'] = dict(
        binabspath=binabspath,
        dry_run=dry_run,
        factsfile=factsfile,
        milestonesfile=milestonesfile,
        tempname=tempname,
        workdir_home=workdir_home,
    )
    for key, value in config:
        FACTS['run_command'][key] = value

    possibly_dump_params()

    if not os.path.exists(FACTS['toolchain_folder']):
        click.echo("Error: Toolchain not found ('%s')" % FACTS['toolchain_folder'])
        sys.exit(1)

    verbose = FACTS['verbose']

    if dry_run:
        click.echo("dry-run: tools in toolchain '%s':" % (FACTS['tc_name'],))
        cnt = 0
        for depth, toolchainroot, toolrelpath, toolname, toolabspath in finder(FACTS['toolchain_folder'])():
            cnt += 1
            click.echo("   %2d %s" %(cnt, os.path.join(toolrelpath, toolname)))
        if cnt == 0:
            click.echo("   Nothing.")

        sys.exit()

    # work!
    if not os.path.exists(workdir_home):
        os.makedirs(workdir_home)
    if not  os.path.exists(factsfile):
        writejson(FACTS, factsfile)
    if not os.path.exists(milestonesfile):
        writejson(INITIAL_MILESTONES, milestonesfile)

    milestones = readjson(milestonesfile)
    tct_skipping = milestones.get('tct_skipping')

    # travel all tools of toolchain
    lastdepth = None
    lasttoolrelpath = None
    skipping = False
    exitcode = 0
    for depth, toolchainroot, toolrelpath, toolname, toolabspath in finder(FACTS['toolchain_folder'])():
        if skipping:
            if exitcode == 99:
                break
            if (depth < lastdepth) or (depth == lastdepth and toolrelpath != lasttoolrelpath):
                skipping = False

        workdir = os.path.join(workdir_home, toolrelpath)
        if tct_skipping:
            if os.path.exists(os.path.join(workdir, 'stop_tct_skipping')):
                tct_skipping = False
        if skipping or tct_skipping:
            continue

        if not os.path.exists(workdir):
            os.makedirs(workdir)
        paramsfile = os.path.join(workdir, 'params.json')
        resultfile = os.path.join(workdir, 'result.json')
        if not os.path.exists(resultfile):
            writejson(INITIAL_RESULT, resultfile)

        cmd = toolabspath + ' ' + paramsfile + ' ' + FACTS['binabspath']
        params = {
            "binabspath": binabspath,
            "cmd": cmd,
            "depth": depth,
            "factsfile": factsfile,
            "milestonesfile": milestonesfile,
            "paramsfile": paramsfile,
            "resultfile": resultfile,
            "temp_home": FACTS['temp_home'],
            "toolabspath": toolabspath,
            "toolchainname": FACTS['tc_name'],
            "toolchain_folder": FACTS['toolchain_folder'],
            "toolchains_home": FACTS['toolchains_home'],
            "toolname": toolname,
            "toolrelpath": toolrelpath,
            "workdir": workdir,
            "workdir_home": workdir_home,
        }
        params['params_help'] = {
            "binabspath": "Path to the 'bin/' folder holding TCT and other scripts",
            "cmd": "The commandline that launched this tool",
            "depth": "Depth of the folder of this tool within the toolchain",
            "factsfile": "Absolute path to the JSON file with all the global facts",
            "milestonesfile": "Absolute path to the JSON file where we collect global milestone facts",
            "paramsfile": "Absolute path to the JSON file that holds the parameters for this tool. The tools should only read from it.",
            "resultfile": "Absolute path to the JSON file where this tool should save its results and processing notes in",
            "temp_home": "Absolute path to the folder where temp files are created in",
            "toolabspath": "Absolute path to this tool. A 'tool' is an executable file with a name starting with 'run_'.",
            "toolchainname": "Name of the toolchain. It is equal to the name of the folder where the toolchain starts.",
            "toolchain_folder": "Absolute path to the active (=current) toolchain",
            "toolchains_home": "Absolute path to the root folder holding toolchains",
            "toolname": "The filename of the executable file. It starts with 'run_'.",
            "toolrelpath": "The relative path in the toolchain",
            "workdir": "Absolute path to the workdir for this tool. The tool should think of this folder as 'tempdir'.",
            "workdir_home":
                ("This is the root of all of our workdir folders. It corresponds to the root folder of the toolchain. "
                 "The folder structure within is the same as the folder structure of the toolchain."),
        }
        for key, value in config:
            params[key] = value
        writejson(params, paramsfile)
        tool_id = os.path.join(toolrelpath, toolname)

        if verbose:
            click.echo()
            click.echo('==================================================')
            click.echo('   %s' % tool_id)

        exitcode = subprocess.call(cmd, shell=True, cwd=workdir)

        stats_exitcodes[exitcode] = stats_exitcodes.get(exitcode, 0) + 1

        facts = readjson(factsfile)
        milestones = readjson(milestonesfile)
        result = readjson(resultfile)
        writejson(result, resultfile)
        facts['TOOL_exitcodes'] = facts.get('TOOL_exitcodes', {})
        facts['TOOL_facts'] = facts.get('TOOL_facts', {})
        facts['TOOL_exitcodes'][tool_id] = exitcode
        facts['TOOL_facts'][toolrelpath] = result.get('FACTS')
        writejson(facts, factsfile)

        toolmilestones = result.get('MILESTONES')
        if toolmilestones:
            if isinstance(toolmilestones, string_types):
                toolmilestones = [toolmilestones]
            ok = isinstance(toolmilestones, type([]))
            ok = [ok]
            if ok[0]:
                def xx(toolmilestones, ok):
                    for item in toolmilestones:
                        if isinstance(item, string_types):
                            milestones[item] = 1
                        elif isinstance(item, type([])):
                            for item2 in toolmilestones:
                                xx(item2, ok)
                        elif isinstance(item, type({})):
                            for key in item:
                                milestones[key] = item[key]
                        else:
                            ok[0] = False
                xx(toolmilestones, ok)
            if 0 or (not ok[0]):
                milestones[toolrelpath] = toolmilestones

        writejson(milestones, milestonesfile)

        if exitcode > 0:
            skipping = True
            lastdepth = depth
            lasttoolrelpath = toolrelpath

    if verbose:
        click.echo()
        click.echo('We saw these exitcodes (code, count):')
        click.echo(data2json(stats_exitcodes))


@cli.group()
def config():
    """Handle the USER configuration file ~/.tctconfig.cfg"""

@config.command()
def list():
    """Print configuration to stdout."""
    buf = StringIO.StringIO()
    tctconfig.write(buf)
    click.echo(buf.getvalue().strip('\n'))

    if FACTS.get('verbose'):
        click.echo('Possible locations: %r' % ['BUILTIN', '/etc/tctconfig.cfg', tctconfig_file_user, 'tctconfig.cfg'])
        click.echo('Locations read from: %r' % tctconfig_files_successfully_read)

@config.command()
@click.argument('key')
@click.option('--section', '-s', default='general', help="The section name. Defaults to 'general'")
def get(key, section):
    """Get the value for KEY from configuration file."""

    try:
        result = tctconfig_user.get(section, key)
    except ConfigParser.NoOptionError:
        result = 'Error: Option not found.'
    click.echo(result)


@config.command()
@click.argument('key')
@click.option('--section', '-s', default='general', help="The section name. Defaults to 'general'")
def remove(key, section):
    """Remove KEY from the given section of the configuration file."""

    removed = False
    try:
        removed = tctconfig_user.remove_option(section, key)
    except ConfigParser.NoSectionError:
        pass
    if removed:
        with file(tctconfig_file_user, 'w') as f2:
            tctconfig_user.write(f2)



@config.command()
@click.argument('key')
@click.argument('value')
@click.option('--section', '-s', default='general', help="The section name. Defaults to 'general'")
def set(key, value, section):
    """Set VALUE for KEY in configuration file."""

    if not section in tctconfig_user.sections():
        tctconfig_user.add_section(section)
    tctconfig_user.set(section, key, value)
    with file(tctconfig_file_user,'w') as f2:
        tctconfig_user.write(f2)

