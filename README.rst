
========================
TCT - The Toolchain Tool
========================


------------------------
A tool to run toolchains
------------------------

:Author:          Martin Bless <martin@mbless.de>
:Repository:      https://github.com/marble/TCT.git
:Version:         Early - but working well already :-)
:See also:        https://github.com/marble/Toolchain_RenderDocumentation

.. highlight:: shell
.. default-role:: code


Description
===========

For Linux-like systems. Run `tct --help` after installation.
TCT has subcommands similar to those you may know from GIT.
Try --help on every subcommand and whenever you're missing information.
TCT will then either display help or stop.

Examples::

   (venv)$  tct               --help
   (venv)$  tct config        --help
   (venv)$  tct config get    --help
   (venv)$  tct config list   --help
   (venv)$  tct config remove --help
   (venv)$  tct config set    --help

   (venv)$ tct clean  --help
   (venv)$ tct run    --help


Install
=======

Prepare A Virtualenv
--------------------

The idea to work with TCT goes like this.

#. Create a place to keep 'virtualenv' installations::

      mkdir ~/venvs

#. Create a place for a 'tct' virtualenv::

      mkdir ~/venvs/tct

#. Create the virtualenv::

      cd ~/venvs/tct
      virtualenv venv  # always use 'venv' as name to make it simple

#. Activate the virtual environment and install whatever you need::

      $  source ~/venvs/tct/venv/bin/activate
      (venv)$  pip install --upgrade pip
      (venv)$  pip install --upgrade sphinx
      (venv)$  # ...


Fetch TCT
---------

::

   # just a place to clone to
   gitdir=~/HTDOCS/github.com/marble/TCT.git

   # the source url
   giturl=https://github.com/marble/TCT.git

   git clone  $giturl $gitdir


Install TCT
-----------

   # activate the virtual environment
   source ~/venvs/tct/venv/bin/activate
   cd $gitdir
   (venv)mbless@srv123:~/HTDOCS/github.com/marble/TCT.git$  # <-- the prompt you get

   (venv)$  pip install .  --upgrade  # install from this dir

   (venv)$  cd ~          # go anywhere
   (venv)$  tct --help    # tct should run just like any GNU tool

   # Celebrate the victory!

   # End of this snippet.


.. highlight:: shell

Basic configuration
-------------------

Show::

   (venv)$  tct config list

TCT itself uses these settings::

   [general]
   toolchains_home = /home/mbless/Toolchains
   temp_home = /tmp/TCT

Toolchains use the section with their name. So for example toolchain 'RenderDocumentation'
respects this section::

   [RenderDocumentation]
   email_admin = martin.bless@gmail.com
   webroot_abspath = /home/mbless/public_html
   email_user_to = martin.bless@gmail.com
   htaccess_template_show_latest = /home/mbless/scripts/config/_htaccess
   email_user_cc = martin.bless@typo3.org
   url_of_webroot = https://docs.typo3.org
   email_user_bcc = martin.bless@gmail.com
   webroot_part_of_builddir = /home/mbless/public_html
   lockfile_name = lockfile.json

Examples::

   (venv)$  tct config set --help
   (venv)$  tct config set --section RenderDocumentation  email_user_to  martin@mbless.de

   # verify
   (venv)$  tct config get --section RenderDocumentation  email_user_to
   (venv)$  tct config list


Other sections like `[ServerSrv123]` or `[ServerMarble]` are in there just
for convenience save and keep settings. Unless you have a toolchain with the same
name they are not used.


Provide Toolchains
==================

Create a place::

   mkdir ~/Toolchains

Clone a toolchain::

   git clone https://github.com/marble/Toolchain_RenderDocumentation  ~/Toolchains/RenderDocumentation


Running Toolchains
==================

Understand
----------

Verify toolchain's home is set::

   $(venv)  tct config get toolchains_home
   /home/mbless/Toolchains

Run::

   $ tct run --help
   $ tct -v run RenderDocumentation    # verbose
   $ tct    run RenderDocumentation    # not verbose
   $ tct -D run RenderDocumentation    # debug display params
   $ tct    run RenderDocumentation -n # dry-run

Show the help that the toolchain brings::

   $ tct    run RenderDocumentation --toolchain-help

Remove older builds from temp area FOR THIS TOOLCHAIN::

   $ tct    run RenderDocumentation --clean -n  # dry-run, just list
   $ tct    run RenderDocumentation --clean     # live-run, delete!

Only one instance of 'RenderDocumentation' can be running at a time.
To assure this a lockfile is created. If a prior run fails to remove
that lockfile at the end you can FORCE the removal:

   $ tct    run RenderDocumentation -T unlock


Do the live-run
---------------

The toolchain 'RenderDocumentation' requires a parameter 'makedir'.
TCT's option `-c, --config` can be used multiply and takes a key value pair
each time.

Start a dry-run like this::

   (venv)$ tct run \
      RenderDocumentation \
      --dry-run \
      --config  makedir  /home/mbless/HTDOCS/github.com/TYPO3-Documentation/TYPO3/Reference/CoreApi.git.make

Start a true live-run like this::

   (venv)$ tct run \
      RenderDocumentation \
      --config  makedir  /home/mbless/HTDOCS/github.com/TYPO3-Documentation/TYPO3/Reference/CoreApi.git.make

Force a rebuild regardless of checksums::

   (venv)$ tct run \
      RenderDocumentation \
      --config  makedir  /home/mbless/HTDOCS/github.com/TYPO3-Documentation/TYPO3/Reference/CoreApi.git.make
      --config  rebuild_needed 1

Send notification email to self instead of real user, be verbose::

   (venv)$ tct -v run \
      RenderDocumentation \
      -c  makedir  /home/mbless/HTDOCS/github.com/TYPO3-Documentation/TYPO3/Reference/CoreApi.git.make
      -c  rebuild_needed 1
      -c  email_user_to  self@my.email.address


About the 'makedir' parameter
-----------------------------

This is special to the 'RenderDocumentation' toolchain. Here's just a short
explanation to make this readme complete for some people:

At the moment 'RenderDocumentation' looks at the :file:`makedir` to find the two files
:file:`buildsettings.sh` and :file:`conf.py`. Both are used readonly.

Depending on how far processing gets a file :file:`build.checksum` may be
created there.


Inspect what happened
---------------------

Each live-run creates a folder structure in the temp area that replicates
the toolchain's folder structure. 'params'-files show with which params the tools
were run. 'result'-files contain the output of a single tool.

All data files are JSON files.

A global FACTS file is created and maintained by TCT. Otherwise it should be
treated as readlonly.

The MILESTONES file is most important. It holds the "collective memory" of all
tools. In general, every value that's in there not only has the value but also
carries the message that THE OBJECT DOES IT EXIST. In other word:
The idea is that if a file path is given in MILESTONES that file should actually
exist.

TCT looks at the result file of a single tool after it has run and picks up
information from there that's named 'MILESTONES'. It then adds that information
to the global :file:`MILESTONES.JSON` thereby overwriting if necessary.


((to be continued))