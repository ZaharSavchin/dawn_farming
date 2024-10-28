# Dawn reg and login script for take away token  
## Скрипт автоматически регистрирует аккаунт, логинится в систему, решает капчу и получает токен.  
### Предварительные требования  
Что нужно установить на ПК для использования:  
`Python 3.12+`  
Гайд по установке Python и VSCode находится в Notion по [ссылке](https://www.notion.so/crypto-davy/ecae4770d89741a8aef963563f2c267e#4fc269e4b9fe4b49a405daf2ed019b7e).

Кроме того, вам понадобится доступ к Gmail API для получения писем с подтверждением регистрации.

Шаги по настройке Gmail API:  
Перейдите на Google Developers Console.  
Создайте проект и включите Gmail API.  
Создайте OAuth 2.0 учетные данные и скачайте файл `credentials.json`.  
Поместите файл credentials.json в директорию `data/gmail/`, вам нужно только `client_id`, `project_id` и 
`client_secret`, остальное НЕ НУЖНО ТРОГАТЬ!
  
## Установка  
Шаги по установке проекта:  

- Скачайте репозиторий  
- Перейдите в каталог проекта  
- Установите зависимости:  

`pip install -r requirements.txt`  
  
## Настройка  
1. Файлы настроек  
В репозитории присутствуют два файла настройки: ``users.txt``, ``proxies.txt``.

`users.txt`:
В этот файл необходимо построчно вставить ваши email и пароли в формате email:password, каждый аккаунт на новой строке. Пример:
```
user1@example.com:password123
user2@example.com:password456
```
`proxies.txt`:
В этом файле прописываются прокси для каждого аккаунта в формате:
```
ip:port:username:password
ip:port:username:password
```
Каждый аккаунт будет использовать уникальный прокси.  

2. **Настройка Gmail API**  
`credentials.json`:  
Этот файл необходимо получить, как указано в разделе "Предварительные требования". Поместите его в папку data/gmail/.

`token-py.json`:
Этот файл создается автоматически при первом запуске, если Gmail API успешно настроен.

3. **Конфигурация приложения**  
Конфигурации скрипта по регистрации и логину хранятся в папке core. Вам не нужно вносить изменения в эти файлы, если только вам не требуется расширить функциональность.

4. **Config.py**


В файле находятся несколько переменных для настройки скрипта, а именно:  
  
`API_KEY = ''` - Ключ API для взаимодействия с ChatGPT. Убедитесь, что вы получили его и вставили в соответствующее поле.  

`MAX_RETRIES = 5` - Максимальное количество попыток повторного выполнения регистрации или логина в случае неудачи (например, ошибка сети или неправильная капча).  

`RETRY_DELAY = 3` - Пауза (в секундах) между повторными запросами. Устанавливает, сколько времени скрипт будет ждать перед следующей попыткой.  

`REGISTER_ONLY = False` - Определяет поведение скрипта:  

`False` — только логин, регистрация не выполняется.  
`True` — только регистрация новых аккаунтов, без последующей попытки логина.  

`MAX_THREADS = 1`
Количество параллельных потоков, используемых при выполнении регистраций и логинов. Увеличение значения может ускорить процесс, если у вас много аккаунтов, но требует осторожного использования при работе с ограниченными ресурсами.

## Как запустить проект:  
Убедитесь, что все настройки корректно внесены в файлы `users.txt`, `proxies.txt` и `credentials.json`.
Запустите скрипт:  

`python main.py`  
Скрипт будет поочередно регистрировать аккаунты, логиниться, решать капчу, получать токены и сохранять их в файл `data/tokens.txt`.

**Дополнительные детали**
Решение капчи осуществляется с использованием API, доступ к которому настраивается в файле `gpt.py`. Убедитесь, что у вас есть ключ API для взаимодействия с сервисом.
Если во время выполнения скрипта возникает ошибка капчи или проблемы с регистрацией, скрипт автоматически повторит попытку несколько раз.
Авторы:


Дополнительная информация
Решение капчи:
Используется внешний API для решения капчи. Проверьте правильность ключа API, прописанного в gpt.py.

Дополнительная информация
Решение капчи:
Используется внешний API для решения капчи. Проверьте правильность ключа API, прописанного в gpt.py.

Прокси:
Если вы используете большое количество аккаунтов, рекомендуется использование разных прокси для каждого аккаунта. Прокси задаются в файле proxies.txt.

Gmail API:
Gmail API используется для проверки писем с подтверждением регистрации. Убедитесь, что вы получили OAuth2-токены и настроили доступ к Gmail, как указано выше. Вот инструкция со скринами:

1. Переходим на https://console.cloud.google.com/apis/credentials/
2. Создаём свой проект с любым названием.
3. Создаём credentials - OAuth client ID: ![image](https://github.com/user-attachments/assets/17b4bcec-1757-4c97-b449-9249df5644ef)
Вначале он попросит там согласиться, что вы для себя делаете, просто протыкивайте кнопки, возвращайтесь в дешборд и снова создавайте креды, гугл выдаст такую табличку. Тут все необходимые данные для файлика.  
![image](https://github.com/user-attachments/assets/82930624-07b0-4c43-b029-41ca69e50a22)
