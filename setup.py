#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Requires python 3.6+

#######################################################################################################################
# Setup global variables and save/load data to/from data file (data.json)
#######################################################################################################################


import json
import configparser
import argparse
import logging
from pathlib import Path

import cfg


def setup_env():
    """Обработка аргументов командной строки и установка путей CONFIG_PATH и DATA_PATH

    --config <путь к конфигурационному файлу>
    --data <путь к файлу данных>

    :return:
    """
    parser = argparse.ArgumentParser(description='Check commits and releases changelogs on github.com and do some actions')
    parser.add_argument('--config', action='store', dest='CONFIG_PATH', type=str,
                        help='Path to app configuration file. Default: current application directory. File mast exist!')
    parser.add_argument('--data', action='store', dest='DATA_PATH', type=str,
                        help='File to store app data. Default: current application directory. Write permissions necessary.')
    args = parser.parse_args()

    if args.CONFIG_PATH:
        cfg.CONFIG_PATH = args.CONFIG_PATH
    file_path = Path(cfg.CONFIG_PATH)
    if not file_path.is_file():
        print(f'Error: configuration file {cfg.CONFIG_PATH} not exist. Exiting...')
        exit(1)

    if args.DATA_PATH:
        cfg.DATA_PATH = args.DATA_PATH

    return True


def read_options(config_path):
    """Чтение конфигурационного файла и установка глобальных переменных из cfg.py

    :param config_path: путь к конфигурационному файлу
    :return: True or False
    """
    config = configparser.ConfigParser()
    if config.read(config_path, encoding='utf-8'):
        repo_list = config.sections()
        for repo in repo_list:
            cfg.OPTIONS[repo] = {'commits': config[repo].getint('commits', 0),
                                 'releases': config[repo].getint('releases', 0),
                                 'only_new': config[repo].getboolean('only_new', True),
                                 'github_token': config[repo].get('github_token', ''),
                                 'line_prefix': config[repo].get('line_prefix', ''),
                                 'log_detail': config[repo].get('log_detail', 'medium'),
                                 'file_max_size': config[repo].getint('file_max_size', 1000000),
                                 'log_text': config[repo].get('log_text', ''),
                                 'log_start': config[repo].get('log_start', ''),
                                 'log_end': config[repo].get('log_end', ''),
                                 'actions': [i.strip() for i in config[repo].get('actions', '').split(',')]}

            line_prefix = cfg.OPTIONS[repo]['line_prefix']
            if line_prefix:
                cfg.OPTIONS[repo]['line_prefix'] = line_prefix + ' '

        cfg.GITHUB_BASE_URL = config['DEFAULT'].get('github_base_url', 'https://api.github.com/repos')
        cfg.UPDATE_INTERVAL = config['DEFAULT'].getint('update_interval', 0)
        cfg.APP_LOGS_TYPE = config['DEFAULT'].get('app_logs_type', 'console')
        cfg.APP_LOGS_FILE = config['DEFAULT'].get('app_logs_file', 'gitmon.log')

        return True
    else:
        return False


def setup_log():
    """Создание логгера

    :return:
    """
    logger = logging.getLogger('GitMon')
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    if cfg.APP_LOGS_TYPE.lower() == 'none':
        log_handler = logging.NullHandler()
    elif cfg.APP_LOGS_TYPE.lower() == 'file':
        log_handler = logging.FileHandler(cfg.APP_LOGS_FILE)
    else:
        log_handler = logging.StreamHandler()
    log_handler.setLevel(logging.INFO)
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)
    return logger


def save_data(data, js_file=cfg.DATA_PATH):
    """Сохранение данных в файл

    :param data: структура типа dict
    :param js_file: путь к файлу данных
    :return:
    """
    cfg.LOGGER.info(f'Saving data to {js_file}...')
    with open(js_file, 'w') as js:
        json.dump(data, js, sort_keys=False, indent=4)


def load_data(js_file=cfg.DATA_PATH):
    """Загрузка данных из файла и возвращение их в виде структуры dict

    :param js_file: путь к файлу данных
    :return:
    """
    cfg.LOGGER.info(f'Loading data from {js_file}...')
    try:
        with open(js_file, 'r') as js:
            return json.loads(js.read())
    except:
        return {}
