# ============================================================================
# YUBIKEY MANAGEMENT DASHBOARD - YubiDash
# Versión: 6.4 (Reportes Mejorados + UI Profesional)
# ============================================================================

import customtkinter as ctk
import json
import os
import tkinter.ttk as ttk
from datetime import datetime
import csv
from tkinter import filedialog
import serial
import serial.tools.list_ports
import threading

# ============================================================================
# CONFIGURACIÓN VISUAL
# ============================================================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

MIDNIGHT_BLUE = "#0f172a"
SLATE_GRAY = "#1e293b"
SUCCESS_GREEN = "#10b981"
BORDER_DEFAULT = "#3b8ed0"
JSON_FILE = "inventario_base.json"

REPORT_COLORS = {
    "loss_bg": "#7f1d1d",
    "loss_bg_light": "#991b1b",
    "loss_text": "#fca5a5",
    "loss_border": "#dc2626",
    "damage_bg": "#5b21b6",
    "damage_bg_light": "#6d28d9",
    "damage_text": "#c4b5fd",
    "damage_border": "#7c3aed",
    "summary_bg": "#1e40af",
    "summary_bg_light": "#1d4ed8",
    "summary_text": "#93c5fd",
    "summary_border": "#3b82f6",
    "card_bg": "#1e293b",
    "card_border": "#334155",
    "table_header": "#0f172a",
    "table_row": "#1e293b",
    "table_row_alt": "#0f172a",
    "table_text": "#e2e8f0",
    "table_border": "#334155"
}

