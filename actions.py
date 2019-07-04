#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Requires python 3.6+

#######################################################################################################################
# Data processing procedures
#######################################################################################################################


import contextlib
import dateutil.parser
import json
from urllib.request import urlopen, Request
from urllib.error import URLError
from github import Github
from subprocess import run, SubprocessError

import cfg
import setup


def get_logs(commands, repos, data, options=cfg.OPTIONS):
    """Создание многострочного лога (блока текста) из данных, хранящихся в data

    :param commands:
    :param repos:
    :param data:
    :param options:
    :return:
    """
    cfg.LOGGER.info(f'Combining several events from {repos} into one changelog')
    log_detail = options[repos]['log_detail'].lower()
    line_prefix = options[repos]['line_prefix']
    release_prefix = '\n' + line_prefix
    log = ''
    try:
        if 'commits' in commands or 'old_commits' in commands:
            for i in data[repos]:
                if f'{i[2]}' == 'COMMIT':
                    log += line_prefix
                    if log_detail == 'small':
                        log += f'- {i[4]}\n'
                    elif log_detail == 'medium':
                        log += f'{dateutil.parser.parse(i[1]).strftime("%Y-%m-%d %H:%M:%S")}: [{i[0]}, {i[2]}] {i[4]}\n'
                    else:
                        log += f'{dateutil.parser.parse(i[1]).strftime("%Y-%m-%d %H:%M:%S")} [{i[0]}] (type - {i[2]}, author - {i[3]}): {i[4]}\n'
        elif 'releases' in commands or 'old_releases' in commands:
            for i in data[repos]:
                if f'{i[2]}' == 'RELEASE':
                    log += line_prefix
                    release_log = release_prefix + release_prefix.join(i[5].splitlines())
                    if log_detail == 'small':
                        log += f'Version: {i[4]}:\n{release_log}\n'
                    elif log_detail == 'medium':
                        log += f'{dateutil.parser.parse(i[1]).strftime("%Y-%m-%d %H:%M:%S")}: [{i[0]}, {i[2]}] {i[4]}:\n{release_log}\n'
                    else:
                        log += f'{dateutil.parser.parse(i[1]).strftime("%Y-%m-%d %H:%M:%S")} [{i[0]}] (type - {i[2]}, author - {i[3]}): {i[4]}:\n{release_log}\n'
    except IndexError as e:
        cfg.LOGGER.error(f'Error in logs from {data[repos]}. Reason: IndexError {e.args}')
        log = ''
    return log


def get_data_for_actions(commands, repos, data, options=cfg.OPTIONS):
    """Подготовка данных для выполнения над ними действий, описанных в конфигурационном файле

    Данные представляют собой:
        - либо многостроный лог, полученный с помощью функции get_logs
        - либо данные, загруженные из файла данных data.json
        - либо блок текста, полученный из конфигурационного файла

    :param commands:
    :param repos:
    :param data:
    :param options:
    :return:
    """
    cfg.LOGGER.info(f'Preparing {repos} changelogs for processing by {commands}')
    try:
        data_for_actions = commands[3].lower()
        if data_for_actions == 'commits' or data_for_actions == 'releases':
            data_for_actions = get_logs(commands, repos, data, options)
        elif data_for_actions == 'old_commits' or data_for_actions == 'old_releases':
            old_data = setup.load_data()
            if old_data:
                data_for_actions = get_logs(commands, repos, old_data, options)
        else:
            data_for_actions = options[repos][data_for_actions] + '\n'
        return data_for_actions
    except IndexError as e:
        cfg.LOGGER.error(f'Error in {repos} local file actions configuration. Reason: IndexError {e.args}.')
        data_for_actions = ''
    return data_for_actions


def action_console(commands, args, repos, data, options=cfg.OPTIONS):
    """Вывод данных, полученных из функции get_data_for_actions, на консоль

    :param commands:
    :param args:
    :param repos:
    :param data:
    :param options:
    :return:
    """
    cfg.LOGGER.info(f'Printing {repos} changelogs to console')
    try:
        if commands[0].lower() == 'local' and commands[1].lower() == 'console' and commands[2].lower() == 'print':
            data_for_actions = get_data_for_actions(commands, repos, data, options)
            if data_for_actions:
                print(data_for_actions.rstrip())
                return True
    except IndexError as e:
        cfg.LOGGER.error(f'Error in {repos} console actions configuration: {commands}. Reason: IndexError {e.args}.')
    return False


