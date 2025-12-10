#!/bin/bash

APP_BIN_PATH=$(python3 setup_deb.py target-path | tr -d '\n')
python3 setup_deb.py flet-config 0.2
flet build linux -o $APP_BIN_PATH

python3 setup_deb.py deb-config 0.2

APP_BIN_PATH=$(python3 setup_deb.py target-path | tr -d '\n')
PACKAGE_DIR=$(python3 setup_deb.py package-dir | tr -d '\n')
APP_NAME=$(python3 setup_deb.py app-name | tr -d '\n')

dpkg-deb --build $PACKAGE_DIR
mv ${PACKAGE_DIR}.deb ${APP_NAME}_0.2_amd64.deb