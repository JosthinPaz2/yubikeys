# ============================================================================
# IMPORTACIÓN DE LIBRERÍAS
# ============================================================================
import customtkinter as ctk      # Librería para crear interfaz gráfica moderna y bonita
import json                       # Para guardar y leer datos en formato JSON
import os                         # Para manejar archivos y carpetas del sistema
import tkinter.ttk as ttk         # Para crear tablas (Treeview)
from datetime import datetime     # Para obtener fecha y hora actual
import csv                        # Para exportar reportes a Excel/CSV
from tkinter import filedialog    # Para abrir ventanas de guardar archivo

# ============================================================================
# CONFIGURACIÓN VISUAL DE LA APLICACIÓN
# ============================================================================
ctk.set_appearance_mode("dark")       # Activa el modo oscuro de la interfaz
ctk.set_default_color_theme("blue")   # Establece el tema de color azul por defecto

# ============================================================================
# DEFINICIÓN DE COLORES PERSONALIZADOS
# ============================================================================
MIDNIGHT_BLUE = "#0f172a"      # Color de fondo principal (azul muy oscuro)
SLATE_GRAY = "#1e293b"         # Color para paneles secundarios (gris azulado)
SUCCESS_GREEN = "#10b981"      # Color para mensajes de éxito (verde)
BORDER_DEFAULT = "#3b8ed0"     # Color por defecto para bordes de campos (azul)
JSON_FILE = "inventario_base.json"  # Nombre del archivo donde se guardan los datos

# ============================================================================
# DICCIONARIO DE COLORES POR ESTADO
# Cada estado de la yubikey tiene un color diferente para identificarlo visualmente
# ============================================================================
ESTADO_COLORES = {
    "Disponible": "#10b981",    # Verde - Yubikey disponible para asignar
    "Available": "#10b981",      # Verde (versión en inglés)
    "En Uso": "#3b82f6",         # Azul - Yubikey siendo usada por alguien
    "In Use": "#3b82f6",          # Azul (versión en inglés)
    "En Break": "#f59e0b",       # Ámbar - Usuario en descanso corto
    "On Break": "#f59e0b",        # Ámbar (versión en inglés)
    "En Lunch": "#f97316",       # Naranja - Usuario en almuerzo
    "On Lunch": "#f97316",        # Naranja (versión en inglés)
    "Pérdida": "#ef4444",        # Rojo - Yubikey perdida
    "Loss": "#ef4444",            # Rojo (versión en inglés)
    "Daño": "#8b5cf6",           # Violeta - Yubikey dañada
    "Damage": "#8b5cf6"           # Violeta (versión en inglés)
}

