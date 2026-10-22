import argparse
import sys
from core.database import DatabaseRestorer

def main():
    parser = argparse.ArgumentParser(description="Herramienta CLI de Restauración de PostgreSQL")
    parser.add_argument("--host", default="localhost", help="Host del servidor PostgreSQL")
    parser.add_argument("--port", default="5432", help="Puerto de PostgreSQL")
    parser.add_argument("--user", default="postgres", help="Usuario de la base de datos")
    parser.add_argument("--password", default="", help="Contraseña del usuario")
    parser.add_argument("--db", default="tren_maya", help="Nombre de la base de datos destino")
    parser.add_argument("--file", default="", help="Ruta completa al archivo .dump (si se omite, toma el más reciente)")
    parser.add_argument("--dir", default="", help="Carpeta personalizada de respaldos")
    parser.add_argument("--create-db", action="store_true", help="Crea la base de datos destino si no existe antes de restaurar")

    args = parser.parse_args()

    restorer = DatabaseRestorer(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        backup_dir=args.dir if args.dir else None
    )

    print("====================================================")
    print("   CLI - RESTAURADOR DE BASE DE DATOS POSTGRESQL    ")
    print("====================================================")

    # Validar conexión
    connected, msg = restorer.test_connection()
    if not connected:
        print(f"❌ Error de conexión: {msg}")
        sys.exit(1)

    # Crear BD si se solicita
    if args.create_db:
        print(f"Creando base de datos '{args.db}'...")
        success, msg = restorer.create_database(args.db)
        print(msg)

    print(f"\nIniciando restauración en la BD: {args.db}")
    
    def print_stream(line):
        print(line, end="")

    try:
        result = restorer.restore_database(
            db_name=args.db,
            backup_file_path=args.file if args.file else None,
            callback_output=print_stream
        )

        print("\n===============================")
        print("         RESULTADO             ")
        print("===============================")
        print(f"Archivo usado: {result['backup_used']}")
        print(f"Exit Code: {result['exit_code']}")
        print(f"Errores detectados: {len(result['errors'])}")
        print(f"Warnings detectados: {len(result['warnings'])}")

        if result['exit_code'] == 0:
            print("✅ ¡Restauración completada con éxito!")
        elif result['exit_code'] == 1:
            print("⚠️ Restauración completada con advertencias/errores ignorados.")
        else:
            print("❌ Ocurrió un error crítico durante la restauración.")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()