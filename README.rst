

========================
TCT - The Toolchain Tool
========================


------------------------
A tool to run toolchains
------------------------

:Author:          Martin Bless <martin@mbless.de>
:Repository:      https://github.com/marble/TCT.git
:Version:         Early Alpha

.. highlight:: shell
.. default-role:: code

Description
===========

For Linux-like systems. Run `tct --help` after installation.

((...))


Install
=======

::

   gitdir=/home/mbless/HTDOCS/github.com/marble/TCT.git
   git clone https://github.com/marble/TCT.git $gitdir

   # activate an existing, virtual environment
   source ~/venvs/tct/venv/bin/activate
   (venv)mbless@srv123:~/HTDOCS/github.com/marble/TCT.git$  # <-- the prompt you get

   # choose only ONE method of the two:

   # method 1:
   (venv)$  cd $gitdir
   (venv)$  pip install --editable .

   # method 2:
   (venv)$  cd $gitdir
   (venv)$  pip install .

   # test
   (venv)$  cd ~
   (venv)$  tct --help

   # victory!


Configure
=========

Learn how to get help::

   (venv)$  tct               --help
   (venv)$  tct config        --help
   (venv)$  tct config get    --help
   (venv)$  tct config list   --help
   (venv)$  tct config remove --help
   (venv)$  tct config set    --help

.. highlight:: none

You will see something like::

   Usage: tct config [OPTIONS] COMMAND [ARGS]...

     Handle the USER configuration file ~/.tctconfig.cfg

   Options:
     --help  Show this message and exit.

   Commands:
     get     Get the value for KEY from configuration...
     list    Print configuration to stdout.
     remove  Remove KEY from the given section of the...
     set     Set VALUE for KEY in configuration file.

.. highlight:: shell


List the current or builtin configuration::

   $ tct config list
   [RenderDocumentation]
   email_admin = martin.bless@gmail.com
   email_user_instead_of_real = martin.bless@gmail.com
   email_user_these_too = martin.bless@gmail.com
   temp_home = /home/marble/Repositories/mbnas/mbgit/tct/TEMPROOT_NOT_VERSIONED
   toolchains_home = /home/marble/Repositories/mbnas/mbgit/toolchains
   webroot_abspath = /home/mbless/public_html


Set proper values once::

   # set admin email
   tct config set  -s RenderDocumentation email_admin  martin.bless@typo3.org

   # if set, send emails user here instead
   tct config set  -s RenderDocumentation email_user_instead_of_real  martin.bless@typo3.org,martin.bless@typo3.org

   # if set, send emails user additionally here
   tct config set  -s RenderDocumentation email_user_these_too  martin.bless@typo3.org,martin.bless@typo3.org

   # the root of tmpfiles for TCT
   tct config set  -s RenderDocumentation temp_HOME  /tmp/TCT

   # Where do we provide toolchains?
   tct config set  -s RenderDocumentation toolchains_home  /home/mbless/Toolchains

   # on the server - no / at the end!
   tct config set  -s RenderDocumentation webroot_abspath  /home/mbless/public_html


Verify::

   $ tct config list
   [RenderDocumentation]
   email_admin = martin.bless@gmail.com
   email_user_instead_of_real = martin.bless@gmail.com
   email_user_these_too = martin.bless@gmail.com
   temp_home = /home/marble/Repositories/mbnas/mbgit/tct/TEMPROOT_NOT_VERSIONED
   toolchains_home = /home/marble/Repositories/mbnas/mbgit/toolchains
   webroot_abspath = /home/mbless/public_html


Run a toolchain::

   # get help
   $ tct run --help

   # run a simulation (dry-run)
   $ tct run \
      RenderDocumentation \
      --dry-run \
      --config makedir /home/mbless/HTDOCS/github.com/TYPO3-Documentation/TYPO3/Reference/CoreApi.git.make

   $ # See the list of tools that are about to be run.
   $ # See something like:
       1 10-Show-Usage/run_01.py
    2 14-Check-Parameters/run_01.py
    3 16-Get-Settings/run_01.py
    4 18-Update-the-Repository/run_01.py
    5 20-Look-for-Documentation/run_01.py
    6 22-Copy-the-project/run_01.py
    7 24-Copy-the-Makedir/run_01.py
    8 26-Inspect-TheProject/run_01.py
    9 28-Check-RebuildNeeded/run_01.py
   10 30-Move-Localizations-away/run_01.py
   11 32-Convert-SettingsYml/run_01.py
   12 34-Fix-Buildsettings/run_01.py
   13 36-Prepare-Sphinx/run_01.py
   14 38-Run-Included-Files-Check/run_01.py
   15 40-Make-Html/run_01.py
   16 42-Make-SingleHtml/run_01.py
   17 44-Make-Latex/run_01.py
   18 46-Tweak-tex-file/run_01.py
   19 48-Tweak-tex-make-file/run_01.py
   20 50-Make-Pdf/run_01.py
   21 52-Cleanup-Html-Builds/run_01.py
   22 54-Create-Package/run_01.py
   23 56-Replace-_static-in-html/run_01.py
   24 58-Remove-_static-from-html/run_01.py
   25 60-Assemble-Result/run_01.py
   26 64-Create-buildinfo/run_01.py



   # do a live run
   $ tct run \
      RenderDocumentation \
      --config makedir /home/mbless/HTDOCS/github.com/TYPO3-Documentation/TYPO3/Reference/CoreApi.git.make
      --config rebuild_needed 1

   # Find all data and the result(s) in `temp_home`


((to be continued))