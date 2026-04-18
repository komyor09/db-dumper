import subprocess

cmd = [
    "mysqldump",
    "--host=192.168.100.211",
    "--port=3308",
    "--user=emisdb",
    "--password=7777777",
    "--default-character-set=utf8mb4",
    "--no-create-info",
    "--skip-triggers",
    "--routines=0",
    "--events=0",
    "--single-transaction",
    "--quick",
    "--column-statistics=0",
    "kbtut_project",
    "students",
    "--where=uid<=3",
]

result = subprocess.run(cmd, capture_output=True)
for line in result.stdout.split(b"\n"):
    if b"INSERT" in line:
        print("HEX:", line[:300].hex())
        print("UTF8:", line[:300].decode("utf-8", errors="replace"))
        break