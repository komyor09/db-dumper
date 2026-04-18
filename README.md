# 🗄️ db_dump.py

> Управляемый CLI-инструмент для полного дампа и восстановления MySQL/MariaDB баз данных.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1?style=flat&logo=mysql&logoColor=white)
![MariaDB](https://img.shields.io/badge/MariaDB-10.0+-003545?style=flat&logo=mariadb&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey?style=flat)

---

## ✨ Возможности

- 📦 Полный дамп: структура, данные, views, триггеры, routines, events
- 🔄 Восстановление с правильным порядком импорта
- 🔀 Раздельные конфиги для **source** и **target** серверов
- 🧹 Автоматическая очистка `DEFINER` после дампа
- 📊 Прогрессбар для каждого шага
- 🔍 Диагностика charset (причина `?????` вместо кириллицы)
- 💾 Конфиг сохраняется в `~/.db_dump_config.json` (без пароля)

---

## 📋 Требования

- Python 3.10+
- `mysqldump` и `mysql` в `PATH` (MySQL Client 8.0+ или MariaDB Client)

---

## 🚀 Быстрый старт

```bash
# 1. Настроить реквизиты
python db_dump.py config-source   # откуда дампить
python db_dump.py config-target   # куда восстанавливать

# 2. Дамп
python db_dump.py dump

# 3. Восстановление
python db_dump.py restore --clean
```

---

## 👨‍💻 Для разработчиков — только Restore

Если у тебя уже есть готовые файлы дампа (`.sql`) и нужно только развернуть базу локально — дамп делать не нужно. Достаточно настроить **target** и запустить restore.

### Шаг 1 — Получи файлы дампа

Положи полученные `.sql` файлы в одну папку, например `dump/`:

```
dump/
├── structure.sql
├── data.sql
├── views.sql
├── routines.sql
├── triggers.sql
└── events.sql
```

> Файлов может быть меньше — отсутствующие автоматически пропускаются.

### Шаг 2 — Настрой target (один раз)

```bash
python db_dump.py config-target
```

```
  Host [localhost]:           ← Enter или впиши свой хост
  Port [3306]:                ← Enter
  User [root]:                ← впиши своего юзера
```

Пароль не сохраняется — запросится при каждом запуске.

### Шаг 3 — Запусти restore

#### Через командную строку

```bash
# Простой restore (базы уже существуют)
python db_dump.py restore

# С чистым стартом — DROP + CREATE каждой базы перед импортом
python db_dump.py restore --clean

# Продолжать даже если часть таблиц выдала ошибку
python db_dump.py restore --force

# Указать папку с дампом явно
python db_dump.py restore --dir /path/to/dump --clean

# Всё через флаги без config-target (удобно в CI/скриптах)
python db_dump.py restore \
  --tgt-host localhost \
  --tgt-port 3306 \
  --tgt-user root \
  --tgt-password secret \
  --dir dump \
  --clean
```

#### Через GUI

1. Запусти `db_dump_gui.py` (или `db_dump_gui.exe`)
2. Перейди на вкладку **⚙ Target** — введи реквизиты своей локальной БД, нажми **Тест соединения**
3. Перейди на вкладку **🔄 Restore**
4. Укажи папку с `.sql` файлами через кнопку 📂 или введи путь вручную
5. Включи **`--clean`** если нужен чистый старт (рекомендуется при первом разворачивании)
6. Нажми **▶ Запустить Restore** — прогресс и лог отображаются прямо в окне

> **Совет:** если видишь ошибки при импорте данных — включи **`--force`**,  
> чтобы restore не останавливался на первой ошибке и импортировал максимум возможного.

### Порядок импорта (выполняется автоматически)

```
routines.sql → structure.sql → data.sql → views.sql → triggers.sql → events.sql
```

Routines идут первыми — `structure.sql` может ссылаться на функции.  
Файлов которых нет в папке — автоматически пропускаются.

### Проверить соединение перед запуском

```bash
python db_dump.py test-target
```

---

## 📖 Все команды

| Команда | Описание |
|---------|----------|
| `config-source` | Настроить source подключение |
| `config-target` | Настроить target подключение |
| `config-show` | Показать оба конфига |
| `dump` | Создать полный дамп (source) |
| `restore` | Восстановить из .sql файлов (target) |
| `test-source` | Проверить source соединение |
| `test-target` | Проверить target соединение |
| `views` | Показать список views в source базах |
| `charset` | Диагностика charset таблиц |

---

## 🗂️ Что дампится

| Шаг | Файл | Содержимое |
|-----|------|------------|
| 1 | `structure.sql` | Таблицы (CREATE TABLE) |
| 2 | `data.sql` | Данные (INSERT) |
| 3 | `views.sql` | Views (все схемы) |
| 4 | `triggers.sql` | Триггеры |
| 5 | `routines.sql` | Процедуры и функции |
| 6 | `events.sql` | Events |
| POST | — | Очистка DEFINER из всех файлов |

---

## ⚙️ Флаги

### `dump`

| Флаг | Описание |
|------|----------|
| `--src-host` | MySQL host (source) |
| `--src-port` | MySQL port (source) |
| `--src-user` | MySQL user (source) |
| `--src-password` | Пароль (лучше не передавать — будет запрошен) |
| `--src-db DB1 DB2` | Список баз данных |
| `--dir` | Папка для .sql файлов (по умолчанию: `dump`) |
| `--no-clean-definer` | Не чистить DEFINER после дампа |

### `restore`

| Флаг | Описание |
|------|----------|
| `--tgt-host` | MySQL host (target) |
| `--tgt-port` | MySQL port (target) |
| `--tgt-user` | MySQL user (target) |
| `--tgt-password` | Пароль (лучше не передавать — будет запрошен) |
| `--dir` | Папка с .sql файлами (по умолчанию: `dump`) |
| `--clean` | DROP + CREATE каждой базы перед импортом |
| `--force` | Продолжать при ошибках |

---

## 💡 Примеры

```bash
# Дамп с явными реквизитами
python db_dump.py dump \
  --src-host 192.168.1.10 \
  --src-port 3308 \
  --src-user emisdb \
  --src-db kbtut_project sess_ved karzdoron \
  --dir /backups/prod

# Восстановление с чистым стартом
python db_dump.py restore \
  --tgt-host 192.168.1.20 \
  --tgt-port 3306 \
  --tgt-user root \
  --dir /backups/prod \
  --clean

# Проверить соединения
python db_dump.py test-source
python db_dump.py test-target

# Диагностика если кириллица превращается в ?????
python db_dump.py charset
```

---

## 🔄 Порядок восстановления

```
routines.sql → structure.sql → data.sql → views.sql → triggers.sql → events.sql
```

> Routines идут первыми — `structure.sql` может содержать выражения ссылающиеся на функции.
> Файлы которых нет в папке автоматически пропускаются.

---

## ⚠️ Кириллица и charset

Если source сервер — старый MariaDB (10.0 и ниже), он может игнорировать charset от клиента и принудительно использовать `latin1`, из-за чего кириллица превращается в `?????`.

**Диагностика:**
```bash
python db_dump.py charset
```

**Решение — выполнить на source сервере:**
```sql
SET GLOBAL character_set_server     = utf8mb4;
SET GLOBAL character_set_client     = utf8mb4;
SET GLOBAL character_set_results    = utf8mb4;
SET GLOBAL character_set_connection = utf8mb4;
SET GLOBAL collation_server         = utf8mb4_general_ci;
```

> `SET GLOBAL` не сохраняется после перезапуска. Для постоянного эффекта добавьте в `my.cnf` / `my.ini` на source сервере:
>
> ```ini
> [mysqld]
> character_set_server     = utf8mb4
> character_set_client     = utf8mb4
> character_set_results    = utf8mb4
> character_set_connection = utf8mb4
> collation_server         = utf8mb4_general_ci
> ```

---

## 📄 Лицензия

MIT