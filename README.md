# WB_OZON_scam

WB_OZON_scam — это приложение для парсинга основной информации с маркетплейсов:
- Wildberries
- Ozon
- Yandex Market

Проект использует Selenium + Chrome profile для получения данных из авторизованных сессий браузера.

Для разворачивания данного проекта на windows машине необходимо выполнить несколько действий:
- Установить библиотеки Python: python -m pip install flask selenium webdriver-manager openpyxl pandas
- Авторизоваться на необходимых маркетплейсах в браузере, который используется при работе парсера
  
    "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  
    --user-data-dir="C:\selenium_profile" ^
  
    --profile-directory="Profile 1"

После этого Selenium сможет использовать сохранённую авторизацию.

Для запуска приложения необходимо запустить start.bat

Для разворачивания проекта в интернете я использую xtunnel
