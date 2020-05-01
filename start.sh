#!/usr/bin/env bash

rm -r /usr/src/app/temp_modules/__pycache__
mv /usr/src/app/temp_modules/* /usr/src/app/modules/
rmdir /usr/src/app/temp_modules
python /usr/src/app/main.py