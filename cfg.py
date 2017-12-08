#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Requires python 3.6+

#######################################################################################################################
# Global variables
# Can be reassigned by the settings from the configuration file
#######################################################################################################################

CONFIG_PATH = 'gitmon.conf'  # main configuration file
DATA_PATH = 'data.json'  # where to save data
UPDATE_INTERVAL = 0  # data check interval in minutes. '0' == one time only
GITHUB_BASE_URL = 'https://api.github.com/repos'  # github base url
APP_LOGS_TYPE = 'console'  # app logs type: none, file, console
APP_LOGS_FILE = 'gitmon.log'  # app logs file
LOGGER = None  # logger object. See setup.setup_log()
OPTIONS = {}  # options, loaded from configuration file
