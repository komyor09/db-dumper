# db_dump.py — MySQL Dump & Restore Utility

Управляемый CLI-инструмент для полного дампа и восстановления MySQL/MariaDB баз данных.
Поддерживает раздельные конфиги для source (откуда дампить) и target (куда восстанавливать).

## Что дампит

| Шаг | Файл | Содержимое |
|-----|------|------------|
| 1 | `structure.sql` | Таблицы (CREATE TABLE) |
| 2 | `data.sql` | Данные (INSERT) |
| 3 | `views.sql` | Views (все схемы) |
| 4 | `triggers.sql` | Триггеры |
| 5 | `routines.sql` | Процедуры и функции |
| 6 | `events.sql` | Events |
| POST | — | Очистка DEFINER из всех файлов |

## Требования

```bash
# Требуется: mysql-client (mysqldump, mysql) в PATH
# Для Windows — MySQL 8.0 или MariaDB клиент
```

## Использование

### 1. Настройка реквизитов (один раз)

```bash
python db_dump.py config-source   # откуда дампить
python db_dump.py config-target   # куда восстанавливать
python db_dump.py config-show     # показать оба конфига
```

Сохраняется в `~/.db_dump_config.json` (пароль не сохраняется, запрашивается каждый раз).

### 2. Полный дамп

```bash
# Использует сохранённые реквизиты
python db_dump.py dump

# Указать папку
python db_dump.py dump --dir /backups/prod

# Переопределить реквизиты через флаги
python db_dump.py dump \
  --src-host 192.168.100.211 \
  --src-port 3308 \
  --src-user emisdb \
  --src-db kbtut_project sess_ved karzdoron \
  --dir dump
```

### 3. Восстановление

```bash
# Базовое восстановление
python db_dump.py restore

# Из конкретной папки
python db_dump.py restore --dir /backups/prod

# Чистый старт — DROP + CREATE каждой базы перед импортом
python db_dump.py restore --clean

# Продолжать при ошибках
python db_dump.py restore --force

# Переопределить target реквизиты
python db_dump.py restore \
  --tgt-host 192.168.100.219 \
  --tgt-port 3333 \
  --tgt-user root
```

### 4. Проверка соединения

```bash
python db_dump.py test-source
python db_dump.py test-target
```

### 5. Список views

```bash
python db_dump.py views
```

### 6. Диагностика charset (если кириллица превращается в ?????)

```bash
python db_dump.py charset
```

Показывает charset каждой таблицы и выдаёт готовые `ALTER TABLE` для таблиц с проблемным charset.

## Флаги dump

| Флаг | Описание |
|------|----------|
| `--src-host` | MySQL host (source) |
| `--src-port` | MySQL port (source) |
| `--src-user` | MySQL user (source) |
| `--src-password` | Пароль (лучше не передавать — будет запрошен) |
| `--src-db DB1 DB2` | Список баз данных |
| `--dir` | Папка для .sql файлов (по умолчанию: `dump`) |
| `--no-clean-definer` | Не чистить DEFINER после дампа |

## Флаги restore

| Флаг | Описание |
|------|----------|
| `--tgt-host` | MySQL host (target) |
| `--tgt-port` | MySQL port (target) |
| `--tgt-user` | MySQL user (target) |
| `--tgt-password` | Пароль (лучше не передавать — будет запрошен) |
| `--dir` | Папка с .sql файлами (по умолчанию: `dump`) |
| `--clean` | DROP + CREATE каждой базы перед импортом |
| `--force` | Продолжать при ошибках |

## Порядок восстановления

```
routines.sql → structure.sql → data.sql → views.sql → triggers.sql → events.sql
```

> Routines идут первыми — structure.sql может содержать выражения ссылающиеся на функции.
> Файлы которых нет в папке автоматически пропускаются.

## Важно: кириллица и charset

Если source сервер — старый MariaDB (10.0 и ниже), он может игнорировать charset от клиента
и принудительно использовать `latin1`, из-за чего кириллица превращается в `?????`.

Решение — выполнить на source сервере:

```sql
SET GLOBAL character_set_server     = utf8mb4;
SET GLOBAL character_set_client     = utf8mb4;
SET GLOBAL character_set_results    = utf8mb4;
SET GLOBAL character_set_connection = utf8mb4;
SET GLOBAL collation_server         = utf8mb4_general_ci;
```

> ⚠️ `SET GLOBAL` не сохраняется после перезапуска сервера. Для постоянного эффекта
> добавьте эти параметры в `my.cnf` / `my.ini` на source сервере в секцию `[mysqld]`.
