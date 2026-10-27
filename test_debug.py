#import subprocess
#import shutil

#backup_path = r"D:\Descargas\backup_tren_carga_2026-10-18_17-21.dump"

# Obtener la ruta absoluta exacta desde el PATH de Windows de forma automática
#pg_exe = shutil.which("pg_restore")

#if not pg_exe:
    # Si por algo fallara, ponemos la ruta fija que sabemos que tienes
#    pg_exe = r"C:\Program Files\PostgreSQL\17\bin\pg_restore.exe"

#print(f"✔ Usando ejecutable en: {pg_exe}\n")

#cmd = [pg_exe, "-l", backup_path]
#result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')

#print("--- PRIMERAS 30 LÍNEAS DEL ÍNDICE DEL DUMP ---")
#lines = result.stdout.splitlines()
#for i, line in enumerate(lines[:30]):
#    print(f"{i+1}: {line}")

#print(f"\nTotal de líneas en el índice: {len(lines)}")

import subprocess
import shutil

backup_path = r"D:\Descargas\backup_tren_carga_2026-10-18_17-21.dump"
pg_exe = shutil.which("pg_restore") or r"C:\Program Files\PostgreSQL\17\bin\pg_restore.exe"

result = subprocess.run([pg_exe, "-l", backup_path], capture_output=True, text=True, encoding='utf-8')

print("--- EJEMPLOS DE LÍNEAS DE TABLAS EN EL DUMP ---")
count = 0
for line in result.stdout.splitlines():
    if "TABLE" in line and "TABLE DATA" not in line:
        print(line)
        count += 1
        if count >= 15:  # Mostrar solo 15 ejemplos
            break