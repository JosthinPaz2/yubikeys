# ============================================================================
# IMPORTACIÓN DE LIBRERÍAS
# ============================================================================
import customtkinter as ctk
import json
import os
import tkinter.ttk as ttk
from datetime import datetime
import csv
from tkinter import filedialog

# ============================================================================
# CONFIGURACIÓN VISUAL DE LA APLICACIÓN
# ============================================================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

MIDNIGHT_BLUE = "#0f172a"
SLATE_GRAY = "#1e293b"
SUCCESS_GREEN = "#10b981"
BORDER_DEFAULT = "#3b8ed0"
JSON_FILE = "inventario_base.json"

# ============================================================================
# DICCIONARIO DE COLORES POR ESTADO
# ============================================================================
ESTADO_COLORES = {
    "Disponible": "#10b981",
    "Available": "#10b981",
    "En Uso": "#3b82f6",
    "In Use": "#3b82f6",
    "En Break": "#f59e0b",
    "On Break": "#f59e0b",
    "En Lunch": "#f97316",
    "On Lunch": "#f97316",
    "Pérdida": "#ef4444",
    "Loss": "#ef4444",
    "Daño": "#8b5cf6",
    "Damage": "#8b5cf6"
}

# ============================================================================
# CLASE PRINCIPAL DE LA APLICACIÓN
# ============================================================================
class YubiDash(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Yubikey Management Dashboard")
        self.geometry("1100x600")
        self.configure(fg_color=MIDNIGHT_BLUE)
        self.resizable(False, False)

        self.initialize_database()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ========================================================================
        # BARRA LATERAL (SIDEBAR)
        # ========================================================================
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=SLATE_GRAY)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="WFM SYSTEM", font=("Inter", 20, "bold")).pack(pady=30)
        
        self.btn_nueva = ctk.CTkButton(self.sidebar, text="Register New", 
                                       command=self.show_nueva_panel, corner_radius=15)
        self.btn_nueva.pack(pady=8, padx=20, fill="x")
        
        self.btn_ingreso = ctk.CTkButton(self.sidebar, text="Break/Lunch", 
                                         command=self.show_ingreso_panel, corner_radius=15)
        self.btn_ingreso.pack(pady=8, padx=20, fill="x")
        
        self.btn_asignacion = ctk.CTkButton(self.sidebar, text="Assign/Return", 
                                            command=self.show_asignacion_panel, corner_radius=15)
        self.btn_asignacion.pack(pady=8, padx=20, fill="x")
        
        self.btn_perdida = ctk.CTkButton(self.sidebar, text="Loss/Damage", 
                                         command=self.show_perdida_panel, corner_radius=15)
        self.btn_perdida.pack(pady=8, padx=20, fill="x")
        
        self.btn_inv = ctk.CTkButton(self.sidebar, text="INVENTORY", 
                                     fg_color="transparent", border_width=1, 
                                     command=self.show_inv_view, corner_radius=15)
        self.btn_inv.pack(pady=8, padx=20, fill="x")
        
        self.btn_report = ctk.CTkButton(self.sidebar, text="REPORTS", 
                                        fg_color="transparent", border_width=1, 
                                        command=self.show_report_view, corner_radius=15)
        self.btn_report.pack(pady=8, padx=20, fill="x")

        # ========================================================================
        # ÁREA PRINCIPAL
        # ========================================================================
        self.view_main = ctk.CTkFrame(self, fg_color="transparent")
        self.view_main.grid(row=0, column=1, sticky="nsew")
        self.view_main.grid_columnconfigure(0, weight=1)
        self.view_main.grid_rowconfigure(0, weight=1)

        self.panel_nueva = ctk.CTkFrame(self.view_main, fg_color="transparent")
        self.panel_ingreso = ctk.CTkFrame(self.view_main, fg_color="transparent")
        self.panel_asignacion = ctk.CTkFrame(self.view_main, fg_color="transparent")
        self.panel_perdida = ctk.CTkFrame(self.view_main, fg_color="transparent")
        self.view_inv = ctk.CTkFrame(self.view_main, fg_color="transparent")
        self.view_report = ctk.CTkFrame(self.view_main, fg_color="transparent")

        self.setup_nueva_panel()
        self.setup_ingreso_panel()
        self.setup_asignacion_panel()
        self.setup_perdida_panel()
        self.setup_inv_view()
        self.setup_report_view()
        
        self.show_nueva_panel()

    def initialize_database(self):
        if not os.path.exists(JSON_FILE):
            with open(JSON_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f)
        else:
            self.migrate_database()

    def migrate_database(self):
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                datos = json.load(f)
            
            migrated = False
            
            for item in datos:
                if 'codigo_pickiks' in item:
                    item['codigo_pipkins'] = item.pop('codigo_pickiks')
                    migrated = True
                
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
                
                if item.get('estado') in state_map:
                    item['estado'] = state_map[item['estado']]
                    migrated = True
                
                if 'historial' in item:
                    for h in item['historial']:
                        if 'codigo_pickiks' in h:
                            h['codigo_pipkins'] = h.pop('codigo_pickiks')
                            migrated = True
                        
                        if h.get('estado') in state_map:
                            h['estado'] = state_map[h['estado']]
                            migrated = True
                        
                        if 'usuario' not in h:
                            h['usuario'] = item.get('usuario', '')
                        if 'codigo_pipkins' not in h:
                            h['codigo_pipkins'] = item.get('codigo_pipkins', '')
                        if 'comentario' not in h:
                            h['comentario'] = ''
                
                if 'historial' not in item:
                    item['historial'] = []
            
            if migrated:
                with open(JSON_FILE, 'w', encoding='utf-8') as f:
                    json.dump(datos, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Migration error: {e}")

    def show_nueva_panel(self):
        self.hide_all_panels()
        self.panel_nueva.pack(fill="both", expand=True, padx=20, pady=20)

    def show_ingreso_panel(self):
        self.hide_all_panels()
        self.panel_ingreso.pack(fill="both", expand=True, padx=20, pady=20)

    def show_asignacion_panel(self):
        self.hide_all_panels()
        self.panel_asignacion.pack(fill="both", expand=True, padx=20, pady=20)

    def show_perdida_panel(self):
        self.hide_all_panels()
        self.panel_perdida.pack(fill="both", expand=True, padx=20, pady=20)

    def show_inv_view(self):
        self.hide_all_panels()
        self.view_inv.pack(fill="both", expand=True, padx=20, pady=20)
        self.load_inventory_table()

    def show_report_view(self):
        self.hide_all_panels()
        self.view_report.pack(fill="both", expand=True, padx=20, pady=20)
        self.load_reports()

    def hide_all_panels(self):
        for panel in [self.panel_nueva, self.panel_ingreso, self.panel_asignacion, 
                      self.panel_perdida, self.view_inv, self.view_report]:
            panel.pack_forget()

    def setup_nueva_panel(self):
        ctk.CTkLabel(self.panel_nueva, text="Register New Yubikey", 
                    font=("Inter", 22, "bold")).pack(pady=30)
        
        self.entry_nueva = ctk.CTkEntry(self.panel_nueva, 
                                        placeholder_text="Scan new serial", 
                                        width=300, height=40, 
                                        font=("Inter", 16), 
                                        border_width=3, 
                                        border_color=BORDER_DEFAULT, 
                                        corner_radius=15)
        self.entry_nueva.pack(pady=10)
        self.entry_nueva.bind("<Return>", self.registrar_nueva_yubikey)
        
        self.label_nueva = ctk.CTkLabel(self.panel_nueva, text="", 
                                        text_color="red", 
                                        font=("Inter", 13, "bold"))
        self.label_nueva.pack(pady=5)
        
        self.setup_recent_table(self.panel_nueva, 'nueva')

    def setup_ingreso_panel(self):
        ctk.CTkLabel(self.panel_ingreso, text="Break / Lunch Check-in/out", 
                    font=("Inter", 22, "bold")).pack(pady=30)
        
        ctk.CTkLabel(self.panel_ingreso, text="Only for yubikeys IN USE", 
                    font=("Inter", 13), text_color="#94a3b8").pack(pady=(0, 20))
        
        self.entry_ingreso = ctk.CTkEntry(self.panel_ingreso, 
                                          placeholder_text="Scan for Check-in/out", 
                                          width=300, height=40, 
                                          font=("Inter", 16), 
                                          border_width=3, 
                                          border_color=BORDER_DEFAULT, 
                                          corner_radius=15)
        self.entry_ingreso.pack(pady=10)
        self.entry_ingreso.bind("<Return>", lambda e: self.process_session_scan('ingreso_salida'))
        
        self.label_ingreso = ctk.CTkLabel(self.panel_ingreso, text="", 
                                          text_color="red", 
                                          font=("Inter", 13, "bold"))
        self.label_ingreso.pack(pady=5)
        
        self.setup_recent_table(self.panel_ingreso, 'ingreso')

    def setup_asignacion_panel(self):
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

    def setup_perdida_panel(self):
        ctk.CTkLabel(self.panel_perdida, text="Loss / Damage Report", 
                    font=("Inter", 22, "bold")).pack(pady=30)
        
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

    def setup_recent_table(self, parent, tipo):
        frame = ctk.CTkFrame(parent, fg_color=SLATE_GRAY, corner_radius=12)
        frame.pack(pady=18, padx=10, fill='x')
        
        ctk.CTkLabel(frame, text="Recent movements", 
                    font=("Inter", 15, "bold"), 
                    text_color="#38bdf8").pack(anchor='w', padx=10, pady=(8, 0))
        
        columns = ("Serial", "Pipkins Code", "Action", "Date", "Time")
        
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure(f'{tipo}.Treeview', 
                       font=('Segoe UI', 11), 
                       rowheight=28, 
                       background=SLATE_GRAY, 
                       fieldbackground=SLATE_GRAY, 
                       foreground="#e0e7ef", 
                       borderwidth=0)
        
        style.configure(f'{tipo}.Treeview.Heading', 
                       font=('Segoe UI', 12, 'bold'), 
                       background="#334155", 
                       foreground="#38bdf8")
        
        tree = ttk.Treeview(frame, columns=columns, show='headings', 
                           height=5, style=f'{tipo}.Treeview')
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor='center', width=120)
        
        tree.pack(side='left', fill='x', expand=True, padx=10, pady=10)
        
        setattr(self, f"tree_recent_{tipo}", tree)
        self.load_recent_data(tipo)

    def load_recent_data(self, tipo):
        tree = getattr(self, f"tree_recent_{tipo}", None)
        if not tree: return
        
        tree.delete(*tree.get_children())
        movimientos = self.get_recent_movements(tipo)
        
        for mov in movimientos:
            tree.insert('', 'end', values=mov)

    def get_recent_movements(self, tipo):
        if not os.path.isfile(JSON_FILE): return []
        
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        movs = []
        for item in datos:
            codigo = item.get('codigo_pipkins', '-')
            
            for h in item.get('historial', []):
                if tipo == 'nueva' and h['accion'] == 'Registro':
                    movs.append((item['serial'], codigo, h['accion'], h['fecha'], h['hora']))
                elif tipo == 'ingreso' and ('Break' in h['accion'] or 'Lunch' in h['accion']):
                    movs.append((item['serial'], codigo, h['accion'], h['fecha'], h['hora']))
                elif tipo == 'asignacion' and ('Assign' in h['accion'] or 'Return' in h['accion']):
                    movs.append((item['serial'], codigo, h['accion'], h['fecha'], h['hora']))
                elif tipo == 'perdida' and h['accion'] in ['Loss', 'Damage']:
                    movs.append((item['serial'], codigo, h['accion'], h['fecha'], h['hora']))
        
        return sorted(movs, key=lambda x: (x[3], x[4]), reverse=True)[:5]

    def serial_exists(self, serial):
        if not os.path.isfile(JSON_FILE):
            return False
        
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        return any(item['serial'].upper() == serial.upper() for item in datos)

    def find_by_pipkins(self, pipkins_code):
        if not os.path.isfile(JSON_FILE):
            return None
        
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        for item in datos:
            if item.get('codigo_pipkins', '').upper() == pipkins_code.upper():
                return item
        
        return None

    def ask_user_and_pipkins(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Manual Yubikey Registration")
        modal.geometry("420x370")
        modal.grab_set()
        
        frame = ctk.CTkFrame(modal, fg_color="#1e293b", corner_radius=18)
        frame.pack(padx=24, pady=24, fill="both", expand=True)
        
        ctk.CTkLabel(frame, text="Manual Registration", 
                    font=("Inter", 24, "bold"), 
                    text_color="#38bdf8").pack(pady=(10, 18))
        
        ctk.CTkLabel(frame, text="Yubikey Serial:", 
                    font=("Inter", 16)).pack(anchor='w', padx=10, pady=(4, 0))
        serial_var = ctk.StringVar()
        serial_entry = ctk.CTkEntry(frame, textvariable=serial_var, 
                                   width=260, font=("Inter", 15), corner_radius=10)
        serial_entry.pack(pady=(0, 10))
        serial_entry.focus_set()
        
        ctk.CTkLabel(frame, text="User:", 
                    font=("Inter", 16)).pack(anchor='w', padx=10, pady=(4, 0))
        usuario_var = ctk.StringVar()
        usuario_entry = ctk.CTkEntry(frame, textvariable=usuario_var, 
                                    width=260, font=("Inter", 15), corner_radius=10)
        usuario_entry.pack(pady=(0, 10))
        
        ctk.CTkLabel(frame, text="Pipkins Code:", 
                    font=("Inter", 16)).pack(anchor='w', padx=10, pady=(4, 0))
        pipkins_var = ctk.StringVar()
        pipkins_entry = ctk.CTkEntry(frame, textvariable=pipkins_var, 
                                    width=260, font=("Inter", 15), corner_radius=10)
        pipkins_entry.pack(pady=(0, 10))
        
        error_label = ctk.CTkLabel(frame, text="", 
                                  text_color="#ef4444", 
                                  font=("Inter", 13, "bold"))
        error_label.pack(pady=(0, 2))
        
        result = {'ok': False, 'serial': '', 'usuario': '', 'pipkins': ''}
        
        def registrar():
            serial = serial_var.get().strip()
            usuario = usuario_var.get().strip()
            pipkins = pipkins_var.get().strip()
            
            if not serial or not usuario or not pipkins:
                error_label.configure(text="All fields are required")
                return
            
            result['ok'] = True
            result['serial'] = serial
            result['usuario'] = usuario
            result['pipkins'] = pipkins
            modal.destroy()
        
        ctk.CTkButton(frame, text="Register", command=registrar, 
                     fg_color="#38bdf8", hover_color="#0ea5e9", 
                     font=("Inter", 17, "bold"), corner_radius=12).pack(pady=16)
        
        modal.wait_window()
        
        if result['ok']:
            return result['serial'], result['usuario'], result['pipkins']
        return None, None, None

    def registrar_nueva_yubikey(self, event=None):
        serial = self.entry_nueva.get().strip().upper()
        
        if not serial:
            self.label_nueva.configure(text="Empty field!", text_color="red")
            self.entry_nueva.configure(border_color="red")
            self.after(2000, lambda: self.entry_nueva.configure(border_color=BORDER_DEFAULT))
            return

        if self.serial_exists(serial):
            self.label_nueva.configure(text="⚠️ Serial already registered", text_color="orange")
            self.entry_nueva.configure(border_color="orange")
            self.after(3000, lambda: self.entry_nueva.configure(border_color=BORDER_DEFAULT))
            self.entry_nueva.delete(0, 'end')
            return

        serial_modal, nombre, codigo = self.ask_user_and_pipkins()
        
        if nombre and codigo:
            now = datetime.now()
            
            nueva = {
                "serial": serial,
                "usuario": nombre,
                "codigo_pipkins": codigo,
                "estado": "In Use",
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
            
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                datos = json.load(f)
            
            datos.append(nueva)
            
            with open(JSON_FILE, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
            
            self.label_nueva.configure(text="Registered and IN USE!", text_color=SUCCESS_GREEN)
            self.entry_nueva.delete(0, 'end')
            
            self.load_recent_data('nueva')
            self.load_inventory_table()
            
            self.after(3000, lambda: self.label_nueva.configure(text=""))

    def ask_break_type(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Select Break/Lunch Type")
        modal.geometry("340x200")
        modal.grab_set()
        
        ctk.CTkLabel(modal, text="Check-in or check-out from?", 
                    font=("Inter", 17, "bold"), 
                    text_color="#38bdf8").pack(pady=(18, 18))
        
        tipo_var = ctk.StringVar(value="Break")
        opciones = ["Break", "Lunch"]
        
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
        modal = ctk.CTkToplevel(self)
        modal.title("Select Action Type")
        modal.geometry("500x350")
        modal.grab_set()
        
        ctk.CTkLabel(modal, text="What action will you perform?", 
                    font=("Inter", 18, "bold"), 
                    text_color="#38bdf8").pack(pady=(20, 15))
        
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
        modal = ctk.CTkToplevel(self)
        modal.title("New User Details")
        modal.geometry("420x320")
        modal.grab_set()
        
        frame = ctk.CTkFrame(modal, fg_color="#1e293b", corner_radius=18)
        frame.pack(padx=24, pady=24, fill="both", expand=True)
        
        ctk.CTkLabel(frame, text="Assign to new user", 
                    font=("Inter", 20, "bold"), 
                    text_color="#38bdf8").pack(pady=(10, 18))
        
        ctk.CTkLabel(frame, text="User name:", 
                    font=("Inter", 15)).pack(anchor='w', padx=10, pady=(4, 0))
        usuario_var = ctk.StringVar()
        usuario_entry = ctk.CTkEntry(frame, textvariable=usuario_var, 
                                    width=260, font=("Inter", 14), corner_radius=10)
        usuario_entry.pack(pady=(0, 10))
        usuario_entry.focus_set()
        
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
        
        ctk.CTkButton(btn_frame, text="Submit", command=aceptar, 
                     fg_color="#38bdf8", hover_color="#0ea5e9", 
                     font=("Inter", 15, "bold"), 
                     corner_radius=12, width=120).pack(side="left", padx=10)
        
        ctk.CTkButton(btn_frame, text="Skip", command=modal.destroy, 
                     fg_color="#475569", hover_color="#64748b", 
                     font=("Inter", 15), 
                     corner_radius=12, width=100).pack(side="left", padx=10)
        
        modal.wait_window()
        
        return result['comentario'] if result['ok'] else ""

    def process_session_scan(self, session):
        if session == 'ingreso_salida':
            entry = self.entry_ingreso
            label = self.label_ingreso
            tipo_tree = 'ingreso'
            tipo_break = self.ask_break_type()
            
            if tipo_break is None:
                label.configure(text="Action cancelled", text_color="orange")
                return
                
        elif session == 'asignacion_retoma':
            entry = self.entry_asignacion
            label = self.label_asignacion
            tipo_tree = 'asignacion'
            tipo_accion = self.ask_asignacion_retoma_type()
            
            if tipo_accion is None:
                label.configure(text="Action cancelled", text_color="orange")
                return
                
        else:
            entry = self.entry_perdida
            label = self.label_perdida
            tipo_tree = 'perdida'
            tipo_accion = None
            
        serial_or_pipkins = entry.get().strip()
        
        if not serial_or_pipkins:
            label.configure(text="Empty field!")
            entry.configure(border_color="red")
            self.after(2000, lambda: entry.configure(border_color=BORDER_DEFAULT))
            return
            
        item_data = None
        found_by_pipkins = False
        
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        for item in datos:
            if item['serial'].strip().upper() == serial_or_pipkins.upper():
                item_data = item
                break
        
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
        
        now = datetime.now()
        fecha = now.strftime('%Y-%m-%d')
        hora = now.strftime('%H:%M:%S')
        accion = ''
        cambio = False
        found = False
        comentario = ""
        
        for item in datos:
            if item['serial'].strip().upper() == serial.upper():
                found = True
                
                if session == 'ingreso_salida':
                    estado_actual = item['estado']
                    estado_seleccionado = f'On {tipo_break}'
                    
                    if estado_actual == 'In Use':
                        item['estado'] = estado_seleccionado
                        accion = f'Check-in to {tipo_break}'
                        item['ultima_conexion'] = fecha
                        cambio = True
                        
                    elif estado_actual == estado_seleccionado:
                        item['estado'] = 'In Use'
                        accion = f'Check-out from {tipo_break}'
                        item['ultima_conexion'] = fecha
                        cambio = True
                        
                    elif estado_actual in ['On Break', 'On Lunch'] and estado_actual != estado_seleccionado:
                        otro = estado_actual.replace('On ', '')
                        accion = f"⚠️ Must check-out from {otro} first"
                        break
                        
                    else:
                        accion = f"❌ Not applicable: state '{estado_actual}'"
                        break
                        
                elif session == 'asignacion_retoma':
                    estado_actual = item['estado']
                    
                    if tipo_accion == 'Return':
                        if estado_actual in ['In Use', 'On Break', 'On Lunch']:
                            usuario_anterior = item['usuario']
                            
                            comentario = self.ask_comentario(
                                "Yubikey Return",
                                f"User '{usuario_anterior}' returns yubikey (no longer works here)\nOptional comment:"
                            )
                            
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
                            
                elif session == 'perdida_dano':
                    estado_actual = item['estado']
                    
                    if estado_actual in ['Loss', 'Damage']:
                        accion = f"❌ Already in state '{estado_actual}'"
                        break
                    
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
                    search_method = "via Pipkins code" if found_by_pipkins else "via serial scanner"
                    
                    comentario = self.ask_comentario(
                        f"Report {tipo_incidente}",
                        f"Reporting {tipo_incidente.lower()} ({search_method})\nSerial: {item['serial']}\nUser: {item.get('usuario', 'N/A')}\nPipkins: {item.get('codigo_pipkins', 'N/A')}\n\nDescribe what happened:"
                    )
                    
                    item['estado'] = tipo_incidente
                    accion = tipo_incidente
                    item['ultima_conexion'] = fecha
                    cambio = True
                        
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
    # VISTA DE INVENTARIO (CON BOTÓN DE EXPORTAR AL LADO DE VIEW DETAILS)
    # ============================================================================
    def setup_inv_view(self):
        ctk.CTkLabel(self.view_inv, text="General Inventory", 
                    font=("Inter", 32, "bold"), 
                    text_color="#38bdf8").pack(pady=15)
        
        filter_frame = ctk.CTkFrame(self.view_inv, fg_color=SLATE_GRAY, corner_radius=12)
        filter_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(filter_frame, text="Filter by state:", 
                    font=("Inter", 14, "bold")).pack(side="left", padx=15, pady=10)
        
        self.filter_var = ctk.StringVar(value="All")
        estados = ["All", "Available", "In Use", "On Break", "On Lunch", "Loss", "Damage"]
        
        for estado in estados:
            ctk.CTkRadioButton(filter_frame, text=estado, 
                             variable=self.filter_var, 
                             value=estado,
                             command=self.filter_inventory, 
                             font=("Inter", 13)).pack(side="left", padx=8, pady=10)
        
        search_frame = ctk.CTkFrame(self.view_inv, fg_color="transparent")
        search_frame.pack(pady=5)
        
        self.search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(search_frame, 
                                   textvariable=self.search_var, 
                                   placeholder_text="Search by serial or user...", 
                                   width=300)
        search_entry.pack(side="left", padx=10)
        
        search_entry.bind("<KeyRelease>", lambda e: self.filter_inventory())
        
        ctk.CTkButton(search_frame, text="📋 View Details", 
                     command=self.show_item_details,
                     fg_color="#38bdf8", hover_color="#0ea5e9", 
                     font=("Inter", 13, "bold")).pack(side="left", padx=10)
        
        ctk.CTkButton(search_frame, text="📥 Export Inventory", 
                     command=self.export_inventory,
                     fg_color="#38bdf8", hover_color="#0ea5e9", 
                     font=("Inter", 13, "bold"),
                     width=180).pack(side="left", padx=10)

        table_frame = ctk.CTkFrame(self.view_inv, fg_color=SLATE_GRAY, corner_radius=15)
        table_frame.pack(expand=True, fill="both", padx=20, pady=10)

        cols = ("Serial", "User", "Pipkins", "State", "Last Connection")
        
        self.inv_tree = ttk.Treeview(table_frame, columns=cols, 
                                    show='headings', style='Custom.Treeview')
        
        style = ttk.Style()
        style.configure('Custom.Treeview', 
                       font=('Segoe UI', 12), 
                       rowheight=35, 
                       background=SLATE_GRAY, 
                       fieldbackground=SLATE_GRAY, 
                       foreground="white")
        style.configure('Custom.Treeview.Heading', 
                       font=('Segoe UI', 13, 'bold'))
        
        for estado, color in ESTADO_COLORES.items():
            self.inv_tree.tag_configure(estado, background=color, foreground="white")
        
        for col in cols:
            self.inv_tree.heading(col, text=col)
            self.inv_tree.column(col, anchor='center', width=150)
        
        self.inv_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.inv_tree.bind("<Double-1>", lambda e: self.show_item_details())
        
        scrollbar = ttk.Scrollbar(self.inv_tree, orient="vertical", 
                                 command=self.inv_tree.yview)
        self.inv_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

    def load_inventory_table(self, refresh=False):
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
        filter_estado = self.filter_var.get()
        search_term = self.search_var.get().lower()
        
        self.inv_tree.delete(*self.inv_tree.get_children())
        
        if not os.path.isfile(JSON_FILE):
            return
        
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        for item in datos:
            estado = item['estado']
            
            if filter_estado != "All" and estado != filter_estado:
                continue
            
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

    def export_inventory(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Export Inventory")
        modal.geometry("400x250")
        modal.grab_set()
        
        ctk.CTkLabel(modal, text="📥 Export Inventory", 
                    font=("Inter", 20, "bold"), 
                    text_color="#38bdf8").pack(pady=20)
        
        ctk.CTkLabel(modal, text="Select export format:", 
                    font=("Inter", 14)).pack(pady=10)
        
        format_var = ctk.StringVar(value="CSV")
        
        ctk.CTkRadioButton(modal, text="📊 CSV (Excel compatible)", 
                          variable=format_var, value="CSV",
                          font=("Inter", 14)).pack(pady=5)
        
        ctk.CTkRadioButton(modal, text="📄 TXT (Text file)", 
                          variable=format_var, value="TXT",
                          font=("Inter", 14)).pack(pady=5)
        
        result = {'ok': False}
        
        def exportar():
            result['ok'] = True
            result['format'] = format_var.get()
            modal.destroy()
        
        def cancelar():
            modal.destroy()
        
        btn_frame = ctk.CTkFrame(modal, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="Export", command=exportar, 
                     fg_color="#38bdf8", hover_color="#0ea5e9", 
                     font=("Inter", 15, "bold"),
                     width=120).pack(side="left", padx=10)
        
        ctk.CTkButton(btn_frame, text="Cancel", command=cancelar, 
                     fg_color="#475569", hover_color="#64748b", 
                     font=("Inter", 15),
                     width=120).pack(side="left", padx=10)
        
        modal.wait_window()
        
        if not result.get('ok'):
            return
        
        formato = result['format']
        fecha_actual = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if formato == "CSV":
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=f"Inventory_Export_{fecha_actual}.csv"
            )
        else:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialfile=f"Inventory_Export_{fecha_actual}.txt"
            )
        
        if not filename:
            return
        
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                datos = json.load(f)
            
            if formato == "CSV":
                self._export_to_csv(filename, datos)
            else:
                self._export_to_txt(filename, datos)
            
            modal_success = ctk.CTkToplevel(self)
            modal_success.title("Export Complete")
            modal_success.geometry("350x150")
            modal_success.grab_set()
            
            ctk.CTkLabel(modal_success, text="✅ Export Complete!", 
                        font=("Inter", 18, "bold"), 
                        text_color=SUCCESS_GREEN).pack(pady=20)
            
            ctk.CTkLabel(modal_success, text=f"Saved to:\n{filename}", 
                        font=("Inter", 10), 
                        text_color="#94a3b8",
                        wraplength=300).pack(pady=10)
            
            ctk.CTkButton(modal_success, text="OK", command=modal_success.destroy, 
                         fg_color="#38bdf8", font=("Inter", 14, "bold")).pack(pady=10)
            
        except Exception as e:
            modal_error = ctk.CTkToplevel(self)
            modal_error.title("Export Error")
            modal_error.geometry("350x150")
            modal_error.grab_set()
            
            ctk.CTkLabel(modal_error, text="❌ Export Error", 
                        font=("Inter", 18, "bold"), 
                        text_color="#ef4444").pack(pady=20)
            
            ctk.CTkLabel(modal_error, text=str(e), 
                        font=("Inter", 10), 
                        text_color="#94a3b8").pack(pady=10)
            
            ctk.CTkButton(modal_error, text="OK", command=modal_error.destroy, 
                         fg_color="#475569", font=("Inter", 14)).pack(pady=10)

    def _export_to_csv(self, filename, datos):
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            writer.writerow(['=' * 80])
            writer.writerow(['YUBIKEY INVENTORY EXPORT'])
            writer.writerow([f'Export Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
            writer.writerow(['=' * 80])
            writer.writerow([])
            
            writer.writerow(['Serial', 'User', 'Pipkins', 'State', 'Last Connection', 'History Date', 'History Action', 'History Comment'])
            writer.writerow(['-' * 80])
            
            for item in datos:
                writer.writerow([
                    item['serial'],
                    item.get('usuario', ''),
                    item.get('codigo_pipkins', ''),
                    item['estado'],
                    item.get('ultima_conexion', '')
                ])
                
                historial = item.get('historial', [])
                for h in historial:
                    writer.writerow([
                        '', '', '', '', '',
                        f"{h.get('fecha', '')} {h.get('hora', '')}",
                        h.get('accion', ''),
                        h.get('comentario', '')
                    ])
                
                writer.writerow([])
            
            writer.writerow(['=' * 80])
            writer.writerow(['SUMMARY'])
            writer.writerow([f'Total Yubikeys: {len(datos)}'])
            
            estados_count = {}
            for item in datos:
                estado = item['estado']
                estados_count[estado] = estados_count.get(estado, 0) + 1
            
            writer.writerow([])
            writer.writerow(['By State:'])
            for estado, count in estados_count.items():
                writer.writerow([f'  {estado}: {count}'])
            
            writer.writerow(['=' * 80])

    def _export_to_txt(self, filename, datos):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("YUBIKEY INVENTORY EXPORT\n")
            f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            for i, item in enumerate(datos, 1):
                f.write(f"[{i}] {item['serial']}\n")
                f.write("-" * 80 + "\n")
                f.write(f"  Current State: {item['estado']}\n")
                f.write(f"  User: {item.get('usuario', 'N/A') or 'N/A'}\n")
                f.write(f"  Pipkins Code: {item.get('codigo_pipkins', 'N/A') or 'N/A'}\n")
                f.write(f"  Last Connection: {item.get('ultima_conexion', 'N/A') or 'N/A'}\n")
                f.write("\n")
                
                f.write("  📋 HISTORY:\n")
                historial = item.get('historial', [])
                
                if not historial:
                    f.write("    No history recorded\n")
                else:
                    for j, h in enumerate(historial, 1):
                        f.write(f"    [{j}] {h.get('fecha', '')} {h.get('hora', '')}\n")
                        f.write(f"        Action: {h.get('accion', '')}\n")
                        f.write(f"        State: {h.get('estado', '')}\n")
                        
                        if h.get('usuario'):
                            f.write(f"        User: {h.get('usuario', '')}\n")
                        if h.get('codigo_pipkins'):
                            f.write(f"        Pipkins: {h.get('codigo_pipkins', '')}\n")
                        if h.get('comentario'):
                            f.write(f"        💬 Comment: {h.get('comentario', '')}\n")
                        
                        f.write("\n")
                
                f.write("\n" + "=" * 80 + "\n\n")
            
            f.write("SUMMARY\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total Yubikeys: {len(datos)}\n\n")
            
            estados_count = {}
            for item in datos:
                estado = item['estado']
                estados_count[estado] = estados_count.get(estado, 0) + 1
            
            f.write("By State:\n")
            for estado, count in estados_count.items():
                f.write(f"  • {estado}: {count}\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("END OF REPORT\n")
            f.write("=" * 80 + "\n")

    def show_item_details(self):
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
        
        modal = ctk.CTkToplevel(self)
        modal.title(f"Details - {serial}")
        modal.geometry("700x550")
        modal.grab_set()
        
        main_frame = ctk.CTkFrame(modal, fg_color="#1e293b", corner_radius=18)
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
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

    def setup_report_view(self):
        ctk.CTkLabel(self.view_report, text="📊 INCIDENT REPORTS", 
                    font=("Inter", 32, "bold"), 
                    text_color="#38bdf8").pack(pady=20)
        
        self.report_tabs = ctk.CTkTabview(self.view_report, corner_radius=15)
        self.report_tabs.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.tab_loss = self.report_tabs.add("🔴 Loss Report")
        self.tab_damage = self.report_tabs.add("🟣 Damage Report")
        self.tab_summary = self.report_tabs.add("📈 Summary")
        
        self.setup_loss_report_tab()
        self.setup_damage_report_tab()
        self.setup_summary_tab()

    def setup_loss_report_tab(self):
        ctk.CTkLabel(self.tab_loss, text="Lost Yubikeys Report", 
                    font=("Inter", 20, "bold"), 
                    text_color="#ef4444").pack(pady=15)
        
        stats_frame = ctk.CTkFrame(self.tab_loss, fg_color=SLATE_GRAY, corner_radius=12)
        stats_frame.pack(fill="x", padx=20, pady=10)
        
        self.loss_count_label = ctk.CTkLabel(stats_frame, text="Total Lost: 0", 
                                            font=("Inter", 16, "bold"), 
                                            text_color="#ef4444")
        self.loss_count_label.pack(pady=10)
        
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
        
        comment_frame = ctk.CTkFrame(self.tab_loss, fg_color=SLATE_GRAY, corner_radius=12)
        comment_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(comment_frame, text="📝 Incident Description", 
                    font=("Inter", 14, "bold"), 
                    text_color="#ef4444").pack(anchor="w", padx=10, pady=5)
        
        self.loss_comment_text = ctk.CTkTextbox(comment_frame, height=100, 
                                               font=("Inter", 12))
        self.loss_comment_text.pack(fill="x", padx=10, pady=10)
        self.loss_comment_text.configure(state="disabled")
        
        self.loss_tree.bind("<<TreeviewSelect>>", self.on_loss_select)
        
        ctk.CTkButton(self.tab_loss, text="📥 Export to CSV", 
                     command=self.export_loss_report,
                     fg_color="#ef4444", hover_color="#dc2626", 
                     font=("Inter", 14, "bold")).pack(pady=10)

    def setup_damage_report_tab(self):
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
        ctk.CTkLabel(self.tab_summary, text="📊 Incident Summary", 
                    font=("Inter", 20, "bold"), 
                    text_color="#38bdf8").pack(pady=15)
        
        summary_frame = ctk.CTkFrame(self.tab_summary, fg_color="transparent")
        summary_frame.pack(fill="x", padx=20, pady=20)
        
        loss_card = ctk.CTkFrame(summary_frame, fg_color="#7f1d1d", corner_radius=15)
        loss_card.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(loss_card, text="🔴 Total Losses", 
                    font=("Inter", 16, "bold")).pack(pady=10)
        self.summary_loss_label = ctk.CTkLabel(loss_card, text="0", 
                                              font=("Inter", 36, "bold"), 
                                              text_color="#ef4444")
        self.summary_loss_label.pack(pady=10)
        
        damage_card = ctk.CTkFrame(summary_frame, fg_color="#5b21b6", corner_radius=15)
        damage_card.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(damage_card, text="🟣 Total Damages", 
                    font=("Inter", 16, "bold")).pack(pady=10)
        self.summary_damage_label = ctk.CTkLabel(damage_card, text="0", 
                                                font=("Inter", 36, "bold"), 
                                                text_color="#8b5cf6")
        self.summary_damage_label.pack(pady=10)
        
        total_card = ctk.CTkFrame(summary_frame, fg_color="#1e40af", corner_radius=15)
        total_card.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(total_card, text="📋 Total Incidents", 
                    font=("Inter", 16, "bold")).pack(pady=10)
        self.summary_total_label = ctk.CTkLabel(total_card, text="0", 
                                               font=("Inter", 36, "bold"), 
                                               text_color="#3b82f6")
        self.summary_total_label.pack(pady=10)
        
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
        if not os.path.isfile(JSON_FILE):
            return
        
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        if hasattr(self, 'loss_tree'):
            self.loss_tree.delete(*self.loss_tree.get_children())
        if hasattr(self, 'damage_tree'):
            self.damage_tree.delete(*self.damage_tree.get_children())
        
        loss_count = 0
        damage_count = 0
        recent_incidents = []
        
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
        
        recent_incidents.sort(key=lambda x: (x['date'], x['time']), reverse=True)
        
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

if __name__ == "__main__":
    app = YubiDash()
    app.mainloop()