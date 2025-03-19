
# 1. Демонстрация работы эндпоинтов
## 1.1. Создание / удаление / изменение / получение информации по короткой ссылке:
Проверка работоспособности эндпоинтов осуществлялась с помощью Postman запросов.
`POST /links/shorten`
![alt text](image.png)

`GET /links/{short_code}`
![alt text](image-1.png)

`DELETE /links/{short_code}`
![alt text](image-2.png)

`PUT /links/{short_code}`
![alt text](image-4.png)

`GET /links/{short_code}/stats`
![alt text](image-5.png)