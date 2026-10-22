import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from core.database import DatabaseRestorer

class RestorerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Restaurador de Base de Datos - Tren Maya")
        self.root.geometry("750x650")
        self.root.minsize(700, 600)

        # Configurar estilo visual moderno
        style = ttk.Style()
        style.theme_use("clam")

        self.create_widgets()

    def create_widgets(self):
        # Frame Principal con Padding
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Título
        title_label = ttk.Label(main_frame, text="Asistente de Restauración PostgreSQL", font=("Arial", 14, "bold"))
        title_label.pack(anchor=tk.W, pady=(0, 10))

        # --- SECCIÓN DE CONEXIÓN ---
        conn_frame = ttk.LabelFrame(main_frame, text=" Configuración de Conexión ", padding=10)
        conn_frame.pack(fill=tk.X, pady=5)

        conn_frame.columnconfigure(1, weight=1)
        conn_frame.columnconfigure(3, weight=1)

        # Host
        ttk.Label(conn_frame, text="Host:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.host_entry = ttk.Entry(conn_frame)
        self.host_entry.insert(0, "localhost")
        self.host_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)

        # Puerto
        ttk.Label(conn_frame, text="Puerto:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.port_entry = ttk.Entry(conn_frame, width=8)
        self.port_entry.insert(0, "5432")
        self.port_entry.grid(row=0, column=3, sticky=tk.EW, padx=5, pady=5)

        # Usuario
        ttk.Label(conn_frame, text="Usuario:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.user_entry = ttk.Entry(conn_frame)
        self.user_entry.insert(0, "postgres")
        self.user_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)

        # Contraseña
        ttk.Label(conn_frame, text="Contraseña:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.pass_entry = ttk.Entry(conn_frame, show="*")
        self.pass_entry.grid(row=1, column=3, sticky=tk.EW, padx=5, pady=5)

        # Botón Probar Conexión y Listar BDs
        btn_test = ttk.Button(conn_frame, text="Conectar y Actualizar BDs", command=self.test_and_load_dbs)
        btn_test.grid(row=2, column=0, columnspan=4, sticky=tk.EW, padx=5, pady=5)

        # --- SECCIÓN DE BASE DE DATOS Y RESPALDO ---
        db_frame = ttk.LabelFrame(main_frame, text=" Base de Datos y Archivo de Respaldo ", padding=10)
        db_frame.pack(fill=tk.X, pady=10)

        db_frame.columnconfigure(1, weight=1)

        # Base de datos destino (Combobox + Opción de crear nueva)
        ttk.Label(db_frame, text="Base de Datos:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.db_combobox = ttk.Combobox(db_frame, values=["tren_maya"])
        self.db_combobox.set("tren_maya")
        self.db_combobox.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)

        btn_new_db = ttk.Button(db_frame, text="Crear Nueva BD", command=self.prompt_create_database)
        btn_new_db.grid(row=0, column=2, padx=5, pady=5)

        # Archivo Backup
        ttk.Label(db_frame, text="Archivo .dump:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.file_entry = ttk.Entry(db_frame)
        self.file_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)

        btn_browse = ttk.Button(db_frame, text="Examinar...", command=self.browse_file)
        btn_browse.grid(row=1, column=2, padx=5, pady=5)

        # Nota al margen
        note_label = ttk.Label(db_frame, text="* Si deja el campo de archivo vacío, se usará automáticamente el más reciente.", font=("Arial", 8, "italic"), foreground="gray")
        note_label.grid(row=2, column=0, columnspan=3, sticky=tk.W, padx=5)

        # --- BOTÓN DE EJECUCIÓN ---
        self.btn_restore = ttk.Button(main_frame, text="INICIAR RESTAURACIÓN", command=self.start_restore_thread)
        self.btn_restore.pack(fill=tk.X, pady=5)

        # --- CONSOLA / LOGS EN TIEMPO REAL ---
        log_frame = ttk.LabelFrame(main_frame, text=" Progreso de la Restauración ", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_text = tk.Text(log_frame, wrap=tk.WORD, bg="black", fg="#00FF00", font=("Consolas", 9))
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def get_restorer_instance(self):
        return DatabaseRestorer(
            host=self.host_entry.get().strip(),
            port=self.port_entry.get().strip(),
            user=self.user_entry.get().strip(),
            password=self.pass_entry.get().strip()
        )

    def test_and_load_dbs(self):
        restorer = self.get_restorer_instance()
        success, msg = restorer.test_connection()
        if not success:
            messagebox.showerror("Error de Conexión", f"No se pudo conectar al servidor:\n{msg}")
            return
        
        dbs = restorer.list_databases()
        if dbs:
            self.db_combobox['values'] = dbs
            messagebox.showinfo("Conexión Exitosa", f"Conexión establecida correctamente.\nSe encontraron {len(dbs)} bases de datos.")
        else:
            messagebox.showwarning("Aviso", "Conexión exitosa, pero no se pudieron listar las bases de datos.")

    def prompt_create_database(self):
        new_db_name = tk.simpledialog.askstring("Crear Base de Datos", "Ingrese el nombre de la nueva base de datos:")
        if not new_db_name:
            return
        
        restorer = self.get_restorer_instance()
        success, msg = restorer.create_database(new_db_name.strip())
        if success:
            messagebox.showinfo("Éxito", msg)
            dbs = restorer.list_databases()
            self.db_combobox['values'] = dbs
            self.db_combobox.set(new_db_name.strip())
        else:
            messagebox.showerror("Error", f"No se pudo crear la base de datos:\n{msg}")

    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Seleccionar archivo de respaldo",
            filetypes=[("Archivos Dump PostgreSQL", "*.dump"), ("Todos los archivos", "*.*")]
        )
        if filename:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, filename)

    def log_message(self, message):
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)

    def start_restore_thread(self):
        db_name = self.db_combobox.get().strip()
        if not db_name:
            messagebox.showwarning("Campo requerido", "Debe seleccionar o escribir una base de datos destino.")
            return

        if not messagebox.askyesno("Confirmar Restauración", f"¿Está seguro de restaurar el respaldo en la base de datos '{db_name}'?\nEsto sobrescribirá los datos actuales."):
            return

        self.btn_restore.config(state=tk.DISABLED)
        self.log_text.delete("1.0", tk.END)

        # Ejecutar en segundo plano para no congelar la interfaz gráfica
        threading.Thread(target=self.run_restore_process, args=(db_name,), daemon=True).start()

    def run_restore_process(self, db_name):
        restorer = self.get_restorer_instance()
        backup_path = self.file_entry.get().strip()

        try:
            self.log_message(f"Iniciando proceso de restauración en '{db_name}'...\n")
            
            result = restorer.restore_database(
                db_name=db_name,
                backup_file_path=backup_path if backup_path else None,
                callback_output=lambda line: self.root.after(0, self.log_message, line)
            )

            self.root.after(0, lambda: self.finalize_restore(result))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error Crítico", str(e)))
            self.root.after(0, lambda: self.btn_restore.config(state=tk.NORMAL))

    def finalize_restore(self, result):
        self.btn_restore.config(state=tk.NORMAL)
        self.log_message("\n====================================\n")
        self.log_message(f"PROCESO FINALIZADO. Exit Code: {result['exit_code']}\n")
        self.log_message(f"Archivo utilizado: {result['backup_used']}\n")

        if result['exit_code'] == 0:
            messagebox.showinfo("Éxito", "¡La base de datos se ha restaurado correctamente sin errores!")
        elif result['exit_code'] == 1:
            messagebox.showwarning("Aviso", "La restauración finalizó, pero se ignoraron algunos errores menores (Exit Code 1).")
        else:
            messagebox.showerror("Error", "Ocurrió un error crítico durante la restauración. Revise la consola.")

if __name__ == "__main__":
    root = tk.Tk()
    app = RestorerApp(root)
    root.mainloop()