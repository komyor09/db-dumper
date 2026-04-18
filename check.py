# Сохраните это в файл check.py
f = open('dump/data.sql', 'rb')
for line in f:
    if b'INSERT INTO `students`' in line:
        print(line[:400].decode('utf-8', errors='replace'))
        break
f.close()