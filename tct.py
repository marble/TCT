#! /usr/bin/env python
# coding: utf-8

from __future__ import print_function
import click
import ConfigParser
import cStringIO as StringIO
import os
import shutil
import subprocess
import sys

from tctlib import *

__VERSION__ = '0.2.0'

PY3 = sys.version_info[0] == 3

if PY3:
    string_types = str,
else:
    string_types = basestring,

FACTS = {'main_cfg_file': None}
INITIAL_MILESTONES = {'dummy':'1'}
INITIAL_RESULT = {'FACTS':[], 'MILESTONES':[], 'loglist': []}
final_exitcode = None
stats_exitcodes = {}

BUILTIN_CFG = """

[general]
temp_home = /tmp/TCT
toolchains_home = /tmp/Toolchains

"""

# How the configuration is found:
# 1. Start with empty 'tctconfig'
# 2. Update with BUILTIN_CFG
# 3. Update with /etc/tctconfig.cfg (if found)
# 4. Update with ~/.tctconfig.cfg (if found). Set as FACTS['main_cfg_file']
# 5. Update with ./tctconfig.cfg (if found)

user_home = os.path.join(os.path.expanduser('~'))
tctconfig_file_user = os.path.join(user_home, '.tctconfig.cfg')

io = StringIO.StringIO(BUILTIN_CFG)
tctconfig = ConfigParser.RawConfigParser()
tctconfig.readfp(io)
FACTS['config_files_parsed'] = tctconfig.read(['/etc/tctconfig.cfg',
                                                    tctconfig_file_user, 'tctconfig.cfg'])
# consider the user cfg file to be 'main'
tctconfig_main = ConfigParser.RawConfigParser()
if len(tctconfig_main.read(tctconfig_file_user)):
    FACTS['main_cfg_file'] = tctconfig_file_user

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
              metavar='KEY VALUE', help='Define or override config key-value pair (repeatable, '
                                        'handed over to the toolchain)')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose mode.')
@click.option('--cfg-file', default=None,
              metavar='PATH', help='Read all configuration from this file only. Don\'t use other \'tctconfig.cfg\' files.')
@click.option('--active-section', default=None,
              metavar='SECTION_NAME', help='Specifies which section of the cfg-file is to be used.')

@click.version_option(__VERSION__)
def cli(toolchains_home, config, verbose, temp_home, cfg_file, active_section):
    """TCT, the toolchain tool, runs all tools of a folder and its subfolders.

    It travels the folder in alphabetical order and topdown. A tool is an
    executable file of any kind that has a name starting with 'run_'. Files are
    run first followed by subfolders. If a tool fails (exitcode != 0) processing
    stops for the rest of that folder and continues with the next. An exitcode
    >= 90 will stop all further processing of the toolchain.

    Use --help with the subcommands.

    """
    global tctconfig_main
    if cfg_file:
        tctconfig = ConfigParser.RawConfigParser()
        FACTS['config_files_parsed'] = tctconfig.read(cfg_file)
        try:
            items = tctconfig.items('general')
        except ConfigParser.NoSectionError:
            items = []
        for key, value in items:
            CONTEXT_SETTINGS['default_map'][key] = value
        if not active_section:
            active_section = CONTEXT_SETTINGS['default_map'].get('active_section')
        # An explicitely specified file will be the main file
        FACTS['main_cfg_file'] = cfg_file
        tctconfig_main = tctconfig

    if not active_section:
        active_section = 'Default'
    FACTS['active_section'] = active_section
    FACTS['argv0'] = sys.argv[0] if len(sys.argv) else ''
    FACTS['cmdline'] = ' '.join(sys.argv)
    FACTS['cwd'] = os.path.abspath(os.getcwd())
    FACTS['toolchains_home'] = os.path.abspath(os.path.normpath(toolchains_home))
    FACTS['verbose'] = verbose
    FACTS['temp_home'] = os.path.abspath(os.path.normpath(temp_home))
    FACTS['run_id'] = logstamp_finegrained()
    for key, value in config:
        FACTS[key] = value
    FACTS['python_exe_abspath'] = subprocess.check_output('which python', shell=True).strip()

    # FACTS['binabspath']:  '/.../tct/venv/bin/' is what we are looking for
    if __name__ == '__main__':
        # when running tct/tct.py directly we need to deduce from the Python executable
        FACTS['binabspath'] = os.path.split(FACTS['python_exe_abspath'])[0]
    else:
        # When we run 'tct' at the commandline, then we actually run '/.../tct/venv/bin/tct'.
        # We prefer to take that value.
        FACTS['binabspath'] = os.path.split(os.path.abspath(os.path.normpath(sys.argv[0])))[0]