def action_file(commands, args, repos, data, options=cfg.OPTIONS):
    """Вывод данных, полученных из функции get_data_for_actions, в файл.

    :param commands:
    :param args: имя файла
    :param repos:
    :param data:
    :param options:
    :return:
    """
    try:
        if commands[0].lower() == 'local' and commands[1].lower() == 'file':
            data_for_actions = get_data_for_actions(commands, repos, data, options)
            file = args
            if data_for_actions and file:
                with open(file, 'a+', newline='\n', buffering=True, encoding='utf-8') as logfile:
                    logfile.seek(0, 0)
                    content = logfile.read()
                max_len = options[repos]['file_max_size']
                if commands[2].lower() == 'write':
                    cfg.LOGGER.info(f'Writing {repos} changelogs to file {args}')
                    content = data_for_actions.splitlines()
                    data_len = len(content)
                    if data_len > max_len:
                        cfg.LOGGER.info(f'File {file} reached {max_len} strings. Truncating...')
                        content = content[0:max_len]
                    content = '\n'.join(i for i in content) + '\n'
                    with open(file, 'w+', newline='\n', buffering=True, encoding='utf-8') as logfile:
                        logfile.write(content)
                elif commands[2].lower() == 'insert':
                    cfg.LOGGER.info(f'Inserting {repos} changelogs to top of the file {args}')
                    content = (data_for_actions + content).splitlines()
                    data_len = len(content)
                    if data_len > max_len:
                        cfg.LOGGER.info(f'File {file} reached {max_len} strings. Truncating...')
                        content = content[0:max_len]
                    content = '\n'.join(i for i in content) + '\n'
                    with open(file, 'w+', newline='\n', buffering=True, encoding='utf-8') as logfile:
                        logfile.write(content)
                elif commands[2].lower() == 'append':
                    cfg.LOGGER.info(f'Appending {repos} changelogs to end of the file {args}')
                    if not content.endswith('\n') and content.strip():
                        content += '\n'
                    content = (content + data_for_actions).splitlines()
                    data_len = len(content)
                    if data_len > max_len:
                        cfg.LOGGER.info(f'File {file} reached {max_len} strings. Truncating...')
                        content = content[data_len - max_len - 1:data_len]
                    content = '\n'.join(i for i in content) + '\n'
                    with open(file, 'w+', newline='\n', buffering=True, encoding='utf-8') as logfile:
                        logfile.write(content)
                elif commands[2].lower() == 'delete':
                    cfg.LOGGER.info(f'Deleting old {repos} changelogs from file {args}')
                    for old_line in data_for_actions.splitlines():
                        content = content.replace(old_line, '').lstrip()
                    with open(file, 'w+', newline='\n', buffering=True, encoding='utf-8') as logfile:
                        logfile.write(content)
                else:
                    cfg.LOGGER.error(f'Error in {repos} local file actions configuration. Reason: unknown command {commands[2]}.')
                    return False
                return True
            else:
                cfg.LOGGER.error(f'Error while processing {repos}. Reason: empty logs or local file name')
    except IndexError as e:
        cfg.LOGGER.error(f'Error in {repos} local file actions configuration. Reason: IndexError {e.args}.')
    return False


def action_shell(commands, args):
    """Выполнение произвольной команды или скрипта

    :param commands: не используется
    :param args: команда и ее аргументы
    :return:
    """
    cfg.LOGGER.info(f'Executing shell command "{args}"')
    if args:
        try:
            run(args=args, shell=True, check=True)
        except SubprocessError as e:
            cfg.LOGGER.error(f'Error {args} execution. Exit status: {e.returncode}.')
        else:
            return True
    cfg.LOGGER.error(f'No shell command is given')
    return False


def action_dockerhub(commands, args, timeout=10):
    """Запуск компиляции вашего образа на hub.docker.com

    Необходимо заранее настроить automated build и прописать путь к его триггеру
    в конфигурационный файл:
    dockerhub.buildimage.latest = <ваш Trigger URL>

    Как настроить automated build: https://docs.docker.com/docker-hub/builds/

    :param commands:
    :param args:
    :param timeout:
    :return:
    """
    cfg.LOGGER.info(f'Executing {commands} on hub.docker.com')
    tag = 'latest'
    url = args
    try:
        if commands[0].lower() == 'dockerhub' and commands[1].lower() == 'buildimage':
            try:
                tag = commands[2]
            except IndexError:
                pass
            params = json.dumps({"docker_tag": f"{tag}"}).encode('utf8')
            trigger_request = Request(url, data=params, headers={'content-type': 'application/json'})
            with contextlib.closing(urlopen(trigger_request, timeout=timeout)) as res:
                cfg.LOGGER.info(f'The result of the {commands} command: {res.msg}')
                if res.status == 200:
                    return True
    except URLError as e:
        if hasattr(e, 'reason'):
            cfg.LOGGER.error(f'We failed to reach a url: {url}. Reason: {e.reason}')
        elif hasattr(e, 'code'):
            cfg.LOGGER.error(f'The server couldn\'t fulfill the request. Error code: {e.code}')
    except IndexError as e:
        cfg.LOGGER.error(f'Error in dockerhub action configuration. Reason: IndexError {e.args}.')
    return False


