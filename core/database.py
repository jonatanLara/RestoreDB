import os
import subprocess
import re
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

class DatabaseRestorer:
    def __init__(self, host="localhost", port="5432", user="postgres", password="", backup_dir=None):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        
        if backup_dir:
            self.backup_dir = backup_dir
        else:
            self.backup_dir = os.path.expanduser("~/backups_tren_maya_database") if os.name != "nt" else "C:\\backups_tren_maya_database"

    def _get_connection(self, db_name="postgres"):
        return psycopg2.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=db_name
        )

    def test_connection(self):
        try:
            conn = self._get_connection("postgres")
            conn.close()
            return True, "Conexión exitosa al servidor PostgreSQL."
        except Exception as e:
            return False, str(e)

    def list_databases(self):
        try:
            conn = self._get_connection("postgres")
            cursor = conn.cursor()
            cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
            dbs = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            return dbs
        except Exception as e:
            return []

    def create_database(self, db_name):
        try:
            conn = self._get_connection("postgres")
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            cursor.execute(f'CREATE DATABASE "{db_name}";')
            cursor.close()
            conn.close()
            return True, f"Base de datos '{db_name}' creada exitosamente."
        except Exception as e:
            return False, str(e)

    def get_latest_backup(self):
        if not os.path.exists(self.backup_dir):
            raise FileNotFoundError(f"La carpeta de respaldos no existe: {self.backup_dir}")
        
        backup_files = [f for f in os.listdir(self.backup_dir) if f.endswith(".dump")]
        if not backup_files:
            raise FileNotFoundError(f"No se encontraron archivos de respaldo (.dump) en: {self.backup_dir}")
        
        backup_files.sort(reverse=True)
        return os.path.join(self.backup_dir, backup_files[0])

    def clean_failed_backups(self):
        cleaned_logs = []
        if not os.path.exists(self.backup_dir):
            return cleaned_logs

        for file in os.listdir(self.backup_dir):
            if file.endswith(".dump.temp"):
                failed_dump = file.replace(".temp", "")
                failed_dump_path = os.path.join(self.backup_dir, failed_dump)
                in_progress_path = os.path.join(self.backup_dir, file)

                cleaned_logs.append(f"Eliminando backup fallido: {failed_dump_path}")
                if os.path.exists(failed_dump_path):
                    os.remove(failed_dump_path)
                if os.path.exists(in_progress_path):
                    os.remove(in_progress_path)
        return cleaned_logs

    def get_dump_schemas(self, backup_file_path):
        """
        Ejecuta pg_restore -l para inspeccionar el contenido del dump
        y extraer los nombres de los esquemas (SCHEMA) de forma robusta.
        """
        if not os.path.isfile(backup_file_path):
            raise FileNotFoundError(f"El archivo no existe: {backup_file_path}")

        cmd = ["pg_restore", "-l", backup_file_path]
        env = os.environ.copy()
        if self.password:
            env["PGPASSWORD"] = self.password

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                env=env,
                check=True
            )
            
            schemas = set()
            for line in result.stdout.splitlines():
                # Buscar líneas que contengan la definición de un esquema
                if "SCHEMA" in line:
                    parts = line.split()
                    # El nombre del esquema suele ser el antepenúltimo o último token antes del propietario,
                    # o podemos buscar el elemento que sigue a "SCHEMA" o "-"
                    if "SCHEMA" in parts:
                        idx = parts.index("SCHEMA")
                        # Revisar los elementos posteriores a la palabra SCHEMA
                        for token in parts[idx+1:]:
                            # Ignorar guiones o palabras clave comunes de metadatos
                            if token not in ["-", "COMMENT", "AS", "AUTHORIZATION"] and not token.startswith("--"):
                                clean_name = token.replace('"', '').strip()
                                if clean_name:
                                    schemas.add(clean_name)
                                break
            
            # Si por alguna razón el parser no detectó ninguno, aseguramos al menos 'public'
            if not schemas:
                schemas.add("public")

            # Ordenar alfabéticamente asegurando que 'public' quede primero
            schema_list = sorted(list(schemas))
            if "public" in schema_list:
                schema_list.remove("public")
                schema_list.insert(0, "public")
                
            return schema_list
        except Exception as e:
            return ["public"]
    
    def get_dump_tables(self, backup_file_path):
        """
        Ejecuta pg_restore -l para extraer las tablas del dump analizando 
        la estructura real de las líneas TABLE del TOC de PostgreSQL.
        """
        if not os.path.isfile(backup_file_path):
            raise FileNotFoundError(f"El archivo no existe: {backup_file_path}")

        cmd = ["pg_restore", "-l", backup_file_path]
        env = os.environ.copy()
        if self.password:
            env["PGPASSWORD"] = self.password

        try:
            result = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding='utf-8', env=env, check=True
            )
            
            tables = set()
            for line in result.stdout.splitlines():
                # Buscamos líneas que contengan TABLE y pertenezcan a la definición de la tabla
                if "TABLE" in line and "TABLE DATA" not in line and not line.strip().startswith(";"):
                    parts = line.split()
                    if "TABLE" in parts:
                        idx = parts.index("TABLE")
                        # Todo lo que está después de "TABLE" hasta el final suelen ser tokens descriptivos
                        tokens = [p.replace('"', '').strip() for p in parts[idx+1:] if p not in ["-", "AS", "AUTHORIZATION"] and not p.startswith("--")]
                        
                        if len(tokens) >= 2:
                            # Por lo general, el último token es el esquema y el penúltimo es la tabla
                            # Ejemplo: ['dictaminacion', 'tc_dictaminacion_ddv_l', 'continuidad_dictamenes'] o similar
                            # Tomaremos el nombre de la tabla y su esquema contenedor principal
                            table_name = tokens[-2]
                            schema_name = tokens[-1]
                            tables.add(f"{schema_name}.{table_name}")
                        elif len(tokens) == 1:
                            tables.add(tokens[0])
                            
            return sorted(list(tables))
        except Exception as e:
            return []
        

    def restore_database(self, db_name, backup_file_path=None, selected_schemas=None, selected_tables=None, callback_output=None):
        """
        Ejecuta pg_restore aplicando la bandera -n de forma dinámica si se especifican esquemas.
        """
        if not backup_file_path or backup_file_path.strip() == "":
            backup_file_path = self.get_latest_backup()
        
        if not os.path.isfile(backup_file_path):
            raise FileNotFoundError(f"El archivo de respaldo no existe: {backup_file_path}")

        self.clean_failed_backups()

        pg_restore_cmd = [
            "pg_restore",
            "-h", self.host,
            "-p", str(self.port),
            "-U", self.user,
            "-d", db_name,
            "-v",
            "--clean",
            "--no-owner",
            "--no-privileges"
        ]

        # Agregar esquemas dinámicamente si se proporcionan
        # Si eligieron esquemas específicos
        if selected_schemas:
            for schema in selected_schemas:
                pg_restore_cmd.extend(["-n", schema])

        # Si eligieron tablas específicas (modo granular para departamentos)
        if selected_tables:
            for table in selected_tables:
                pg_restore_cmd.extend(["-t", table])

        pg_restore_cmd.append(backup_file_path)

        env = os.environ.copy()
        if self.password:
            env["PGPASSWORD"] = self.password

        process = subprocess.Popen(
            pg_restore_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            env=env,
            bufsize=1
        )

        output_lines = []
        for line in process.stdout:
            if callback_output:
                callback_output(line)
            output_lines.append(line)

        process.wait()
        exit_code = process.returncode

        full_output = "".join(output_lines)
        errors = [line for line in output_lines if "error" in line.lower()]
        warnings = [line for line in output_lines if "warning" in line.lower() or "precaución" in line.lower()]

        return {
            "exit_code": exit_code,
            "backup_used": backup_file_path,
            "errors": errors,
            "warnings": warnings,
            "full_output": full_output
        }