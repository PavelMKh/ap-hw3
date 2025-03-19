
# 1. Демонстрация работы эндпоинтов
Проверка работоспособности эндпоинтов осуществлялась с помощью Postman запросов.
# 1.1. Обязательные функции
## 1.1.1. Создание / удаление / изменение / получение информации по короткой ссылке:
`POST /links/shorten`
![alt text](image.png)

`GET /links/{short_code}`
![alt text](image-1.png)

`DELETE /links/{short_code}`
![alt text](image-2.png)

`PUT /links/{short_code}`
![alt text](image-4.png)

## 1.1.2. Статистика по ссылке:
`GET /links/{short_code}/stats`
![alt text](image-5.png)

## 1.1.3. Создание кастомных ссылок с уникальным alias:
`POST /links/custom_shorten`
![alt text](image-6.png)

## 1.1.4. Поиск ссылки по оригинальному URL:
`GET /links/search?original_url={url}`
![alt text](image-7.png)
![alt text](image-8.png)

## 1.1.5. Указание времени жизни ссылки:
`POST /links/shorten`
![alt text](image-9.png)

`POST /links/custom_shorten`
![alt text](image-10.png)

## 1.2. Дополнительные функции