#! /bin/false

#   # run this file like this:
#   (venv)$  cd path/to/tct/Contrib
#   (venv)$  source install.source-me.sh

cp -p check_include_files.py $($PATH | cut -d : -f 1)
cp -p jq                     $($PATH | cut -d : -f 1)