# ============================================================================
# CLASE DE CONFIGURACIÓN RESPONSIVA
# ============================================================================
class ResponsiveConfig:
    def __init__(self):
        self.screen_width = 1100
        self.screen_height = 600
        self.is_laptop = False
        self.scale_factor = 1.0
        self.detect_screen()
    
    def detect_screen(self):
        try:
            root = ctk.CTk()
            self.screen_width = root.winfo_screenwidth()
            self.screen_height = root.winfo_screenheight()
            root.destroy()
            self.is_laptop = self.screen_width <= 1536
            if self.screen_width >= 1920:
                self.scale_factor = 1.2
            elif self.screen_width >= 1536:
                self.scale_factor = 1.0
            else:
                self.scale_factor = 0.9
        except:
            self.is_laptop = False
            self.scale_factor = 1.0
    
    def get_window_size(self):
        if self.is_laptop:
            return f"{int(self.screen_width * 0.95)}x{int(self.screen_height * 0.90)}"
        else:
            return "1400x800"
    
    def get_font_size(self, base_size):
        return int(base_size * self.scale_factor)
    
    def get_sidebar_width(self):
        return 200 if self.is_laptop else 240
    
    def get_entry_width(self):
        return 350 if self.is_laptop else 450
    
    def get_modal_size(self, base_width=500, base_height=350):
        if self.is_laptop:
            return f"{int(base_width * 0.9)}x{int(base_height * 0.85)}"
        else:
            return f"{base_width}x{base_height}"
    
    def center_modal(self, parent, width, height):
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        
        modal_x = parent_x + (parent_w // 2) - (width // 2)
        modal_y = parent_y + (parent_h // 2) - (height // 2)
        
        return f"{width}x{height}+{modal_x}+{modal_y}"

RESPONSIVE = ResponsiveConfig()

ESTADO_COLORES = {
    "Available": "#10b981",
    "In Use": "#3b82f6",
    "On Break": "#f59e0b",
    "On Lunch": "#f97316",
    "Loss": "#ef4444",
    "Damage": "#8b5cf6"
}

# ============================================================================
# CLASE SCANNER SERIAL
# ============================================================================
class SerialScanner:
    def __init__(self, app):
        self.app = app
        self.serial_port = None
        self.is_connected = False
        self.read_thread = None
        self.is_reading = False
        self.auto_scan_enabled = False
        self.current_panel = None
        self.port_name = None
        self.baud_rate = 9600
        
    def find_ports(self):
        ports = serial.tools.list_ports.comports()
        return [
            {
                "device": port.device,
                "description": port.description or "Unknown device",
                "hwid": port.hwid or "",
            }
            for port in ports
        ]

    def get_port_label(self, port_info):
        description = port_info.get("description", "Unknown device")
        device = port_info.get("device", "")
        hwid = port_info.get("hwid", "")
        label = device
        if description and description != "Unknown device":
            label = f"{device} — {description}"
        if hwid:
            label = f"{label} | {hwid}"
        return label
    
    def connect(self, port_name, baud_rate=9600):
        try:
            self.port_name = port_name
            self.baud_rate = baud_rate
            self.serial_port = serial.Serial(port_name, baud_rate, timeout=1)
            self.is_connected = True
            self.start_reading()
            return True
        except Exception as e:
            print(f"Error conectando: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        self.is_reading = False
        self.auto_scan_enabled = False
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=2)
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.is_connected = False
        self.port_name = None
        self.baud_rate = 9600
    
    def start_reading(self):
        self.is_reading = True
        self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
        self.read_thread.start()
    
    def _read_loop(self):
        while self.is_reading and self.is_connected:
            try:
                if self.serial_port and self.serial_port.is_open and self.serial_port.in_waiting > 0:
                    data = self.serial_port.readline().decode('utf-8').strip()
                    if data and self.auto_scan_enabled:
                        serial_data = ''.join(c for c in data if c.isalnum()).upper()
                        if len(serial_data) >= 6:
                            self.app.after(0, self.app.process_serial_data, serial_data)
            except Exception as e:
                print(f"Error leyendo: {e}")
                break
    
    def enable_auto_scan(self, panel_name):
        self.auto_scan_enabled = True
        self.current_panel = panel_name
    
    def disable_auto_scan(self):
        self.auto_scan_enabled = False
        self.current_panel = None

# ============================================================================
# CLASE PRINCIPAL
# ============================================================================
class YubiDash(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Yubikey Management Dashboard - WFM System")
        self.geometry(RESPONSIVE.get_window_size())
        self.minsize(1100, 650)
        self.configure(fg_color=MIDNIGHT_BLUE)
        self.resizable(True, True)
        
        self.screen_width = RESPONSIVE.screen_width
        self.screen_height = RESPONSIVE.screen_height
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.current_sidebar_width = RESPONSIVE.get_sidebar_width()
        self.bind("<Configure>", self.on_window_resize)
        
        self.scanner = SerialScanner(self)
        self.current_panel_name = None
        self.scanner_active = False
        self.pending_scanner_panel = None
        
        self.initialize_database()
        self.setup_ui()
        
        dispositivo = "💻 Laptop" if RESPONSIVE.is_laptop else "🖥️ Desktop"
        print(f"✓ YubiDash iniciado - {dispositivo} ({self.screen_width}x{self.screen_height})")

    def on_window_resize(self, event):
        if event.widget == self:
            nuevo_ancho = RESPONSIVE.get_sidebar_width()
            if nuevo_ancho != self.current_sidebar_width:
                self.sidebar.configure(width=nuevo_ancho)
                self.current_sidebar_width = nuevo_ancho

    def setup_ui(self):
        # ====================================================================
        # BARRA LATERAL
        # ====================================================================
        self.sidebar = ctk.CTkFrame(self, width=self.current_sidebar_width, 
                                   corner_radius=0, fg_color=SLATE_GRAY)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        
        title_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        title_frame.pack(pady=20, padx=15, fill="x")
        
        ctk.CTkLabel(title_frame, text="🔐 WFM SYSTEM", 
                    font=("Inter", RESPONSIVE.get_font_size(22), "bold"),
                    text_color="#38bdf8").pack()
        
        ctk.CTkLabel(title_frame, text="YubiKey Manager", 
                    font=("Inter", 11),
                    text_color="#94a3b8").pack()
        
        self.status_frame = ctk.CTkFrame(self.sidebar, fg_color="#0f172a", 
                                        corner_radius=10, border_width=1,
                                        border_color="#334155")
        self.status_frame.pack(pady=15, padx=15, fill="x")
        
        status_header = ctk.CTkFrame(self.status_frame, fg_color="transparent")
        status_header.pack(fill="x", padx=10, pady=5)
        
        self.status_dot = ctk.CTkLabel(status_header, text="🔴", 
                                      font=("Segoe UI", 16))
        self.status_dot.pack(side="left", padx=5)
        
        ctk.CTkLabel(status_header, text="Scanner Status", 
                    font=("Inter", 11, "bold"), 
                    text_color="#94a3b8").pack(side="left", padx=5)
        
        self.status_label = ctk.CTkLabel(self.status_frame, 
                                        text="Desconectado", 
                                        font=("Inter", RESPONSIVE.get_font_size(12), "bold"), 
                                        text_color="#ef4444")
        self.status_label.pack(pady=8)
        
        self.btn_config_port = ctk.CTkButton(self.status_frame,
                                            text="🔌 Configurar",
                                            command=self.show_port_config,
                                            fg_color="#475569",
                                            hover_color="#64748b",
                                            font=("Inter", 11),
                                            height=30,
                                            width=100,
                                            corner_radius=8)
        self.btn_config_port.pack(pady=8)
        
        btn_config = {
            "corner_radius": 10,
            "height": 42,
            "font": ("Inter", RESPONSIVE.get_font_size(13), "bold")
        }
        
        ctk.CTkLabel(self.sidebar, text="MAIN MENU", 
                    font=("Inter", 11, "bold"),
                    text_color="#64748b").pack(pady=(15, 5), padx=15, anchor="w")
        
        self.btn_nueva = ctk.CTkButton(self.sidebar, text="📝 Register New", 
                                       command=self.show_nueva_panel,
                                       fg_color="#3b82f6", hover_color="#2563eb",
                                       **btn_config)
        self.btn_nueva.pack(pady=4, padx=15, fill="x")
        
        self.btn_ingreso = ctk.CTkButton(self.sidebar, text="⏸️ Break/Lunch", 
                                         command=self.show_ingreso_panel,
                                         fg_color="#f59e0b", hover_color="#d97706",
                                         **btn_config)
        self.btn_ingreso.pack(pady=4, padx=15, fill="x")
        
        self.btn_asignacion = ctk.CTkButton(self.sidebar, text="🔄 Assign/Return", 
                                            command=self.show_asignacion_panel,
                                            fg_color="#8b5cf6", hover_color="#7c3aed",
                                            **btn_config)
        self.btn_asignacion.pack(pady=4, padx=15, fill="x")
        
        self.btn_perdida = ctk.CTkButton(self.sidebar, text="⚠️ Loss/Damage", 
                                         command=self.show_perdida_panel,
                                         fg_color="#ef4444", hover_color="#dc2626",
                                         **btn_config)
        self.btn_perdida.pack(pady=4, padx=15, fill="x")
        
        ctk.CTkLabel(self.sidebar, text="DATA & REPORTS", 
                    font=("Inter", 11, "bold"),
                    text_color="#64748b").pack(pady=(20, 5), padx=15, anchor="w")
        
        self.btn_inv = ctk.CTkButton(self.sidebar, text="📋 INVENTORY", 
                                     fg_color="#1e293b", hover_color="#334155",
                                     border_width=1, border_color="#475569",
                                     command=self.show_inv_view, **btn_config)
        self.btn_inv.pack(pady=4, padx=15, fill="x")
        
        self.btn_report = ctk.CTkButton(self.sidebar, text="📊 REPORTS", 
                                        fg_color="#1e293b", hover_color="#334155",
                                        border_width=1, border_color="#475569",
                                        command=self.show_report_view, **btn_config)
        self.btn_report.pack(pady=4, padx=15, fill="x")
        
        # ====================================================================
        # ÁREA PRINCIPAL
        # ====================================================================
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
        
        self.setup_all_panels()
        self.show_nueva_panel()

    def setup_all_panels(self):
        self.setup_nueva_panel()
        self.setup_ingreso_panel()
        self.setup_asignacion_panel()
        self.setup_perdida_panel()
        self.setup_inv_view()
        self.setup_report_view()

    def hide_all_panels(self):
        for panel in [self.panel_nueva, self.panel_ingreso, self.panel_asignacion, 
                      self.panel_perdida, self.view_inv, self.view_report]:
            panel.pack_forget()

    # ========================================================================
    # PANEL DE REPORTES MEJORADO (HERMOSO)
    # ========================================================================
    def setup_report_view(self):
        # Header principal
        header_frame = ctk.CTkFrame(self.view_report, fg_color="transparent")
        header_frame.pack(fill="x", padx=50, pady=(30, 20))
        
        ctk.CTkLabel(header_frame, text="📊 Incident Reports & Analytics", 
                    font=("Inter", RESPONSIVE.get_font_size(36), "bold"), 
                    text_color="#38bdf8").pack()
        
        ctk.CTkLabel(header_frame, text="Track losses, damages, and system statistics", 
                    font=("Inter", 14),
                    text_color="#94a3b8").pack(pady=8)
        
        # Tabs mejorados
        self.report_tabs = ctk.CTkTabview(self.view_report, corner_radius=15,
                                         fg_color="transparent",
                                         border_width=0)
        self.report_tabs.pack(fill="both", expand=True, padx=50, pady=20)
        
        # Configurar apariencia de tabs
        self.report_tabs._segmented_button.configure(
            fg_color="#1e293b",
            selected_color="#3b82f6",
            selected_hover_color="#2563eb",
            unselected_color="#1e293b",
            unselected_hover_color="#334155",
            corner_radius=10,
            height=35
        )
        
        self.tab_loss = self.report_tabs.add("  🔴 Loss  ")
        self.tab_damage = self.report_tabs.add("  🟣 Damage  ")
        self.tab_summary = self.report_tabs.add("  📈 Summary  ")
        
        # Configurar cada tab
        self.setup_loss_report_tab_beautiful()
        self.setup_damage_report_tab_beautiful()
        self.setup_summary_tab_beautiful()

    def setup_loss_report_tab_beautiful(self):
        """Configuración hermosa para la pestaña de pérdidas"""
        
        # Tarjeta de estadísticas principal
        stats_card = ctk.CTkFrame(self.tab_loss, fg_color=REPORT_COLORS["loss_bg"],
                                 corner_radius=20, border_width=2,
                                 border_color=REPORT_COLORS["loss_border"])
        stats_card.pack(fill="x", padx=40, pady=25)
        
        # Contenido de la tarjeta
        ctk.CTkLabel(stats_card, text="🔴 Total Lost Yubikeys", 
                    font=("Inter", RESPONSIVE.get_font_size(18), "bold"),
                    text_color="white").pack(pady=(20, 10))
        
        self.loss_count_label = ctk.CTkLabel(stats_card, text="0", 
                                            font=("Inter", RESPONSIVE.get_font_size(72), "bold"),
                                            text_color=REPORT_COLORS["loss_text"])
        self.loss_count_label.pack(pady=10)
        
        ctk.CTkLabel(stats_card, text="yubikeys reported as lost", 
                    font=("Inter", 14),
                    text_color=REPORT_COLORS["loss_text"]).pack(pady=(0, 20))
        
        # Tabla hermosa
        table_card = ctk.CTkFrame(self.tab_loss, fg_color=REPORT_COLORS["card_bg"],
                                 corner_radius=15, border_width=1,
                                 border_color=REPORT_COLORS["card_border"])
        table_card.pack(fill="both", expand=True, padx=40, pady=20)
        
        # Header de la tabla
        table_header = ctk.CTkFrame(table_card, fg_color="transparent")
        table_header.pack(fill="x", padx=25, pady=(20, 15))
        
        ctk.CTkLabel(table_header, text="📋 Lost Yubikeys List", 
                    font=("Inter", RESPONSIVE.get_font_size(20), "bold"),
                    text_color=REPORT_COLORS["loss_text"]).pack()
        
        # Frame para la tabla con scroll
        tree_frame = ctk.CTkFrame(table_card, fg_color=REPORT_COLORS["table_header"],
                                 corner_radius=10, border_width=1,
                                 border_color=REPORT_COLORS["table_border"])
        tree_frame.pack(fill="both", expand=True, padx=25, pady=(0, 25))
        
        # Columnas
        loss_cols = ("Serial", "User", "Pipkins", "Date", "Time")
        self.loss_tree = ttk.Treeview(tree_frame, columns=loss_cols,
                                     show='headings', height=12)
        
        # Estilo personalizado de la tabla
        style = ttk.Style()
        style.configure('Loss.Treeview',
                       font=('Inter', 12),
                       rowheight=40,
                       background=REPORT_COLORS["table_row"],
                       fieldbackground=REPORT_COLORS["table_row"],
                       foreground=REPORT_COLORS["table_text"],
                       borderwidth=0)
        
        style.configure('Loss.Treeview.Heading',
                       font=('Inter', 13, 'bold'),
                       background=REPORT_COLORS["table_header"],
                       foreground=REPORT_COLORS["loss_text"],
                       borderwidth=0)
        
        style.map('Loss.Treeview',
                 background=[('selected', REPORT_COLORS["loss_bg"])],
                 foreground=[('selected', 'white')])
        
        # Configurar columnas
        col_widths = {"Serial": 150, "User": 200, "Pipkins": 120, "Date": 130, "Time": 100}
        for col in loss_cols:
            self.loss_tree.heading(col, text=col, anchor="w")
            self.loss_tree.column(col, anchor="w", width=col_widths.get(col, 150), minwidth=100)
        
        # Scrollbars
        scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.loss_tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.loss_tree.xview)
        self.loss_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        self.loss_tree.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        scrollbar_y.grid(row=0, column=1, sticky="ns", pady=2)
        scrollbar_x.grid(row=1, column=0, sticky="ew", padx=2)
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Botón de exportar
        ctk.CTkButton(self.tab_loss, text="📥 Export to CSV",
                     command=self.export_loss_report,
                     fg_color="#ef4444", hover_color="#dc2626",
                     font=("Inter", RESPONSIVE.get_font_size(14), "bold"),
                     height=45, width=220, corner_radius=12).pack(pady=20)

    def setup_damage_report_tab_beautiful(self):
        """Configuración hermosa para la pestaña de daños"""
        
        # Tarjeta de estadísticas principal
        stats_card = ctk.CTkFrame(self.tab_damage, fg_color=REPORT_COLORS["damage_bg"],
                                 corner_radius=20, border_width=2,
                                 border_color=REPORT_COLORS["damage_border"])
        stats_card.pack(fill="x", padx=40, pady=25)
        
        ctk.CTkLabel(stats_card, text="🟣 Total Damaged Yubikeys",
                    font=("Inter", RESPONSIVE.get_font_size(18), "bold"),
                    text_color="white").pack(pady=(20, 10))
        
        self.damage_count_label = ctk.CTkLabel(stats_card, text="0",
                                              font=("Inter", RESPONSIVE.get_font_size(72), "bold"),
                                              text_color=REPORT_COLORS["damage_text"])
        self.damage_count_label.pack(pady=10)
        
        ctk.CTkLabel(stats_card, text="yubikeys reported as damaged",
                    font=("Inter", 14),
                    text_color=REPORT_COLORS["damage_text"]).pack(pady=(0, 20))
        
        # Tabla hermosa
        table_card = ctk.CTkFrame(self.tab_damage, fg_color=REPORT_COLORS["card_bg"],
                                 corner_radius=15, border_width=1,
                                 border_color=REPORT_COLORS["card_border"])
        table_card.pack(fill="both", expand=True, padx=40, pady=20)
        
        table_header = ctk.CTkFrame(table_card, fg_color="transparent")
        table_header.pack(fill="x", padx=25, pady=(20, 15))
        
        ctk.CTkLabel(table_header, text="📋 Damaged Yubikeys List",
                    font=("Inter", RESPONSIVE.get_font_size(20), "bold"),
                    text_color=REPORT_COLORS["damage_text"]).pack()
        
        tree_frame = ctk.CTkFrame(table_card, fg_color=REPORT_COLORS["table_header"],
                                 corner_radius=10, border_width=1,
                                 border_color=REPORT_COLORS["table_border"])
        tree_frame.pack(fill="both", expand=True, padx=25, pady=(0, 25))
        
        damage_cols = ("Serial", "User", "Pipkins", "Date", "Time")
        self.damage_tree = ttk.Treeview(tree_frame, columns=damage_cols,
                                       show='headings', height=12)
        
        style = ttk.Style()
        style.configure('Damage.Treeview',
                       font=('Inter', 12),
                       rowheight=40,
                       background=REPORT_COLORS["table_row"],
                       fieldbackground=REPORT_COLORS["table_row"],
                       foreground=REPORT_COLORS["table_text"],
                       borderwidth=0)
        
        style.configure('Damage.Treeview.Heading',
                       font=('Inter', 13, 'bold'),
                       background=REPORT_COLORS["table_header"],
                       foreground=REPORT_COLORS["damage_text"],
                       borderwidth=0)
        
        style.map('Damage.Treeview',
                 background=[('selected', REPORT_COLORS["damage_bg"])],
                 foreground=[('selected', 'white')])
        
        col_widths = {"Serial": 150, "User": 200, "Pipkins": 120, "Date": 130, "Time": 100}
        for col in damage_cols:
            self.damage_tree.heading(col, text=col, anchor="w")
            self.damage_tree.column(col, anchor="w", width=col_widths.get(col, 150), minwidth=100)
        
        scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.damage_tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.damage_tree.xview)
        self.damage_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        self.damage_tree.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        scrollbar_y.grid(row=0, column=1, sticky="ns", pady=2)
        scrollbar_x.grid(row=1, column=0, sticky="ew", padx=2)
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkButton(self.tab_damage, text="📥 Export to CSV",
                     command=self.export_damage_report,
                     fg_color="#8b5cf6", hover_color="#7c3aed",
                     font=("Inter", RESPONSIVE.get_font_size(14), "bold"),
                     height=45, width=220, corner_radius=12).pack(pady=20)

    def setup_summary_tab_beautiful(self):
        """Configuración hermosa para la pestaña de resumen"""
        
        # Stats superiores en tarjetas
        top_stats_frame = ctk.CTkFrame(self.tab_summary, fg_color="transparent")
        top_stats_frame.pack(fill="x", padx=40, pady=25)
        
        # Tarjeta de pérdidas
        loss_card = ctk.CTkFrame(top_stats_frame, fg_color=REPORT_COLORS["loss_bg"],
                                corner_radius=20, border_width=2,
                                border_color=REPORT_COLORS["loss_border"])
        loss_card.pack(side="left", fill="both", expand=True, padx=15)
        
        ctk.CTkLabel(loss_card, text="🔴 Total Losses",
                    font=("Inter", RESPONSIVE.get_font_size(18), "bold"),
                    text_color="white").pack(pady=(20, 10))
        
        self.summary_loss_label = ctk.CTkLabel(loss_card, text="0",
                                              font=("Inter", RESPONSIVE.get_font_size(56), "bold"),
                                              text_color="white")
        self.summary_loss_label.pack(pady=10)
        
        # Tarjeta de daños
        damage_card = ctk.CTkFrame(top_stats_frame, fg_color=REPORT_COLORS["damage_bg"],
                                  corner_radius=20, border_width=2,
                                  border_color=REPORT_COLORS["damage_border"])
        damage_card.pack(side="left", fill="both", expand=True, padx=15)
        
        ctk.CTkLabel(damage_card, text="🟣 Total Damages",
                    font=("Inter", RESPONSIVE.get_font_size(18), "bold"),
                    text_color="white").pack(pady=(20, 10))
        
        self.summary_damage_label = ctk.CTkLabel(damage_card, text="0",
                                                font=("Inter", RESPONSIVE.get_font_size(56), "bold"),
                                                text_color="white")
        self.summary_damage_label.pack(pady=10)
        
        # Tarjeta de total
        total_card = ctk.CTkFrame(top_stats_frame, fg_color=REPORT_COLORS["summary_bg"],
                                 corner_radius=20, border_width=2,
                                 border_color=REPORT_COLORS["summary_border"])
        total_card.pack(side="left", fill="both", expand=True, padx=15)
        
        ctk.CTkLabel(total_card, text="📋 Total Incidents",
                    font=("Inter", RESPONSIVE.get_font_size(18), "bold"),
                    text_color="white").pack(pady=(20, 10))
        
        self.summary_total_label = ctk.CTkLabel(total_card, text="0",
                                               font=("Inter", RESPONSIVE.get_font_size(56), "bold"),
                                               text_color="white")
        self.summary_total_label.pack(pady=10)
        
        # Tarjeta de estadísticas de inventario
        inv_stats_card = ctk.CTkFrame(self.tab_summary, fg_color=REPORT_COLORS["card_bg"],
                                     corner_radius=20, border_width=1,
                                     border_color=REPORT_COLORS["card_border"])
        inv_stats_card.pack(fill="both", expand=True, padx=40, pady=25)
        
        ctk.CTkLabel(inv_stats_card, text="📦 Inventory Statistics by State",
                    font=("Inter", RESPONSIVE.get_font_size(22), "bold"),
                    text_color="#38bdf8").pack(pady=(25, 15))
        
        self.summary_text = ctk.CTkTextbox(inv_stats_card,
                                          font=("Inter", RESPONSIVE.get_font_size(14)),
                                          fg_color=REPORT_COLORS["table_header"],
                                          border_width=0,
                                          corner_radius=12,
                                          text_color=REPORT_COLORS["table_text"])
        self.summary_text.pack(fill="both", expand=True, padx=25, pady=20)

    # ========================================================================
    # MODAL DE CONFIGURACIÓN DE PUERTO CON SCROLL
    # ========================================================================
    def show_port_config(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Serial Port Configuration")
        
        modal_width = 550 if not RESPONSIVE.is_laptop else 450
        modal_height = 500 if not RESPONSIVE.is_laptop else 450
        modal.geometry(RESPONSIVE.center_modal(self, modal_width, modal_height))
        modal.minsize(450, 400)
        
        modal.grab_set()

        def close_modal():
            if not self.scanner.is_connected:
                self.pending_scanner_panel = None
            modal.destroy()

        modal.protocol("WM_DELETE_WINDOW", close_modal)
        
        main_frame = ctk.CTkFrame(modal, fg_color=SLATE_GRAY, corner_radius=15,
                                 border_width=1, border_color="#334155")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        scrollable_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent",
                                                 corner_radius=10)
        scrollable_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        ctk.CTkLabel(scrollable_frame, text="🔌 Serial Port Configuration",
                    font=("Inter", RESPONSIVE.get_font_size(20), "bold"),
                    text_color="#38bdf8").pack(pady=15)

        current_port_text = "🔴 Not connected"
        current_port_color = "#ef4444"
        if self.scanner.is_connected and self.scanner.port_name:
            current_port_text = f"🟢 Connected to {self.scanner.port_name} @ {self.scanner.baud_rate} baud"
            current_port_color = SUCCESS_GREEN

        ctk.CTkLabel(scrollable_frame, text=current_port_text,
                    font=("Inter", 13, "bold"),
                    text_color=current_port_color,
                    wraplength=420,
                    justify="center").pack(pady=(0, 10))
        
        current_frame = ctk.CTkFrame(scrollable_frame, fg_color="#0f172a", corner_radius=10)
        current_frame.pack(fill="x", padx=20, pady=15)
        
        if self.scanner.is_connected:
            status_text = f"✅ Connected: {self.scanner.port_name} @ {self.scanner.baud_rate} baud"
            status_color = SUCCESS_GREEN
        else:
            status_text = "🔴 Not Connected"
            status_color = "#ef4444"
        
        ctk.CTkLabel(current_frame, text="Current Status:",
                    font=("Inter", 12, "bold"),
                    text_color="#94a3b8").pack(anchor="w", padx=15, pady=(10, 5))
        
        ctk.CTkLabel(current_frame, text=status_text,
                    font=("Inter", 14, "bold"),
                    text_color=status_color,
                    wraplength=400).pack(anchor="w", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(scrollable_frame, text="Available Ports:",
                    font=("Inter", 12, "bold"),
                    text_color="#94a3b8").pack(anchor="w", padx=20, pady=(15, 5))

        ports_count_label = ctk.CTkLabel(scrollable_frame, text="Detected ports: 0",
                        font=("Inter", 11),
                        text_color="#64748b")
        ports_count_label.pack(anchor="w", padx=20, pady=(0, 5))
        
        ports_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        ports_frame.pack(fill="x", padx=20)

        port_var = ctk.StringVar()
        port_widgets = []

        def rebuild_port_list():
            for widget in port_widgets:
                widget.destroy()
            port_widgets.clear()

            ports = self.scanner.find_ports()
            ports_count_label.configure(text=f"Detected ports: {len(ports)}")
            if not ports:
                port_var.set("")
                ctk.CTkLabel(ports_frame, text="⚠️ No serial ports found",
                            font=("Inter", 12),
                            text_color="#f59e0b",
                            wraplength=400).pack(anchor="w", pady=6)
                return ports

            selected_device = self.scanner.port_name if self.scanner.port_name else ports[0]["device"]
            if selected_device not in [p["device"] for p in ports]:
                selected_device = ports[0]["device"]
            port_var.set(selected_device)

            for port in ports:
                radio = ctk.CTkRadioButton(
                    ports_frame,
                    text=self.scanner.get_port_label(port),
                    variable=port_var,
                    value=port["device"],
                    font=("Inter", 13)
                )
                radio.pack(anchor="w", pady=3)
                port_widgets.append(radio)

            return ports

        ports = rebuild_port_list()
        
        ctk.CTkLabel(scrollable_frame, text="Baud Rate:",
                    font=("Inter", 12, "bold"),
                    text_color="#94a3b8").pack(anchor="w", padx=20, pady=(15, 5))
        
        baud_var = ctk.StringVar(value=str(self.scanner.baud_rate if self.scanner.baud_rate else 9600))
        baud_rates = ["4800", "9600", "14400", "19200", "38400", "57600", "115200", "230400", "250000"]
        
        baud_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        baud_frame.pack(fill="x", padx=20)
        
        for i, baud in enumerate(baud_rates):
            ctk.CTkRadioButton(baud_frame, text=baud, variable=baud_var, value=baud,
                             font=("Inter", 12)).grid(row=i//3, column=i%3, padx=10, pady=3)

        ctk.CTkLabel(scrollable_frame, text="Tip: use the baud rate required by your scanner or Arduino.",
                    font=("Inter", 11),
                    text_color="#64748b",
                    wraplength=430,
                    justify="left").pack(anchor="w", padx=20, pady=(8, 0))
        
        btn_height = 40 if not RESPONSIVE.is_laptop else 35
        btn_width = 130 if not RESPONSIVE.is_laptop else 110
        
        def connect_selected():
            if ports:
                port = port_var.get()
                baud = int(baud_var.get())
                
                if self.scanner.is_connected:
                    self.scanner.disconnect()
                
                if self.scanner.connect(port, baud):
                    self.update_scanner_status(True, port)
                    self.show_message("✅ Connected",
                                    f"Connected to {port} @ {baud} baud",
                                    "success")
                    if self.pending_scanner_panel:
                        panel = self.pending_scanner_panel
                        self.pending_scanner_panel = None
                        self.scanner.enable_auto_scan(panel)
                        self.scanner_active = True
                        self.current_panel_name = panel
                        self.update_scanner_buttons_state()
                        self.show_message("📡 Scanner Active",
                                        f"Scanning on panel: {panel.upper()}\n\nPoint the scanner now",
                                        "success")
                    modal.destroy()
                else:
                    self.show_message("❌ Connection Error",
                                    f"Could not connect to {port}",
                                    "error")
            else:
                self.show_message("⚠️ No Ports", "No serial ports available", "warning")

        def refresh_ports():
            nonlocal ports
            ports = rebuild_port_list()
        
        btn_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="✅ Connect", command=connect_selected,
                     fg_color="#38bdf8", hover_color="#0ea5e9",
                     font=("Inter", RESPONSIVE.get_font_size(14), "bold"),
                     width=btn_width, height=btn_height, corner_radius=10).pack(side="left", padx=10)

        ctk.CTkButton(btn_frame, text="🔄 Refresh", command=refresh_ports,
                     fg_color="#64748b", hover_color="#475569",
                     font=("Inter", RESPONSIVE.get_font_size(13)),
                     width=btn_width, height=btn_height, corner_radius=10).pack(side="left", padx=10)
        
        ctk.CTkButton(btn_frame, text="Close", command=close_modal,
                     fg_color="#475569", hover_color="#64748b",
                     font=("Inter", RESPONSIVE.get_font_size(13)),
                     width=btn_width-30, height=btn_height, corner_radius=10).pack(side="left", padx=10)

    def toggle_scanner(self, panel):
        if not self.scanner.is_connected:
            self.pending_scanner_panel = panel
            self.show_port_config()
        else:
            if self.scanner_active:
                self.scanner.disable_auto_scan()
                self.scanner_active = False
                self.update_scanner_buttons_state()
                self.show_message("⏹️ Scanner Stopped",
                                "Scanner has been deactivated",
                                "info")
            else:
                self.scanner.enable_auto_scan(panel)
                self.scanner_active = True
                self.pending_scanner_panel = None
                self.current_panel_name = panel
                self.update_scanner_buttons_state()
                self.show_message("📡 Scanner Active",
                                f"Scanning on panel: {panel.upper()}\n\nPoint the scanner now",
                                "success")

    def update_scanner_buttons_state(self):
        if self.scanner_active:
            btn_text = "⏹️ Stop Scanner"
            btn_color = "#ef4444"
            hover_color = "#dc2626"
        else:
            btn_text = "📡 Activate Scanner"
            btn_color = "#3b82f6"
            hover_color = "#2563eb"
        
        for panel_name in ['nueva', 'ingreso', 'asignacion', 'perdida']:
            btn_attr = f"btn_scan_{panel_name}"
            if hasattr(self, btn_attr):
                btn = getattr(self, btn_attr)
                btn.configure(text=btn_text, fg_color=btn_color, hover_color=hover_color)

    def process_serial_data(self, serial_data):
        if not serial_data:
            return

        panel = self.scanner.current_panel or self.current_panel_name
        if not panel:
            return

        if panel == 'nueva' and hasattr(self, 'entry_nueva'):
            self.entry_nueva.delete(0, 'end')
            self.entry_nueva.insert(0, serial_data)
            self.on_register_submit()
        elif panel == 'ingreso' and hasattr(self, 'entry_ingreso'):
            self.entry_ingreso.delete(0, 'end')
            self.entry_ingreso.insert(0, serial_data)
            self.process_break_lunch_scan()
        elif panel == 'asignacion' and hasattr(self, 'entry_asignacion'):
            self.entry_asignacion.delete(0, 'end')
            self.entry_asignacion.insert(0, serial_data)
            self.process_assign_return_scan()
        elif panel == 'perdida' and hasattr(self, 'entry_perdida'):
            self.entry_perdida.delete(0, 'end')
            self.entry_perdida.insert(0, serial_data)
            self.process_loss_damage_scan()

    def update_scanner_status(self, connected, port_name=""):
        if connected:
            self.status_dot.configure(text="🟢")
            self.status_label.configure(text=f"Connected\n{port_name}",
                                       text_color=SUCCESS_GREEN)
            self.btn_config_port.configure(text="🔌 Disconnect",
                                          command=self.disconnect_scanner,
                                          fg_color="#ef4444",
                                          hover_color="#dc2626")
        else:
            self.status_dot.configure(text="🔴")
            self.status_label.configure(text="Disconnected", text_color="#ef4444")
            self.btn_config_port.configure(text="🔌 Configure",
                                          command=self.show_port_config,
                                          fg_color="#475569",
                                          hover_color="#64748b")
            self.scanner_active = False
            self.update_scanner_buttons_state()

    def disconnect_scanner(self):
        if self.scanner.is_connected:
            self.scanner.disconnect()
            self.pending_scanner_panel = None
            self.update_scanner_status(False)
            self.show_message("🔌 Disconnected", "Scanner disconnected", "info")

    # ========================================================================
    # MODAL CON SCROLL PARA VER DETALLES COMPLETOS CON HISTORIAL
    # ========================================================================
    def show_item_details(self):
        selected = self.inv_tree.selection()
        if not selected:
            self.show_message("⚠️ Select Item", "Please select a yubikey from the table", "warning")
            return
        
        item = self.inv_tree.item(selected[0])
        serial = item['values'][0]
        
        yubi_data = self.find_yubikey(serial)
        if not yubi_data:
            return
        
        modal = ctk.CTkToplevel(self)
        modal.title(f"📱 Details - {serial}")
        
        modal_width = 800 if not RESPONSIVE.is_laptop else 650
        modal_height = 650 if not RESPONSIVE.is_laptop else 550
        modal.geometry(RESPONSIVE.center_modal(self, modal_width, modal_height))
        modal.minsize(600, 500)
        
        modal.grab_set()
        
        main_frame = ctk.CTkFrame(modal, fg_color=SLATE_GRAY, corner_radius=18,
                                 border_width=1, border_color="#334155")
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        scrollable_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent",
                                                 corner_radius=10)
        scrollable_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        ctk.CTkLabel(scrollable_frame, text=f"📱 {serial}",
                    font=("Inter", RESPONSIVE.get_font_size(28), "bold"),
                    text_color="#38bdf8").pack(pady=15)
        
        info_card = ctk.CTkFrame(scrollable_frame, fg_color="#0f172a", corner_radius=12,
                                border_width=2, border_color=ESTADO_COLORES.get(yubi_data['estado'], "#64748b"))
        info_card.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(info_card, text="📊 Current Information",
                    font=("Inter", RESPONSIVE.get_font_size(16), "bold"),
                    text_color="#38bdf8").pack(pady=(15, 10))
        
        info_text = f"""
        🔹 State: {yubi_data['estado']}
        🔹 User: {yubi_data.get('usuario', 'N/A') or 'N/A'}
        🔹 Pipkins Code: {yubi_data.get('codigo_pipkins', 'N/A') or 'N/A'}
        🔹 Last Connection: {yubi_data.get('ultima_conexion', 'N/A')}
        🔹 Total History Records: {len(yubi_data.get('historial', []))}
        """
        
        ctk.CTkLabel(info_card, text=info_text,
                    font=("Inter", RESPONSIVE.get_font_size(13)),
                    text_color="#e2e8f0",
                    justify="left").pack(pady=15, padx=20)
        
        ctk.CTkLabel(scrollable_frame, text="📜 Complete History Timeline",
                    font=("Inter", RESPONSIVE.get_font_size(20), "bold"),
                    text_color="#38bdf8").pack(pady=(20, 15))
        
        historial = yubi_data.get('historial', [])
        
        if not historial:
            ctk.CTkLabel(scrollable_frame, text="No history registered",
                        font=("Inter", 13),
                        text_color="#94a3b8").pack(pady=20)
        else:
            for i, h in enumerate(reversed(historial)):
                event_card = ctk.CTkFrame(scrollable_frame, fg_color="#1e293b",
                                         corner_radius=10, border_width=1,
                                         border_color="#334155")
                event_card.pack(fill="x", pady=8, padx=20)
                
                header_frame = ctk.CTkFrame(event_card, fg_color="transparent")
                header_frame.pack(fill="x", padx=15, pady=(12, 8))
                
                action_icon = self.get_action_icon(h['accion'])
                ctk.CTkLabel(header_frame, text=f"{action_icon} {h['accion']}",
                            font=("Inter", RESPONSIVE.get_font_size(14), "bold"),
                            text_color=ESTADO_COLORES.get(h['estado'], "#38bdf8")).pack(side="left")
                
                datetime_text = f"📅 {h['fecha']}  ⏰ {h['hora']}"
                ctk.CTkLabel(header_frame, text=datetime_text,
                            font=("Inter", 11),
                            text_color="#94a3b8").pack(side="right")
                
                ctk.CTkFrame(event_card, height=1, fg_color="#334155").pack(fill="x", padx=15, pady=5)
                
                details_frame = ctk.CTkFrame(event_card, fg_color="transparent")
                details_frame.pack(fill="x", padx=15, pady=8)
                
                if h.get('usuario'):
                    ctk.CTkLabel(details_frame, text=f"👤 User: {h['usuario']}",
                                font=("Inter", 12),
                                text_color="#cbd5e1").pack(anchor="w", pady=2)
                
                if h.get('codigo_pipkins'):
                    ctk.CTkLabel(details_frame, text=f"🔢 Pipkins: {h['codigo_pipkins']}",
                                font=("Inter", 12),
                                text_color="#cbd5e1").pack(anchor="w", pady=2)
                
                ctk.CTkLabel(details_frame, text=f"📌 State: {h['estado']}",
                            font=("Inter", 12, "bold"),
                            text_color=ESTADO_COLORES.get(h['estado'], "#94a3b8")).pack(anchor="w", pady=5)
                
                if h.get('comentario'):
                    comment_frame = ctk.CTkFrame(event_card, fg_color="#0f172a", corner_radius=8)
                    comment_frame.pack(fill="x", padx=15, pady=8)
                    ctk.CTkLabel(comment_frame, text=f"💬 {h['comentario']}",
                                font=("Inter", 11),
                                text_color="#fbbf24",
                                wraplength=550,
                                justify="left").pack(padx=12, pady=8)
        
        ctk.CTkButton(scrollable_frame, text="Close", command=modal.destroy,
                     fg_color="#475569", hover_color="#64748b",
                     font=("Inter", RESPONSIVE.get_font_size(14), "bold"),
                     width=150, height=40, corner_radius=10).pack(pady=20)

    def get_action_icon(self, action):
        icons = {
            "Registro": "🆕",
            "Check-in": "⬇️",
            "Check-out": "⬆️",
            "Assign": "👉",
            "Return": "👈",
            "Loss": "❌",
            "Damage": "⚠️",
            "Break": "☕",
            "Lunch": "🍽️"
        }
        for key, icon in icons.items():
            if key in action:
                return icon
        return "📌"

    def show_current_state_modal(self, serial, usuario, pipkins, estado_actual, action_type,
                                found_by=None, search_value=None):
        modal = ctk.CTkToplevel(self)
        modal.title("Current Status")
        
        modal_width = 600 if not RESPONSIVE.is_laptop else 500
        modal_height = 500 if not RESPONSIVE.is_laptop else 450
        modal.geometry(RESPONSIVE.center_modal(self, modal_width, modal_height))
        modal.minsize(450, 400)
        
        modal.grab_set()
        
        main_frame = ctk.CTkFrame(modal, fg_color=SLATE_GRAY, corner_radius=18,
                                 border_width=1, border_color="#334155")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        scrollable_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent",
                                                 corner_radius=10)
        scrollable_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        if action_type == 'break_lunch':
            title_text = "⏸️ Break/Lunch Check-in/out"
            title_color = "#f59e0b"
        elif action_type == 'assign_return':
            title_text = "🔄 Assign/Return Yubikey"
            title_color = "#8b5cf6"
        elif action_type == 'loss_damage':
            title_text = "⚠️ Loss/Damage Report"
            title_color = "#ef4444"
        else:
            title_text = "📱 Current Yubikey Status"
            title_color = "#38bdf8"
        
        ctk.CTkLabel(scrollable_frame, text=title_text,
                    font=("Inter", RESPONSIVE.get_font_size(22), "bold"),
                    text_color=title_color).pack(pady=15)
        
        info_card = ctk.CTkFrame(scrollable_frame, fg_color="#0f172a", corner_radius=12,
                                border_width=2, border_color=ESTADO_COLORES.get(estado_actual, "#64748b"))
        info_card.pack(fill="x", padx=20, pady=20)
        
        found_info = ""
        if found_by and action_type == 'loss_damage':
            found_info = f"🔍 Found by {found_by}: {search_value}\n\n"
        
        info_text = f"""{found_info}Serial: {serial}
User: {usuario}
Pipkins: {pipkins}

Current State: {estado_actual.upper()}
"""
        
        ctk.CTkLabel(info_card, text=info_text,
                    font=("Inter", RESPONSIVE.get_font_size(14)),
                    text_color="#e2e8f0",
                    justify="center",
                    wraplength=400).pack(pady=20)
        
        if action_type == 'break_lunch':
            if estado_actual in ['On Break', 'On Lunch']:
                msg = f"⚠️ This yubikey is already {estado_actual.upper()}\n\nDo you want to CHECK-OUT (return to In Use)?"
                btn_text = "✅ Check-Out"
                btn_color = "#3b82f6"
            elif estado_actual == 'In Use':
                msg = "✅ Yubikey is currently IN USE\n\nDo you want to check-in to Break or Lunch?"
                btn_text = "✅ Proceed to Break/Lunch"
                btn_color = "#f59e0b"
            else:
                msg = f"❌ Cannot perform break/lunch operation\nCurrent state: {estado_actual}\n\nOnly yubikeys IN USE can check-in to break/lunch."
                btn_text = "Close"
                btn_color = "#475569"
            
            def proceed():
                modal.destroy()
                if estado_actual in ['On Break', 'On Lunch']:
                    self.update_break_lunch_state(serial, 'In Use', check_out=True)
                elif estado_actual == 'In Use':
                    self.ask_break_type(serial)
        
        elif action_type == 'assign_return':
            if estado_actual == 'Available':
                msg = "✅ Yubikey is AVAILABLE\n\nDo you want to ASSIGN to a new user?"
                btn_text = "✅ Assign to User"
                btn_color = "#10b981"
            elif estado_actual in ['In Use', 'On Break', 'On Lunch']:
                msg = f"⚠️ Yubikey is {estado_actual.upper()}\n\nDo you want to RETURN (mark as available)?"
                btn_text = "✅ Return Yubikey"
                btn_color = "#ef4444"
            elif estado_actual in ['Loss', 'Damage']:
                msg = f"❌ Cannot assign/return: state is {estado_actual}\n\nThis yubikey is reported as {estado_actual.upper()}."
                btn_text = "Close"
                btn_color = "#475569"
            else:
                msg = f"⚠️ Unexpected state: {estado_actual}"
                btn_text = "Close"
                btn_color = "#475569"
            
            def proceed():
                modal.destroy()
                if estado_actual == 'Available':
                    self.ask_nuevo_usuario_pipkins(serial)
                elif estado_actual in ['In Use', 'On Break', 'On Lunch']:
                    self.ask_return_comment(serial)
        
        elif action_type == 'loss_damage':
            if estado_actual in ['Loss', 'Damage']:
                msg = f"⚠️ Already in state '{estado_actual}'\n\nThis yubikey is already reported as {estado_actual.upper()}."
                btn_text = "Close"
                btn_color = "#475569"
            else:
                msg = "⚠️ Report incident for this yubikey\n\nSelect the incident type:"
                btn_text = "Continue"
                btn_color = "#ef4444"
            
            def proceed():
                modal.destroy()
                if estado_actual not in ['Loss', 'Damage']:
                    self.ask_loss_damage_type(serial, found_by, search_value)
        
        else:
            msg = f"📌 Current state: {estado_actual}"
            btn_text = "Close"
            btn_color = "#475569"
            
            def proceed():
                modal.destroy()
        
        ctk.CTkLabel(scrollable_frame, text=msg,
                    font=("Inter", RESPONSIVE.get_font_size(13)),
                    text_color="#94a3b8",
                    justify="center",
                    wraplength=450).pack(pady=15)
        
        if btn_text != "Close" or action_type != 'break_lunch':
            ctk.CTkButton(scrollable_frame, text=btn_text, command=proceed,
                         fg_color=btn_color,
                         hover_color="#dc2626" if btn_color == "#ef4444" else
                                   "#059669" if btn_color == "#10b981" else
                                   "#d97706" if btn_color == "#f59e0b" else
                                   "#2563eb" if btn_color == "#3b82f6" else "#64748b",
                         font=("Inter", RESPONSIVE.get_font_size(15), "bold"),
                         width=250, height=45, corner_radius=10).pack(pady=20)
        
        ctk.CTkButton(scrollable_frame, text="Cancel", command=modal.destroy,
                     fg_color="#475569", hover_color="#64748b",
                     font=("Inter", RESPONSIVE.get_font_size(14)),
                     width=120, height=40, corner_radius=10).pack(pady=10)

    def setup_nueva_panel(self):
        header_frame = ctk.CTkFrame(self.panel_nueva, fg_color="transparent")
        header_frame.pack(fill="x", padx=40, pady=(20, 10))
        
        ctk.CTkLabel(header_frame, text="📝 Register New Yubikey",
                    font=("Inter", RESPONSIVE.get_font_size(28), "bold"),
                    text_color="#38bdf8").pack()
        
        ctk.CTkLabel(header_frame, text="Scan or manually enter the yubikey serial number",
                    font=("Inter", 13),
                    text_color="#94a3b8").pack(pady=5)
        
        input_card = ctk.CTkFrame(self.panel_nueva, fg_color=SLATE_GRAY,
                                 corner_radius=15, border_width=1,
                                 border_color="#334155")
        input_card.pack(fill="x", padx=40, pady=20)
        
        input_frame = ctk.CTkFrame(input_card, fg_color="transparent")
        input_frame.pack(fill="x", padx=30, pady=25)
        
        ctk.CTkLabel(input_frame, text="Yubikey Serial:",
                    font=("Inter", RESPONSIVE.get_font_size(16), "bold"),
                    text_color="#e2e8f0").pack(anchor="w", pady=(0, 10))
        
        self.entry_nueva = ctk.CTkEntry(input_frame,
                                       placeholder_text="Type serial or use scanner...",
                                       width=RESPONSIVE.get_entry_width(),
                                       height=50,
                                       font=("Inter", RESPONSIVE.get_font_size(16)),
                                       border_width=2,
                                       border_color=BORDER_DEFAULT,
                                       corner_radius=10)
        self.entry_nueva.pack(fill="x", pady=10)
        self.entry_nueva.bind("<Return>", lambda e: self.on_register_submit())
        
        self.btn_scan_nueva = ctk.CTkButton(input_frame,
                                           text="📡 Activate Scanner",
                                           command=lambda: self.toggle_scanner('nueva'),
                                           fg_color="#3b82f6",
                                           hover_color="#2563eb",
                                           font=("Inter", RESPONSIVE.get_font_size(14), "bold"),
                                           height=45,
                                           corner_radius=10)
        self.btn_scan_nueva.pack(fill="x", pady=15)
        
        self.label_nueva = ctk.CTkLabel(input_card, text="",
                                       font=("Inter", RESPONSIVE.get_font_size(14), "bold"))
        self.label_nueva.pack(pady=15)
        
        self.setup_recent_table_responsive(self.panel_nueva, 'nueva')

    def on_register_submit(self):
        serial = self.entry_nueva.get().strip().upper()
        if not serial:
            self.label_nueva.configure(text="⚠️ Empty field", text_color="#f59e0b")
            return
        
        if self.serial_exists(serial):
            self.label_nueva.configure(text="⚠️ Serial already registered", text_color="#f59e0b")
            return
        
        self.ask_user_and_pipkins(serial)

    def setup_ingreso_panel(self):
        header_frame = ctk.CTkFrame(self.panel_ingreso, fg_color="transparent")
        header_frame.pack(fill="x", padx=40, pady=(20, 10))
        
        ctk.CTkLabel(header_frame, text="⏸️ Break / Lunch Check-in/out",
                    font=("Inter", RESPONSIVE.get_font_size(28), "bold"),
                    text_color="#f59e0b").pack()
        
        ctk.CTkLabel(header_frame, text="Only for yubikeys currently IN USE",
                    font=("Inter", 13),
                    text_color="#94a3b8").pack(pady=5)
        
        input_card = ctk.CTkFrame(self.panel_ingreso, fg_color=SLATE_GRAY,
                                 corner_radius=15, border_width=1,
                                 border_color="#334155")
        input_card.pack(fill="x", padx=40, pady=20)
        
        input_frame = ctk.CTkFrame(input_card, fg_color="transparent")
        input_frame.pack(fill="x", padx=30, pady=25)
        
        ctk.CTkLabel(input_frame, text="Yubikey Serial:",
                    font=("Inter", RESPONSIVE.get_font_size(16), "bold"),
                    text_color="#e2e8f0").pack(anchor="w", pady=(0, 10))
        
        self.entry_ingreso = ctk.CTkEntry(input_frame,
                                         placeholder_text="Type serial or use scanner...",
                                         width=RESPONSIVE.get_entry_width(),
                                         height=50,
                                         font=("Inter", RESPONSIVE.get_font_size(16)),
                                         border_width=2,
                                         border_color=BORDER_DEFAULT,
                                         corner_radius=10)
        self.entry_ingreso.pack(fill="x", pady=10)
        self.entry_ingreso.bind("<Return>", lambda e: self.process_break_lunch_scan())
        
        self.btn_scan_ingreso = ctk.CTkButton(input_frame,
                                             text="📡 Activate Scanner",
                                             command=lambda: self.toggle_scanner('ingreso'),
                                             fg_color="#3b82f6",
                                             hover_color="#2563eb",
                                             font=("Inter", RESPONSIVE.get_font_size(14), "bold"),
                                             height=45,
                                             corner_radius=10)
        self.btn_scan_ingreso.pack(fill="x", pady=15)
        
        self.label_ingreso = ctk.CTkLabel(input_card, text="",
                                         font=("Inter", RESPONSIVE.get_font_size(14), "bold"))
        self.label_ingreso.pack(pady=15)
        
        self.setup_recent_table_responsive(self.panel_ingreso, 'ingreso')

    def process_break_lunch_scan(self):
        serial = self.entry_ingreso.get().strip().upper()
        if not serial:
            self.label_ingreso.configure(text="⚠️ Empty field", text_color="#f59e0b")
            return
        
        item_data = self.find_yubikey(serial)
        if not item_data:
            self.label_ingreso.configure(text="❌ Serial not found", text_color="#ef4444")
            self.after(3000, lambda: self.label_ingreso.configure(text=""))
            return
        
        estado_actual = item_data['estado']
        usuario = item_data.get('usuario', 'N/A') or 'N/A'
        pipkins = item_data.get('codigo_pipkins', 'N/A') or 'N/A'
        
        self.show_current_state_modal(serial, usuario, pipkins, estado_actual, 'break_lunch')

    def update_break_lunch_state(self, serial, tipo_break, check_out=False):
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        for item in datos:
            if item['serial'].upper() == serial.upper():
                now = datetime.now()
                if check_out:
                    item['estado'] = 'In Use'
                    accion = 'Check-out from Break/Lunch'
                else:
                    item['estado'] = f'On {tipo_break}'
                    accion = f'Check-in to {tipo_break}'
                
                item['ultima_conexion'] = now.strftime("%Y-%m-%d")
                item['historial'].append({
                    'accion': accion,
                    'fecha': now.strftime("%Y-%m-%d"),
                    'hora': now.strftime("%H:%M:%S"),
                    'estado': item['estado'],
                    'usuario': item.get('usuario', ''),
                    'codigo_pipkins': item.get('codigo_pipkins', ''),
                    'comentario': accion
                })
                break
        
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)
        
        if check_out:
            msg = f"✅ Checked-out - Back to In Use"
        else:
            msg = f"✅ Check-in to {tipo_break}"
        
        self.label_ingreso.configure(text=msg,
                                    text_color=SUCCESS_GREEN,
                                    font=("Inter", RESPONSIVE.get_font_size(14), "bold"))
        self.entry_ingreso.delete(0, 'end')
        self.load_recent_data('ingreso')
        self.after(3000, lambda: self.label_ingreso.configure(text=""))

    def ask_break_type(self, serial):
        modal = ctk.CTkToplevel(self)
        modal.title("Select Break Type")
        
        modal_width = 450 if not RESPONSIVE.is_laptop else 380
        modal_height = 320 if not RESPONSIVE.is_laptop else 280
        modal.geometry(RESPONSIVE.center_modal(self, modal_width, modal_height))
        modal.minsize(350, 260)
        
        modal.grab_set()
        
        main_frame = ctk.CTkFrame(modal, fg_color=SLATE_GRAY, corner_radius=18,
                                 border_width=1, border_color="#334155")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        scrollable_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent",
                                                 corner_radius=10)
        scrollable_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        ctk.CTkLabel(scrollable_frame, text="⏸️ Change state to?",
                    font=("Inter", RESPONSIVE.get_font_size(20), "bold"),
                    text_color="#38bdf8").pack(pady=20)
        
        tipo_var = ctk.StringVar(value="Break")
        
        options_frame = ctk.CTkFrame(scrollable_frame, fg_color=SLATE_GRAY,
                                    corner_radius=12, border_width=1,
                                    border_color="#334155")
        options_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkRadioButton(options_frame, text="⏸️ Break", variable=tipo_var, value="Break",
                         font=("Inter", RESPONSIVE.get_font_size(16)),
                         fg_color="#f59e0b").pack(anchor="w", padx=25, pady=12)
        ctk.CTkRadioButton(options_frame, text="🍽️ Lunch", variable=tipo_var, value="Lunch",
                         font=("Inter", RESPONSIVE.get_font_size(16)),
                         fg_color="#f97316").pack(anchor="w", padx=25, pady=12)
        
        def confirmar():
            tipo = tipo_var.get()
            self.update_break_lunch_state(serial, tipo)
            modal.destroy()
        
        btn_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="✅ Confirm", command=confirmar,
                     fg_color="#38bdf8", hover_color="#0ea5e9",
                     font=("Inter", RESPONSIVE.get_font_size(15), "bold"),
                     width=150, height=40, corner_radius=10).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Cancel", command=modal.destroy,
                     fg_color="#475569", hover_color="#64748b",
                     font=("Inter", RESPONSIVE.get_font_size(14)),
                     width=120, height=40, corner_radius=10).pack(side="left", padx=10)

    def setup_asignacion_panel(self):
        header_frame = ctk.CTkFrame(self.panel_asignacion, fg_color="transparent")
        header_frame.pack(fill="x", padx=40, pady=(20, 10))
        
        ctk.CTkLabel(header_frame, text="🔄 Assign / Return",
                    font=("Inter", RESPONSIVE.get_font_size(28), "bold"),
                    text_color="#8b5cf6").pack()
        
        ctk.CTkLabel(header_frame, text="Assign available yubikeys or return in-use ones",
                    font=("Inter", 13),
                    text_color="#94a3b8").pack(pady=5)
        
        input_card = ctk.CTkFrame(self.panel_asignacion, fg_color=SLATE_GRAY,
                                 corner_radius=15, border_width=1,
                                 border_color="#334155")
        input_card.pack(fill="x", padx=40, pady=20)
        
        input_frame = ctk.CTkFrame(input_card, fg_color="transparent")
        input_frame.pack(fill="x", padx=30, pady=25)
        
        ctk.CTkLabel(input_frame, text="Yubikey Serial:",
                    font=("Inter", RESPONSIVE.get_font_size(16), "bold"),
                    text_color="#e2e8f0").pack(anchor="w", pady=(0, 10))
        
        self.entry_asignacion = ctk.CTkEntry(input_frame,
                                            placeholder_text="Type serial or use scanner...",
                                            width=RESPONSIVE.get_entry_width(),
                                            height=50,
                                            font=("Inter", RESPONSIVE.get_font_size(16)),
                                            border_width=2,
                                            border_color=BORDER_DEFAULT,
                                            corner_radius=10)
        self.entry_asignacion.pack(fill="x", pady=10)
        self.entry_asignacion.bind("<Return>", lambda e: self.process_assign_return_scan())
        
        self.btn_scan_asignacion = ctk.CTkButton(input_frame,
                                                text="📡 Activate Scanner",
                                                command=lambda: self.toggle_scanner('asignacion'),
                                                fg_color="#3b82f6",
                                                hover_color="#2563eb",
                                                font=("Inter", RESPONSIVE.get_font_size(14), "bold"),
                                                height=45,
                                                corner_radius=10)
        self.btn_scan_asignacion.pack(fill="x", pady=15)
        
        self.label_asignacion = ctk.CTkLabel(input_card, text="",
                                            font=("Inter", RESPONSIVE.get_font_size(14), "bold"))
        self.label_asignacion.pack(pady=15)
        
        self.setup_recent_table_responsive(self.panel_asignacion, 'asignacion')

    def process_assign_return_scan(self):
        serial = self.entry_asignacion.get().strip().upper()
        if not serial:
            self.label_asignacion.configure(text="⚠️ Empty field", text_color="#f59e0b")
            return
        
        item_data = self.find_yubikey(serial)
        if not item_data:
            self.label_asignacion.configure(text="❌ Serial not found", text_color="#ef4444")
            self.after(3000, lambda: self.label_asignacion.configure(text=""))
            return
        
        estado_actual = item_data['estado']
        usuario = item_data.get('usuario', 'N/A') or 'N/A'
        pipkins = item_data.get('codigo_pipkins', 'N/A') or 'N/A'
        
        self.show_current_state_modal(serial, usuario, pipkins, estado_actual, 'assign_return')

    def setup_perdida_panel(self):
        header_frame = ctk.CTkFrame(self.panel_perdida, fg_color="transparent")
        header_frame.pack(fill="x", padx=40, pady=(20, 10))
        
        ctk.CTkLabel(header_frame, text="⚠️ Loss / Damage Report",
                    font=("Inter", RESPONSIVE.get_font_size(28), "bold"),
                    text_color="#ef4444").pack()
        
        ctk.CTkLabel(header_frame, text="Report lost or damaged yubikeys",
                    font=("Inter", 13),
                    text_color="#94a3b8").pack(pady=5)
        
        input_card = ctk.CTkFrame(self.panel_perdida, fg_color=SLATE_GRAY,
                                 corner_radius=15, border_width=1,
                                 border_color="#334155")
        input_card.pack(fill="x", padx=40, pady=20)
        
        input_frame = ctk.CTkFrame(input_card, fg_color="transparent")
        input_frame.pack(fill="x", padx=30, pady=25)
        
        ctk.CTkLabel(input_frame, text="Yubikey Serial OR Pipkins Code:",
                    font=("Inter", RESPONSIVE.get_font_size(16), "bold"),
                    text_color="#e2e8f0").pack(anchor="w", pady=(0, 10))
        
        ctk.CTkLabel(input_frame, text="💡 Tip: Enter serial OR Pipkins code, then press Enter",
                    font=("Inter", 11),
                    text_color="#94a3b8").pack(anchor="w", pady=(0, 15))
        
        self.entry_perdida = ctk.CTkEntry(input_frame,
                                         placeholder_text="Type serial or Pipkins code...",
                                         width=RESPONSIVE.get_entry_width(),
                                         height=50,
                                         font=("Inter", RESPONSIVE.get_font_size(16)),
                                         border_width=2,
                                         border_color=BORDER_DEFAULT,
                                         corner_radius=10)
        self.entry_perdida.pack(fill="x", pady=10)
        self.entry_perdida.bind("<Return>", lambda e: self.process_loss_damage_scan())
        
        self.btn_scan_perdida = ctk.CTkButton(input_frame,
                                             text="📡 Activate Scanner",
                                             command=lambda: self.toggle_scanner('perdida'),
                                             fg_color="#3b82f6",
                                             hover_color="#2563eb",
                                             font=("Inter", RESPONSIVE.get_font_size(14), "bold"),
                                             height=45,
                                             corner_radius=10)
        self.btn_scan_perdida.pack(fill="x", pady=15)
        
        self.label_perdida = ctk.CTkLabel(input_card, text="",
                                         font=("Inter", RESPONSIVE.get_font_size(14), "bold"))
        self.label_perdida.pack(pady=15)
        
        self.setup_recent_table_responsive(self.panel_perdida, 'perdida')

    def process_loss_damage_scan(self):
        search_value = self.entry_perdida.get().strip().upper()
        if not search_value:
            self.label_perdida.configure(text="⚠️ Empty field", text_color="#f59e0b")
            return
        
        item_data = self.find_yubikey(search_value)
        
        if not item_data:
            item_data = self.find_by_pipkins(search_value)
            search_method = "Pipkins code"
        else:
            search_method = "Serial"
        
        if not item_data:
            self.label_perdida.configure(text="❌ Serial or Pipkins not found", text_color="#ef4444")
            self.after(3000, lambda: self.label_perdida.configure(text=""))
            return
        
        estado_actual = item_data['estado']
        serial = item_data['serial']
        usuario = item_data.get('usuario', 'N/A') or 'N/A'
        pipkins = item_data.get('codigo_pipkins', 'N/A') or 'N/A'
        
        self.show_current_state_modal(serial, usuario, pipkins, estado_actual, 'loss_damage',
                                     found_by=search_method, search_value=search_value)

    def find_by_pipkins(self, pipkins_code):
        if not os.path.isfile(JSON_FILE):
            return None
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        for item in datos:
            if item.get('codigo_pipkins', '').upper() == pipkins_code.upper():
                return item
        return None

    def find_yubikey(self, serial):
        if not os.path.isfile(JSON_FILE):
            return None
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        for item in datos:
            if item['serial'].upper() == serial.upper():
                return item
        return None

    def serial_exists(self, serial):
        return self.find_yubikey(serial) is not None

    def show_message(self, title, message, type="info"):
        modal = ctk.CTkToplevel(self)
        modal.title(title)
        
        modal_width = 500 if not RESPONSIVE.is_laptop else 400
        modal_height = 280 if not RESPONSIVE.is_laptop else 240
        modal.geometry(RESPONSIVE.center_modal(self, modal_width, modal_height))
        modal.minsize(350, 220)
        
        modal.grab_set()
        
        if type == "info":
            color = "#38bdf8"
            icon = "ℹ️"
        elif type == "error":
            color = "#ef4444"
            icon = "❌"
        elif type == "warning":
            color = "#f59e0b"
            icon = "⚠️"
        else:
            color = SUCCESS_GREEN
            icon = "✅"
        
        main_frame = ctk.CTkFrame(modal, fg_color=SLATE_GRAY, corner_radius=15,
                                 border_width=1, border_color="#334155")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        scrollable_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent",
                                                 corner_radius=10)
        scrollable_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        ctk.CTkLabel(scrollable_frame, text=f"{icon} {message}",
                    font=("Inter", RESPONSIVE.get_font_size(14)),
                    text_color=color,
                    wraplength=350,
                    justify="center").pack(pady=30)
        
        ctk.CTkButton(scrollable_frame, text="OK", command=modal.destroy,
                     fg_color="#475569", hover_color="#64748b",
                     font=("Inter", RESPONSIVE.get_font_size(14)),
                     width=120, height=38, corner_radius=10).pack(pady=15)

    def load_recent_data(self, tipo):
        tree = getattr(self, f"tree_recent_{tipo}", None)
        if not tree:
            return
        tree.delete(*tree.get_children())
        movimientos = self.get_recent_movements(tipo)
        for mov in movimientos:
            tree.insert('', 'end', values=mov)

    def get_recent_movements(self, tipo):
        if not os.path.isfile(JSON_FILE):
            return []
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
            state_map = {
                'Disponible': 'Available', 'En Uso': 'In Use',
                'En Break': 'On Break', 'En Lunch': 'On Lunch',
                'Pérdida': 'Loss', 'Perdida': 'Loss',
                'Daño': 'Damage', 'Dano': 'Damage'
            }
            
            for item in datos:
                if 'codigo_pickiks' in item:
                    item['codigo_pipkins'] = item.pop('codigo_pickiks')
                    migrated = True
                
                if item.get('estado') in state_map:
                    item['estado'] = state_map[item['estado']]
                    migrated = True
                
                if 'historial' not in item:
                    item['historial'] = []
            
            if migrated:
                with open(JSON_FILE, 'w', encoding='utf-8') as f:
                    json.dump(datos, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Migration error: {e}")

    def show_nueva_panel(self):
        self.hide_all_panels()
        self.current_panel_name = 'nueva'
        self.panel_nueva.pack(fill="both", expand=True)

    def show_ingreso_panel(self):
        self.hide_all_panels()
        self.current_panel_name = 'ingreso'
        self.panel_ingreso.pack(fill="both", expand=True)

    def show_asignacion_panel(self):
        self.hide_all_panels()
        self.current_panel_name = 'asignacion'
        self.panel_asignacion.pack(fill="both", expand=True)

    def show_perdida_panel(self):
        self.hide_all_panels()
        self.current_panel_name = 'perdida'
        self.panel_perdida.pack(fill="both", expand=True)

    def show_inv_view(self):
        self.hide_all_panels()
        self.current_panel_name = 'inventory'
        self.view_inv.pack(fill="both", expand=True)
        self.load_inventory_table()

    def show_report_view(self):
        self.hide_all_panels()
        self.current_panel_name = 'reports'
        self.view_report.pack(fill="both", expand=True)
        self.load_reports()

    def load_inventory_table(self):
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
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"Inventory_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        
        if filename:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                datos = json.load(f)
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Serial', 'User', 'Pipkins', 'State', 'Last Connection'])
                for item in datos:
                    writer.writerow([
                        item['serial'],
                        item.get('usuario', ''),
                        item.get('codigo_pipkins', ''),
                        item['estado'],
                        item.get('ultima_conexion', '')
                    ])
            
            self.show_message("✅ Export Complete", f"Saved to:\n{filename}", "success")

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
        
        for item in datos:
            for h in item.get('historial', []):
                if h['accion'] == 'Loss':
                    loss_count += 1
                    self.loss_tree.insert('', 'end', values=(
                        item['serial'],
                        item.get('usuario', '-'),
                        item.get('codigo_pipkins', '-'),
                        h['fecha'],
                        h['hora']
                    ))
                elif h['accion'] == 'Damage':
                    damage_count += 1
                    self.damage_tree.insert('', 'end', values=(
                        item['serial'],
                        item.get('usuario', '-'),
                        item.get('codigo_pipkins', '-'),
                        h['fecha'],
                        h['hora']
                    ))
        
        if hasattr(self, 'loss_count_label'):
            self.loss_count_label.configure(text=str(loss_count))
        if hasattr(self, 'damage_count_label'):
            self.damage_count_label.configure(text=str(damage_count))
        if hasattr(self, 'summary_loss_label'):
            self.summary_loss_label.configure(text=str(loss_count))
        if hasattr(self, 'summary_damage_label'):
            self.summary_damage_label.configure(text=str(damage_count))
        if hasattr(self, 'summary_total_label'):
            self.summary_total_label.configure(text=str(loss_count + damage_count))
        
        summary = f"""
📊 YUBIKEY INCIDENT SUMMARY
{'='*50}

🔴 Total Losses: {loss_count}
🟣 Total Damages: {damage_count}
📋 Total Incidents: {loss_count + damage_count}

📦 Total Yubikeys in System: {len(datos)}

📈 BY STATE:
{'-'*50}
"""
        
        estados_count = {}
        for item in datos:
            estado = item['estado']
            estados_count[estado] = estados_count.get(estado, 0) + 1
        
        for estado, count in sorted(estados_count.items()):
            summary += f"\n  • {estado}: {count}"
        
        summary += f"\n\n{'='*50}\nLast Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        if hasattr(self, 'summary_text'):
            self.summary_text.delete("1.0", "end")
            self.summary_text.insert("1.0", summary)

    def export_loss_report(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
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
            
            self.show_message("✅ Export Complete", f"Saved to:\n{filename}", "success")

    def export_damage_report(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
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
            
            self.show_message("✅ Export Complete", f"Saved to:\n{filename}", "success")

    def ask_user_and_pipkins(self, serial):
        modal = ctk.CTkToplevel(self)
        modal.title("Complete Registration")
        
        modal_width = 500 if not RESPONSIVE.is_laptop else 420
        modal_height = 420 if not RESPONSIVE.is_laptop else 370
        modal.geometry(RESPONSIVE.center_modal(self, modal_width, modal_height))
        modal.minsize(400, 340)
        
        modal.grab_set()
        
        main_frame = ctk.CTkFrame(modal, fg_color=SLATE_GRAY, corner_radius=18,
                                 border_width=1, border_color="#334155")
        main_frame.pack(padx=24, pady=24, fill="both", expand=True)
        
        scrollable_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent",
                                                 corner_radius=10)
        scrollable_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        ctk.CTkLabel(scrollable_frame, text="📝 Complete Registration",
                    font=("Inter", RESPONSIVE.get_font_size(22), "bold"),
                    text_color="#38bdf8").pack(pady=15)
        
        ctk.CTkLabel(scrollable_frame, text=f"Serial: {serial}",
                    font=("Inter", 14, "bold"),
                    text_color=SUCCESS_GREEN).pack(pady=5)
        
        campos = [("User Name:", "usuario_var"), ("Pipkins Code:", "pipkins_var")]
        vars_dict = {}
        
        input_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        input_frame.pack(fill="x", padx=20, pady=15)
        
        for label_text, var_name in campos:
            ctk.CTkLabel(input_frame, text=label_text,
                        font=("Inter", RESPONSIVE.get_font_size(15), "bold"),
                        text_color="#e2e8f0").pack(anchor='w', pady=(15, 5))
            var = ctk.StringVar()
            entry = ctk.CTkEntry(input_frame, textvariable=var,
                               width=RESPONSIVE.get_entry_width(),
                               font=("Inter", RESPONSIVE.get_font_size(14)),
                               corner_radius=10, height=45)
            entry.pack(fill="x")
            vars_dict[var_name] = var
        
        error_label = ctk.CTkLabel(scrollable_frame, text="",
                                  text_color="#ef4444",
                                  font=("Inter", 13, "bold"))
        error_label.pack(pady=(0, 2))
        
        result = {'ok': False}
        
        def registrar():
            usuario = vars_dict['usuario_var'].get().strip()
            pipkins = vars_dict['pipkins_var'].get().strip()
            if not usuario or not pipkins:
                error_label.configure(text="⚠️ All fields are required")
                return
            self.save_new_yubikey(serial, usuario, pipkins)
            result['ok'] = True
            modal.destroy()
        
        ctk.CTkButton(scrollable_frame, text="✅ Register Yubikey", command=registrar,
                     fg_color="#38bdf8", hover_color="#0ea5e9",
                     font=("Inter", RESPONSIVE.get_font_size(16), "bold"),
                     corner_radius=12, height=45, width=200).pack(pady=20)

    def save_new_yubikey(self, serial, usuario, pipkins):
        now = datetime.now()
        nueva = {
            "serial": serial,
            "usuario": usuario,
            "codigo_pipkins": pipkins,
            "estado": "In Use",
            "ultima_conexion": now.strftime("%Y-%m-%d"),
            "historial": [{
                "accion": "Registro",
                "fecha": now.strftime("%Y-%m-%d"),
                "hora": now.strftime("%H:%M:%S"),
                "usuario": usuario,
                "codigo_pipkins": pipkins,
                "estado": "In Use",
                "comentario": "Initial registration"
            }]
        }
        
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        datos.append(nueva)
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)
        
        self.label_nueva.configure(text="✅ Registered Successfully!",
                                  text_color=SUCCESS_GREEN,
                                  font=("Inter", RESPONSIVE.get_font_size(14), "bold"))
        self.entry_nueva.delete(0, 'end')
        self.load_recent_data('nueva')
        self.load_inventory_table()
        self.after(3000, lambda: self.label_nueva.configure(text=""))

    def setup_recent_table_responsive(self, parent, tipo):
        table_card = ctk.CTkFrame(parent, fg_color=SLATE_GRAY,
                                 corner_radius=15, border_width=1,
                                 border_color="#334155")
        table_card.pack(fill="both", expand=True, padx=40, pady=20)
        
        header = ctk.CTkFrame(table_card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 10))
        
        ctk.CTkLabel(header, text="📋 Recent Movements",
                    font=("Inter", RESPONSIVE.get_font_size(16), "bold"),
                    text_color="#38bdf8").pack(anchor="w")
        
        tree_frame = ctk.CTkFrame(table_card, fg_color="#0f172a",
                                 corner_radius=10)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = ("Serial", "Pipkins", "Action", "Date", "Time")
        
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure(f'{tipo}.Treeview',
                       font=('Inter', RESPONSIVE.get_font_size(11)),
                       rowheight=32,
                       background="#0f172a",
                       fieldbackground="#0f172a",
                       foreground="#e2e8f0",
                       borderwidth=0)
        
        style.configure(f'{tipo}.Treeview.Heading',
                       font=('Inter', RESPONSIVE.get_font_size(12), "bold"),
                       background="#1e293b",
                       foreground="#38bdf8",
                       borderwidth=0)
        
        style.map(f'{tipo}.Treeview',
                 background=[('selected', '#3b82f6')],
                 foreground=[('selected', 'white')])
        
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                           height=6, style=f'{tipo}.Treeview')
        
        col_widths = {
            "Serial": 180,
            "Pipkins": 120,
            "Action": 250,
            "Date": 120,
            "Time": 100
        }
        
        for col in columns:
            tree.heading(col, text=col, anchor="w")
            tree.column(col, anchor="w", width=col_widths.get(col, 150), minwidth=80)
        
        scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scrollbar_y.grid(row=0, column=1, sticky="ns", pady=5)
        scrollbar_x.grid(row=1, column=0, sticky="ew", padx=5)
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        setattr(self, f"tree_recent_{tipo}", tree)
        self.load_recent_data(tipo)

    def setup_inv_view(self):
        header_frame = ctk.CTkFrame(self.view_inv, fg_color="transparent")
        header_frame.pack(fill="x", padx=40, pady=(20, 10))
        
        ctk.CTkLabel(header_frame, text="📋 General Inventory",
                    font=("Inter", RESPONSIVE.get_font_size(32), "bold"),
                    text_color="#38bdf8").pack()
        
        filter_card = ctk.CTkFrame(self.view_inv, fg_color=SLATE_GRAY,
                                  corner_radius=15, border_width=1,
                                  border_color="#334155")
        filter_card.pack(fill="x", padx=40, pady=15)
        
        filter_frame = ctk.CTkFrame(filter_card, fg_color="transparent")
        filter_frame.pack(fill="x", padx=25, pady=15)
        
        ctk.CTkLabel(filter_frame, text="🔍 Filter by State:",
                    font=("Inter", RESPONSIVE.get_font_size(14), "bold"),
                    text_color="#e2e8f0").pack(anchor="w", pady=(0, 10))
        
        radio_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        radio_frame.pack(fill="x")
        
        self.filter_var = ctk.StringVar(value="All")
        estados = ["All", "Available", "In Use", "On Break", "On Lunch", "Loss", "Damage"]
        colors = {"All": "#64748b", "Available": "#10b981", "In Use": "#3b82f6",
                 "On Break": "#f59e0b", "On Lunch": "#f97316", "Loss": "#ef4444", "Damage": "#8b5cf6"}
        
        for i, estado in enumerate(estados):
            ctk.CTkRadioButton(radio_frame, text=estado,
                             variable=self.filter_var,
                             value=estado,
                             command=self.filter_inventory,
                             fg_color=colors[estado],
                             font=("Inter", 12)).grid(row=i//4, column=i%4, padx=10, pady=5)
        
        search_frame = ctk.CTkFrame(filter_card, fg_color="transparent")
        search_frame.pack(fill="x", padx=25, pady=(0, 15))
        
        self.search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(search_frame,
                                   textvariable=self.search_var,
                                   placeholder_text="🔎 Search by serial or user...",
                                   width=400,
                                   height=40,
                                   font=("Inter", 13))
        search_entry.pack(side="left", padx=(0, 10))
        search_entry.bind("<KeyRelease>", lambda e: self.filter_inventory())
        
        ctk.CTkButton(search_frame, text="📋 View Details",
                     command=self.show_item_details,
                     fg_color="#3b82f6", hover_color="#2563eb",
                     font=("Inter", 13, "bold"),
                     height=40, width=140).pack(side="left", padx=5)
        
        ctk.CTkButton(search_frame, text="📥 Export CSV",
                     command=self.export_inventory,
                     fg_color="#10b981", hover_color="#059669",
                     font=("Inter", 13, "bold"),
                     height=40, width=140).pack(side="left", padx=5)

        table_card = ctk.CTkFrame(self.view_inv, fg_color=SLATE_GRAY,
                                 corner_radius=15, border_width=1,
                                 border_color="#334155")
        table_card.pack(fill="both", expand=True, padx=40, pady=15)
        
        tree_frame = ctk.CTkFrame(table_card, fg_color="#0f172a",
                                 corner_radius=10)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=15)
        
        cols = ("Serial", "User", "Pipkins", "State", "Last Connection")
        
        self.inv_tree = ttk.Treeview(tree_frame, columns=cols,
                                    show='headings', style='Custom.Treeview')
        
        style = ttk.Style()
        style.configure('Custom.Treeview',
                       font=('Inter', RESPONSIVE.get_font_size(12)),
                       rowheight=38,
                       background="#0f172a",
                       fieldbackground="#0f172a",
                       foreground="#e2e8f0")
        style.configure('Custom.Treeview.Heading',
                       font=('Inter', RESPONSIVE.get_font_size(13), "bold"),
                       background="#1e293b",
                       foreground="#38bdf8")
        
        style.map('Custom.Treeview',
                 background=[('selected', '#3b82f6')],
                 foreground=[('selected', 'white')])
        
        for estado, color in ESTADO_COLORES.items():
            self.inv_tree.tag_configure(estado, background=color, foreground="white")
        
        col_widths_inv = {
            "Serial": 180,
            "User": 200,
            "Pipkins": 120,
            "State": 140,
            "Last Connection": 150
        }
        
        for col in cols:
            self.inv_tree.heading(col, text=col, anchor="w")
            self.inv_tree.column(col, anchor="w", width=col_widths_inv.get(col, 150), minwidth=100)
        
        scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.inv_tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.inv_tree.xview)
        self.inv_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        self.inv_tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scrollbar_y.grid(row=0, column=1, sticky="ns", pady=5)
        scrollbar_x.grid(row=1, column=0, sticky="ew", padx=5)
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.inv_tree.bind("<Double-1>", lambda e: self.show_item_details())

    def ask_return_comment(self, serial):
        modal = ctk.CTkToplevel(self)
        modal.title("Return Yubikey")
        
        modal_width = 500 if not RESPONSIVE.is_laptop else 420
        modal_height = 350 if not RESPONSIVE.is_laptop else 300
        modal.geometry(RESPONSIVE.center_modal(self, modal_width, modal_height))
        modal.minsize(380, 280)
        
        modal.grab_set()
        
        main_frame = ctk.CTkFrame(modal, fg_color=SLATE_GRAY, corner_radius=18,
                                 border_width=1, border_color="#334155")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        scrollable_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent",
                                                 corner_radius=10)
        scrollable_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        ctk.CTkLabel(scrollable_frame, text="🔄 Return Yubikey",
                    font=("Inter", RESPONSIVE.get_font_size(20), "bold"),
                    text_color="#8b5cf6").pack(pady=15)
        
        ctk.CTkLabel(scrollable_frame, text="Optional comment (why is it being returned):",
                    font=("Inter", RESPONSIVE.get_font_size(13)),
                    text_color="#94a3b8").pack(pady=10)
        
        comment_text = ctk.CTkTextbox(scrollable_frame, width=400, height=100,
                                     font=("Inter", RESPONSIVE.get_font_size(13)),
                                     corner_radius=10)
        comment_text.pack(pady=10, padx=30)
        try:
            modal.after(100, lambda: comment_text.focus())
        except:
            pass
        
        result = {'ok': False, 'comentario': ''}
        
        def aceptar():
            comentario = comment_text.get("1.0", "end-1c").strip()
            result['ok'] = True
            result['comentario'] = comentario
            self.save_return_yubikey(serial, comentario)
            modal.destroy()
        
        btn_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        btn_frame.pack(pady=15)
        
        ctk.CTkButton(btn_frame, text="✅ Return", command=aceptar,
                     fg_color="#ef4444", hover_color="#dc2626",
                     font=("Inter", RESPONSIVE.get_font_size(15), "bold"),
                     width=130, height=40, corner_radius=10).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Skip", command=lambda: aceptar(),
                     fg_color="#475569", hover_color="#64748b",
                     font=("Inter", RESPONSIVE.get_font_size(14)),
                     width=100, height=40, corner_radius=10).pack(side="left", padx=10)

    def save_return_yubikey(self, serial, comentario):
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        for item in datos:
            if item['serial'].upper() == serial.upper():
                now = datetime.now()
                usuario_anterior = item.get('usuario', 'N/A')
                
                item['estado'] = 'Available'
                item['usuario'] = ''
                item['codigo_pipkins'] = ''
                item['ultima_conexion'] = now.strftime("%Y-%m-%d")
                
                item['historial'].append({
                    'accion': f'Return (previous: {usuario_anterior})',
                    'fecha': now.strftime("%Y-%m-%d"),
                    'hora': now.strftime("%H:%M:%S"),
                    'estado': 'Available',
                    'usuario': '',
                    'codigo_pipkins': '',
                    'comentario': comentario or "User returned yubikey"
                })
                break
        
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)
        
        self.label_asignacion.configure(text="✅ Returned successfully!",
                                       text_color=SUCCESS_GREEN,
                                       font=("Inter", RESPONSIVE.get_font_size(14), "bold"))
        self.entry_asignacion.delete(0, 'end')
        self.load_recent_data('asignacion')
        self.load_inventory_table()
        self.after(3000, lambda: self.label_asignacion.configure(text=""))

    def ask_nuevo_usuario_pipkins(self, serial):
        modal = ctk.CTkToplevel(self)
        modal.title("Assign to New User")
        
        modal_width = 500 if not RESPONSIVE.is_laptop else 420
        modal_height = 400 if not RESPONSIVE.is_laptop else 350
        modal.geometry(RESPONSIVE.center_modal(self, modal_width, modal_height))
        modal.minsize(400, 320)
        
        modal.grab_set()
        
        main_frame = ctk.CTkFrame(modal, fg_color=SLATE_GRAY, corner_radius=18,
                                 border_width=1, border_color="#334155")
        main_frame.pack(padx=24, pady=24, fill="both", expand=True)
        
        scrollable_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent",
                                                 corner_radius=10)
        scrollable_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        ctk.CTkLabel(scrollable_frame, text="🔄 Assign Yubikey",
                    font=("Inter", RESPONSIVE.get_font_size(22), "bold"),
                    text_color="#38bdf8").pack(pady=15)
        
        ctk.CTkLabel(scrollable_frame, text=f"Serial: {serial}",
                    font=("Inter", 14, "bold"),
                    text_color=SUCCESS_GREEN).pack(pady=5)
        
        campos = [("User Name:", "usuario_var"), ("Pipkins Code:", "pipkins_var")]
        vars_dict = {}
        
        input_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        input_frame.pack(fill="x", padx=20, pady=15)
        
        for label_text, var_name in campos:
            ctk.CTkLabel(input_frame, text=label_text,
                        font=("Inter", RESPONSIVE.get_font_size(15), "bold"),
                        text_color="#e2e8f0").pack(anchor='w', pady=(15, 5))
            var = ctk.StringVar()
            entry = ctk.CTkEntry(input_frame, textvariable=var,
                               width=RESPONSIVE.get_entry_width(),
                               font=("Inter", RESPONSIVE.get_font_size(14)),
                               corner_radius=10, height=45)
            entry.pack(fill="x")
            vars_dict[var_name] = var
        
        error_label = ctk.CTkLabel(scrollable_frame, text="",
                                  text_color="#ef4444",
                                  font=("Inter", 13, "bold"))
        error_label.pack(pady=(0, 2))
        
        result = {'ok': False}
        
        def asignar():
            usuario = vars_dict['usuario_var'].get().strip()
            pipkins = vars_dict['pipkins_var'].get().strip()
            if not usuario or not pipkins:
                error_label.configure(text="⚠️ All fields are required")
                return
            self.save_assign_yubikey(serial, usuario, pipkins)
            result['ok'] = True
            modal.destroy()
        
        ctk.CTkButton(scrollable_frame, text="✅ Assign Yubikey", command=asignar,
                     fg_color="#38bdf8", hover_color="#0ea5e9",
                     font=("Inter", RESPONSIVE.get_font_size(16), "bold"),
                     corner_radius=12, height=45, width=200).pack(pady=20)

    def save_assign_yubikey(self, serial, usuario, pipkins):
        now = datetime.now()
        
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        for item in datos:
            if item['serial'].upper() == serial.upper():
                item['estado'] = 'In Use'
                item['usuario'] = usuario
                item['codigo_pipkins'] = pipkins
                item['ultima_conexion'] = now.strftime("%Y-%m-%d")
                
                item['historial'].append({
                    'accion': f'Assign to {usuario}',
                    'fecha': now.strftime("%Y-%m-%d"),
                    'hora': now.strftime("%H:%M:%S"),
                    'estado': 'In Use',
                    'usuario': usuario,
                    'codigo_pipkins': pipkins,
                    'comentario': 'Assigned via Assign/Return panel'
                })
                break
        
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)
        
        self.label_asignacion.configure(text="✅ Assigned successfully!",
                                       text_color=SUCCESS_GREEN,
                                       font=("Inter", RESPONSIVE.get_font_size(14), "bold"))
        self.entry_asignacion.delete(0, 'end')
        self.load_recent_data('asignacion')
        self.load_inventory_table()
        self.after(3000, lambda: self.label_asignacion.configure(text=""))

    def ask_loss_damage_type(self, serial, found_by, search_value):
        modal = ctk.CTkToplevel(self)
        modal.title("Select Incident Type")
        
        modal_width = 450 if not RESPONSIVE.is_laptop else 380
        modal_height = 350 if not RESPONSIVE.is_laptop else 300
        modal.geometry(RESPONSIVE.center_modal(self, modal_width, modal_height))
        modal.minsize(350, 280)
        
        modal.grab_set()
        
        main_frame = ctk.CTkFrame(modal, fg_color=SLATE_GRAY, corner_radius=18,
                                 border_width=1, border_color="#334155")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        scrollable_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent",
                                                 corner_radius=10)
        scrollable_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        ctk.CTkLabel(scrollable_frame, text="⚠️ Select Incident Type",
                    font=("Inter", RESPONSIVE.get_font_size(20), "bold"),
                    text_color="#38bdf8").pack(pady=20)
        
        if found_by:
            ctk.CTkLabel(scrollable_frame, text=f"Found via {found_by}: {search_value}",
                        font=("Inter", 12),
                        text_color="#94a3b8").pack(pady=(0, 10))
        
        tipo_var = ctk.StringVar(value="Loss")
        
        options_frame = ctk.CTkFrame(scrollable_frame, fg_color=SLATE_GRAY,
                                    corner_radius=12, border_width=1,
                                    border_color="#334155")
        options_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkRadioButton(options_frame, text="🔴 Loss", variable=tipo_var, value="Loss",
                         font=("Inter", RESPONSIVE.get_font_size(16)),
                         fg_color="#ef4444").pack(anchor="w", padx=25, pady=12)
        ctk.CTkRadioButton(options_frame, text="🟣 Damage", variable=tipo_var, value="Damage",
                         font=("Inter", RESPONSIVE.get_font_size(16)),
                         fg_color="#8b5cf6").pack(anchor="w", padx=25, pady=12)
        
        def confirmar():
            tipo = tipo_var.get()
            self.ask_loss_damage_comment(serial, tipo, found_by, search_value)
            modal.destroy()
        
        btn_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="✅ Confirm", command=confirmar,
                     fg_color="#38bdf8", hover_color="#0ea5e9",
                     font=("Inter", RESPONSIVE.get_font_size(15), "bold"),
                     width=150, height=40, corner_radius=10).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Cancel", command=modal.destroy,
                     fg_color="#475569", hover_color="#64748b",
                     font=("Inter", RESPONSIVE.get_font_size(14)),
                     width=120, height=40, corner_radius=10).pack(side="left", padx=10)

    def ask_loss_damage_comment(self, serial, tipo_incidente, found_by, search_value):
        modal = ctk.CTkToplevel(self)
        modal.title(f"Report {tipo_incidente}")
        
        modal_width = 550 if not RESPONSIVE.is_laptop else 450
        modal_height = 450 if not RESPONSIVE.is_laptop else 400
        modal.geometry(RESPONSIVE.center_modal(self, modal_width, modal_height))
        modal.minsize(400, 350)
        
        modal.grab_set()
        
        main_frame = ctk.CTkFrame(modal, fg_color=SLATE_GRAY, corner_radius=18,
                                 border_width=1, border_color="#334155")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        scrollable_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent",
                                                 corner_radius=10)
        scrollable_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        ctk.CTkLabel(scrollable_frame, text=f"📝 {tipo_incidente} Report",
                    font=("Inter", RESPONSIVE.get_font_size(22), "bold"),
                    text_color="#ef4444" if tipo_incidente == "Loss" else "#8b5cf6").pack(pady=15)
        
        item_data = self.find_yubikey(serial)
        if item_data:
            usuario = item_data.get('usuario', 'N/A') or 'N/A'
            pipkins = item_data.get('codigo_pipkins', 'N/A') or 'N/A'
            
            info_text = f"""Serial: {serial}
User: {usuario}
Pipkins: {pipkins}
Found via: {found_by} ({search_value})"""
            
            ctk.CTkLabel(scrollable_frame, text=info_text,
                        font=("Inter", 13),
                        text_color="#94a3b8",
                        justify="left").pack(pady=10)
        
        ctk.CTkLabel(scrollable_frame, text="Describe what happened:",
                    font=("Inter", RESPONSIVE.get_font_size(14), "bold"),
                    text_color="#e2e8f0").pack(anchor="w", padx=30, pady=(15, 5))
        
        comment_text = ctk.CTkTextbox(scrollable_frame, width=400, height=120,
                                     font=("Inter", RESPONSIVE.get_font_size(13)),
                                     corner_radius=10)
        comment_text.pack(pady=10, padx=30)
        try:
            modal.after(100, lambda: comment_text.focus())
        except:
            pass
        
        result = {'ok': False, 'comentario': ''}
        
        def aceptar():
            comentario = comment_text.get("1.0", "end-1c").strip()
            result['ok'] = True
            result['comentario'] = comentario
            self.save_loss_damage_report(serial, tipo_incidente, comentario)
            modal.destroy()
        
        btn_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        btn_frame.pack(pady=15)
        
        ctk.CTkButton(btn_frame, text="✅ Submit", command=aceptar,
                     fg_color="#38bdf8", hover_color="#0ea5e9",
                     font=("Inter", RESPONSIVE.get_font_size(15), "bold"),
                     width=130, height=40, corner_radius=10).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Skip", command=lambda: aceptar(),
                     fg_color="#475569", hover_color="#64748b",
                     font=("Inter", RESPONSIVE.get_font_size(14)),
                     width=100, height=40, corner_radius=10).pack(side="left", padx=10)

    def save_loss_damage_report(self, serial, tipo_incidente, comentario):
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        for item in datos:
            if item['serial'].upper() == serial.upper():
                now = datetime.now()
                item['estado'] = tipo_incidente
                item['ultima_conexion'] = now.strftime("%Y-%m-%d")
                
                item['historial'].append({
                    'accion': tipo_incidente,
                    'fecha': now.strftime("%Y-%m-%d"),
                    'hora': now.strftime("%H:%M:%S"),
                    'estado': tipo_incidente,
                    'usuario': item.get('usuario', ''),
                    'codigo_pipkins': item.get('codigo_pipkins', ''),
                    'comentario': comentario or f"Reported via {tipo_incidente.lower()} panel"
                })
                break
        
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)
        
        self.label_perdida.configure(text=f"✅ {tipo_incidente} reported!",
                                    text_color=SUCCESS_GREEN,
                                    font=("Inter", RESPONSIVE.get_font_size(14), "bold"))
        self.entry_perdida.delete(0, 'end')
        self.load_recent_data('perdida')
        self.load_inventory_table()
        self.after(3000, lambda: self.label_perdida.configure(text=""))

    def on_closing(self):
        if self.scanner.is_connected:
            self.scanner.disconnect()
        self.destroy()

# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================
if __name__ == "__main__":
    app = YubiDash()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()