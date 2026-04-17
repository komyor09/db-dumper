# db_dump.py — MySQL Dump & Restore Utility

Управляемый CLI-инструмент для полного дампа и восстановления MySQL баз данных.

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

## Установка

```bash
pip install --break-system-packages mysql-connector-python   # не нужен, используем subprocess
# Требуется: mysql-client (mysqldump, mysql) в PATH
```

## Использование

### 1. Настройка реквизитов (один раз)
```bash
python db_dump.py config
```
Сохраняется в `~/.db_dump_config.json` (без пароля).

### 2. Полный дамп
```bash
# Использует сохранённые реквизиты
python db_dump.py dump

# Указать папку
python db_dump.py dump --dir /backups/prod

# Переопределить всё через флаги
python db_dump.py dump \
  --host 192.168.100.211 \
  --port 3308 \
  --user emisdb \
  --db kbtut_project sess_ved karzdoron \
  --dir dump
```

### 3. Восстановление
```bash
python db_dump.py restore
python db_dump.py restore --dir /backups/prod
```

### 4. Проверка соединения
```bash
python db_dump.py test
```

### 5. Список views
```bash
python db_dump.py views
```

## Флаги

| Флаг | Описание |
|------|----------|
| `--host` | MySQL host |
| `--port` | MySQL port |
| `--user` | MySQL user |
| `--password` | Пароль (лучше не передавать — будет запрошен) |
| `--db DB1 DB2` | Список баз данных |
| `--dir` | Папка для .sql файлов |
| `--no-clean-definer` | Не чистить DEFINER после дампа |

## Порядок восстановления

```
structure.sql → data.sql → views.sql → routines.sql → triggers.sql → events.sql
```

Файлы которых нет в папке — автоматически пропускаются.
