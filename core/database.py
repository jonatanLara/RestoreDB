import os
import subprocess
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
        """Establece conexión con PostgreSQL."""
        return psycopg2.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=db_name
        )

    def test_connection(self):
        """Prueba la conexión al servidor PostgreSQL."""
        try:
            conn = self._get_connection("postgres")
            conn.close()
            return True, "Conexión exitosa al servidor PostgreSQL."
        except Exception as e:
            return False, str(e)

    def list_databases(self):
        """Lista todas las bases de datos disponibles en el servidor."""
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
        """Crea una nueva base de datos en el servidor."""
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
        """Obtiene el archivo .dump más reciente en el directorio de respaldos."""
        if not os.path.exists(self.backup_dir):
            raise FileNotFoundError(f"La carpeta de respaldos no existe: {self.backup_dir}")
        
        backup_files = [f for f in os.listdir(self.backup_dir) if f.endswith(".dump")]
        if not backup_files:
            raise FileNotFoundError(f"No se encontraron archivos de respaldo (.dump) en: {self.backup_dir}")
        
        backup_files.sort(reverse=True)
        return os.path.join(self.backup_dir, backup_files[0])

    def clean_failed_backups(self):
        """Limpia archivos temporales o respaldos fallidos anteriores."""
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

    def restore_database(self, db_name, backup_file_path=None, callback_output=None):
        """
        Ejecuta pg_restore de manera síncrona/en tiempo real.
        callback_output es una función que recibe cada línea de texto generada.
        """
        if not backup_file_path or backup_file_path.strip() == "":
            backup_file_path = self.get_latest_backup()
        
        if not os.path.isfile(backup_file_path):
            raise FileNotFoundError(f"El archivo de respaldo no existe: {backup_file_path}")

        # Limpiar fallidos antes de arrancar
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
            "--no-privileges",
            backup_file_path
        ]

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