def dump_params(facts):
    click.echo(data2json(facts))
    sys.exit()


def possibly_dump_params():
    if FACTS['dump_params']:
        dump_params(FACTS)


@cli.command()
@click.option('--dump-params', '-D', is_flag=True, help='Dump parameters and exit.')
def list(dump_params):
    """List available toolchains."""

    FACTS['dump_params'] = dump_params
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
@click.option('--dump-params', '-D', is_flag=True, help='Dump parameters and exit.')
@click.option('--yes', is_flag=True, prompt='CLEAN the whole temp folder - really?')
def clean(dump_params, yes):
    """Clean the temp folder."""

    FACTS['clean_command'] = dict(dry_run=not yes)
    FACTS['dump_params'] = dump_params
    possibly_dump_params()
    live_run = yes
    dry_run = not live_run
    verbose = FACTS['verbose']
    temp_home = FACTS['temp_home']

    # sanity check
    ok = True
    parts = temp_home.split(os.path.sep)

    if ok and not temp_home.startswith(os.path.sep):
        ok = False
    if ok and len(parts) < 3:
        ok = False
    if ok and parts[1] not in ['temp', 'tmp', 'home']:
        ok = False
    if ok and parts[1] == 'home' and len(parts) < 4:
        ok = False

    if not ok:
        click.echo("CLEAN doesn't dare deleting in '%s':" % temp_home)

    elif ok and dry_run:
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

    elif ok and live_run:
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
    else:
        pass


@cli.command()
@click.argument('toolchain')
@click.option('--config', '-c', nargs=2, multiple=True,
              metavar='KEY VALUE', help='Define or override config key-value pair (repeatable)')
@click.option('--dry-run', '-n', is_flag=True, help='Perform a trial run with no changes made.')
@click.option('--clean-but', default=None, type=click.IntRange(0, 99),
              help=('Remove subdirs from toolchains\'s temp folder. But keep the last 0..99 '
                    'in order of folder name. Afterwards exit.'))
@click.option('--toolchain-help', is_flag=True, help='Tell the toolchain to display its help text. '
              'The toolchain should do that and then exit.')
@click.option('--toolchain-action', '-T', multiple=True,
              metavar='ACTION',
              help='Tell the toolchain to execute the action. (repeatable)')
