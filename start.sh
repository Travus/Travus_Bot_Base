#!/usr/bin/env bash

mv /usr/src/app/temp_modules/* /usr/src/app/modules/ 2> /dev/null
rm -rf /usr/src/app/temp_modules/__pycache__
rm -rf /usr/src/app/temp_modules
python /usr/src/app/main.py