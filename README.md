# GitMon
### A program for automating the polling of commits and releases sections of any repository on github.com and performing the actions specified by the user.
Программа для автоматизации опроса разделов commits и releases любого репозитария на github.com и выполнения действий, заданных пользователем.

## Примеры использования:
   1) У вас есть проект на hub.docker.com, который имеет зависимости от чужого кода, размещенного на github.com.
      Вы хотите, чтобы при появлении новых commits и/или releases в том коде автоматически запускалась
      компиляция вашего образа на hub.docker.com.
   2) Вы хотите получить сразу по нескольким проектам с github.com лог изменений, расположенных
      в хронологическом порядке и сохранить их в файл.
   3) При появлении изменений в любом из проектов выполнить произвольный shell-скрипт.
   
## Примеры конфигурационного файла:
См. /examples/gitmon.conf (https://github.com/MrKsey/GitMon/tree/master/examples)

## Требования:
python 3.6+

## Запуск:
- отредактировать конфигурационный файл gitmon.conf
- запустить: python gitmon.py --config /path/to/gitmon.conf

## Запуск в DOCKER:

Создайте локальный каталог (например /home/gitmon), отредактируйте и поместите туда файл "gitmon.conf" и подключите этот каталог к каталогу контейнера "/usr/src/gitmon/data" (пример ниже).

Create local directory (like /home/gitmon), edit and put the "gitmon.conf" file there and connect this directory to the container directory "/usr/src/gitmon/data":
```
docker pull ksey/gitmon
docker run --name GitMon -d -v /home/gitmon:/usr/src/gitmon/data
```
