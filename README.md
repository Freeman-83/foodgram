## FOODGRAM

FOODGRAM («Продуктовый помощник»): приложение, объединяющее людей, неравнодушных к кулинарии. Здесь пользователи могут опубликовать свои рецепты, подписываться на публикации других авторов и добавлять их рецепты в избранное. Также есть возможность скачать список покупок для приготовления выбранных блюд.

Сайт проекта: [https://foodmaster.ddns.net/](https://foodmaster.ddns.net/)

API: [https://foodmaster.ddns.net/api/docs/](https://foodmaster.ddns.net/api/docs/)

### Стек технологий:

Python, Django, Django Rest Framework, Docker, Gunicorn, NGINX, PostgreSQL, Yandex Cloud, Continuous Integration, Continuous Deployment

### Развернуть проект на удаленном сервере:

- Клонировать репозиторий:
```
https://github.com/Freeman-83/foodgram-project-react
```

- Установить на сервере Docker, Docker Compose:

```
sudo apt install curl                                   # установка утилиты для скачивания файлов
curl -fsSL https://get.docker.com -o get-docker.sh      # скачать скрипт для установки
sh get-docker.sh                                        # запуск скрипта
sudo apt-get install docker-compose-plugin              # последняя версия docker compose
```

- Находясь в папке infra скопировать на сервер файлы docker-compose.production.yml, nginx_production.conf:

```
scp docker-compose.yml nginx.conf username@IP:/home/username/   # username - имя пользователя на сервере
                                                                # IP - публичный IP сервера
```

- Для работы с GitHub Actions необходимо в репозитории в разделе Secrets > Actions создать переменные окружения:
```
SECRET_KEY              # секретный ключ Django проекта
DOCKER_PASSWORD         # пароль от Docker Hub
DOCKER_USERNAME         # логин Docker Hub
HOST                    # публичный IP сервера
USER                    # имя пользователя на сервере
PASSPHRASE              # пароль удаленного сервера
SSH_KEY                 # приватный ssh-ключ
TELEGRAM_TO             # ID телеграм-аккаунта для посылки сообщения
TELEGRAM_TOKEN          # токен бота, посылающего сообщение

POSTGRES_DB             # postgres
POSTGRES_USER           # postgres
POSTGRES_PASSWORD       # postgres
DB_HOST                 # db
DB_PORT                 # 5432 (порт по умолчанию)
```

- Создать и запустить контейнеры Docker, выполнить команду на сервере

```
sudo docker compose -f docker-compose.production.yml up
```

- После успешной сборки выполнить миграции:
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
```

- Создать суперпользователя:
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
```

- Собрать статику:
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /app/static/
```

- Скачать базу ингредиентов из файла ingredients.csv:
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py import_csv
```

- Для остановки контейнеров Docker:
```
sudo docker compose -f docker-compose.production.yml down -v      # с удалением
sudo docker compose -f docker-compose.production.yml stop         # без удаления
```

### Деплой на сервер (CD-CI) осуществляется через "push" в ветку master.
#### Процедура включает в себя:
- проверку кода на соответствие стандарту PEP8 (flake8)
- сборка и доставка докер-образов frontend и backend на Docker Hub
- разворачивание проекта на удаленном сервере
- отправка сообщения в Telegram (в случае успешного завершения вышеуказанных процедур)

### Запуск проекта на локальной машине:

- Клонировать репозиторий:
```
https://github.com/Freeman-83/foodgram-project-react
```

- В директории infra в файле .env указать следующие данные:
```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
SECRET_KEY='Из настроек Django-settings'
```

- Создать и запустить контейнеры Docker.


- После запуска проект будут доступен по адресу: [http://localhost/](http://localhost/)


- Документация будет доступна по адресу: [http://localhost/api/docs/](http://localhost/api/docs/)


### Автор:

### Марин Михаил