# ============================================================================
# CLASE PRINCIPAL DE LA APLICACIÓN
# Hereda de ctk.CTk que es la ventana principal de CustomTkinter
# ============================================================================
class YubiDash(ctk.CTk):
    def __init__(self):
        """
        Constructor de la clase - Se ejecuta cuando se crea la aplicación
        Aquí se configura toda la interfaz gráfica
        """
        super().__init__()  # Llama al constructor de la clase padre (ctk.CTk)
        
        # Configuración básica de la ventana
        self.title("Yubikey Management Dashboard")  # Título de la ventana
        self.geometry("1100x600")                   # Tamaño de la ventana (ancho x alto)
        self.configure(fg_color=MIDNIGHT_BLUE)      # Color de fondo de la ventana
        self.resizable(False, False)                # No permite cambiar el tamaño de la ventana

        # Inicializa la base de datos (crea el archivo JSON si no existe)
        self.initialize_database()

        # Configura el sistema de grid para dividir la ventana en columnas y filas
        self.grid_columnconfigure(1, weight=1)  # La columna 1 (derecha) se expande
        self.grid_rowconfigure(0, weight=1)     # La fila 0 ocupa todo el alto

        # ========================================================================
        # CREACIÓN DE LA BARRA LATERAL (SIDEBAR)
        # ========================================================================
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=SLATE_GRAY)
        self.sidebar.grid(row=0, column=0, sticky="nsew")  # Posiciona en la columna 0
        
        # Título de la barra lateral
        ctk.CTkLabel(self.sidebar, text="WFM SYSTEM", font=("Inter", 20, "bold")).pack(pady=30)
        
        # Botón: Registrar Nueva Yubikey
        self.btn_nueva = ctk.CTkButton(self.sidebar, text="Register New", 
                                       command=self.show_nueva_panel, corner_radius=15)
        self.btn_nueva.pack(pady=8, padx=20, fill="x")  # fill="x" hace que ocupe todo el ancho
        
        # Botón: Control de Break/Lunch
        self.btn_ingreso = ctk.CTkButton(self.sidebar, text="Break/Lunch", 
                                         command=self.show_ingreso_panel, corner_radius=15)
        self.btn_ingreso.pack(pady=8, padx=20, fill="x")
        
        # Botón: Asignar o Retornar Yubikey
        self.btn_asignacion = ctk.CTkButton(self.sidebar, text="Assign/Return", 
                                            command=self.show_asignacion_panel, corner_radius=15)
        self.btn_asignacion.pack(pady=8, padx=20, fill="x")
        
        # Botón: Reportar Pérdida o Daño
        self.btn_perdida = ctk.CTkButton(self.sidebar, text="Loss/Damage", 
                                         command=self.show_perdida_panel, corner_radius=15)
        self.btn_perdida.pack(pady=8, padx=20, fill="x")
        
        # Botón: Ver Inventario Completo
        self.btn_inv = ctk.CTkButton(self.sidebar, text="INVENTORY", 
                                     fg_color="transparent", border_width=1, 
                                     command=self.show_inv_view, corner_radius=15)
        self.btn_inv.pack(pady=8, padx=20, fill="x")
        
        # Botón: Ver Reportes de Incidentes
        self.btn_report = ctk.CTkButton(self.sidebar, text="REPORTS", 
                                        fg_color="transparent", border_width=1, 
                                        command=self.show_report_view, corner_radius=15)
        self.btn_report.pack(pady=8, padx=20, fill="x")

        # ========================================================================
        # CREACIÓN DEL ÁREA PRINCIPAL (DONDE CAMBIAN LOS PANELES)
        # ========================================================================
        self.view_main = ctk.CTkFrame(self, fg_color="transparent")
        self.view_main.grid(row=0, column=1, sticky="nsew")  # Posiciona en la columna 1 (derecha)
        self.view_main.grid_columnconfigure(0, weight=1)
        self.view_main.grid_rowconfigure(0, weight=1)

        # Creación de los 6 paneles que se mostrarán según el botón presionado
        self.panel_nueva = ctk.CTkFrame(self.view_main, fg_color="transparent")
        self.panel_ingreso = ctk.CTkFrame(self.view_main, fg_color="transparent")
        self.panel_asignacion = ctk.CTkFrame(self.view_main, fg_color="transparent")
        self.panel_perdida = ctk.CTkFrame(self.view_main, fg_color="transparent")
        self.view_inv = ctk.CTkFrame(self.view_main, fg_color="transparent")
        self.view_report = ctk.CTkFrame(self.view_main, fg_color="transparent")

        # Configura cada panel con sus elementos (títulos, campos, tablas, etc.)
        self.setup_nueva_panel()
        self.setup_ingreso_panel()
        self.setup_asignacion_panel()
        self.setup_perdida_panel()
        self.setup_inv_view()
        self.setup_report_view()
        
        # Muestra el primer panel por defecto (Registrar Nueva)
        self.show_nueva_panel()

    # ============================================================================
    # MÉTODO PARA INICIALIZAR LA BASE DE DATOS
    # ============================================================================
    def initialize_database(self):
        """
        Verifica si el archivo JSON existe. Si no existe, lo crea vacío.
        Si ya existe, ejecuta la migración para actualizar datos antiguos.
        """
        if not os.path.exists(JSON_FILE):
            # Crea el archivo JSON vacío
            with open(JSON_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f)  # Guarda una lista vacía
        else:
            # Si el archivo ya existe, migra los datos antiguos al nuevo formato
            self.migrate_database()

    # ============================================================================
    # MÉTODO PARA MIGRAR DATOS ANTIGUOS AL NUEVO FORMATO
    # ============================================================================
    def migrate_database(self):
        """
        Convierte los datos del formato antiguo al nuevo:
        - Cambia 'codigo_pickiks' por 'codigo_pipkins' (corrección ortográfica)
        - Traduce estados de español a inglés (Disponible → Available, etc.)
        - Agrega campos faltantes al historial
        """
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                datos = json.load(f)  # Lee todos los datos del JSON
            
            migrated = False  # Bandera para saber si se hicieron cambios
            
            for item in datos:
                # Corrige el nombre del campo 'codigo_pickiks' a 'codigo_pipkins'
                if 'codigo_pickiks' in item:
                    item['codigo_pipkins'] = item.pop('codigo_pickiks')
                    migrated = True
                
                # Diccionario para traducir estados de español a inglés
                state_map = {
                    'Disponible': 'Available',
                    'En Uso': 'In Use',
                    'En Break': 'On Break',
                    'En Lunch': 'On Lunch',
                    'Pérdida': 'Loss',
                    'Perdida': 'Loss',
                    'Daño': 'Damage',
                    'Dano': 'Damage'
                }
                
                # Traduce el estado principal de la yubikey
                if item.get('estado') in state_map:
                    item['estado'] = state_map[item['estado']]
                    migrated = True
                
                # Procesa cada entrada del historial
                if 'historial' in item:
                    for h in item['historial']:
                        # Corrige nombre de campo en el historial
                        if 'codigo_pickiks' in h:
                            h['codigo_pipkins'] = h.pop('codigo_pickiks')
                            migrated = True
                        
                        # Traduce estados en el historial
                        if h.get('estado') in state_map:
                            h['estado'] = state_map[h['estado']]
                            migrated = True
                        
                        # Agrega campos faltantes con valores por defecto
                        if 'usuario' not in h:
                            h['usuario'] = item.get('usuario', '')
                        if 'codigo_pipkins' not in h:
                            h['codigo_pipkins'] = item.get('codigo_pipkins', '')
                        if 'comentario' not in h:
                            h['comentario'] = ''
                
                # Si no tiene historial, crea uno vacío
                if 'historial' not in item:
                    item['historial'] = []
            
            # Si se hicieron cambios, guarda el archivo actualizado
            if migrated:
                with open(JSON_FILE, 'w', encoding='utf-8') as f:
                    json.dump(datos, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Migration error: {e}")  # Muestra error si falla la migración

    # ============================================================================
    # MÉTODOS PARA MOSTRAR/OCULTAR PANELES
    # ============================================================================
    def show_nueva_panel(self):
        """Muestra el panel de Registrar Nueva Yubikey"""
        self.hide_all_panels()  # Oculta todos los paneles primero
        self.panel_nueva.pack(fill="both", expand=True, padx=20, pady=20)

    def show_ingreso_panel(self):
        """Muestra el panel de Break/Lunch"""
        self.hide_all_panels()
        self.panel_ingreso.pack(fill="both", expand=True, padx=20, pady=20)

    def show_asignacion_panel(self):
        """Muestra el panel de Asignación/Retoma"""
        self.hide_all_panels()
        self.panel_asignacion.pack(fill="both", expand=True, padx=20, pady=20)

    def show_perdida_panel(self):
        """Muestra el panel de Pérdida/Daño"""
        self.hide_all_panels()
        self.panel_perdida.pack(fill="both", expand=True, padx=20, pady=20)

    def show_inv_view(self):
        """Muestra el panel de Inventario y carga la tabla"""
        self.hide_all_panels()
        self.view_inv.pack(fill="both", expand=True, padx=20, pady=20)
        self.load_inventory_table()  # Carga los datos en la tabla

    def show_report_view(self):
        """Muestra el panel de Reportes y carga los datos"""
        self.hide_all_panels()
        self.view_report.pack(fill="both", expand=True, padx=20, pady=20)
        self.load_reports()  # Carga los reportes de pérdidas y daños

    def hide_all_panels(self):
        """Oculta todos los paneles principales"""
        for panel in [self.panel_nueva, self.panel_ingreso, self.panel_asignacion, 
                      self.panel_perdida, self.view_inv, self.view_report]:
            panel.pack_forget()  # pack_forget() oculta el widget sin destruirlo

    # ============================================================================
    # CONFIGURACIÓN DEL PANEL DE REGISTRAR NUEVA YUBIKEY
    # ============================================================================
    def setup_nueva_panel(self):
        """Configura todos los elementos del panel de registro"""
        # Título del panel
        ctk.CTkLabel(self.panel_nueva, text="Register New Yubikey", 
                    font=("Inter", 22, "bold")).pack(pady=30)
        
        # Campo de texto para escanear/el serial
        self.entry_nueva = ctk.CTkEntry(self.panel_nueva, 
                                        placeholder_text="Scan new serial", 
                                        width=300, height=40, 
                                        font=("Inter", 16), 
                                        border_width=3, 
                                        border_color=BORDER_DEFAULT, 
                                        corner_radius=15)
        self.entry_nueva.pack(pady=10)
        
        # Permite presionar Enter para registrar
        self.entry_nueva.bind("<Return>", self.registrar_nueva_yubikey)
        
        # Label para mostrar mensajes de error o éxito
        self.label_nueva = ctk.CTkLabel(self.panel_nueva, text="", 
                                        text_color="red", 
                                        font=("Inter", 13, "bold"))
        self.label_nueva.pack(pady=5)
        
        # Tabla de movimientos recientes
        self.setup_recent_table(self.panel_nueva, 'nueva')

    # ============================================================================
    # CONFIGURACIÓN DEL PANEL DE BREAK/LUNCH
    # ============================================================================
    def setup_ingreso_panel(self):
        """Configura el panel de control de Break/Lunch"""
        ctk.CTkLabel(self.panel_ingreso, text="Break / Lunch Check-in/out", 
                    font=("Inter", 22, "bold")).pack(pady=30)
        
        # Instrucción para el usuario
        ctk.CTkLabel(self.panel_ingreso, text="Only for yubikeys IN USE", 
                    font=("Inter", 13), text_color="#94a3b8").pack(pady=(0, 20))
        
        # Campo para escanear serial
        self.entry_ingreso = ctk.CTkEntry(self.panel_ingreso, 
                                          placeholder_text="Scan for Check-in/out", 
                                          width=300, height=40, 
                                          font=("Inter", 16), 
                                          border_width=3, 
                                          border_color=BORDER_DEFAULT, 
                                          corner_radius=15)
        self.entry_ingreso.pack(pady=10)
        
        # Al presionar Enter, ejecuta process_session_scan con el parámetro 'ingreso_salida'
        self.entry_ingreso.bind("<Return>", lambda e: self.process_session_scan('ingreso_salida'))
        
        # Label para mensajes
        self.label_ingreso = ctk.CTkLabel(self.panel_ingreso, text="", 
                                          text_color="red", 
                                          font=("Inter", 13, "bold"))
        self.label_ingreso.pack(pady=5)
        
        # Tabla de movimientos recientes
        self.setup_recent_table(self.panel_ingreso, 'ingreso')

    # ============================================================================
    # CONFIGURACIÓN DEL PANEL DE ASIGNACIÓN/RETOMA
    # ============================================================================
    def setup_asignacion_panel(self):
        """Configura el panel de asignar o retornar yubikeys"""
        ctk.CTkLabel(self.panel_asignacion, text="Assign / Return", 
                    font=("Inter", 22, "bold")).pack(pady=30)
        
        self.entry_asignacion = ctk.CTkEntry(self.panel_asignacion, 
                                             placeholder_text="Scan to Assign/Return", 
                                             width=300, height=40, 
                                             font=("Inter", 16), 
                                             border_width=3, 
                                             border_color=BORDER_DEFAULT, 
                                             corner_radius=15)
        self.entry_asignacion.pack(pady=10)
        
        self.entry_asignacion.bind("<Return>", lambda e: self.process_session_scan('asignacion_retoma'))
        
        self.label_asignacion = ctk.CTkLabel(self.panel_asignacion, text="", 
                                             text_color="red", 
                                             font=("Inter", 13, "bold"))
        self.label_asignacion.pack(pady=5)
        
        self.setup_recent_table(self.panel_asignacion, 'asignacion')

    # ============================================================================
    # CONFIGURACIÓN DEL PANEL DE PÉRDIDA/DAÑO
    # ============================================================================
    def setup_perdida_panel(self):
        """Configura el panel para reportar pérdidas o daños"""
        ctk.CTkLabel(self.panel_perdida, text="Loss / Damage Report", 
                    font=("Inter", 22, "bold")).pack(pady=30)
        
        # Instrucción: permite buscar por serial O por código Pipkins
        ctk.CTkLabel(self.panel_perdida, text="Scan serial or enter Pipkins code", 
                    font=("Inter", 13), text_color="#94a3b8").pack(pady=(0, 20))
        
        self.entry_perdida = ctk.CTkEntry(self.panel_perdida, 
                                          placeholder_text="Scan serial or enter Pipkins code", 
                                          width=300, height=40, 
                                          font=("Inter", 16), 
                                          border_width=3, 
                                          border_color=BORDER_DEFAULT, 
                                          corner_radius=15)
        self.entry_perdida.pack(pady=10)
        
        self.entry_perdida.bind("<Return>", lambda e: self.process_session_scan('perdida_dano'))
        
        self.label_perdida = ctk.CTkLabel(self.panel_perdida, text="", 
                                          text_color="red", 
                                          font=("Inter", 13, "bold"))
        self.label_perdida.pack(pady=5)
        
        self.setup_recent_table(self.panel_perdida, 'perdida')

    # ============================================================================
    # CONFIGURACIÓN DE TABLAS DE MOVIMIENTOS RECIENTES
    # ============================================================================
    def setup_recent_table(self, parent, tipo):
        """
        Crea una tabla para mostrar los últimos 5 movimientos
        
        Parámetros:
        - parent: El panel donde se colocará la tabla
        - tipo: El tipo de movimientos a mostrar ('nueva', 'ingreso', 'asignacion', 'perdida')
        """
        # Frame contenedor de la tabla
        frame = ctk.CTkFrame(parent, fg_color=SLATE_GRAY, corner_radius=12)
        frame.pack(pady=18, padx=10, fill='x')
        
        # Título de la tabla
        ctk.CTkLabel(frame, text="Recent movements", 
                    font=("Inter", 15, "bold"), 
                    text_color="#38bdf8").pack(anchor='w', padx=10, pady=(8, 0))
        
        # Columnas de la tabla
        columns = ("Serial", "Pipkins Code", "Action", "Date", "Time")
        
        # Configura el estilo de la tabla
        style = ttk.Style()
        style.theme_use('clam')  # Usa el tema 'clam' para mejor apariencia
        
        # Configura estilo del cuerpo de la tabla
        style.configure(f'{tipo}.Treeview', 
                       font=('Segoe UI', 11), 
                       rowheight=28, 
                       background=SLATE_GRAY, 
                       fieldbackground=SLATE_GRAY, 
                       foreground="#e0e7ef", 
                       borderwidth=0)
        
        # Configura estilo de los encabezados
        style.configure(f'{tipo}.Treeview.Heading', 
                       font=('Segoe UI', 12, 'bold'), 
                       background="#334155", 
                       foreground="#38bdf8")
        
        # Crea la tabla (Treeview)
        tree = ttk.Treeview(frame, columns=columns, show='headings', 
                           height=5, style=f'{tipo}.Treeview')
        
        # Configura cada columna
        for col in columns:
            tree.heading(col, text=col)  # Encabezado
            tree.column(col, anchor='center', width=120)  # Alineación y ancho
        
        tree.pack(side='left', fill='x', expand=True, padx=10, pady=10)
        
        # Guarda la referencia a la tabla como atributo de la clase
        setattr(self, f"tree_recent_{tipo}", tree)
        
        # Carga los datos en la tabla
        self.load_recent_data(tipo)

    def load_recent_data(self, tipo):
        """
        Carga los datos en la tabla de movimientos recientes
        
        Parámetros:
        - tipo: El tipo de movimientos a cargar
        """
        tree = getattr(self, f"tree_recent_{tipo}", None)  # Obtiene la tabla
        if not tree: return  # Si no existe, sale
        
        tree.delete(*tree.get_children())  # Limpia la tabla
        movimientos = self.get_recent_movements(tipo)  # Obtiene los datos
        
        for mov in movimientos:
            tree.insert('', 'end', values=mov)  # Inserta cada movimiento

    def get_recent_movements(self, tipo):
        """
        Obtiene los últimos 5 movimientos del tipo especificado desde el JSON
        
        Parámetros:
        - tipo: 'nueva', 'ingreso', 'asignacion', o 'perdida'
        
        Retorna:
        - Lista de tuplas con los movimientos
        """
        if not os.path.isfile(JSON_FILE): return []
        
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        movs = []
        for item in datos:
            codigo = item.get('codigo_pipkins', '-')
            
            # Recorre el historial de cada yubikey
            for h in item.get('historial', []):
                # Filtra según el tipo de panel
                if tipo == 'nueva' and h['accion'] == 'Registro':
                    movs.append((item['serial'], codigo, h['accion'], h['fecha'], h['hora']))
                elif tipo == 'ingreso' and ('Break' in h['accion'] or 'Lunch' in h['accion']):
                    movs.append((item['serial'], codigo, h['accion'], h['fecha'], h['hora']))
                elif tipo == 'asignacion' and ('Assign' in h['accion'] or 'Return' in h['accion']):
                    movs.append((item['serial'], codigo, h['accion'], h['fecha'], h['hora']))
                elif tipo == 'perdida' and h['accion'] in ['Loss', 'Damage']:
                    movs.append((item['serial'], codigo, h['accion'], h['fecha'], h['hora']))
        
        # Ordena por fecha y hora (más reciente primero) y toma solo los primeros 5
        return sorted(movs, key=lambda x: (x[3], x[4]), reverse=True)[:5]

    # ============================================================================
    # MÉTODOS DE BÚSQUEDA Y VALIDACIÓN
    # ============================================================================
    def serial_exists(self, serial):
        """
        Verifica si un serial ya existe en la base de datos
        
        Parámetros:
        - serial: El serial a buscar
        
        Retorna:
        - True si existe, False si no
        """
        if not os.path.isfile(JSON_FILE):
            return False
        
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        # Busca en todos los items si algún serial coincide (ignorando mayúsculas/minúsculas)
        return any(item['serial'].upper() == serial.upper() for item in datos)

    def find_by_pipkins(self, pipkins_code):
        """
        Busca una yubikey por su código Pipkins
        
        Parámetros:
        - pipkins_code: El código Pipkins a buscar
        
        Retorna:
        - El item completo si lo encuentra, None si no
        """
        if not os.path.isfile(JSON_FILE):
            return None
        
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        for item in datos:
            if item.get('codigo_pipkins', '').upper() == pipkins_code.upper():
                return item
        
        return None

    # ============================================================================
    # MODALES (VENTANAS EMERGENTES)
    # ============================================================================
    def ask_user_and_pipkins(self):
        """
        Muestra un modal para ingresar manualmente los datos de una yubikey nueva
        
        Retorna:
        - Tupla con (serial, usuario, codigo_pipkins) o (None, None, None) si cancela
        """
        modal = ctk.CTkToplevel(self)  # Crea ventana emergente
        modal.title("Manual Yubikey Registration")
        modal.geometry("420x370")
        modal.grab_set()  # Hace que el modal sea modal (bloquea la ventana principal)
        
        frame = ctk.CTkFrame(modal, fg_color="#1e293b", corner_radius=18)
        frame.pack(padx=24, pady=24, fill="both", expand=True)
        
        # Título del modal
        ctk.CTkLabel(frame, text="Manual Registration", 
                    font=("Inter", 24, "bold"), 
                    text_color="#38bdf8").pack(pady=(10, 18))
        
        # Campo: Serial
        ctk.CTkLabel(frame, text="Yubikey Serial:", 
                    font=("Inter", 16)).pack(anchor='w', padx=10, pady=(4, 0))
        serial_var = ctk.StringVar()
        serial_entry = ctk.CTkEntry(frame, textvariable=serial_var, 
                                   width=260, font=("Inter", 15), corner_radius=10)
        serial_entry.pack(pady=(0, 10))
        serial_entry.focus_set()  # Pone el cursor en este campo
        
        # Campo: Usuario
        ctk.CTkLabel(frame, text="User:", 
                    font=("Inter", 16)).pack(anchor='w', padx=10, pady=(4, 0))
        usuario_var = ctk.StringVar()
        usuario_entry = ctk.CTkEntry(frame, textvariable=usuario_var, 
                                    width=260, font=("Inter", 15), corner_radius=10)
        usuario_entry.pack(pady=(0, 10))
        
        # Campo: Código Pipkins
        ctk.CTkLabel(frame, text="Pipkins Code:", 
                    font=("Inter", 16)).pack(anchor='w', padx=10, pady=(4, 0))
        pipkins_var = ctk.StringVar()
        pipkins_entry = ctk.CTkEntry(frame, textvariable=pipkins_var, 
                                    width=260, font=("Inter", 15), corner_radius=10)
        pipkins_entry.pack(pady=(0, 10))
        
        # Label para mensajes de error
        error_label = ctk.CTkLabel(frame, text="", 
                                  text_color="#ef4444", 
                                  font=("Inter", 13, "bold"))
        error_label.pack(pady=(0, 2))
        
        # Diccionario para guardar el resultado
        result = {'ok': False, 'serial': '', 'usuario': '', 'pipkins': ''}
        
        # Función interna que se ejecuta al presionar el botón
        def registrar():
            serial = serial_var.get().strip()
            usuario = usuario_var.get().strip()
            pipkins = pipkins_var.get().strip()
            
            # Valida que todos los campos estén llenos
            if not serial or not usuario or not pipkins:
                error_label.configure(text="All fields are required")
                return
            
            result['ok'] = True
            result['serial'] = serial
            result['usuario'] = usuario
            result['pipkins'] = pipkins
            modal.destroy()  # Cierra el modal
        
        # Botón para confirmar
        ctk.CTkButton(frame, text="Register", command=registrar, 
                     fg_color="#38bdf8", hover_color="#0ea5e9", 
                     font=("Inter", 17, "bold"), corner_radius=12).pack(pady=16)
        
        modal.wait_window()  # Espera a que el modal se cierre
        
        if result['ok']:
            return result['serial'], result['usuario'], result['pipkins']
        return None, None, None

    def ask_break_type(self):
        """
        Muestra un modal para seleccionar si es Break o Lunch
        
        Retorna:
        - "Break" o "Lunch" según la selección, None si cancela
        """
        modal = ctk.CTkToplevel(self)
        modal.title("Select Break/Lunch Type")
        modal.geometry("340x200")
        modal.grab_set()
        
        ctk.CTkLabel(modal, text="Check-in or check-out from?", 
                    font=("Inter", 17, "bold"), 
                    text_color="#38bdf8").pack(pady=(18, 18))
        
        tipo_var = ctk.StringVar(value="Break")  # Valor por defecto
        opciones = ["Break", "Lunch"]
        
        # Crea los radio buttons
        for op in opciones:
            ctk.CTkRadioButton(modal, text=op, variable=tipo_var, value=op, 
                             font=("Inter", 15)).pack(anchor='w', padx=40, pady=8)
        
        result = {'ok': False}
        
        def aceptar():
            result['ok'] = True
            modal.destroy()
        
        ctk.CTkButton(modal, text="Continue", command=aceptar, 
                     fg_color="#38bdf8", hover_color="#0ea5e9", 
                     font=("Inter", 15, "bold"), width=150, 
                     corner_radius=10).pack(pady=18)
        
        modal.wait_window()
        
        if result['ok']:
            return tipo_var.get()
        return None

    def ask_asignacion_retoma_type(self):
        """
        Muestra un modal para seleccionar si es Asignación o Retoma
        
        Retorna:
        - "Assign" o "Return" según la selección, None si cancela
        """
        modal = ctk.CTkToplevel(self)
        modal.title("Select Action Type")
        modal.geometry("500x350")
        modal.grab_set()
        
        ctk.CTkLabel(modal, text="What action will you perform?", 
                    font=("Inter", 18, "bold"), 
                    text_color="#38bdf8").pack(pady=(20, 15))
        
        # Instrucciones para cada opción
        ctk.CTkLabel(modal, text="• Assign: Give AVAILABLE yubikey to new user", 
                    font=("Inter", 13), text_color="#94a3b8", 
                    justify="left").pack(pady=8, padx=30, anchor="w")
        ctk.CTkLabel(modal, text="• Return: User RETURNS yubikey (no longer works here)", 
                    font=("Inter", 13), text_color="#94a3b8", 
                    justify="left").pack(pady=8, padx=30, anchor="w")
        
        tipo_var = ctk.StringVar(value="Assign")
        opciones = ["Assign", "Return"]
        
        for op in opciones:
            ctk.CTkRadioButton(modal, text=op, variable=tipo_var, value=op, 
                             font=("Inter", 15, "bold")).pack(anchor='w', padx=50, pady=15)
        
        result = {'ok': False}
        
        def aceptar():
            result['ok'] = True
            modal.destroy()
        
        ctk.CTkButton(modal, text="Continue", command=aceptar, 
                     fg_color="#38bdf8", hover_color="#0ea5e9", 
                     font=("Inter", 15, "bold"), width=200, 
                     corner_radius=12).pack(pady=25)
        
        modal.wait_window()
        
        if result['ok']:
            return tipo_var.get()
        return None

    def ask_nuevo_usuario_pipkins(self):
        """
        Muestra un modal para ingresar los datos del nuevo usuario al asignar
        
        Retorna:
        - Tupla con (usuario, codigo_pipkins) o (None, None) si cancela
        """
        modal = ctk.CTkToplevel(self)
        modal.title("New User Details")
        modal.geometry("420x320")
        modal.grab_set()
        
        frame = ctk.CTkFrame(modal, fg_color="#1e293b", corner_radius=18)
        frame.pack(padx=24, pady=24, fill="both", expand=True)
        
        ctk.CTkLabel(frame, text="Assign to new user", 
                    font=("Inter", 20, "bold"), 
                    text_color="#38bdf8").pack(pady=(10, 18))
        
        # Campo: Usuario
        ctk.CTkLabel(frame, text="User name:", 
                    font=("Inter", 15)).pack(anchor='w', padx=10, pady=(4, 0))
        usuario_var = ctk.StringVar()
        usuario_entry = ctk.CTkEntry(frame, textvariable=usuario_var, 
                                    width=260, font=("Inter", 14), corner_radius=10)
        usuario_entry.pack(pady=(0, 10))
        usuario_entry.focus_set()
        
        # Campo: Código Pipkins
        ctk.CTkLabel(frame, text="Pipkins Code:", 
                    font=("Inter", 15)).pack(anchor='w', padx=10, pady=(4, 0))
        pipkins_var = ctk.StringVar()
        pipkins_entry = ctk.CTkEntry(frame, textvariable=pipkins_var, 
                                    width=260, font=("Inter", 14), corner_radius=10)
        pipkins_entry.pack(pady=(0, 10))
        
        error_label = ctk.CTkLabel(frame, text="", 
                                  text_color="#ef4444", 
                                  font=("Inter", 13, "bold"))
        error_label.pack(pady=(0, 2))
        
        result = {'ok': False, 'usuario': '', 'pipkins': ''}
        
        def aceptar():
            usuario = usuario_var.get().strip()
            pipkins = pipkins_var.get().strip()
            
            if not usuario or not pipkins:
                error_label.configure(text="All fields are required")
                return
            
            result['ok'] = True
            result['usuario'] = usuario
            result['pipkins'] = pipkins
            modal.destroy()
        
        ctk.CTkButton(frame, text="Assign", command=aceptar, 
                     fg_color="#38bdf8", hover_color="#0ea5e9", 
                     font=("Inter", 16, "bold"), 
                     corner_radius=12).pack(pady=16)
        
        modal.wait_window()
        
        if result['ok']:
            return result['usuario'], result['pipkins']
        return None, None

    def ask_comentario(self, titulo, mensaje):
        """
        Muestra un modal para ingresar un comentario (para Retoma, Pérdida o Daño)
        
        Parámetros:
        - titulo: Título del modal
        - mensaje: Mensaje a mostrar
        
        Retorna:
        - El comentario ingresado o string vacío si omite
        """
        modal = ctk.CTkToplevel(self)
        modal.title(titulo)
        modal.geometry("500x350")
        modal.grab_set()
        
        frame = ctk.CTkFrame(modal, fg_color="#1e293b", corner_radius=18)
        frame.pack(padx=24, pady=24, fill="both", expand=True)
        
        ctk.CTkLabel(frame, text=mensaje, 
                    font=("Inter", 16, "bold"), 
                    text_color="#38bdf8", 
                    wraplength=420).pack(pady=(10, 10))
        
        # Área de texto para el comentario
        comentario_text = ctk.CTkTextbox(frame, width=430, height=150, 
                                        font=("Inter", 13))
        comentario_text.pack(pady=10, padx=10)
        comentario_text.focus_set()
        
        result = {'ok': False, 'comentario': ''}
        
        def aceptar():
            comentario = comentario_text.get("1.0", "end-1c").strip()
            result['ok'] = True
            result['comentario'] = comentario
            modal.destroy()
        
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        # Botón Submit
        ctk.CTkButton(btn_frame, text="Submit", command=aceptar, 
                     fg_color="#38bdf8", hover_color="#0ea5e9", 
                     font=("Inter", 15, "bold"), 
                     corner_radius=12, width=120).pack(side="left", padx=10)
        
        # Botón Skip (omitir)
        ctk.CTkButton(btn_frame, text="Skip", command=modal.destroy, 
                     fg_color="#475569", hover_color="#64748b", 
                     font=("Inter", 15), 
                     corner_radius=12, width=100).pack(side="left", padx=10)
        
        modal.wait_window()
        
        return result['comentario'] if result['ok'] else ""

    # ============================================================================
    # REGISTRO DE NUEVA YUBIKEY
    # ============================================================================
    def registrar_nueva_yubikey(self, event=None):
        """
        Registra una nueva yubikey en el sistema
        
        Flujo:
        1. Lee el serial del campo de texto
        2. Valida que no esté vacío
        3. Valida que no exista ya
        4. Muestra modal para pedir usuario y código Pipkins
        5. Crea el registro en JSON
        6. Actualiza tablas
        """
        # Obtiene el serial del campo de texto y lo convierte a mayúsculas
        serial = self.entry_nueva.get().strip().upper()
        
        # Valida que no esté vacío
        if not serial:
            self.label_nueva.configure(text="Empty field!", text_color="red")
            self.entry_nueva.configure(border_color="red")
            self.after(2000, lambda: self.entry_nueva.configure(border_color=BORDER_DEFAULT))
            return

        # Valida que no exista ya
        if self.serial_exists(serial):
            self.label_nueva.configure(text="⚠️ Serial already registered", text_color="orange")
            self.entry_nueva.configure(border_color="orange")
            self.after(3000, lambda: self.entry_nueva.configure(border_color=BORDER_DEFAULT))
            self.entry_nueva.delete(0, 'end')
            return

        # Muestra modal para pedir usuario y código Pipkins
        serial_modal, nombre, codigo = self.ask_user_and_pipkins()
        
        if nombre and codigo:
            now = datetime.now()
            
            # Crea el nuevo registro
            nueva = {
                "serial": serial,
                "usuario": nombre,
                "codigo_pipkins": codigo,
                "estado": "In Use",  # Estado inicial: En Uso
                "ultima_conexion": now.strftime("%Y-%m-%d"),
                "historial": [{
                    "accion": "Registro",
                    "fecha": now.strftime("%Y-%m-%d"),
                    "hora": now.strftime("%H:%M:%S"),
                    "usuario": nombre,
                    "codigo_pipkins": codigo,
                    "estado": "In Use",
                    "comentario": "Initial registration"
                }]
            }
            
            # Lee el JSON actual
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                datos = json.load(f)
            
            # Agrega el nuevo registro
            datos.append(nueva)
            
            # Guarda el JSON actualizado
            with open(JSON_FILE, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
            
            # Muestra mensaje de éxito
            self.label_nueva.configure(text="Registered and IN USE!", text_color=SUCCESS_GREEN)
            self.entry_nueva.delete(0, 'end')
            
            # Actualiza tablas
            self.load_recent_data('nueva')
            self.load_inventory_table()
            
            # Limpia el mensaje después de 3 segundos
            self.after(3000, lambda: self.label_nueva.configure(text=""))

    # ============================================================================
    # PROCESAMIENTO PRINCIPAL DE ESCANEOS
    # ============================================================================
    def process_session_scan(self, session):
        """
        Método principal que procesa todos los escaneos
        
        Parámetros:
        - session: Tipo de sesión ('ingreso_salida', 'asignacion_retoma', 'perdida_dano')
        
        Este método maneja:
        - Break/Lunch Check-in/out
        - Assign/Return
        - Loss/Damage Report
        """
        # ========================================================================
        # CONFIGURACIÓN INICIAL SEGÚN EL TIPO DE SESIÓN
        # ========================================================================
        if session == 'ingreso_salida':
            entry = self.entry_ingreso
            label = self.label_ingreso
            tipo_tree = 'ingreso'
            tipo_break = self.ask_break_type()  # Pregunta si es Break o Lunch
            
            if tipo_break is None:
                label.configure(text="Action cancelled", text_color="orange")
                return
                
        elif session == 'asignacion_retoma':
            entry = self.entry_asignacion
            label = self.label_asignacion
            tipo_tree = 'asignacion'
            tipo_accion = self.ask_asignacion_retoma_type()  # Pregunta si es Assign o Return
            
            if tipo_accion is None:
                label.configure(text="Action cancelled", text_color="orange")
                return
                
        else:  # perdida_dano
            entry = self.entry_perdida
            label = self.label_perdida
            tipo_tree = 'perdida'
            tipo_accion = None
            
        # ========================================================================
        # OBTENER SERIAL O CÓDIGO PIPKINS DEL CAMPO DE TEXTO
        # ========================================================================
        serial_or_pipkins = entry.get().strip()
        
        # Valida que no esté vacío
        if not serial_or_pipkins:
            label.configure(text="Empty field!")
            entry.configure(border_color="red")
            self.after(2000, lambda: entry.configure(border_color=BORDER_DEFAULT))
            return
            
        # ========================================================================
        # BUSCAR LA YUBIKEY EN LA BASE DE DATOS
        # ========================================================================
        item_data = None
        found_by_pipkins = False
        
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        # Primero busca por serial
        for item in datos:
            if item['serial'].strip().upper() == serial_or_pipkins.upper():
                item_data = item
                break
        
        # Si no encuentra por serial, busca por código Pipkins
        if not item_data:
            item_data = self.find_by_pipkins(serial_or_pipkins)
            
            if item_data:
                found_by_pipkins = True
                serial = item_data['serial']
            else:
                label.configure(text="❌ Serial or Pipkins code not found", text_color="red")
                entry.configure(border_color="red")
                self.after(3000, lambda: entry.configure(border_color=BORDER_DEFAULT))
                entry.delete(0, 'end')
                entry.focus_set()
                return
        else:
            serial = item_data['serial']
            
        label.configure(text="")
        
        # ========================================================================
        # PREPARAR VARIABLES PARA EL PROCESAMIENTO
        # ========================================================================
        now = datetime.now()
        fecha = now.strftime('%Y-%m-%d')
        hora = now.strftime('%H:%M:%S')
        accion = ''
        cambio = False
        found = False
        comentario = ""
        
        # ========================================================================
        # PROCESAR SEGÚN EL TIPO DE SESIÓN
        # ========================================================================
        for item in datos:
            if item['serial'].strip().upper() == serial.upper():
                found = True
                
                # --------------------------------------------------------------
                # BREAK/LUNCH CHECK-IN/OUT
                # --------------------------------------------------------------
                if session == 'ingreso_salida':
                    estado_actual = item['estado']
                    estado_seleccionado = f'On {tipo_break}'
                    
                    if estado_actual == 'In Use':
                        # Check-in: De "In Use" a "On Break" o "On Lunch"
                        item['estado'] = estado_seleccionado
                        accion = f'Check-in to {tipo_break}'
                        item['ultima_conexion'] = fecha
                        cambio = True
                        
                    elif estado_actual == estado_seleccionado:
                        # Check-out: De "On Break/Lunch" a "In Use"
                        item['estado'] = 'In Use'
                        accion = f'Check-out from {tipo_break}'
                        item['ultima_conexion'] = fecha
                        cambio = True
                        
                    elif estado_actual in ['On Break', 'On Lunch'] and estado_actual != estado_seleccionado:
                        # Error: Está en el otro tipo de break
                        otro = estado_actual.replace('On ', '')
                        accion = f"⚠️ Must check-out from {otro} first"
                        break
                        
                    else:
                        accion = f"❌ Not applicable: state '{estado_actual}'"
                        break
                        
                # --------------------------------------------------------------
                # ASIGNACIÓN/RETOMA
                # --------------------------------------------------------------
                elif session == 'asignacion_retoma':
                    estado_actual = item['estado']
                    
                    if tipo_accion == 'Return':
                        # RETORNO: El usuario devuelve la yubikey
                        if estado_actual in ['In Use', 'On Break', 'On Lunch']:
                            usuario_anterior = item['usuario']
                            pipkins_anterior = item.get('codigo_pipkins', 'N/A')
                            
                            # Pide comentario opcional
                            comentario = self.ask_comentario(
                                "Yubikey Return",
                                f"User '{usuario_anterior}' returns yubikey (no longer works here)\nOptional comment:"
                            )
                            
                            # Limpia los datos y cambia a Available
                            item['estado'] = 'Available'
                            item['usuario'] = ''
                            item['codigo_pipkins'] = ''
                            accion = f'Return (previous: {usuario_anterior})'
                            item['ultima_conexion'] = fecha
                            cambio = True
                            
                        elif estado_actual == 'Available':
                            accion = "❌ Cannot return: already AVAILABLE"
                            break
                            
                        elif estado_actual in ['Loss', 'Damage']:
                            accion = f"❌ Cannot return: state is '{estado_actual}'"
                            break
                            
                        else:
                            accion = f"❌ Invalid state for return: '{estado_actual}'"
                            break
                            
                    elif tipo_accion == 'Assign':
                        # ASIGNACIÓN: Dar yubikey a nuevo usuario
                        if estado_actual == 'Available':
                            nuevo_usuario, nuevo_pipkins = self.ask_nuevo_usuario_pipkins()
                            
                            if nuevo_usuario and nuevo_pipkins:
                                item['estado'] = 'In Use'
                                item['usuario'] = nuevo_usuario
                                item['codigo_pipkins'] = nuevo_pipkins
                                accion = f'Assign to {nuevo_usuario}'
                                item['ultima_conexion'] = fecha
                                cambio = True
                            else:
                                accion = "Assignment cancelled"
                                break
                                
                        elif estado_actual in ['In Use', 'On Break', 'On Lunch']:
                            accion = f"❌ Already ASSIGNED to '{item['usuario']}'. Must RETURN first."
                            break
                            
                        elif estado_actual in ['Loss', 'Damage']:
                            accion = f"❌ Cannot assign: state is '{estado_actual}'"
                            break
                            
                        else:
                            accion = f"❌ Invalid state for assignment: '{estado_actual}'"
                            break
                            
                # --------------------------------------------------------------
                # PÉRDIDA/DAÑO
                # --------------------------------------------------------------
                elif session == 'perdida_dano':
                    estado_actual = item['estado']
                    
                    if estado_actual in ['Loss', 'Damage']:
                        accion = f"❌ Already in state '{estado_actual}'"
                        break
                    
                    # Pregunta si es Loss o Damage
                    modal = ctk.CTkToplevel(self)
                    modal.title("Select Incident Type")
                    modal.geometry("400x250")
                    modal.grab_set()
                    
                    ctk.CTkLabel(modal, text="What type of incident is this?", 
                                font=("Inter", 17, "bold"), 
                                text_color="#38bdf8").pack(pady=(18, 18))
                    
                    tipo_var = ctk.StringVar(value="Loss")
                    opciones = ["Loss", "Damage"]
                    
                    for op in opciones:
                        ctk.CTkRadioButton(modal, text=op, variable=tipo_var, value=op, 
                                         font=("Inter", 15)).pack(anchor='w', padx=40, pady=8)
                    
                    result_modal = {'ok': False}
                    
                    def aceptar_modal():
                        result_modal['ok'] = True
                        modal.destroy()
                    
                    ctk.CTkButton(modal, text="Continue", command=aceptar_modal, 
                                 fg_color="#38bdf8", hover_color="#0ea5e9", 
                                 font=("Inter", 15, "bold"),
                                 width=150, corner_radius=10).pack(pady=18)
                    
                    modal.wait_window()
                    
                    if not result_modal['ok']:
                        accion = "Action cancelled"
                        break
                    
                    tipo_incidente = tipo_var.get()
                    
                    # Indica cómo se encontró la yubikey
                    search_method = "via Pipkins code" if found_by_pipkins else "via serial scanner"
                    
                    # Pide comentario detallado
                    comentario = self.ask_comentario(
                        f"Report {tipo_incidente}",
                        f"Reporting {tipo_incidente.lower()} ({search_method})\nSerial: {item['serial']}\nUser: {item.get('usuario', 'N/A')}\nPipkins: {item.get('codigo_pipkins', 'N/A')}\n\nDescribe what happened:"
                    )
                    
                    item['estado'] = tipo_incidente
                    accion = tipo_incidente
                    item['ultima_conexion'] = fecha
                    cambio = True
                        
                # ========================================================================
                # AGREGAR AL HISTORIAL
                # ========================================================================
                if 'historial' not in item:
                    item['historial'] = []
                
                item['historial'].append({
                    'fecha': fecha,
                    'hora': hora,
                    'accion': accion,
                    'estado': item['estado'],
                    'usuario': item['usuario'],
                    'codigo_pipkins': item.get('codigo_pipkins', ''),
                    'comentario': comentario
                })
                break
        
        if not found:
            accion = "Serial not found"
            
        # ========================================================================
        # GUARDAR CAMBIOS EN EL JSON
        # ========================================================================
        if cambio:
            with open(JSON_FILE, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
            
            entry.configure(border_color=SUCCESS_GREEN)
            label.configure(text=f"✓ {accion}", text_color=SUCCESS_GREEN)
            self.after(500, lambda: entry.configure(border_color=BORDER_DEFAULT))
            entry.delete(0, 'end')
            
            self.load_inventory_table(refresh=True)
            self.load_recent_data(tipo_tree)
            self.after(3000, lambda: label.configure(text=""))
        else:
            entry.configure(border_color="orange")
            label.configure(text=accion, text_color="orange")
            self.after(1000, lambda: entry.configure(border_color=BORDER_DEFAULT))
        
        entry.focus_set()

    # ============================================================================
    # CONFIGURACIÓN DE LA VISTA DE INVENTARIO
    # ============================================================================
    def setup_inv_view(self):
        """Configura la vista de inventario con tabla, filtros y búsqueda"""
        # Título
        ctk.CTkLabel(self.view_inv, text="General Inventory", 
                    font=("Inter", 32, "bold"), 
                    text_color="#38bdf8").pack(pady=15)
        
        # Frame de filtros
        filter_frame = ctk.CTkFrame(self.view_inv, fg_color=SLATE_GRAY, corner_radius=12)
        filter_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(filter_frame, text="Filter by state:", 
                    font=("Inter", 14, "bold")).pack(side="left", padx=15, pady=10)
        
        # Variable para el filtro seleccionado
        self.filter_var = ctk.StringVar(value="All")
        
        # Estados disponibles para filtrar
        estados = ["All", "Available", "In Use", "On Break", "On Lunch", "Loss", "Damage"]
        
        # Crea radio buttons para cada estado
        for estado in estados:
            ctk.CTkRadioButton(filter_frame, text=estado, 
                             variable=self.filter_var, 
                             value=estado,
                             command=self.filter_inventory, 
                             font=("Inter", 13)).pack(side="left", padx=8, pady=10)
        
        # Frame de búsqueda
        search_frame = ctk.CTkFrame(self.view_inv, fg_color="transparent")
        search_frame.pack(pady=5)
        
        self.search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(search_frame, 
                                   textvariable=self.search_var, 
                                   placeholder_text="Search by serial or user...", 
                                   width=300)
        search_entry.pack(side="left", padx=10)
        
        # Al escribir, filtra automáticamente
        search_entry.bind("<KeyRelease>", lambda e: self.filter_inventory())
        
        # Botón para ver detalles
        ctk.CTkButton(search_frame, text="📋 View Details", 
                     command=self.show_item_details,
                     fg_color="#38bdf8", hover_color="#0ea5e9", 
                     font=("Inter", 13, "bold")).pack(side="left", padx=10)

        # Frame de la tabla
        table_frame = ctk.CTkFrame(self.view_inv, fg_color=SLATE_GRAY, corner_radius=15)
        table_frame.pack(expand=True, fill="both", padx=20, pady=10)

        # Columnas de la tabla
        cols = ("Serial", "User", "Pipkins", "State", "Last Connection")
        
        # Crea la tabla
        self.inv_tree = ttk.Treeview(table_frame, columns=cols, 
                                    show='headings', style='Custom.Treeview')
        
        # Configura el estilo
        style = ttk.Style()
        style.configure('Custom.Treeview', 
                       font=('Segoe UI', 12), 
                       rowheight=35, 
                       background=SLATE_GRAY, 
                       fieldbackground=SLATE_GRAY, 
                       foreground="white")
        style.configure('Custom.Treeview.Heading', 
                       font=('Segoe UI', 13, 'bold'))
        
        # Configura colores por estado
        for estado, color in ESTADO_COLORES.items():
            self.inv_tree.tag_configure(estado, background=color, foreground="white")
        
        # Configura columnas
        for col in cols:
            self.inv_tree.heading(col, text=col)
            self.inv_tree.column(col, anchor='center', width=150)
        
        self.inv_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Doble click para ver detalles
        self.inv_tree.bind("<Double-1>", lambda e: self.show_item_details())
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.inv_tree, orient="vertical", 
                                 command=self.inv_tree.yview)
        self.inv_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

    def load_inventory_table(self, refresh=False):
        """Carga todos los datos del inventario en la tabla"""
        if not hasattr(self, 'inv_tree'):
            return
        
        self.inv_tree.delete(*self.inv_tree.get_children())
        
        if not os.path.isfile(JSON_FILE):
            return
        
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        for item in datos:
            estado = item['estado']
            values = (
                item['serial'],
                item.get('usuario', '-') or '-',
                item.get('codigo_pipkins', '-') or '-',
                estado,
                item.get('ultima_conexion', '-')
            )
            self.inv_tree.insert('', 'end', values=values, tags=(estado,))

    def filter_inventory(self):
        """Filtra el inventario por estado y/o búsqueda de texto"""
        filter_estado = self.filter_var.get()
        search_term = self.search_var.get().lower()
        
        self.inv_tree.delete(*self.inv_tree.get_children())
        
        if not os.path.isfile(JSON_FILE):
            return
        
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        for item in datos:
            estado = item['estado']
            
            # Filtra por estado
            if filter_estado != "All" and estado != filter_estado:
                continue
            
            # Filtra por búsqueda de texto
            if search_term and (search_term not in item['serial'].lower() and 
                               search_term not in item.get('usuario', '').lower()):
                continue
            
            values = (
                item['serial'],
                item.get('usuario', '-') or '-',
                item.get('codigo_pipkins', '-') or '-',
                estado,
                item.get('ultima_conexion', '-')
            )
            self.inv_tree.insert('', 'end', values=values, tags=(estado,))

    def show_item_details(self):
        """Muestra los detalles completos de una yubikey seleccionada"""
        selected = self.inv_tree.selection()
        
        if not selected:
            modal = ctk.CTkToplevel(self)
            modal.title("History Details")
            modal.geometry("400x200")
            modal.grab_set()
            
            ctk.CTkLabel(modal, text="⚠️ Select a yubikey first", 
                        font=("Inter", 16, "bold"), 
                        text_color="orange").pack(pady=40)
            
            ctk.CTkButton(modal, text="Close", command=modal.destroy, 
                         fg_color="#475569").pack(pady=10)
            return
        
        item = self.inv_tree.item(selected[0])
        serial = item['values'][0]
        
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        yubi_data = None
        for yubi in datos:
            if yubi['serial'] == serial:
                yubi_data = yubi
                break
        
        if not yubi_data:
            return
        
        # Crea el modal de detalles
        modal = ctk.CTkToplevel(self)
        modal.title(f"Details - {serial}")
        modal.geometry("700x550")
        modal.grab_set()
        
        main_frame = ctk.CTkFrame(modal, fg_color="#1e293b", corner_radius=18)
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Header con información actual
        header = ctk.CTkFrame(main_frame, fg_color="#334155", corner_radius=12)
        header.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(header, text=f"Serial: {serial}", 
                    font=("Inter", 20, "bold"), 
                    text_color="#38bdf8").pack(pady=10)
        
        info_frame = ctk.CTkFrame(header, fg_color="transparent")
        info_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(info_frame, text=f"State: {yubi_data['estado']}", 
                    font=("Inter", 14, "bold"), 
                    text_color=ESTADO_COLORES.get(yubi_data['estado'], "white")).pack(side="left", padx=20)
        
        ctk.CTkLabel(info_frame, text=f"User: {yubi_data.get('usuario', '-') or '-'}", 
                    font=("Inter", 14)).pack(side="left", padx=20)
        
        ctk.CTkLabel(info_frame, text=f"Pipkins: {yubi_data.get('codigo_pipkins', '-') or '-'}", 
                    font=("Inter", 14)).pack(side="left", padx=20)
        
        # Historial completo
        ctk.CTkLabel(main_frame, text="📋 Complete History", 
                    font=("Inter", 16, "bold"), 
                    text_color="#38bdf8").pack(pady=(15, 10), padx=15)
        
        scroll_frame = ctk.CTkScrollableFrame(main_frame, width=640, height=280, 
                                             fg_color="#0f172a", corner_radius=10)
        scroll_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        historial = yubi_data.get('historial', [])
        
        if not historial:
            ctk.CTkLabel(scroll_frame, text="No history registered", 
                        font=("Inter", 13), 
                        text_color="#94a3b8").pack(pady=20)
        else:
            # Muestra el historial en orden inverso (más reciente primero)
            for i, h in enumerate(reversed(historial)):
                item_frame = ctk.CTkFrame(scroll_frame, fg_color="#1e293b", corner_radius=8)
                item_frame.pack(fill="x", pady=8, padx=10)
                
                header_hist = ctk.CTkFrame(item_frame, fg_color="transparent")
                header_hist.pack(fill="x", padx=10, pady=(10, 5))
                
                ctk.CTkLabel(header_hist, text=f"✓ {h['accion']}", 
                            font=("Inter", 13, "bold"), 
                            text_color=ESTADO_COLORES.get(h['estado'], "#38bdf8")).pack(side="left")
                
                ctk.CTkLabel(header_hist, text=f"{h['fecha']} {h['hora']}", 
                            font=("Inter", 11), 
                            text_color="#94a3b8").pack(side="right")
                
                if h.get('usuario'):
                    ctk.CTkLabel(item_frame, text=f"User: {h['usuario']}", 
                                font=("Inter", 12), 
                                text_color="#cbd5e1").pack(anchor="w", padx=10, pady=(0, 3))
                
                if h.get('codigo_pipkins'):
                    ctk.CTkLabel(item_frame, text=f"Pipkins: {h['codigo_pipkins']}", 
                                font=("Inter", 12), 
                                text_color="#cbd5e1").pack(anchor="w", padx=10, pady=(0, 3))
                
                if h.get('comentario'):
                    ctk.CTkLabel(item_frame, text=f"💬 {h['comentario']}", 
                                font=("Inter", 11), 
                                text_color="#fbbf24", 
                                justify="left").pack(anchor="w", padx=10, pady=5)
                
                ctk.CTkLabel(item_frame, text=f"State: {h['estado']}", 
                            font=("Inter", 11), 
                            text_color=ESTADO_COLORES.get(h['estado'], "#94a3b8")).pack(anchor="w", padx=10, pady=(0, 10))
        
        ctk.CTkButton(main_frame, text="Close", command=modal.destroy, 
                     fg_color="#475569", hover_color="#64748b", 
                     font=("Inter", 14, "bold")).pack(pady=15)

    # ============================================================================
    # CONFIGURACIÓN DE REPORTES
    # ============================================================================
    def setup_report_view(self):
        """Configura la vista de reportes con pestañas para Loss, Damage y Summary"""
        ctk.CTkLabel(self.view_report, text="📊 INCIDENT REPORTS", 
                    font=("Inter", 32, "bold"), 
                    text_color="#38bdf8").pack(pady=20)
        
        # Crea el contenedor de pestañas
        self.report_tabs = ctk.CTkTabview(self.view_report, corner_radius=15)
        self.report_tabs.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Agrega las 3 pestañas
        self.tab_loss = self.report_tabs.add("🔴 Loss Report")
        self.tab_damage = self.report_tabs.add("🟣 Damage Report")
        self.tab_summary = self.report_tabs.add("📈 Summary")
        
        # Configura cada pestaña
        self.setup_loss_report_tab()
        self.setup_damage_report_tab()
        self.setup_summary_tab()

    def setup_loss_report_tab(self):
        """Configura la pestaña de reporte de pérdidas"""
        ctk.CTkLabel(self.tab_loss, text="Lost Yubikeys Report", 
                    font=("Inter", 20, "bold"), 
                    text_color="#ef4444").pack(pady=15)
        
        # Frame de estadísticas
        stats_frame = ctk.CTkFrame(self.tab_loss, fg_color=SLATE_GRAY, corner_radius=12)
        stats_frame.pack(fill="x", padx=20, pady=10)
        
        self.loss_count_label = ctk.CTkLabel(stats_frame, text="Total Lost: 0", 
                                            font=("Inter", 16, "bold"), 
                                            text_color="#ef4444")
        self.loss_count_label.pack(pady=10)
        
        # Tabla de pérdidas
        table_frame = ctk.CTkFrame(self.tab_loss, fg_color=SLATE_GRAY, corner_radius=12)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        cols = ("Serial", "User", "Pipkins", "Date", "Reported By")
        self.loss_tree = ttk.Treeview(table_frame, columns=cols, 
                                     show='headings', height=8)
        
        style = ttk.Style()
        style.configure('Loss.Treeview', 
                       font=('Segoe UI', 11), 
                       rowheight=30, 
                       background=SLATE_GRAY, 
                       fieldbackground=SLATE_GRAY, 
                       foreground="white")
        style.configure('Loss.Treeview.Heading', 
                       font=('Segoe UI', 12, 'bold'), 
                       background="#7f1d1d", 
                       foreground="#ef4444")
        
        for col in cols:
            self.loss_tree.heading(col, text=col)
            self.loss_tree.column(col, anchor='center', width=140)
        
        self.loss_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Frame para mostrar el comentario
        comment_frame = ctk.CTkFrame(self.tab_loss, fg_color=SLATE_GRAY, corner_radius=12)
        comment_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(comment_frame, text="📝 Incident Description", 
                    font=("Inter", 14, "bold"), 
                    text_color="#ef4444").pack(anchor="w", padx=10, pady=5)
        
        self.loss_comment_text = ctk.CTkTextbox(comment_frame, height=100, 
                                               font=("Inter", 12))
        self.loss_comment_text.pack(fill="x", padx=10, pady=10)
        self.loss_comment_text.configure(state="disabled")
        
        # Evento al seleccionar un item
        self.loss_tree.bind("<<TreeviewSelect>>", self.on_loss_select)
        
        # Botón para exportar
        ctk.CTkButton(self.tab_loss, text="📥 Export to CSV", 
                     command=self.export_loss_report,
                     fg_color="#ef4444", hover_color="#dc2626", 
                     font=("Inter", 14, "bold")).pack(pady=10)

    def setup_damage_report_tab(self):
        """Configura la pestaña de reporte de daños"""
        ctk.CTkLabel(self.tab_damage, text="Damaged Yubikeys Report", 
                    font=("Inter", 20, "bold"), 
                    text_color="#8b5cf6").pack(pady=15)
        
        stats_frame = ctk.CTkFrame(self.tab_damage, fg_color=SLATE_GRAY, corner_radius=12)
        stats_frame.pack(fill="x", padx=20, pady=10)
        
        self.damage_count_label = ctk.CTkLabel(stats_frame, text="Total Damaged: 0", 
                                              font=("Inter", 16, "bold"), 
                                              text_color="#8b5cf6")
        self.damage_count_label.pack(pady=10)
        
        table_frame = ctk.CTkFrame(self.tab_damage, fg_color=SLATE_GRAY, corner_radius=12)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        cols = ("Serial", "User", "Pipkins", "Date", "Reported By")
        self.damage_tree = ttk.Treeview(table_frame, columns=cols, 
                                       show='headings', height=8)
        
        style = ttk.Style()
        style.configure('Damage.Treeview', 
                       font=('Segoe UI', 11), 
                       rowheight=30, 
                       background=SLATE_GRAY, 
                       fieldbackground=SLATE_GRAY, 
                       foreground="white")
        style.configure('Damage.Treeview.Heading', 
                       font=('Segoe UI', 12, 'bold'), 
                       background="#5b21b6", 
                       foreground="#8b5cf6")
        
        for col in cols:
            self.damage_tree.heading(col, text=col)
            self.damage_tree.column(col, anchor='center', width=140)
        
        self.damage_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        comment_frame = ctk.CTkFrame(self.tab_damage, fg_color=SLATE_GRAY, corner_radius=12)
        comment_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(comment_frame, text="📝 Damage Description", 
                    font=("Inter", 14, "bold"), 
                    text_color="#8b5cf6").pack(anchor="w", padx=10, pady=5)
        
        self.damage_comment_text = ctk.CTkTextbox(comment_frame, height=100, 
                                                 font=("Inter", 12))
        self.damage_comment_text.pack(fill="x", padx=10, pady=10)
        self.damage_comment_text.configure(state="disabled")
        
        self.damage_tree.bind("<<TreeviewSelect>>", self.on_damage_select)
        
        ctk.CTkButton(self.tab_damage, text="📥 Export to CSV", 
                     command=self.export_damage_report,
                     fg_color="#8b5cf6", hover_color="#7c3aed", 
                     font=("Inter", 14, "bold")).pack(pady=10)

    def setup_summary_tab(self):
        """Configura la pestaña de resumen"""
        ctk.CTkLabel(self.tab_summary, text="📊 Incident Summary", 
                    font=("Inter", 20, "bold"), 
                    text_color="#38bdf8").pack(pady=15)
        
        summary_frame = ctk.CTkFrame(self.tab_summary, fg_color="transparent")
        summary_frame.pack(fill="x", padx=20, pady=20)
        
        # Tarjeta de pérdidas
        loss_card = ctk.CTkFrame(summary_frame, fg_color="#7f1d1d", corner_radius=15)
        loss_card.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(loss_card, text="🔴 Total Losses", 
                    font=("Inter", 16, "bold")).pack(pady=10)
        self.summary_loss_label = ctk.CTkLabel(loss_card, text="0", 
                                              font=("Inter", 36, "bold"), 
                                              text_color="#ef4444")
        self.summary_loss_label.pack(pady=10)
        
        # Tarjeta de daños
        damage_card = ctk.CTkFrame(summary_frame, fg_color="#5b21b6", corner_radius=15)
        damage_card.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(damage_card, text="🟣 Total Damages", 
                    font=("Inter", 16, "bold")).pack(pady=10)
        self.summary_damage_label = ctk.CTkLabel(damage_card, text="0", 
                                                font=("Inter", 36, "bold"), 
                                                text_color="#8b5cf6")
        self.summary_damage_label.pack(pady=10)
        
        # Tarjeta de total
        total_card = ctk.CTkFrame(summary_frame, fg_color="#1e40af", corner_radius=15)
        total_card.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(total_card, text="📋 Total Incidents", 
                    font=("Inter", 16, "bold")).pack(pady=10)
        self.summary_total_label = ctk.CTkLabel(total_card, text="0", 
                                               font=("Inter", 36, "bold"), 
                                               text_color="#3b82f6")
        self.summary_total_label.pack(pady=10)
        
        # Incidentes recientes
        recent_frame = ctk.CTkFrame(self.tab_summary, fg_color=SLATE_GRAY, corner_radius=12)
        recent_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(recent_frame, text="🕐 Recent Incidents", 
                    font=("Inter", 16, "bold"), 
                    text_color="#38bdf8").pack(anchor="w", padx=15, pady=10)
        
        self.recent_incidents_text = ctk.CTkTextbox(recent_frame, height=200, 
                                                   font=("Inter", 11))
        self.recent_incidents_text.pack(fill="both", expand=True, padx=15, pady=10)
        self.recent_incidents_text.configure(state="disabled")

    def load_reports(self):
        """Carga todos los datos de reportes"""
        if not os.path.isfile(JSON_FILE):
            return
        
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        # Limpia las tablas
        if hasattr(self, 'loss_tree'):
            self.loss_tree.delete(*self.loss_tree.get_children())
        if hasattr(self, 'damage_tree'):
            self.damage_tree.delete(*self.damage_tree.get_children())
        
        loss_count = 0
        damage_count = 0
        recent_incidents = []
        
        # Recorre todos los items y sus historiales
        for item in datos:
            for h in item.get('historial', []):
                if h['accion'] == 'Loss':
                    loss_count += 1
                    
                    self.loss_tree.insert('', 'end', values=(
                        item['serial'],
                        item.get('usuario', '-'),
                        item.get('codigo_pipkins', '-'),
                        h['fecha'],
                        h.get('usuario', '-')
                    ))
                    
                    recent_incidents.append({
                        'date': h['fecha'],
                        'time': h['hora'],
                        'type': 'LOSS',
                        'serial': item['serial'],
                        'user': item.get('usuario', '-'),
                        'comment': h.get('comentario', '')
                    })
                    
                elif h['accion'] == 'Damage':
                    damage_count += 1
                    
                    self.damage_tree.insert('', 'end', values=(
                        item['serial'],
                        item.get('usuario', '-'),
                        item.get('codigo_pipkins', '-'),
                        h['fecha'],
                        h.get('usuario', '-')
                    ))
                    
                    recent_incidents.append({
                        'date': h['fecha'],
                        'time': h['hora'],
                        'type': 'DAMAGE',
                        'serial': item['serial'],
                        'user': item.get('usuario', '-'),
                        'comment': h.get('comentario', '')
                    })
        
        # Actualiza las etiquetas de conteo
        if hasattr(self, 'loss_count_label'):
            self.loss_count_label.configure(text=f"Total Lost: {loss_count}")
        if hasattr(self, 'damage_count_label'):
            self.damage_count_label.configure(text=f"Total Damaged: {damage_count}")
        if hasattr(self, 'summary_loss_label'):
            self.summary_loss_label.configure(text=str(loss_count))
        if hasattr(self, 'summary_damage_label'):
            self.summary_damage_label.configure(text=str(damage_count))
        if hasattr(self, 'summary_total_label'):
            self.summary_total_label.configure(text=str(loss_count + damage_count))
        
        # Ordena incidentes recientes (más reciente primero)
        recent_incidents.sort(key=lambda x: (x['date'], x['time']), reverse=True)
        
        # Muestra los últimos 10 incidentes
        if hasattr(self, 'recent_incidents_text'):
            self.recent_incidents_text.configure(state="normal")
            self.recent_incidents_text.delete("1.0", "end")
            
            if recent_incidents:
                for inc in recent_incidents[:10]:
                    type_color = "🔴" if inc['type'] == 'LOSS' else "🟣"
                    text = f"{type_color} {inc['date']} {inc['time']} - {inc['serial']}\n"
                    text += f"   User: {inc['user']}\n"
                    text += f"   Type: {inc['type']}\n"
                    
                    if inc['comment']:
                        text += f"   💬 {inc['comment']}\n"
                    
                    text += "\n"
                    self.recent_incidents_text.insert("end", text)
            else:
                self.recent_incidents_text.insert("end", "No incidents recorded yet.")
            
            self.recent_incidents_text.configure(state="disabled")

    def on_loss_select(self, event):
        """Maneja la selección de un item en la tabla de pérdidas"""
        selection = self.loss_tree.selection()
        if not selection:
            return
        
        item = self.loss_tree.item(selection[0])
        serial = item['values'][0]
        
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        comment = ""
        for yubi in datos:
            if yubi['serial'] == serial:
                for h in yubi.get('historial', []):
                    if h['accion'] == 'Loss':
                        comment = h.get('comentario', 'No description provided')
                        break
                break
        
        self.loss_comment_text.configure(state="normal")
        self.loss_comment_text.delete("1.0", "end")
        self.loss_comment_text.insert("1.0", comment if comment else "No description provided")
        self.loss_comment_text.configure(state="disabled")

    def on_damage_select(self, event):
        """Maneja la selección de un item en la tabla de daños"""
        selection = self.damage_tree.selection()
        if not selection:
            return
        
        item = self.damage_tree.item(selection[0])
        serial = item['values'][0]
        
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        comment = ""
        for yubi in datos:
            if yubi['serial'] == serial:
                for h in yubi.get('historial', []):
                    if h['accion'] == 'Damage':
                        comment = h.get('comentario', 'No description provided')
                        break
                break
        
        self.damage_comment_text.configure(state="normal")
        self.damage_comment_text.delete("1.0", "end")
        self.damage_comment_text.insert("1.0", comment if comment else "No description provided")
        self.damage_comment_text.configure(state="disabled")

    def export_loss_report(self):
        """Exporta el reporte de pérdidas a CSV"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"Loss_Report_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        
        if filename:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                datos = json.load(f)
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Serial', 'User', 'Pipkins', 'Date', 'Time', 'Description'])
                
                for item in datos:
                    for h in item.get('historial', []):
                        if h['accion'] == 'Loss':
                            writer.writerow([
                                item['serial'],
                                item.get('usuario', ''),
                                item.get('codigo_pipkins', ''),
                                h['fecha'],
                                h['hora'],
                                h.get('comentario', '')
                            ])
            
            print(f"Loss report exported to {filename}")

    def export_damage_report(self):
        """Exporta el reporte de daños a CSV"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"Damage_Report_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        
        if filename:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                datos = json.load(f)
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Serial', 'User', 'Pipkins', 'Date', 'Time', 'Description'])
                
                for item in datos:
                    for h in item.get('historial', []):
                        if h['accion'] == 'Damage':
                            writer.writerow([
                                item['serial'],
                                item.get('usuario', ''),
                                item.get('codigo_pipkins', ''),
                                h['fecha'],
                                h['hora'],
                                h.get('comentario', '')
                            ])
            
            print(f"Damage report exported to {filename}")

# ============================================================================
# PUNTO DE ENTRADA DE LA APLICACIÓN
# ============================================================================
if __name__ == "__main__":
    app = YubiDash()  # Crea la instancia de la aplicación
    app.mainloop()    # Inicia el bucle principal de eventos