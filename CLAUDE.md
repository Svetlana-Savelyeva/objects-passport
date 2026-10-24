# Паспорта объектов — правила для правок

Сайт: `index.html` (статичный, GitHub Pages). Данные: `data/objects.json`, `data/fields.json`, файлы в `files/<id>/`.

## Никогда
- Не записывать пароль в репозиторий, коммиты или файлы вне `.secrets/` (папка в .gitignore).
- Не коммитить `.secrets/`. Не класть коды/пароли открытым текстом в `data/objects.json`.
- Если пароля нет в разговоре — попросить его у пользователя.

## Рабочий цикл
Правки приходят и с сайта (коммиты через GitHub API по ключу пользователя), поэтому ВСЕГДА начинать с `git pull --rebase origin main`.
```bash
git pull --rebase origin main
export PASSPORT_KEY='<пароль из разговора>'
python3 tools/passport.py open    # -> .secrets/objects.plain.json
# править .secrets/objects.plain.json (скриптом на Python, не вручную целиком)
python3 tools/passport.py seal    # -> data/objects.json
git add data files index.html && git commit && git push
```

## Модель объекта (в plain-файле)
- Навигация: num, name, address, apt (№ квартиры, если его нет в address), city, district, districtColor, entrance, floor, coords, nav, metroLine, metro, metroWalk, access*, parking, photoLink, extraLink, order
- Квартира: checkIn, checkOut (время «ЧЧ:ММ»), area, rooms ("Студия", "1", "2", "3", "4", "5+"), beds, guests, sleep (состав спальных мест: `{bed140|bed160|bed180|single|sofa|sofasm|chair|bunk: количество}`; beds = сумма мест), ceiling, floorsTotal, view
- Удобства: `amenities` — `{key: true}` есть, `{key: false}` нет, ключа нет — не заполнено. Ключи: balcony, loggia, boiler, dishwasher (ПММ), ac, washer, dryer, oven, microwave, tv, iron, hairdryer, crib, pets, elevator, storage, workspace, bath, shower, flowheater (проточный водонагреватель), steamer (отпариватель), coffee (кофемашина), kettle, mosquito (москитные сетки), blackout (блэкаут-шторы), heatedfloor (тёплый пол), vacuum (пылесос), alice (колонка Алиса), videocall (видеозвонок), cctv (камера видеонаблюдения). Цвет иконок — по группам AM_GROUP в index.html. Свои удобства — в `data/fields.json` → `amenities: [{key: "c…", label, icon}]`, иконка из набора GEN в index.html
- Интернет: provider, contract, payer (кто платит: «Собственник», «Мы», «Гость», «Включено в квартплату» или свой текст), account*, providerPhone, wifiName, wifiPass*, netNotes (заметки по интернету)
- УК: ukName, ukPhone, ukDispatch (аварийная/диспетчерская), ukEmail, ukApp (приложение/личный кабинет), ukOffice, ukNotes
- nearby, notes
- `custom`: `[{label, value, secret?}]` — свои строки. Секретными (`secret: true`) делать строки с кодами: кейбокс, умный замок, калитка, код…
- `tasks`: регулярные задачи `[{id, title, freq: m|q|h|y, day, start (месяц 1-12 для q/h/y), remind (за сколько дней), since (YYYY-MM-DD)}]`. Отметки выполнения — `data/tasks.json` → `done: {"<objId>|<taskId>|<YYYY-MM срока>": "YYYY-MM-DD"}`
- `photos`: `[{path: "files/<id>/имя.jpg", caption, type}]`; первое изображение — обложка
- `*` — шифруются при seal.

## Свои строки
При добавлении строки к одному объекту — спросить пользователя, добавить ли её ко всем остальным. Если да: добавить `{label, value: ""}` (с тем же `secret`) во все объекты, где строки с таким label нет, и записать её в `data/fields.json` → `rows`. Удаление у отдельного объекта — только у него.

## Новый объект
id: `o-<NN>` для Петербурга, `msk-NN`, `izh-NN` для других городов. Добавить строки из `data/fields.json` с пустыми значениями.
