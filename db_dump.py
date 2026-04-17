#!/usr/bin/env python3
"""
MySQL Dump & Restore Utility
Source и Target — отдельные конфиги подключения.
"""

import argparse
import getpass
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


# ─────────────────────────────────────────────
# DATA MODELS
# ─────────────────────────────────────────────

@dataclass
class ConnectionConfig:
    host: str = "localhost"
    port: int = 3306
    user: str = "root"
    password: str = ""
    databases: list = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["password"] = ""      # пароль никогда не пишем в файл
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "ConnectionConfig":
        return cls(
            host=d.get("host", "localhost"),
            port=int(d.get("port", 3306)),
            user=d.get("user", "root"),
            password=d.get("password", ""),
            databases=d.get("databases", []),
        )

    def label(self) -> str:
        return f"{self.user}@{self.host}:{self.port}"


# ─────────────────────────────────────────────
# CONFIG FILE  (раздельные: source / target)
# ─────────────────────────────────────────────

CONFIG_PATH = Path.home() / ".db_dump_config.json"


def _load_raw() -> dict:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"[WARN] Конфиг повреждён, дефолтные значения: {e}")
    return {}


def load_source_config() -> ConnectionConfig:
    return ConnectionConfig.from_dict(_load_raw().get("source", {}))


def load_target_config() -> ConnectionConfig:
    return ConnectionConfig.from_dict(_load_raw().get("target", {}))


def save_source_config(cfg: ConnectionConfig) -> None:
    raw = _load_raw()
    raw["source"] = cfg.to_dict()
    _write_config(raw)
    print(f"[OK] Source конфиг сохранён → {CONFIG_PATH}")


def save_target_config(cfg: ConnectionConfig) -> None:
    raw = _load_raw()
    raw["target"] = cfg.to_dict()
    _write_config(raw)
    print(f"[OK] Target конфиг сохранён → {CONFIG_PATH}")


