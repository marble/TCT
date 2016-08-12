

================
Notes
================

.. highlight:: shell


Start the virtual environment::

   source /home/marble/Repositories/mbnas/mbgit/tct/venv/bin/activate



On srv123
=========

::

   mkdir ~/venvs
   mkdir ~/venvs/tct
   cd ~/venvs/tct
   virtualenv venv
   source ~/venvs/tct/venv/bin/activate

::

   pip install --upgrade pip
   pip install --upgrade sphinx
   pip install --upgrade click


::
   bash
   source ~/venvs/tct/venv/bin/activate

   (venv)mbless@srv123: cd ~/HTDOCS/bitbucket.org
   (venv)mbless@srv123: hg clone http://bitbucket.org/birkenfeld/pygments-main birkenfeld/pygments-main
   (venv)mbless@srv123: cd ~/HTDOCS/bitbucket.org/birkenfeld/pygments-main
   (venv)mbless@srv123:  pip install --upgrade .

::
   # do as: (venv)mbless@srv123:
   cd ~/HTDOCS/bitbucket.org
   hg clone https://bitbucket.org/xperseguers/sphinx-contrib xperseguers/sphinx-contrib

   cd ~/HTDOCS/bitbucket.org/xperseguers/sphinx-contrib/googlechart
   pip install --upgrade .

   cd ~/HTDOCS/bitbucket.org/xperseguers/sphinx-contrib/googlemaps
   pip install --upgrade .

   cd ~/HTDOCS/bitbucket.org/xperseguers/sphinx-contrib/httpdomain
   pip install --upgrade .

   cd ~/HTDOCS/bitbucket.org/xperseguers/sphinx-contrib/numfig
   pip install --upgrade .

   cd ~/HTDOCS/bitbucket.org/xperseguers/sphinx-contrib/slide
   pip install --upgrade .

   cd ~/HTDOCS/bitbucket.org/xperseguers/sphinx-contrib/youtube
   pip install --upgrade .




