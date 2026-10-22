# 🛠️ Sistema Modular de Restauración de Bases de Datos PostgreSQL

Herramienta diseñada para automatizar y facilitar la restauración de respaldos (`.dump`) de PostgreSQL, optimizada tanto para usuarios inexpertos mediante una interfaz gráfica amigable como para administradores mediante línea de comandos (CLI).

<p align="center">
  <img 
    src="https://github.com/jonatanLara/jonatanLara/blob/main/src/header_3_t.png?raw=true" 
    alt="Hoja Calendario"
    width="73%"
  />
</p>

<p align="center">
  <a href="https://github.com/jonatanLara">🐙 GitHub</a> |
  <a href="https://www.youtube.com/@jonatanlara">📺 YouTube</a> |
  <a href="https://www.instagram.com/jonatanlaraortiz/">📸 Instagram</a>
</p>
<br>

<br>

## 📂 Estructura del Proyecto

```text
restorer_tool/
│
├── core/
│   ├── __init__.py
│   └── database.py      # Lógica central: Conexión, listado/creación de BDs y ejecución de pg_restore
│
├── cli.py               # Interfaz de Línea de Comandos basada en argparse
├── gui.py               # Interfaz Gráfica de Usuario construida en Tkinter
└── README.md            # Documentación técnica del proyecto

```

## Características Técnicas Principales

### 1. Arquitectura Desacoplada (`core/database.py`):

- Toda la lógica de negocio, manejo de subprocesos y comunicación con PostgreSQL está aislada de las interfaces de usuario.
- Soporte para autenticación mediante contraseña segura (PGPASSWORD mediante variables de entorno del subproceso para evitar exponer credenciales en la terminal).

### 2. Detección Dinámica y Resiliencia:

- Búsqueda automática del último backup: Si no se especifica un archivo, el sistema escanea el directorio predeterminado ordenando por marcas de tiempo en orden descendente.
- Autolimpieza de fallos: Detecta automáticamente archivos temporales rezagados (.dump.temp) de ejecuciones interrumpidas y los elimina de manera segura antes de iniciar una nueva transacción.
- Gestión de Bases de Datos: Permite listar las bases de datos activas en el servidor o crear una nueva base de datos al vuelo directamente desde la herramienta.

### 3. Interfaz Gráfica (gui.py):

- Construida con Tkinter y diseño adaptable (ttk).
- Implementa multihilos (Threading) para evitar que la ventana se congele durante la ejecución de grandes volúmenes de datos con pg_restore.
- Consola integrada con estilo "Terminal" (stderr/stdout en tiempo real con codificación UTF-8).

### 4. Interfaz de Línea de Comandos (cli.py):

- Parámetros flexibles configurables mediante argumentos estándar (--host, --port, --user, --password, --db, --file, --create-db).

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas!  
Si tienes mejoras, errores que reportar o ideas para funciones nuevas, no dudes en abrir un issue o pull request.

---

## 📄 Licencia

Este proyecto está bajo la licencia [MIT](LICENSE).

---