def action_github(commands, args, repos, data, options=cfg.OPTIONS):
    """Вывод данных, полученных из функции get_data_for_actions, в файл вашего репозитария на github.com

    Необходимо заранее сгенерить personal access token (https://github.com/settings/tokens) и прописать его
    в конфигурационный файл:
    github_token: <ваш token>

    :param commands:
    :param args:
    :param repos:
    :param data:
    :param options:
    :return:
    """
    cfg.LOGGER.info(f'Performing {commands} for repo {repos} on github')
    try:
        if commands[0].lower() == 'github':
            gh = Github(login_or_token=options[repos]['github_token'])
            user = gh.get_user()
            if user:
                cfg.LOGGER.info(f'Connected to {user.name} github')
                repo = user.get_repo(commands[1])
                cfg.LOGGER.info(f'Accessing repo {repo.full_name}')
                # file = '/' + args
                file = args
                try:
                    repo.create_file(file, f'GitMon create file', '')
                except:
                    pass
                cfg.LOGGER.info(f'Reading {file}')
                gh_content = repo.get_file_contents(file)
                content = gh_content.decoded_content.decode('utf-8')
                data_for_actions = get_data_for_actions(commands, repos, data, options)
                max_len = options[repos]['file_max_size']
                if data_for_actions:
                    cfg.LOGGER.info(f'Processing file {file}')
                    if commands[2].lower() == 'write':
                        cfg.LOGGER.info(f'Writing {repos} changelogs to file {file}')
                        content = data_for_actions.splitlines()
                        data_len = len(content)
                        if data_len > max_len:
                            cfg.LOGGER.info(f'File {file} reached {max_len} strings. Truncating...')
                            content = content[0:max_len]
                        content = '\n'.join(i for i in content) + '\n'
                    elif commands[2].lower() == 'insert':
                        cfg.LOGGER.info(f'Inserting {repos} changelogs to top of the file {file}')
                        content = (data_for_actions + content).splitlines()
                        data_len = len(content)
                        if data_len > max_len:
                            cfg.LOGGER.info(f'File {file} reached {max_len} strings. Truncating...')
                            content = content[0:max_len]
                        content = '\n'.join(i for i in content) + '\n'
                    elif commands[2].lower() == 'append':
                        cfg.LOGGER.info(f'Appending {repos} changelogs to end of the file {file}')
                        if not content.endswith('\n') and content.strip():
                            content += '\n'
                        content = (content + data_for_actions).splitlines()
                        data_len = len(content)
                        if data_len > max_len:
                            cfg.LOGGER.info(f'File {file} reached {max_len} strings. Truncating...')
                            content = content[data_len - max_len - 1:data_len]
                        content = '\n'.join(i for i in content) + '\n'
                    elif commands[2].lower() == 'delete':
                        cfg.LOGGER.info(f'Deleting old {repos} changelogs from file {file}')
                        for old_line in data_for_actions.splitlines():
                            content = content.replace(old_line, '')
                    if repo.update_file(file, f'GitMon update file {file} with {repos} changelog', content.lstrip(), gh_content.sha):
                        return True
            else:
                cfg.LOGGER.info(f'Unable to connect to user {user.name} github. Check the token.')
    except IndexError as e:
        cfg.LOGGER.error(f'Error in {repos} actions configuration: {commands}. Reason: IndexError {e.args}.')
    return False


def process_actions(repos, data, options=cfg.OPTIONS):
    """Функция-селектор действий над данными

    :param repos:
    :param data:
    :param options:
    :return:
    """
    try:
        actions = options[repos]['actions']
        if data[repos] and actions:
            for action in actions:
                try:
                    [commands, args] = [i.strip() for i in action.split('=')]
                except ValueError as e:
                    cfg.LOGGER.error(f'Error in {repos} actions configuration: {action}. Reason: ValueError {e.args}.')
                    return False
                commands = commands.split('.')
                try:
                    if commands[0].lower() == 'local':
                        if commands[1].lower() == 'console':
                            action_console(commands, args, repos, data)
                        elif commands[1].lower() == 'file':
                            action_file(commands, args, repos, data)
                        elif commands[1].lower() == 'shell':
                            action_shell(commands, args)
                    elif commands[0] == 'dockerhub':
                        action_dockerhub(commands, args)
                    elif commands[0] == 'github':
                        action_github(commands, args, repos, data)
                    else:
                        cfg.LOGGER.error(f'Unknown command in {repos} actions configuration: {action}')
                        return False
                except KeyError as e:
                    cfg.LOGGER.error(f'Error in command string {commands}. Reason: KeyError {e.args}.')
                    return False
            return True
    except KeyError as e:
        cfg.LOGGER.error(f'No actions for {repos}. Reason: KeyError {e.args}.')
    return False
