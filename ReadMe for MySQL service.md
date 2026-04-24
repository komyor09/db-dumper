# Установка MariaDB 10.8 + настройка (порт 3307, удалённый доступ, UTF-8)

---

## 1. Установка MariaDB 10.8

👉 Скачать:
https://mariadb.org/download/

Выбирай:

* Version: **10.8.x**
* OS: Windows
* Installer: MSI

---

## 2. Во время установки

Обязательно указать:

* ✔ Root password (запомнить!)
* ✔ Port → **3307**
* ✔ Service name → можно оставить `MariaDB`

---

## 3. Где находится конфиг

Обычно:

```text
C:\Program Files\MariaDB 10.8\data\my.ini
```

---

## 4. Настройка порта

Найди:

```ini
port=3306
```

Замени на:

```ini
port=3307
```

---

## 5. Настройка UTF-8 (ОЧЕНЬ важно)

Добавь или проверь:

```ini
[client]
default-character-set=utf8mb4

[mysql]
default-character-set=utf8mb4

[mysqld]
character-set-server=utf8mb4
collation-server=utf8mb4_unicode_ci
```

---

## 6. Разрешить подключения извне

Найди:

```ini
bind-address=127.0.0.1
```

Замени на:

```ini
bind-address=0.0.0.0
```

---

## 7. Перезапуск сервиса

Открой PowerShell от администратора:

```powershell
net stop MariaDB
net start MariaDB
```

(если сервис называется иначе — смотри в services.msc)

---

## 8. Открыть порт в Firewall

```powershell
netsh advfirewall firewall add rule name="MariaDB 3307" dir=in action=allow protocol=TCP localport=3307
```

---

## 9. Разрешить доступ пользователю

Подключись локально:

```bash
mysql -u root -p
```

---

### Быстрый вариант (для разработки):

```sql
CREATE USER 'root'@'%' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;
```

---

### Более безопасный вариант:

```sql
CREATE USER 'user'@'192.168.%' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON *.* TO 'user'@'192.168.%';
FLUSH PRIVILEGES;
```

---

## 10. Проверка подключения

С другого ПК:

```bash
mysql -h YOUR_IP -P 3307 -u root -p
```

---

## 11. Добавить MariaDB в PATH

Путь обычно:

```text
C:\Program Files\MariaDB 10.8\bin
```

Добавить в переменную среды `Path`

---

## 12. Проверка

```bash
mysql --version
```

Должно быть что-то вроде:

```text
mysql  Ver 15.1 Distrib 10.8.x-MariaDB
```

---

## 13. Частые проблемы

❌ Access denied
→ нет прав (`GRANT` не выполнен)

❌ Can't connect to server
→ порт закрыт или bind-address не изменён

❌ mysql не найден
→ PATH не настроен

---

## Готово

Теперь MariaDB:

✔ работает на порту 3307
✔ принимает подключения из сети
✔ использует UTF-8 (utf8mb4)
✔ готова для dump / restore

---
