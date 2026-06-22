import os
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk
import formnesneleri
from formnesneleri import asm_text

class ModernButton(tk.Button):
    def __init__(self, master, hover_bg="#454545", **kwargs):
        self.normal_bg = kwargs.get("bg", "#333333")
        self.hover_bg = hover_bg
        
        kwargs["bg"] = self.normal_bg
        kwargs["bd"] = kwargs.get("bd", 0)
        kwargs["relief"] = kwargs.get("relief", "flat")
        kwargs["activebackground"] = hover_bg
        kwargs["activeforeground"] = kwargs.get("activeforeground", "white")
        
        super().__init__(master, **kwargs)
        self.bind("<Enter>", lambda e: self.config(bg=self.hover_bg))
        self.bind("<Leave>", lambda e: self.config(bg=self.normal_bg))


class AsmDesignerIDE:
    def __init__(self, root):
        self.root = root
        self.root.title("EBS Modern Assembly Studio & Form Designer")
        self.root.geometry("1300x800")
        self.root.state('zoomed')
        
        # Tema ve Stil Ayarları
        self.bg_dark = "#1E1E1E"
        self.bg_panel = "#252526"
        self.bg_accent = "#2D2D30"
        self.fg_light = "#DCDCDC"
        
        self.root.configure(bg=self.bg_dark)
        self.MASM_PATH = r"C:\masm32"
        
        # Formun Tasarım Özellikleri
        self.form_width = 600
        self.form_height = 420
        self.form_bg = "#252526"
        self.form_title = "EBS Studio Projesi"
        
        self.widgets_list = []
        self.selected_widget = None  
        self.counters = {}
        
        # Visual Studio / WinForms benzeri temel kontrol seti
        self.component_map = {
            "Button": formnesneleri.AsmButton,
            "Label": formnesneleri.AsmLabel,
            "TextBox": formnesneleri.AsmTextBox,
            "PasswordBox": formnesneleri.AsmPasswordBox,
            "TextArea": formnesneleri.AsmTextArea,
            "CheckBox": formnesneleri.AsmCheckBox,
            "RadioButton": formnesneleri.AsmRadioButton,
            "ComboBox": formnesneleri.AsmComboBox,
            "ListBox": formnesneleri.AsmListBox,
            "GroupBox": formnesneleri.AsmGroupBox,
            "PictureBox": formnesneleri.AsmPictureBox,
            "ProgressBar": formnesneleri.AsmProgressBar,
            "Slider": formnesneleri.AsmSlider,
            "DateTimePicker": formnesneleri.AsmDateTimePicker,
            "Panel": formnesneleri.AsmPanel,
            "HorizontalLine": formnesneleri.AsmHorizontalLine,
        }
        for control_name in self.component_map:
            self.counters[control_name] = 0
        
        self.setup_ui()
        self.select_form() 
        self.generate_asm_code()

    def setup_ui(self):
        # Grid Ağırlık Ayarları (Visual Studio Düzeni İçin Ana Pencere Bölmesi)
        self.root.grid_rowconfigure(0, weight=0) # Üst Bar sabit
        self.root.grid_rowconfigure(1, weight=1) # Orta Tasarım Alanı esnek
        self.root.grid_rowconfigure(2, weight=0) # Alt Terminal sabit yükseklik
        self.root.grid_columnconfigure(0, weight=1)

        # 1. ÜST BAR (Derleme Kontrolü)
        top_bar = tk.Frame(self.root, bg=self.bg_accent, height=45)
        top_bar.grid(row=0, column=0, sticky="ew")
        top_bar.pack_propagate(False)
        
        btn_compile = ModernButton(
            top_bar, text="▶  DERLE VE ÇALIŞTIR", fg="white", bg="#107C41", hover_bg="#18914F",
            font=("Segoe UI", 10, "bold"), padx=15, command=self.compile_and_run
        )
        btn_compile.pack(side=tk.LEFT, padx=10, pady=6)
        
        # 2. ORTA ALAN (Sol Panel, Sağ Panel ve Merkez Sahne)
        workspace_frame = tk.Frame(self.root, bg=self.bg_dark)
        workspace_frame.grid(row=1, column=0, sticky="nsew")

        # Sol Panel, Sağ Panel ve Merkez Sahne yan yana diziliyor
        workspace_frame.grid_columnconfigure(0, weight=0) # Sol Panel Sabit
        workspace_frame.grid_columnconfigure(1, weight=1) # Merkez Sahne Esnek
        workspace_frame.grid_columnconfigure(2, weight=0) # Sağ Panel Sabit
        workspace_frame.grid_rowconfigure(0, weight=1)

        # SOL PANEL (Toolbox)
        self.left_panel = tk.Frame(workspace_frame, bg=self.bg_panel, width=220)
        self.left_panel.grid(row=0, column=0, sticky="ns")
        self.left_panel.pack_propagate(False)
        
        lbl_toolbox = tk.Label(self.left_panel, text="TOOLBOX", fg="#858585", bg=self.bg_panel, font=("Segoe UI", 9, "bold"))
        lbl_toolbox.pack(pady=12, fill=tk.X)

        # Kontrol sayisi arttigi icin Toolbox kaydirilabilir yapildi.
        toolbox_canvas = tk.Canvas(self.left_panel, bg=self.bg_panel, highlightthickness=0)
        toolbox_scroll = tk.Scrollbar(self.left_panel, orient="vertical", command=toolbox_canvas.yview)
        toolbox_inner = tk.Frame(toolbox_canvas, bg=self.bg_panel)
        toolbox_inner.bind(
            "<Configure>",
            lambda e: toolbox_canvas.configure(scrollregion=toolbox_canvas.bbox("all"))
        )
        toolbox_canvas.create_window((0, 0), window=toolbox_inner, anchor="nw", width=205)
        toolbox_canvas.configure(yscrollcommand=toolbox_scroll.set)
        toolbox_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        toolbox_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        toolbox_canvas.bind_all("<MouseWheel>", lambda e: toolbox_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        for type_name in self.component_map.keys():
            btn = ModernButton(
                toolbox_inner, text=f"➕  {type_name}", fg=self.fg_light, bg=self.bg_accent, hover_bg="#3E3E42",
                anchor="w", padx=14, height=2, font=("Segoe UI", 9),
                command=lambda t=type_name: self.add_widget(t)
            )
            btn.pack(fill=tk.X, padx=8, pady=3)

        # SAĞ PANEL (Properties)
        self.right_panel = tk.Frame(workspace_frame, bg=self.bg_panel, width=360)
        self.right_panel.grid(row=0, column=2, sticky="ns")
        self.right_panel.pack_propagate(False)
        
        self.lbl_props_title = tk.Label(self.right_panel, text="PROPERTIES", fg="#858585", bg=self.bg_panel, font=("Segoe UI", 9, "bold"))
        self.lbl_props_title.pack(pady=12, fill=tk.X)
        
        self.props_frame = tk.Frame(self.right_panel, bg=self.bg_panel, padx=15)
        self.props_frame.pack(fill=tk.X, expand=False)
        
        self.prop_entries = {}
        fields = [
            ("Name / Title", "name"), 
            ("X / Width", "x"), 
            ("Y / Height", "y"), 
            ("Custom W / BG", "w"), 
            ("Custom H / -", "h")
        ]
        
        for label_text, field_name in fields:
            row = tk.Frame(self.props_frame, bg=self.bg_panel, pady=6)
            row.pack(fill=tk.X)
            
            lbl = tk.Label(row, text=label_text, fg=self.fg_light, bg=self.bg_panel, font=("Segoe UI", 9), width=14, anchor="w")
            lbl.pack(side=tk.LEFT)
            
            ent = tk.Entry(row, bg=self.bg_accent, fg="white", bd=1, relief="solid", insertbackground="white", font=("Segoe UI", 9))
            ent.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)
            self.prop_entries[field_name] = ent
            
        self.btn_prop_apply = ModernButton(
            self.props_frame, text="Değerleri Uygula", fg="white", bg="#007ACC", hover_bg="#1C97FF",
            font=("Segoe UI", 9, "bold"), height=2, command=self.apply_properties
        )
        self.btn_prop_apply.pack(fill=tk.X, pady=12)

        # EVENT PANELI - Visual Studio Properties penceresindeki simsek/event mantigi
        self.event_title = tk.Label(self.right_panel, text="EVENTS", fg="#858585", bg=self.bg_panel, font=("Segoe UI", 9, "bold"))
        self.event_title.pack(pady=(5, 4), fill=tk.X)
        self.events_frame = tk.Frame(self.right_panel, bg=self.bg_panel, padx=15)
        self.events_frame.pack(fill=tk.BOTH, expand=True)
        self.event_list = tk.Listbox(self.events_frame, bg=self.bg_accent, fg="white", selectbackground="#007ACC", bd=0, height=5, font=("Segoe UI", 9))
        self.event_list.pack(fill=tk.X, pady=(0, 6))
        self.event_list.bind("<Double-Button-1>", self.create_selected_event)
        self.btn_create_event = ModernButton(self.events_frame, text="Seçili Eventi Oluştur / Aç", fg="white", bg="#007ACC", hover_bg="#1C97FF", font=("Segoe UI", 9, "bold"), command=self.create_selected_event)
        self.btn_create_event.pack(fill=tk.X, pady=(0, 8))

        snippet_row = tk.Frame(self.events_frame, bg=self.bg_panel)
        snippet_row.pack(fill=tk.X, pady=(0, 6))
        for title, snippet in [
            ("MsgBox", "    invoke MessageBox, hForm, ADDR msgCustom, ADDR msgCaption, MB_OK\n"),
            ("IF", "    .IF eax == 1\n        ; kod\n    .ELSE\n        ; kod\n    .ENDIF\n"),
            ("FOR", "    mov ecx, 10\n@@for_loop:\n    ; kod\n    loop @@for_loop\n"),
            ("FOREACH", "    ; ForEach icin dizi adresi/eleman sayisi gerekir\n    ; burada her eleman icin kod yazilir\n"),
        ]:
            b = ModernButton(snippet_row, text=title, fg=self.fg_light, bg=self.bg_accent, hover_bg="#3E3E42", font=("Segoe UI", 8), command=lambda sn=snippet: self.insert_event_snippet(sn))
            b.pack(side=tk.LEFT, padx=2)

        self.event_code = tk.Text(self.events_frame, bg="#1E1E1E", fg="#DCDCDC", insertbackground="white", font=("Consolas", 9), bd=0, height=10)
        self.event_code.pack(fill=tk.BOTH, expand=True)
        self.event_code.bind("<KeyRelease>", self.save_current_event_code)
        self.current_event_name = None

        # MERKEZ DIZAYN ALANI
        self.canvas_container = tk.Frame(workspace_frame, bg=self.bg_dark)
        self.canvas_container.grid(row=0, column=1, sticky="nsew")
        self.canvas_container.grid_rowconfigure(0, weight=1)
        self.canvas_container.grid_columnconfigure(0, weight=1)
        self.canvas_container.grid_columnconfigure(1, weight=1)

        self.designer_host = tk.Frame(self.canvas_container, bg=self.bg_dark)
        self.designer_host.grid(row=0, column=0, sticky="nsew")
        self.preview_host = tk.Frame(self.canvas_container, bg=self.bg_dark)
        self.preview_host.grid(row=0, column=1, sticky="nsew")

        tk.Label(self.designer_host, text="Tasarım", fg="#858585", bg=self.bg_dark, font=("Segoe UI", 9, "bold")).pack(pady=(8, 0))
        tk.Label(self.preview_host, text="Anlık Native Önizleme", fg="#858585", bg=self.bg_dark, font=("Segoe UI", 9, "bold")).pack(pady=(8, 0))

        self.form_canvas = tk.Canvas(
            self.designer_host, width=self.form_width, height=self.form_height,
            bg=self.form_bg, highlightbackground="#3F3F46", highlightthickness=1
        )
        self.form_canvas.ide = self
        self.form_canvas.pack(expand=True, anchor=tk.CENTER)
        self.form_canvas.bind("<Button-1>", self.on_form_canvas_click)

        self.preview_canvas = tk.Canvas(
            self.preview_host, width=self.form_width, height=self.form_height,
            bg="#F0F0F0", highlightbackground="#BDBDBD", highlightthickness=1
        )
        self.preview_canvas.pack(expand=True, anchor=tk.CENTER)

        self.draw_grid()
        self.update_live_preview()

        # 3. EN ALT DOCK PANELİ
        # Notebook doğrudan root'a değil, sabit yükseklikli bir dock frame içine alınır.
        # Böylece kod ve terminal alanı pencerenin en altında boydan boya sabitlenir.
        self.bottom_dock = tk.Frame(self.root, bg=self.bg_dark, height=240, highlightthickness=1, highlightbackground="#3F3F46")
        self.bottom_dock.grid(row=2, column=0, sticky="nsew")
        self.bottom_dock.grid_rowconfigure(0, weight=1)
        self.bottom_dock.grid_columnconfigure(0, weight=1)
        self.bottom_dock.grid_propagate(False)

        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook', background=self.bg_dark, borderwidth=0)
        style.configure('TNotebook.Tab', background=self.bg_panel, foreground=self.fg_light, borderwidth=0, padding=[15, 4])
        style.map('TNotebook.Tab', background=[('selected', self.bg_accent)], foreground=[('selected', "white")])

        self.notebook = ttk.Notebook(self.bottom_dock)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        self.code_frame = tk.Frame(self.notebook, bg="#1E1E1E")
        self.code_frame.grid_rowconfigure(0, weight=1)
        self.code_frame.grid_columnconfigure(0, weight=1)
        self.code_view = tk.Text(self.code_frame, bg="#1E1E1E", fg="#DCDCDC", font=("Consolas", 10), bd=0, wrap=tk.NONE)
        self.code_scroll_y = tk.Scrollbar(self.code_frame, orient=tk.VERTICAL, command=self.code_view.yview)
        self.code_scroll_x = tk.Scrollbar(self.code_frame, orient=tk.HORIZONTAL, command=self.code_view.xview)
        self.code_view.configure(yscrollcommand=self.code_scroll_y.set, xscrollcommand=self.code_scroll_x.set)
        self.code_view.grid(row=0, column=0, sticky="nsew")
        self.code_scroll_y.grid(row=0, column=1, sticky="ns")
        self.code_scroll_x.grid(row=1, column=0, sticky="ew")
        self.notebook.add(self.code_frame, text=" 📜 Otomatik Assembly Kodu ")

        self.console_frame = tk.Frame(self.notebook, bg="#1E1E1E")
        self.console_frame.grid_rowconfigure(0, weight=1)
        self.console_frame.grid_columnconfigure(0, weight=1)
        self.console = tk.Text(self.console_frame, bg="#1E1E1E", fg="#00FF00", font=("Consolas", 9), bd=0, wrap=tk.WORD)
        self.console_scroll_y = tk.Scrollbar(self.console_frame, orient=tk.VERTICAL, command=self.console.yview)
        self.console.configure(yscrollcommand=self.console_scroll_y.set)
        self.console.grid(row=0, column=0, sticky="nsew")
        self.console_scroll_y.grid(row=0, column=1, sticky="ns")
        self.notebook.add(self.console_frame, text=" 💻 Çıktı / Terminal ")

        self.log("[Sistem] Alt çıktı alanları dock panel olarak pencerenin altına sabitlendi.")

    def on_form_canvas_click(self, event):
        # Sadece boş tasarım alanına tıklanınca ana form seçilir.
        # Nesne üstündeki tıklamalar BaseComponent içinde "break" ile durdurulur.
        current = self.form_canvas.find_withtag("current")
        if not current or "grid" in self.form_canvas.gettags(current[0]):
            self.select_form()
        return "break"

    def draw_grid(self):
        self.form_canvas.delete("grid")
        grid_size = 15
        for i in range(0, self.form_width, grid_size):
            for j in range(0, self.form_height, grid_size):
                self.form_canvas.create_oval(i, j, i+1, j+1, fill="#3F3F46", outline="#3F3F46", tags="grid")
        self.form_canvas.tag_lower("grid")

    def add_widget(self, widget_type):
        self.counters[widget_type] += 1
        name = f"{widget_type.lower()}_{self.counters[widget_type]}"
        
        component_class = self.component_map[widget_type]
        new_widget = component_class(self.form_canvas, name, 45, 45, self.generate_asm_code)
        
        self.widgets_list.append(new_widget)
        self.select_widget(new_widget)
        self.generate_asm_code()

    def select_widget(self, widget):
        if self.selected_widget and self.selected_widget != widget:
            self.selected_widget.unfocus()
            
        self.selected_widget = widget
        widget.focus()
        self.lbl_props_title.config(text=f"PROPERTIES: {widget.name.upper()}")
        self.update_properties_ui()
        self.update_events_ui()

    def select_form(self):
        if self.selected_widget:
            self.selected_widget.unfocus()
        self.selected_widget = None
        self.lbl_props_title.config(text="PROPERTIES: MAIN_FORM")
        
        for f in self.prop_entries.values(): f.delete(0, tk.END)
        self.prop_entries["name"].insert(0, self.form_title)
        self.prop_entries["x"].insert(0, str(self.form_width))
        self.prop_entries["y"].insert(0, str(self.form_height))
        self.prop_entries["w"].insert(0, self.form_bg)
        self.prop_entries["h"].insert(0, "N/A")
        self.prop_entries["h"].config(state="disabled")
        self.update_events_ui()

    def update_properties_ui(self):
        if self.selected_widget is None: return
        w = self.selected_widget
        self.prop_entries["h"].config(state="normal")
        
        for field, value in [("name", w.name), ("x", w.x), ("y", w.y), ("w", w.width), ("h", w.height)]:
            self.prop_entries[field].delete(0, tk.END)
            self.prop_entries[field].insert(0, str(value))

    def apply_properties(self):
        if self.selected_widget is None:
            try:
                self.form_title = self.prop_entries["name"].get()
                self.form_width = int(self.prop_entries["x"].get())
                self.form_height = int(self.prop_entries["y"].get())
                self.form_bg = self.prop_entries["w"].get()
                
                self.form_canvas.config(width=self.form_width, height=self.form_height, bg=self.form_bg)
                self.preview_canvas.config(width=self.form_width, height=self.form_height)
                self.draw_grid()
                self.generate_asm_code()
                self.log("[Düzenleme] Ana form mimari özellikleri güncellendi.")
            except ValueError:
                messagebox.showerror("Hata", "Genişlik ve Yükseklik sayısal olmalıdır.")
        else:
            try:
                new_name = self.prop_entries["name"].get()
                new_x = int(self.prop_entries["x"].get())
                new_y = int(self.prop_entries["y"].get())
                new_w = int(self.prop_entries["w"].get())
                new_h = int(self.prop_entries["h"].get())
                
                self.selected_widget.name = new_name
                self.selected_widget.update_geometry(new_x, new_y, new_w, new_h)
                self.lbl_props_title.config(text=f"PROPERTIES: {new_name.upper()}")
                self.generate_asm_code()
            except ValueError:
                messagebox.showerror("Hata", "Lütfen koordinat alanlarına geçerli tamsayı girin.")

    def log(self, text):
        self.console.insert(tk.END, text + "\n")
        self.console.see(tk.END)

    def update_events_ui(self):
        self.event_list.delete(0, tk.END)
        self.event_code.delete("1.0", tk.END)
        self.current_event_name = None
        if self.selected_widget is None:
            self.event_title.config(text="EVENTS: MAIN_FORM")
            for ev in ["Load", "Close"]:
                self.event_list.insert(tk.END, ev)
            return
        self.event_title.config(text=f"EVENTS: {self.selected_widget.name.upper()}")
        for ev in self.selected_widget.available_events():
            mark = "  ✓" if self.selected_widget.events.get(ev) else ""
            self.event_list.insert(tk.END, ev + mark)

    def create_selected_event(self, event=None):
        if self.selected_widget is None:
            return "break"
        sel = self.event_list.curselection()
        if not sel:
            if self.event_list.size() > 0:
                self.event_list.selection_set(0)
                sel = (0,)
            else:
                return "break"
        event_name = self.event_list.get(sel[0]).replace("  ✓", "")
        self.current_event_name = event_name
        code = self.selected_widget.ensure_event(event_name)
        self.event_code.delete("1.0", tk.END)
        self.event_code.insert(tk.END, code)
        self.update_events_ui()
        for i in range(self.event_list.size()):
            if self.event_list.get(i).startswith(event_name):
                self.event_list.selection_set(i)
                break
        self.current_event_name = event_name
        self.event_code.delete("1.0", tk.END)
        self.event_code.insert(tk.END, self.selected_widget.events[event_name])
        self.notebook.select(0)
        self.generate_asm_code()
        self.log(f"[Event] {self.selected_widget.name}.{event_name} olusturuldu/acildi.")
        return "break"

    def save_current_event_code(self, event=None):
        if self.selected_widget is not None and self.current_event_name:
            self.selected_widget.events[self.current_event_name] = self.event_code.get("1.0", tk.END)
            self.generate_asm_code()

    def insert_event_snippet(self, snippet):
        if self.selected_widget is None or not self.current_event_name:
            self.create_selected_event()
        self.event_code.insert(tk.INSERT, snippet)
        self.save_current_event_code()

    def event_notification_const(self, widget, event_name):
        mapping = {
            "Click": "BN_CLICKED",
            "SelectionChange": "CBN_SELCHANGE" if widget.__class__.__name__ == "AsmComboBox" else "LBN_SELCHANGE",
            "DoubleClick": "LBN_DBLCLK",
            "DropDown": "CBN_DROPDOWN",
            "Change": "EN_CHANGE" if "Text" in widget.__class__.__name__ or "Password" in widget.__class__.__name__ else "0",
            "GotFocus": "EN_SETFOCUS",
            "LostFocus": "EN_KILLFOCUS",
        }
        return mapping.get(event_name, "BN_CLICKED")

    def update_live_preview(self):
        if not hasattr(self, "preview_canvas"):
            return
        c = self.preview_canvas
        c.delete("all")
        c.config(width=self.form_width, height=self.form_height, bg="#F0F0F0")
        c.create_rectangle(0, 0, self.form_width, self.form_height, fill="#F0F0F0", outline="#BDBDBD")
        for w in self.widgets_list:
            self.draw_preview_widget(c, w)

    def draw_preview_widget(self, c, w):
        x, y, ww, hh = w.x, w.y, w.width, w.height
        name = w.name
        cls = w.__class__.__name__
        if cls == "AsmButton":
            c.create_rectangle(x, y, x+ww, y+hh, fill="#F7F7F7", outline="#8A8A8A")
            c.create_text(x+ww/2, y+hh/2, text=name, fill="#000000", font=("Segoe UI", 9, "bold"))
        elif cls in ("AsmLabel",):
            c.create_text(x+4, y+hh/2, text=name, fill="#000000", anchor="w", font=("Segoe UI", 9))
        elif cls in ("AsmTextBox", "AsmPasswordBox"):
            c.create_rectangle(x, y, x+ww, y+hh, fill="#FFFFFF", outline="#9E9E9E")
            c.create_text(x+5, y+hh/2, text=("••••" if cls == "AsmPasswordBox" else ""), fill="#000000", anchor="w", font=("Segoe UI", 9))
        elif cls == "AsmTextArea":
            c.create_rectangle(x, y, x+ww, y+hh, fill="#FFFFFF", outline="#9E9E9E")
        elif cls == "AsmCheckBox":
            c.create_rectangle(x, y+5, x+14, y+19, fill="#FFFFFF", outline="#555555")
            c.create_text(x+20, y+hh/2, text=name, fill="#000000", anchor="w", font=("Segoe UI", 9))
        elif cls == "AsmRadioButton":
            c.create_oval(x, y+5, x+14, y+19, fill="#FFFFFF", outline="#555555")
            c.create_text(x+20, y+hh/2, text=name, fill="#000000", anchor="w", font=("Segoe UI", 9))
        elif cls == "AsmComboBox":
            c.create_rectangle(x, y, x+ww, y+24, fill="#FFFFFF", outline="#9E9E9E")
            c.create_rectangle(x+ww-22, y+1, x+ww-1, y+23, fill="#EEEEEE", outline="#B0B0B0")
            c.create_text(x+ww-11, y+12, text="▼", fill="#000000", font=("Segoe UI", 7))
        elif cls == "AsmListBox":
            c.create_rectangle(x, y, x+ww, y+hh, fill="#FFFFFF", outline="#9E9E9E")
        elif cls == "AsmGroupBox":
            c.create_rectangle(x, y+8, x+ww, y+hh, fill="", outline="#9E9E9E")
            c.create_text(x+12, y+8, text=name, fill="#000000", anchor="w", font=("Segoe UI", 9))
        elif cls == "AsmPictureBox":
            c.create_rectangle(x, y, x+ww, y+hh, fill="#DADADA", outline="#777777")
            c.create_line(x, y, x+ww, y+hh, fill="#AAAAAA")
            c.create_line(x+ww, y, x, y+hh, fill="#AAAAAA")
        elif cls == "AsmProgressBar":
            c.create_rectangle(x, y, x+ww, y+hh, fill="#FFFFFF", outline="#9E9E9E")
            c.create_rectangle(x+2, y+2, x+int(ww*0.55), y+hh-2, fill="#06B025", outline="")
        elif cls == "AsmSlider":
            c.create_line(x+8, y+hh/2, x+ww-8, y+hh/2, fill="#777777", width=2)
            c.create_rectangle(x+ww/2-5, y+4, x+ww/2+5, y+hh-4, fill="#EAEAEA", outline="#777777")
        elif cls == "AsmHorizontalLine":
            c.create_line(x, y+1, x+ww, y+1, fill="#999999")
        else:
            c.create_rectangle(x, y, x+ww, y+hh, fill="#EFEFEF", outline="#9E9E9E")
            c.create_text(x+ww/2, y+hh/2, text=name, fill="#000000", font=("Segoe UI", 9))

    def generate_asm_code(self, live_props=False):
        if live_props:
            self.update_properties_ui()

        caption = asm_text(self.form_title)
        self.update_live_preview()
        const_lines = ""
        for idx, w in enumerate(self.widgets_list, start=1001):
            const_lines += f"    {w.id_symbol()} equ {idx}\n"

        code = f""".386
.model flat, stdcall
option casemap:none

include \\masm32\\include\\windows.inc
include \\masm32\\include\\user32.inc
include \\masm32\\include\\kernel32.inc
include \\masm32\\include\\comctl32.inc
includelib \\masm32\\lib\\user32.lib
includelib \\masm32\\lib\\kernel32.lib
includelib \\masm32\\lib\\comctl32.lib

WinMain proto :DWORD, :DWORD, :DWORD, :DWORD
WndProc proto :DWORD, :DWORD, :DWORD, :DWORD

.const
    IDC_BASE equ 1000
{const_lines}
.data
    ClassName   db "EBS_Modern_Form", 0
    CaptionText db "{caption}", 0
    BtnClass      db "BUTTON", 0
    StaticClass   db "STATIC", 0
    EditClass     db "EDIT", 0
    ComboClass    db "COMBOBOX", 0
    ListClass     db "LISTBOX", 0
    ProgressClass db "msctls_progress32", 0
    TrackbarClass db "msctls_trackbar32", 0
    DateTimeClass db "SysDateTimePick32", 0
    msgCaption db "Event", 0
    msgCustom db "Mesaj", 0

"""

        for w in self.widgets_list:
            code += w.get_asm_data()
            for ev, ev_code in getattr(w, "events", {}).items():
                if ev_code:
                    code += f'    msg_{w.handler_name(ev)} db "{asm_text(w.name + " " + ev)}", 0\n' 

        code += f"""
.data?
    hInstance   HINSTANCE ?
    hForm       HWND ?

.code
start:
    invoke GetModuleHandle, NULL
    mov hInstance, eax
    invoke WinMain, hInstance, NULL, NULL, SW_SHOWDEFAULT
    invoke ExitProcess, eax

WinMain proc hInst:HINSTANCE, hPrevInst:HINSTANCE, CmdLine:LPSTR, CmdShow:DWORD
    LOCAL wc:WNDCLASSEX
    LOCAL msg:MSG

    invoke InitCommonControls

    mov wc.cbSize, SIZEOF WNDCLASSEX
    mov wc.style, CS_HREDRAW or CS_VREDRAW
    mov wc.lpfnWndProc, OFFSET WndProc
    mov wc.cbClsExtra, 0
    mov wc.cbWndExtra, 0
    push hInst
    pop wc.hInstance
    mov wc.hbrBackground, COLOR_BTNFACE+1
    mov wc.lpszMenuName, NULL
    mov wc.lpszClassName, OFFSET ClassName
    invoke LoadIcon, NULL, IDI_APPLICATION
    mov wc.hIcon, eax
    mov wc.hIconSm, eax
    invoke LoadCursor, NULL, IDC_ARROW
    mov wc.hCursor, eax
    invoke RegisterClassEx, ADDR wc

    ; Main form
    invoke CreateWindowEx, NULL, ADDR ClassName, ADDR CaptionText, \\
            WS_OVERLAPPED or WS_CAPTION or WS_SYSMENU or WS_MINIMIZEBOX, \\
            CW_USEDEFAULT, CW_USEDEFAULT, {self.form_width + 16}, {self.form_height + 39}, NULL, NULL, hInst, NULL
    mov hForm, eax

    ; Designed components
"""

        for w in self.widgets_list:
            code += w.get_asm_creation()

        code += """    invoke ShowWindow, hForm, CmdShow
    invoke UpdateWindow, hForm

@@MsgLoop:
    invoke GetMessage, ADDR msg, NULL, 0, 0
    cmp eax, 0
    je @@ExitLoop
    invoke TranslateMessage, ADDR msg
    invoke DispatchMessage, ADDR msg
    jmp @@MsgLoop

@@ExitLoop:
    mov eax, msg.wParam
    ret
WinMain endp

WndProc proc hWnd:HWND, uMsg:UINT, wParam:WPARAM, lParam:LPARAM
    .IF uMsg == WM_COMMAND
        mov eax, wParam
        mov edx, eax
        shr edx, 16
        and eax, 0FFFFh
"""

        for w in self.widgets_list:
            for ev, ev_code in getattr(w, "events", {}).items():
                if ev_code:
                    notify = self.event_notification_const(w, ev)
                    code += f"    .IF eax == {w.id_symbol()}\n"
                    code += f"        .IF edx == {notify}\n"
                    code += f"            call {w.handler_name(ev)}\n"
                    code += "            xor eax, eax\n            ret\n"
                    code += "        .ENDIF\n"
                    code += "    .ENDIF\n"

        code += """    .ELSEIF uMsg == WM_DESTROY
        invoke PostQuitMessage, NULL
        xor eax, eax
        ret
    .ELSE
        invoke DefWindowProc, hWnd, uMsg, wParam, lParam
        ret
    .ENDIF
    xor eax, eax
    ret
WndProc endp

"""

        for w in self.widgets_list:
            for ev, ev_code in getattr(w, "events", {}).items():
                if ev_code:
                    code += f"{w.handler_name(ev)} proc\n"
                    code += ev_code.rstrip() + "\n"
                    code += "    ret\n"
                    code += f"{w.handler_name(ev)} endp\n\n"

        code += """end start
"""
        self.code_view.delete("1.0", tk.END)
        self.code_view.insert(tk.END, code)

    def compile_and_run(self):
        self.notebook.select(1)
        self.log("[Süreç] Proje binary dosyaya dönüştürülüyor...")
        asm_file = "studio_code.asm"
        obj_file = "studio_code.obj"
        exe_file = "studio_code.exe"
        
        try:
            with open(asm_file, "w", encoding="ascii", errors="replace") as f:
                f.write(self.code_view.get("1.0", tk.END))
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya yazma hatası: {e}")
            return

        ml_path = os.path.join(self.MASM_PATH, "bin", "ml.exe")
        link_path = os.path.join(self.MASM_PATH, "bin", "link.exe")

        if not os.path.exists(ml_path) or not os.path.exists(link_path):
            self.log("[HATA] Derleyici setleri bulunamadı.")
            return

        comp_res = subprocess.run([ml_path, "/c", "/coff", "/Cp", asm_file], capture_output=True, text=True, creationflags=0x08000000)
        if comp_res.returncode != 0:
            self.log("[HATA] Derleme Hatası:\n" + comp_res.stdout)
            return

        link_res = subprocess.run([link_path, "/SUBSYSTEM:WINDOWS", obj_file], capture_output=True, text=True, creationflags=0x08000000)
        if link_res.returncode != 0:
            self.log("[HATA] Link Hatası:\n" + link_res.stdout)
            return

        self.log("[Başarılı] Derlenen native exe başlatılıyor...")
        try:
            subprocess.Popen([exe_file])
        except Exception as e:
            self.log(f"[HATA] Çalıştırma hatası: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = AsmDesignerIDE(root)
    root.mainloop()