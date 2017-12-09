#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Requires python 3.6+

#######################################################################################################################
# Программа для автоматизации опроса разделов commits и releases
# любого репозитария на github.com и выполнения действий, заданных пользователем.
#
# Примеры использования:
#   1) У вас есть проект на hub.docker.com, который имеет зависимости от чужого кода, размещенного на github.com.
#      Вы хотите, чтобы при появлении новых commits и/или releases в том коде автоматически запускалась
#      компиляция вашего образа на hub.docker.com.
#   2) Вы хотите получить сразу по нескольким проектам с github.com лог изменений, расположенных
#      в хронологическом порядке и сохранить их в файл.
#   3) При появлении изменений в любом из проектов выполнить произвольный shell-скрипт.
#   ...
#
#######################################################################################################################


import time
import dateutil.parser
import json
from urllib.request import urlopen
from urllib.error import URLError

import cfg
import setup
import actions


def get_last_updates(repo, updates_from, count):
    """Получение changelog репозитария github.com

    :param repo: название репозитария в виде Имя_Владельца/Проект
    :param updates_from: 'commits' или 'releases'
    :param count: количество строк changelog
    :return: updates - результат запроса в виде списка
    """
    url = f'{cfg.GITHUB_BASE_URL}/{repo}/{updates_from}?per_page={count}'
    cfg.LOGGER.info(f'Getting {updates_from} for {repo} from {url}...')
    try:
        response = urlopen(url).read()
    except URLError as e:
        if hasattr(e, 'reason'):
            cfg.LOGGER.error(f'We failed to reach a url: {url}. Reason: {e.reason}')
        elif hasattr(e, 'code'):
            cfg.LOGGER.error(f'The server couldn\'t fulfill the request. Error code: {e.code}')
        return False
    updates = json.loads(response.decode())
    if type(updates) is list:
        updates = updates[:count]
    else:
        updates = [updates, ]
    return updates


def set_data(options=cfg.OPTIONS):
    """Запись полученных данных о репозитариях в структуру типа dict

    :param options: настройки, определяющие тип собираемых данных. Настройки беруться из конфигурационного файла.
    :return: словарь с данными
    """
    cfg.LOGGER.info(f'Fill the DATA structure according to the configuration file {cfg.CONFIG_PATH}')
    data = {}
    for repos in options.keys():
        if int(options[repos]['commits']) > 0:
            for repo_name in [i.strip() for i in str(repos).split(',')]:
                changelog = get_last_updates(repo_name, updates_from='commits', count=int(options[repos]['commits']))
                if changelog:
                    for update in changelog:
                        if repos not in data:
                            data[repos] = [[repo_name,
                                            update['commit']['committer']['date'],
                                            'COMMIT',
                                            update['commit']['author']['name'],
                                            (update['commit']['message'].split('\n'))[0]]]
                        else:
                            data[repos].append([repo_name,
                                                update['commit']['committer']['date'],
                                                'COMMIT',
                                                update['commit']['author']['name'],
                                                (update['commit']['message'].split('\n'))[0]])

        if int(options[repos]['releases']) > 0:
            for repo_name in [i.strip() for i in str(repos).split(',')]:
                changelog = get_last_updates(repo_name, updates_from='releases', count=int(options[repos]['releases']))
                if changelog:
                    for update in changelog:
                        if repos not in data:
                            data[repos] = [[repo_name,
                                            update['published_at'],
                                            'RELEASE',
                                            update['author']['login'],
                                            update['name'],
                                            update['body']]]
                        else:
                            data[repos].append([repo_name,
                                                update['published_at'],
                                                'RELEASE',
                                                update['author']['login'],
                                                update['name'],
                                                update['body']])
        if repos in data:  # sort data by descending timestamps
            data[repos] = sorted(data[repos], key=lambda x: dateutil.parser.parse(x[1]), reverse=True)
    return data


def filter_new_logs(repos, data, old_data, options=cfg.OPTIONS):
    """Формирование структуры только с новыми данными.

    :param repos: наименование репозитария
    :param data: весь объем данных
    :param old_data: только старые данные (загружаются из файла data.json)
    :param options: проверка флага 'only_new' для репозитария (определяется конфигурационным файлом)
    :return: new_data = data - old_data
    """
    cfg.LOGGER.info(f'Selecting only new logs for repo {repos}')
    if options[repos]['only_new']:
        new_logs = []
        if old_data and repos in old_data:
            if old_data[repos] and data[repos]:
                if old_data[repos][0] != data[repos][0]:
                    last_log = old_data[repos][0]
                    for log in data[repos]:
                        if dateutil.parser.parse(log[1]) > dateutil.parser.parse(last_log[1]):
                            new_logs.append(log)
                        else:
                            break
                    data[repos] = new_logs
                else:
                    data[repos] = old_data[repos]
    return data


if __name__ == '__main__':
    setup.setup_env()  # reading and setting CONFIG_PATH and DATA_PATH in cfg.py
    if setup.read_options(cfg.CONFIG_PATH):  # reading configuration file from CONFIG_PATH
        cfg.LOGGER = setup.setup_log()
        cfg.LOGGER.info(f'|===>')
        cfg.LOGGER.info(f'We begin to collect data from the {list(cfg.OPTIONS.keys())} github repositories.')
        while True:  # if cfg.UPDATE_INTERVAL == 0 we do cycle one time and exit
            cfg.LOGGER.info(f'...')
            data = set_data()
            if data:
                cfg.LOGGER.info(f'Reading {cfg.DATA_PATH}.')
                old_data = setup.load_data()
                for repos in cfg.OPTIONS.keys():
                    if cfg.OPTIONS[repos]['only_new'] and old_data:
                        data = filter_new_logs(repos, data, old_data)
                        if old_data[repos][0] == data[repos][0]:
                            cfg.LOGGER.info(f'No new changelogs for {repos}.')
                            continue
                    actions.process_actions(repos, data)  # process the data in accordance with the configuration file
                setup.save_data(data)  # save data to data.json
                if cfg.UPDATE_INTERVAL == 0:
                    cfg.LOGGER.info(f'Processing complete. Exiting...')
                    break
                cfg.LOGGER.info(f'Processing complete. Sleeping {cfg.UPDATE_INTERVAL} minutes.')
                time.sleep(cfg.UPDATE_INTERVAL * 60)  # repeat cycle every UPDATE_INTERVAL minutes
            else:
                cfg.LOGGER.warn(f'Error getting data for {list(cfg.OPTIONS.keys())}.')
    else:
        print(f'Error reading configuration file {cfg.CONFIG_PATH}. Exiting...')
        exit(1)
