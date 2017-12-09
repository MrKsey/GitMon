# GitMon
### A program for automating the polling of commits and releases sections of any repository on github.com and performing the actions specified by the user.
Программа для автоматизации опроса разделов commits и releases любого репозитария на github.com и выполнения действий, заданных пользователем.

# Примеры использования:
   1) У вас есть проект на hub.docker.com, который имеет зависимости от чужого кода, размещенного на github.com.
      Вы хотите, чтобы при появлении новых commits и/или releases в том коде автоматически запускалась
      компиляция вашего образа на hub.docker.com.
   2) Вы хотите получить сразу по нескольким проектам с github.com лог изменений, расположенных
      в хронологическом порядке и сохранить их в файл.
   3) При появлении изменений в любом из проектов выполнить произвольный shell-скрипт.
   
# Примеры конфигурационного файла:
См. examples/gitmon.conf

# Требования:
python 3.6+

# Запуск:
- отредактировать конфигурационный файл
- запустить: python gitmon.py --config /path/to/gitmon.conf