def _write_config(data: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ─────────────────────────────────────────────
# PRINT HELPERS
# ─────────────────────────────────────────────

def print_header(text: str) -> None:
    sep = "─" * 60
    print(f"\n{sep}")
    print(f"  {text}")
    print(sep)


def print_step(step: str, name: str) -> None:
    print(f"\n[STEP] {step}: {name}")


def print_ok(msg: str) -> None:
    print(f"  ✓  {msg}")


def print_err(msg: str) -> None:
    print(f"  ✗  {msg}", file=sys.stderr)


def print_skip(msg: str) -> None:
    print(f"  -  {msg}")


# ─────────────────────────────────────────────
# SYSTEM CHECKS
# ─────────────────────────────────────────────

def check_tool(name: str) -> bool:
    finder = "where" if sys.platform == "win32" else "which"
    result = subprocess.run([finder, name], capture_output=True)
    return result.returncode == 0


def require_tools(*tools: str) -> None:
    missing = [t for t in tools if not check_tool(t)]
    if missing:
        print_err(f"Не найдены утилиты: {', '.join(missing)}")
        print_err("Убедитесь, что mysql-client установлен и доступен в PATH.")
        sys.exit(1)


# ─────────────────────────────────────────────
# SUBPROCESS HELPERS
# ─────────────────────────────────────────────

def build_base_args(cfg: ConnectionConfig) -> list:
    return [
        f"--host={cfg.host}",
        f"--port={cfg.port}",
        f"--user={cfg.user}",
        f"--password={cfg.password}",
    ]


def _filter_stderr(text: str) -> list:
    noise = [
        "Using a password on the command line",
        "Warning: Using a password",
    ]
    return [l for l in text.splitlines() if not any(n in l for n in noise)]


def run_to_file(cmd: list, output_file: Path, description: str = "") -> bool:
    label = description or output_file.name
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        # Открываем в бинарном режиме — байты от mysqldump идут на диск без
        # какого-либо перекодирования Python/системой. Кириллица сохраняется
        # ровно так, как её отдаёт mysqldump (utf8mb4).
        with open(output_file, "wb") as out:
            result = subprocess.run(cmd, stdout=out, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print_err(f"{label} — код {result.returncode}")
            lines = _filter_stderr(result.stderr.decode("utf-8", errors="replace"))
            if lines:
                print_err("\n    ".join(lines))
            return False
        return True
    except FileNotFoundError:
        print_err(f"Команда не найдена: {cmd[0]}")
        return False
    except PermissionError as e:
        print_err(f"Нет прав на запись: {e}")
        return False
    except Exception as e:
        print_err(f"Ошибка: {e}")
        return False


def run_from_file(cmd: list, input_file: Path, description: str = "") -> bool:
    label = description or input_file.name
    try:
        # Бинарный режим: mysql читает байты напрямую, без конвертации Python
        with open(input_file, "rb") as f:
            result = subprocess.run(cmd, stdin=f, capture_output=True)
        if result.returncode != 0:
            print_err(f"{label} — код {result.returncode}")
            lines = _filter_stderr(result.stderr.decode("utf-8", errors="replace"))
            if lines:
                print_err("\n    ".join(lines))
            return False
        return True
    except Exception as e:
        print_err(f"{label}: {e}")
        return False


def run_query(cfg: ConnectionConfig, query: str) -> Optional[str]:
    cmd = ["mysql"] + build_base_args(cfg) + ["--default-character-set=utf8mb4", "-N", "-e", query]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        lines = _filter_stderr(result.stderr)
        if lines:
            print_err("\n".join(lines))
        return None
    return result.stdout.strip()


# ─────────────────────────────────────────────
# CONNECTION
# ─────────────────────────────────────────────

def test_connection(cfg: ConnectionConfig, label: str = "") -> bool:
    tag = label or cfg.label()
    print_step("TEST", tag)
    out = run_query(cfg, "SELECT VERSION();")
    if out:
        print_ok(f"Сервер {out} — соединение установлено")
        return True
    print_err(f"Не удалось подключиться к {tag}")
    return False


def ask_password(cfg: ConnectionConfig, prompt_label: str) -> ConnectionConfig:
    if not cfg.password:
        cfg.password = getpass.getpass(f"  {prompt_label} Password: ")
    return cfg


# ─────────────────────────────────────────────
# VIEW DISCOVERY
# ─────────────────────────────────────────────

def get_views(cfg: ConnectionConfig) -> dict:
    if not cfg.databases:
        return {}
    schemas = ",".join(f"'{db}'" for db in cfg.databases)
    query = (
        f"SELECT TABLE_SCHEMA, TABLE_NAME "
        f"FROM information_schema.VIEWS "
        f"WHERE TABLE_SCHEMA IN ({schemas});"
    )
    out = run_query(cfg, query)
    views = {}
    if out:
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) == 2:
                schema, view = parts[0].strip(), parts[1].strip()
                views.setdefault(schema, []).append(view)
    return views


# ─────────────────────────────────────────────
# DEFINER CLEANUP
# ─────────────────────────────────────────────

def strip_definers(dump_dir: Path) -> bool:
    sql_files = list(dump_dir.glob("*.sql"))
    if not sql_files:
        print_err("Нет .sql файлов для очистки")
        return False
    errors = False
    for f in sql_files:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
            cleaned = re.sub(r"DEFINER=`[^`]*`@`[^`]*`\s*", "", content)
            f.write_text(cleaned, encoding="utf-8")
            print_ok(f"Очищен: {f.name}")
        except Exception as e:
            print_err(f"{f.name}: {e}")
            errors = True
    return not errors


# ─────────────────────────────────────────────
# DUMP STEPS
# ─────────────────────────────────────────────

COMMON_FLAGS = ["--column-statistics=0", "--default-character-set=utf8mb4"]


def dump_structure(cfg: ConnectionConfig, dump_dir: Path) -> bool:
    print_step("1/6", "Structure (таблицы)")
    cmd = (["mysqldump"] + build_base_args(cfg)
           + ["--databases"] + cfg.databases
           + ["--no-data", "--skip-triggers", "--routines=0", "--events=0"]
           + COMMON_FLAGS)
    ok = run_to_file(cmd, dump_dir / "structure.sql", "structure")
    if ok: print_ok("structure.sql")
    return ok


def dump_data(cfg: ConnectionConfig, dump_dir: Path) -> bool:
    print_step("2/6", "Data (данные)")
    cmd = (["mysqldump"] + build_base_args(cfg)
           + ["--databases"] + cfg.databases
           + ["--no-create-info", "--skip-triggers", "--routines=0", "--events=0",
              "--single-transaction", "--quick"]
           + COMMON_FLAGS)
    ok = run_to_file(cmd, dump_dir / "data.sql", "data")
    if ok: print_ok("data.sql")
    return ok


def dump_views(cfg: ConnectionConfig, dump_dir: Path) -> bool:
    print_step("3/6", "Views")
    views = get_views(cfg)
    if not views:
        print_skip("Views не найдены — пропускаем")
        return True

    all_parts = []

    for schema, view_list in views.items():
        print(f"    {schema}: {', '.join(view_list)}")

        cmd = (["mysqldump"] + build_base_args(cfg)
               + [schema] + view_list
               + ["--no-create-db", "--no-data", "--skip-triggers",
                  "--routines=0", "--events=0"]
               + COMMON_FLAGS)

        result = subprocess.run(cmd, capture_output=True)

        if result.returncode != 0:
            lines = _filter_stderr(result.stderr.decode("utf-8", errors="replace"))
            if lines:
                print_err("\n".join(lines))
            return False

        # Добавляем USE чтобы views.sql не падал с "No database selected"
        # (дамп без --databases не включает эту директиву автоматически)
        all_parts.append(f"USE `{schema}`;\n" + result.stdout.decode("utf-8", errors="replace"))

    out_file = dump_dir / "views.sql"
    out_file.write_text("\n".join(all_parts), encoding="utf-8")

    print_ok(f"views.sql ({sum(len(v) for v in views.values())} view(s))")
    return True

def dump_triggers(cfg: ConnectionConfig, dump_dir: Path) -> bool:
    print_step("4/6", "Triggers")
    cmd = (["mysqldump"] + build_base_args(cfg)
           + ["--databases"] + cfg.databases
           + ["--no-data", "--no-create-info", "--triggers",
              "--skip-routines", "--skip-events"]
           + COMMON_FLAGS)
    ok = run_to_file(cmd, dump_dir / "triggers.sql", "triggers")
    if ok: print_ok("triggers.sql")
    return ok


def dump_routines(cfg: ConnectionConfig, dump_dir: Path) -> bool:
    print_step("5/6", "Routines")
    cmd = (["mysqldump"] + build_base_args(cfg)
           + ["--databases"] + cfg.databases
           + ["--no-data", "--no-create-info", "--routines",
              "--skip-triggers", "--skip-events"]
           + COMMON_FLAGS)
    ok = run_to_file(cmd, dump_dir / "routines.sql", "routines")
    if ok: print_ok("routines.sql")
    return ok


def dump_events(cfg: ConnectionConfig, dump_dir: Path) -> bool:
    print_step("6/6", "Events")
    cmd = (["mysqldump"] + build_base_args(cfg)
           + ["--databases"] + cfg.databases
           + ["--no-data", "--no-create-info", "--events",
              "--skip-triggers", "--skip-routines"]
           + COMMON_FLAGS)
    ok = run_to_file(cmd, dump_dir / "events.sql", "events")
    if ok: print_ok("events.sql")
    return ok


# ─────────────────────────────────────────────
# RESTORE
# ─────────────────────────────────────────────

# routines идут ПЕРВЫМИ — structure.sql может содержать DEFAULT/CHECK
# выражения, ссылающиеся на функции; без routines такой импорт упадёт.
RESTORE_ORDER = ["routines.sql", "structure.sql", "data.sql",
                 "views.sql", "triggers.sql", "events.sql"]


def _get_databases_from_dir(dump_dir: Path) -> list[str]:
    """Извлекает список баз из structure.sql (строки CREATE DATABASE)."""
    struct = dump_dir / "structure.sql"
    if not struct.exists():
        return []
    dbs = []
    for line in struct.read_bytes().decode("utf-8", errors="replace").splitlines():
        m = re.match(r"CREATE DATABASE[^`]*`([^`]+)`", line, re.IGNORECASE)
        if m:
            dbs.append(m.group(1))
    return dbs


def drop_and_recreate_databases(cfg: ConnectionConfig, dump_dir: Path) -> bool:
    """DROP + CREATE каждой базы — чистый старт перед restore."""
    dbs = _get_databases_from_dir(dump_dir)
    if not dbs:
        print_err("Не удалось определить список баз из structure.sql")
        return False
    for db in dbs:
        print(f"    DROP DATABASE IF EXISTS `{db}`  →  CREATE DATABASE")
        ok1 = run_query(cfg, f"DROP DATABASE IF EXISTS `{db}`;") is not None
        ok2 = run_query(cfg, f"CREATE DATABASE `{db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;") is not None
        if not (ok1 and ok2):
            print_err(f"Не удалось пересоздать базу `{db}`")
            return False
    return True


def restore(cfg: ConnectionConfig, dump_dir: Path,
            force: bool = False, clean: bool = False) -> bool:
    print_header(f"RESTORE  {cfg.label()}  ←  {dump_dir}")

    if clean:
        print_step("PRE", "Сброс баз (--clean)")
        if not drop_and_recreate_databases(cfg, dump_dir):
            return False

    errors = False
    t0 = time.time()
    for filename in RESTORE_ORDER:
        sql_file = dump_dir / filename
        if not sql_file.exists():
            print_skip(f"{filename} — не найден, пропуск")
            continue
        print_step("→", filename)
        cmd = ["mysql"] + build_base_args(cfg) + ["--default-character-set=utf8mb4"]
        if force:
            cmd.append("--force")   # продолжать при ошибках (не останавливаться)
        ok = run_from_file(cmd, sql_file, filename)
        if ok:
            print_ok(f"{filename} — импортирован")
        else:
            errors = True
            if not force:
                print_err("Остановка. Используйте --force чтобы продолжать при ошибках,")
                print_err("или --clean для сброса баз перед restore.")
                break
    elapsed = time.time() - t0
    print_header("ИТОГ RESTORE")
    if errors:
        print_err("Часть файлов импортирована с ошибками")
    else:
        print_ok(f"Restore завершён за {elapsed:.1f}с")
    return not errors


# ─────────────────────────────────────────────
# DUMP ORCHESTRATOR
# ─────────────────────────────────────────────

def run_dump(cfg: ConnectionConfig, dump_dir: Path, skip_definer: bool) -> None:
    print_header(f"DUMP  {cfg.label()}  →  {dump_dir}")
    dump_dir.mkdir(parents=True, exist_ok=True)
    if not cfg.databases:
        print_err("Список баз пуст. Запустите: db_dump.py config-source")
        sys.exit(1)
    require_tools("mysqldump", "mysql")
    if not test_connection(cfg, f"SOURCE {cfg.label()}"):
        sys.exit(1)
    steps = [dump_structure, dump_data, dump_views,
             dump_triggers, dump_routines, dump_events]
    failed = []
    t0 = time.time()
    for step_fn in steps:
        if not step_fn(cfg, dump_dir):
            failed.append(step_fn.__name__)
    if not skip_definer:
        print_step("POST", "Очистка DEFINER")
        strip_definers(dump_dir)
    elapsed = time.time() - t0
    print_header("ИТОГ DUMP")
    if failed:
        print_err(f"Упавшие шаги: {', '.join(failed)}")
        sys.exit(1)
    else:
        print_ok(f"Дамп завершён за {elapsed:.1f}с → {dump_dir}")


# ─────────────────────────────────────────────
# INTERACTIVE CONFIG EDITORS
# ─────────────────────────────────────────────

def _prompt(label: str, default: str = "") -> str:
    val = input(f"  {label} [{default}]: ").strip()
    return val if val else default


def configure_source() -> None:
    cfg = load_source_config()
    print_header("НАСТРОЙКА SOURCE (откуда дампить)")
    cfg.host = _prompt("Host", cfg.host)
    cfg.port = int(_prompt("Port", str(cfg.port)))
    cfg.user = _prompt("User", cfg.user)
    print(f"\n  Текущие базы: {cfg.databases or '—'}")
    raw = input("  Databases (через пробел, Enter = оставить): ").strip()
    if raw:
        cfg.databases = raw.split()
    save_source_config(cfg)


def configure_target() -> None:
    cfg = load_target_config()
    print_header("НАСТРОЙКА TARGET (куда восстанавливать)")
    cfg.host = _prompt("Host", cfg.host)
    cfg.port = int(_prompt("Port", str(cfg.port)))
    cfg.user = _prompt("User", cfg.user)
    save_target_config(cfg)


def show_config() -> None:
    raw = _load_raw()
    print_header("ТЕКУЩИЙ КОНФИГ")
    for role in ("source", "target"):
        section = raw.get(role, {})
        if section:
            print(f"\n  [{role.upper()}]")
            print(f"    host:      {section.get('host', '—')}")
            print(f"    port:      {section.get('port', '—')}")
            print(f"    user:      {section.get('user', '—')}")
            print(f"    databases: {section.get('databases', [])}")
        else:
            print(f"\n  [{role.upper()}]  — не настроен")
    print()


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def _add_src_args(p):
    g = p.add_argument_group("source override")
    g.add_argument("--src-host",     dest="src_host")
    g.add_argument("--src-port",     dest="src_port",      type=int)
    g.add_argument("--src-user",     dest="src_user")
    g.add_argument("--src-password", dest="src_password")
    g.add_argument("--src-db",       dest="src_databases", nargs="+", metavar="DB")


def _add_tgt_args(p):
    g = p.add_argument_group("target override")
    g.add_argument("--tgt-host",     dest="tgt_host")
    g.add_argument("--tgt-port",     dest="tgt_port",     type=int)
    g.add_argument("--tgt-user",     dest="tgt_user")
    g.add_argument("--tgt-password", dest="tgt_password")


def _apply_src(cfg: ConnectionConfig, args) -> ConnectionConfig:
    if getattr(args, "src_host",      None): cfg.host      = args.src_host
    if getattr(args, "src_port",      None): cfg.port      = args.src_port
    if getattr(args, "src_user",      None): cfg.user      = args.src_user
    if getattr(args, "src_databases", None): cfg.databases = args.src_databases
    if getattr(args, "src_password",  None):
        cfg.password = args.src_password
    else:
        cfg = ask_password(cfg, "Source")
    return cfg


def _apply_tgt(cfg: ConnectionConfig, args) -> ConnectionConfig:
    if getattr(args, "tgt_host", None): cfg.host = args.tgt_host
    if getattr(args, "tgt_port", None): cfg.port = args.tgt_port
    if getattr(args, "tgt_user", None): cfg.user = args.tgt_user
    if getattr(args, "tgt_password", None):
        cfg.password = args.tgt_password
    else:
        cfg = ask_password(cfg, "Target")
    return cfg


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="db_dump",
        description="MySQL Dump & Restore — source и target раздельные конфиги",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  python db_dump.py config-source              # Настроить source (откуда дампить)
  python db_dump.py config-target              # Настроить target (куда восстанавливать)
  python db_dump.py config-show                # Показать оба конфига

  python db_dump.py dump                       # Дамп с source реквизитами
  python db_dump.py dump --dir /backups/prod   # Дамп в нужную папку

  python db_dump.py restore                    # Restore с target реквизитами
  python db_dump.py restore --dir /backups/prod

  python db_dump.py test-source                # Проверить source соединение
  python db_dump.py test-target                # Проверить target соединение

  # Переопределить реквизиты прямо в команде:
  python db_dump.py dump --src-host 192.168.1.10 --src-port 3308 --src-user root --src-db db1 db2
  python db_dump.py restore --tgt-host 192.168.1.20 --tgt-port 3306 --tgt-user root
        """,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("config-source", help="Настроить source подключение")
    sub.add_parser("config-target", help="Настроить target подключение")
    sub.add_parser("config-show",   help="Показать оба конфига")
    sub.add_parser("test-source",   help="Проверить source соединение")
    sub.add_parser("test-target",   help="Проверить target соединение")

    p_dump = sub.add_parser("dump", help="Создать полный дамп (source)")
    p_dump.add_argument("--dir", default="dump")
    p_dump.add_argument("--no-clean-definer", action="store_true")
    _add_src_args(p_dump)

    p_res = sub.add_parser("restore", help="Восстановить из .sql (target)")
    p_res.add_argument("--dir", default="dump")
    p_res.add_argument(
        "--force", action="store_true",
        help="Продолжать при ошибках (передаёт --force в mysql)"
    )
    p_res.add_argument(
        "--clean", action="store_true",
        help="DROP + CREATE каждой базы перед импортом (чистый старт)"
    )
    _add_tgt_args(p_res)

    p_views = sub.add_parser("views", help="Показать views в source базах")
    _add_src_args(p_views)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "config-source":
        configure_source(); return

    if args.command == "config-target":
        configure_target(); return

    if args.command == "config-show":
        show_config(); return

    if args.command == "test-source":
        require_tools("mysql")
        src = ask_password(load_source_config(), "Source")
        sys.exit(0 if test_connection(src, f"SOURCE {src.label()}") else 1)

    if args.command == "test-target":
        require_tools("mysql")
        tgt = ask_password(load_target_config(), "Target")
        sys.exit(0 if test_connection(tgt, f"TARGET {tgt.label()}") else 1)

    if args.command == "dump":
        src = _apply_src(load_source_config(), args)
        run_dump(src, Path(args.dir), skip_definer=args.no_clean_definer)
        return

    if args.command == "restore":
        require_tools("mysql")
        tgt = _apply_tgt(load_target_config(), args)
        if not test_connection(tgt, f"TARGET {tgt.label()}"):
            sys.exit(1)
        ok = restore(tgt, Path(args.dir),
                     force=args.force, clean=args.clean)
        sys.exit(0 if ok else 1)

    if args.command == "views":
        require_tools("mysql")
        src = _apply_src(load_source_config(), args)
        if not test_connection(src, f"SOURCE {src.label()}"):
            sys.exit(1)
        views = get_views(src)
        if not views:
            print("Views не найдены")
            return
        for schema, vlist in views.items():
            print(f"\n  {schema}:")
            for v in vlist:
                print(f"    - {v}")


if __name__ == "__main__":
    main()
