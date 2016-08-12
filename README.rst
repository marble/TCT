

========================
TCT - The Toolchain Tool
========================


------------------------
A tool to run toolchains
------------------------

:Author:          Martin Bless <martin@mbless.de>
:Repository:      https://github.com/marble/TCT.git


Description
===========

For Linux-like systems. Run `tct --help` after installation.

((...))


Installation
============

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
   tct --help


((to be continued))

