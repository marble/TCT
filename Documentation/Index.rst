

=======================
TCT - A Tool Chain Tool
=======================

.. highlight:: shell





What is TCT?

Often we run a program or script to get a task done.
Let's call such a program or script 'tool'. Complex tasks
often require a series of tools to be run.

TCT, the tool chain tool, is a commandline tool designed to run
a series of tools.

Goal
====

Make as little assumptions as possible about what can be used as a tool.

TCT should impose almost no restrictions.

Development should ((stattfinden können)) lazily.

Expandable, fixed order, nested hierarchy,

Tools hinzufügbar independent of other tools (they don't have to be changed)

The task is about administration, control processing

Wir wollen ein extrovertiertes Programm
tct is to externalize its whole knowledge.


Conventions
===========

A tool is an executable with a name starting with 'run_'.

A toolchain is given as a folder. The foldername is the name of the toolchain.

Process a folder:
TCT will run all tools in that folder in alphabetical order. After that it
looks out for subfolders and processes one by one in alphabetically order too.
This is a recursive process with topdown behavior.

We have one facts file facts.json.

When a tool is run it receives a parameter. It's the path of a temp directory it may use.
Two files are in there:
params.json
result.json

TCT uses abspaths.

exitcode 99 will stop further processing.


Garanties
=========
The tool can expect to be run in workdir.
parm1 = abs path to parms.json
parm2 = abs path to bin folder (where jq is in)

A Tool Should
=============
Write only within its workdir
Leave results in result.json.
Place important results in {'FACTS': ...} within the results. TCT will copy these to the global facts file.


Restrictions
============

Python executables must use "#! /usr/bin/env python"


When tools fail
===============
processing of the current folder (and its subfolders) stops.
But continues otherwise.


Shell Scripts
=============
https://stedolan.github.io/jq/

Cool
====
You can change the names of files and folders at any time.
They only have the "alphabetically" meaning.


Conventions
===========
Only a few thing: FACTS, MILESTONES, resultfile, paramsfile,
Filenames and Foldernames are free!

Exitcodes
=========
Sometimes we detect errors. Then we set exitcode to > 0

Or a tool aborts. Then exitcode is set as well.

Biggest challenge
=================

keep development costs low
allow early start
provide extandability

debugging should be easy.
should be possible just by looking at the files.


To get a complex task done we often


- Perform complex task
- multiple steps, that may or may not be necessary

- It aims to make the process of writing command line tools quick and fun
  while also preventing any frustration caused by the inability to implement
  an intended CLI API.

  Click in three points:

  -   arbitrary nesting of commands
  -   automatic help page generation
  -   supports lazy loading of subcommands at runtime

  Read the docs at http://click.pocoo.org/



- For Linux
- TCT is a commandline program and has its own virtualenv
- TCT runs a toolchain,


Here it means:

- In the context of the TCT a tool is an executable file that has a name starting with exactly
  these four letters: 'run_'



Components

- commandline interface by 'click' http://mbless.de/blog/2015/01/15/about-gui-programming.html#click


More

-  Click has a chapter of how to distribute commandline scripts:
   http://click.pocoo.org/6/setuptools/#setuptools-integration !!!

How to setup dev environment for TCT
   - we want to run the command
   - we want to code and test the changes

   ::

      project=/home/user/tct
      mkdir -p $project
      virtualenv $project/venv
      source $project/venv/bin/activate
      cd $project
      touch tct.py   # and edit!
      touch setup.py # and edit!
      pip install --editable .
      tct --help