@click.option('--dump-params', '-D', is_flag=True, help='Dump parameters and exit.')
def run(toolchain, config, dry_run, toolchain_help, toolchain_action, clean_but, dump_params):
    """Run a toolchain.

    TOOLCHAIN is the name of the toolchain to be run. It must either be the name of
    a subfolder in TOOLCHAINS_HOME or an absolute path to the toolchain folder.
    """

    FACTS['dump_params'] = dump_params
    FACTS['toolchain_name'] = toolchain
    FACTS['toolchain_folder'] = os.path.join(FACTS['toolchains_home'], toolchain)
    FACTS['toolchain_help'] = toolchain_help
    FACTS['toolchain_actions'] = toolchain_action # from singular to plural
    FACTS['toolchain_temp_home'] = os.path.join(FACTS['temp_home'], toolchain)
    tempname = '%s' % (FACTS['run_id'],)
    workdir_home = os.path.join(FACTS['toolchain_temp_home'], tempname)
    factsfile = os.path.join(workdir_home, 'facts.json')
    milestonesfile = os.path.join(workdir_home, 'milestones.json')
    binabspath = FACTS['binabspath']

    possibly_dump_params()

    if clean_but is not None:
        parts = FACTS['toolchain_temp_home'].split('/')
        ok = len(parts) >= 4 and parts[-2] == 'TCT'
        for top, dirs, files in os.walk(FACTS['toolchain_temp_home']):
            dirs.sort(reverse=True)
            cnt = 0
            for dir in dirs:
                cnt +=1
                dest = os.path.join(top,dir)
                if cnt <= clean_but:
                    todo = 'keep'
                else:
                    todo = 'remove'
                if dry_run or FACTS['verbose']:
                    print('%2d (%d to keep)  %s: %s' % (cnt, clean_but, todo, dest))
                if not dry_run and cnt > clean_but:
                    shutil.rmtree(os.path.join(top, dir))
            break
        sys.exit(0)

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

    FACTS['tctconfig'] = {}
    for section in tctconfig.sections():
        FACTS['tctconfig'][section] = FACTS['tctconfig'].get(section, {})
        for option in tctconfig.options(section):
            FACTS['tctconfig'][section][option] = tctconfig.get(section, option)

    possibly_dump_params()

    if not os.path.exists(FACTS['toolchain_folder']):
        click.echo("Error: Toolchain not found ('%s')" % FACTS['toolchain_folder'])
        sys.exit(1)

    verbose = FACTS['verbose']

    if dry_run:
        click.echo("dry-run: tools in toolchain '%s':" % (FACTS['toolchain_name'],))
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
        # skipping means: Skip all the rest in the current folder, including subfolders
        if skipping:
            # exitcodes >= 90 stop the toolchain
            # usually we use: 90 .. 97 for some planned stopping
            # 98 for: stop for debugging
            # 99 for: we stop because we detected some kind of problem
            if exitcode >= 90:
                break
            if (depth < lastdepth) or (depth == lastdepth and toolrelpath != lasttoolrelpath):
                skipping = False

        toolname_pure = os.path.splitext(toolname)[0][4:]
        toolfolderabspath = os.path.split(toolabspath)[0]
        workdir = os.path.join(workdir_home, toolrelpath)
        if tct_skipping:
            if os.path.exists(os.path.join(workdir, 'stop_tct_skipping')):
                tct_skipping = False
        if skipping or tct_skipping:
            continue

        if not os.path.exists(workdir):
            os.makedirs(workdir)
        paramsfile = os.path.join(workdir, 'params_' + toolname[4:] + '.json')
        resultfile = os.path.join(workdir, 'result_' + toolname[4:] + '.json')
        if not os.path.exists(resultfile):
            writejson(INITIAL_RESULT, resultfile)

        cmd = [toolabspath, paramsfile, FACTS['binabspath']]
        params = {
            "binabspath": binabspath,
            "cmd": ' '.join(cmd),
            "depth": depth,
            "factsfile": factsfile,
            "milestonesfile": milestonesfile,
            "paramsfile": paramsfile,
            "resultfile": resultfile,
            "temp_home": FACTS['temp_home'],
            "toolabspath": toolabspath,
            "toolchain_actions": FACTS['toolchain_actions'],
            "toolchain_name": FACTS['toolchain_name'],
            "toolchain_folder": FACTS['toolchain_folder'],
            "toolchain_help": FACTS['toolchain_help'],
            "toolchain_temp_home": FACTS['toolchain_temp_home'],
            "toolchains_home": FACTS['toolchains_home'],
            "toolfolderabspath": toolfolderabspath,
            "toolname": toolname,
            "toolname_pure": toolname_pure,
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
            "toolchain_actions": "List of actions (=words) the toolchain should do.",
            "toolchain_name": "Name of the toolchain. It is equal to the name of the folder where the toolchain starts.",
            "toolchain_folder": "Absolute path to the active (=current) toolchain",
            "toolchain_help": "If True, the toolchain should display its help and exit.",
            "toolchain_temp_home": "Absolute path to the root folder for temp files of this toolchain.",
            "toolchains_home": "Absolute path to the root folder holding toolchains",
            "toolfolderabspath": "Absolute path to the folder of the current tool.",
            "toolname": "The filename of the executable file. It starts with 'run_', like 'run_01-Initialize.sh'",
            "toolname_pure": "The meaningful part of the toolname, like '01-Initialize'",
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


        # START the tool


        if cmd[0].endswith('.py'):
            # If tool is a Python script we explicitly run it like 'python tool.py params ...' because
            # PyCharm in that case automatically turns debugging mode on for spawned subprocesses if
            # debugging is already active.
            cmd.insert(0, FACTS['python_exe_abspath'])
            exitcode = subprocess.call(cmd, shell=False, cwd=workdir)
        else:
            # If tool is not a Python script let the shell find out how to run the tool.
            exitcode = subprocess.call(cmd, shell=True, cwd=workdir)

        if verbose:
            click.echo('   exitcode: %s' % exitcode)

        stats_exitcodes[exitcode] = stats_exitcodes.get(exitcode, 0) + 1

        facts = readjson(factsfile)
        milestones = readjson(milestonesfile)
        final_exitcode = milestones.get('FINAL_EXITCODE')
        result = readjson(resultfile)
        writejson(result, resultfile)

        milestones['tools_exitcodes'] = milestones.get('tools_exitcodes', {})
        milestones['tools_facts'] = milestones.get('tools_facts', {})
        milestones['tools_exitcodes'][tool_id] = exitcode
        milestones['tools_facts'][toolrelpath] = result.get('FACTS')

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
    if final_exitcode is not None:
        if verbose:
            click.echo('exiting with exitcode %s' % final_exitcode)
        sys.exit(final_exitcode)


@cli.group()
def config():
    """List and get cfg data. Update main cfg file (~/.tctconfig.cfg or specified)"""

@config.command()
@click.option('--dump-params', '-D', is_flag=True, help='Dump parameters and exit.')
def list(dump_params):
    """Print configuration to stdout."""

    FACTS['dump_params'] = dump_params
    possibly_dump_params()

    buf = StringIO.StringIO()
    tctconfig.write(buf)
    click.echo(buf.getvalue().strip('\n'))

    if FACTS.get('verbose'):
        click.echo('Possible locations: %r' % ['BUILTIN', '/etc/tctconfig.cfg', tctconfig_file_user, 'tctconfig.cfg'])
        click.echo('Locations read from: %r' % FACTS['config_files_parsed'])

@config.command()
@click.argument('key')
@click.option('--section', '-s', default='general', help="The section name. Defaults to 'general'")
@click.option('--dump-params', '-D', is_flag=True, help='Dump parameters and exit.')
def get(key, section, dump_params):
    """Get the value for KEY from main configuration file."""

    FACTS['dump_params'] = dump_params
    possibly_dump_params()

    try:
        result = tctconfig_main.get(section, key)
    except ConfigParser.NoOptionError:
        result = 'Error: Option not found.'
    click.echo(result)


@config.command()
@click.argument('key')
@click.option('--section', '-s', default='general', help="The section name. Defaults to 'general'")
@click.option('--dump-params', '-D', is_flag=True, help='Dump parameters and exit.')
def remove(key, section, dump_params):
    """Remove KEY from the given section of the main configuration file."""

    global tctconfig_main
    FACTS['dump_params'] = dump_params
    possibly_dump_params()

    if FACTS['main_cfg_file']:
        removed = False
        try:
            removed = tctconfig_main.remove_option(section, key)
        except ConfigParser.NoSectionError:
            pass
        if removed:
            with file(FACTS['main_cfg_file'], 'w') as f2:
                tctconfig_main.write(f2)
    else:
        click.echo('There is no \'main_cfg_file\'')


@config.command()
@click.argument('key')
@click.argument('value')
@click.option('--section', '-s', default='general', help="The section name. Defaults to 'general'")
@click.option('--dump-params', '-D', is_flag=True, help='Dump parameters and exit.')
def set(key, value, section, dump_params):
    """Set VALUE for KEY in main configuration file."""

    global tctconfig_main
    FACTS['dump_params'] = dump_params
    possibly_dump_params()

    if FACTS['main_cfg_file']:
        if not section in tctconfig_main.sections():
            tctconfig_main.add_section(section)
        tctconfig_main.set(section, key, value)
        with file(FACTS['main_cfg_file'], 'w') as f2:
            tctconfig_main.write(f2)
    else:
        click.echo('There is no \'main_cfg_file\'')


if 1 and __name__ == "__main__":
    # while developing: Simulate commandline parameters
    # assume cwd=/home/marble/Repositories/mbnas/mbgit/tct, so ../Makedirs/manual_gettingstarted.make is correct

    subprocess.call('tct -v run RenderDocumentation -T unlock', shell=True)
    subprocess.call('tct -v run RenderDocumentation --clean-but 0', shell=True)
    if 1:
        sys.argv[1:] = [e for e in (
            '-v run RenderDocumentation '
            # '-c makedir ../Makedirs/manual_gettingstarted.make '
            # '-c makedir /home/marble/Repositories/mbnas/mbgit/Makedirs/Public-Info-000.make '
            # '-c makedir /home/marble/Repositories/mbnas/mbgit/Makedirs/ext_sphinx.make '
            # '-c makedir /home/marble/Repositories/mbnas/mbgit/Makedirs/manual_sphinx.make-fr_FR '
            # '-c makedir /home/marble/Repositories/mbnas/mbgit/Makedirs/manual_sphinx.make '
            # '-c makedir /home/marble/Repositories/mbnas/mbgit/Makedirs/manual_sphinx-from-ter.make '
            '-c makedir /home/marble/Repositories/mbnas/mbgit/Makedirs/00makedir '
            # '-c giturl https://github.com/kaystrobach/TYPO3.dyncss '
            # '-c gitdir /tmp/T3REPOS/https-github-com-kaystrobach-TYPO3-dyncss '
            '-c giturl https://github.com/kaystrobach/FLOW.Developmenttools '
            '-c giturl https://git.typo3.org/TYPO3CMS/Extensions/extension_builder '
            '-c email_admin_send_extra_mail 1 '
            '-c email_user_do_not_send 1 '
            '-c rebuild_needed 1 '
            '-c talk 2 '
            '-c make_singlehtml 0 '
            '-c make_latex 0 '
            '-c make_package 1 ').split(' ') if e]
    cli()

elif __name__ == "__main__":
    cli()

