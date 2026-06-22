import tkinter as tk


def asm_identifier(value):
    """MASM icin guvenli sembol adi uretir."""
    value = str(value).strip() or "item"
    cleaned = []
    for ch in value:
        if ch.isalnum() or ch == "_":
            cleaned.append(ch)
        else:
            cleaned.append("_")
    ident = "".join(cleaned)
    ident = "".join(ch if ord(ch) < 128 else "_" for ch in ident)
    ident = ident.strip("_") or "item"
    if ident[0].isdigit():
        ident = "n_" + ident
    return ident


def asm_text(value):
    """MASM ASCII build icin guvenli db metni uretir."""
    value = str(value)
    table = str.maketrans({
        "ç": "c", "Ç": "C", "ğ": "g", "Ğ": "G",
        "ı": "i", "İ": "I", "ö": "o", "Ö": "O",
        "ş": "s", "Ş": "S", "ü": "u", "Ü": "U",
    })
    value = value.translate(table)
    value = value.replace('\\', '\\\\').replace('"', "'")
    return "".join(ch if 32 <= ord(ch) <= 126 else "?" for ch in value)


class BaseComponent:
    """Canvas uzerindeki form nesnelerine secme, surukleme ve boyutlandirma verir."""

    MIN_WIDTH = 40
    MIN_HEIGHT = 20
    RESIZER_SIZE = 8
    DEFAULT_WIDTH = 120
    DEFAULT_HEIGHT = 35
    PREVIEW_TEXT_COLOR = "#FFFFFF"

    def __init__(self, canvas, name, x, y, bg_color, focus_color, on_update_callback):
        self.canvas = canvas
        self.name = name
        self.x = int(x)
        self.y = int(y)
        self.width = int(self.DEFAULT_WIDTH)
        self.height = int(self.DEFAULT_HEIGHT)
        self.bg_color = bg_color
        self.focus_color = focus_color
        self.on_update = on_update_callback
        # Visual Studio benzeri event altyapisi. Deger None ise henuz olusturulmamis demektir.
        self.events = {event_name: None for event_name in self.available_events()}

        self.start_x = 0
        self.start_y = 0
        self.start_w_x = 0
        self.start_w_y = 0

        self.rect = canvas.create_rectangle(
            self.x, self.y, self.x + self.width, self.y + self.height,
            fill=bg_color, outline="#555555", width=1
        )
        self.txt = canvas.create_text(
            self.x + (self.width / 2), self.y + (self.height / 2),
            text=self.preview_text(), fill=self.PREVIEW_TEXT_COLOR, font=("Segoe UI", 9, "bold")
        )
        self.resizer = canvas.create_rectangle(
            self.x + self.width - self.RESIZER_SIZE,
            self.y + self.height - self.RESIZER_SIZE,
            self.x + self.width,
            self.y + self.height,
            fill="#FFFFFF", outline="#555555"
        )

        self.canvas.tag_bind(self.rect, "<Enter>", lambda e: self.canvas.config(cursor="fleur"))
        self.canvas.tag_bind(self.txt, "<Enter>", lambda e: self.canvas.config(cursor="fleur"))
        self.canvas.tag_bind(self.resizer, "<Enter>", lambda e: self.canvas.config(cursor="sizing"))
        for item in (self.rect, self.txt, self.resizer):
            self.canvas.tag_bind(item, "<Leave>", lambda e: self.canvas.config(cursor=""))

        for item in (self.rect, self.txt):
            self.canvas.tag_bind(item, "<Button-1>", self.on_click)
            self.canvas.tag_bind(item, "<B1-Motion>", self.on_drag)
            self.canvas.tag_bind(item, "<ButtonRelease-1>", self.on_release)

        self.canvas.tag_bind(self.resizer, "<Button-1>", self.on_resize_start)
        self.canvas.tag_bind(self.resizer, "<B1-Motion>", self.on_resize_drag)
        self.canvas.tag_bind(self.resizer, "<ButtonRelease-1>", self.on_release)

    def preview_text(self):
        return self.name

    def symbol(self):
        return asm_identifier(self.name)

    def text_symbol(self):
        return f"txt_{self.symbol()}"

    def id_symbol(self):
        return f"IDC_{self.symbol().upper()}"

    def handler_name(self, event_name):
        return f"{self.symbol()}_{asm_identifier(event_name)}"

    def available_events(self):
        return ["Click"]

    def ensure_event(self, event_name):
        if event_name not in self.events:
            self.events[event_name] = None
        if self.events[event_name] is None:
            self.events[event_name] = self.default_event_code(event_name)
        return self.events[event_name]

    def default_event_code(self, event_name):
        if event_name == "Click":
            return f'    invoke MessageBox, hForm, ADDR msg_{self.handler_name(event_name)}, ADDR msgCaption, MB_OK\n'
        return "    ; event code here\n"

    def _ide(self):
        return getattr(self.canvas, "ide", None)

    def _select_self(self):
        ide = self._ide()
        if ide is not None:
            ide.select_widget(self)
        else:
            self.focus()

    def on_click(self, event):
        self._select_self()
        self.start_x = event.x
        self.start_y = event.y
        return "break"

    def unfocus(self):
        self.canvas.itemconfig(self.rect, outline="#555555", width=1)

    def focus(self):
        self.canvas.itemconfig(self.rect, outline=self.focus_color, width=2)
        self.canvas.tag_raise(self.rect)
        self.canvas.tag_raise(self.txt)
        self.canvas.tag_raise(self.resizer)

    def on_drag(self, event):
        dx = event.x - self.start_x
        dy = event.y - self.start_y
        self.x += dx
        self.y += dy
        self.redraw()
        self.start_x = event.x
        self.start_y = event.y
        self.on_update(live_props=True)
        return "break"

    def on_resize_start(self, event):
        self._select_self()
        self.start_w_x = event.x
        self.start_w_y = event.y
        return "break"

    def on_resize_drag(self, event):
        dw = event.x - self.start_w_x
        dh = event.y - self.start_w_y
        self.width = max(self.MIN_WIDTH, self.width + dw)
        self.height = max(self.MIN_HEIGHT, self.height + dh)
        self.redraw()
        self.start_w_x = event.x
        self.start_w_y = event.y
        self.on_update(live_props=True)
        return "break"

    def on_release(self, event):
        self.on_update(live_props=True)
        return "break"

    def redraw(self):
        self.canvas.coords(self.rect, self.x, self.y, self.x + self.width, self.y + self.height)
        self.canvas.coords(self.txt, self.x + (self.width / 2), self.y + (self.height / 2))
        self.canvas.coords(
            self.resizer,
            self.x + self.width - self.RESIZER_SIZE,
            self.y + self.height - self.RESIZER_SIZE,
            self.x + self.width,
            self.y + self.height
        )
        self.canvas.itemconfig(self.txt, text=self.preview_text())
        self.focus()

    def update_geometry(self, x, y, w, h):
        self.x = int(x)
        self.y = int(y)
        self.width = int(w)
        self.height = int(h)
        self.redraw()
        self.on_update(live_props=False)

    def get_asm_data(self):
        return f'    {self.text_symbol()} db "{asm_text(self.name)}", 0\n'

    def window_text_arg(self):
        return f"ADDR {self.text_symbol()}"

    def ex_style(self):
        return "NULL"

    def asm_class(self):
        return "StaticClass"

    def style(self):
        return "WS_CHILD or WS_VISIBLE"

    def post_create_code(self):
        return ""

    def get_asm_creation(self):
        code = f"    ; --- {self.__class__.__name__[3:]}: {asm_text(self.name)} ---\n"
        code += f"    invoke CreateWindowEx, {self.ex_style()}, ADDR {self.asm_class()}, {self.window_text_arg()}, \\\n"
        code += f"            {self.style()}, \\\n"
        code += f"            {self.x}, {self.y}, {self.width}, {self.height}, hForm, NULL, hInst, NULL\n"
        code += self.post_create_code()
        code += "\n"
        return code


class AsmButton(BaseComponent):
    DEFAULT_WIDTH = 120
    DEFAULT_HEIGHT = 35
    def __init__(self, canvas, name, x, y, on_update_callback):
        super().__init__(canvas, name, x, y, "#107C41", "#109B53", on_update_callback)
    def asm_class(self): return "BtnClass"
    def style(self): return "WS_CHILD or WS_VISIBLE or BS_PUSHBUTTON"


class AsmLabel(BaseComponent):
    DEFAULT_WIDTH = 120
    DEFAULT_HEIGHT = 28
    def __init__(self, canvas, name, x, y, on_update_callback):
        super().__init__(canvas, name, x, y, "#007ACC", "#1F9EFF", on_update_callback)
    def asm_class(self): return "StaticClass"
    def style(self): return "WS_CHILD or WS_VISIBLE or SS_LEFT"


class AsmTextBox(BaseComponent):
    def available_events(self): return ["Change", "GotFocus", "LostFocus"]
    DEFAULT_WIDTH = 160
    DEFAULT_HEIGHT = 28
    def __init__(self, canvas, name, x, y, on_update_callback):
        super().__init__(canvas, name, x, y, "#5A5A5A", "#C586C0", on_update_callback)
    def asm_class(self): return "EditClass"
    def ex_style(self): return "WS_EX_CLIENTEDGE"
    def style(self): return "WS_CHILD or WS_VISIBLE or WS_TABSTOP or ES_LEFT or ES_AUTOHSCROLL"


class AsmPasswordBox(AsmTextBox):
    def style(self): return "WS_CHILD or WS_VISIBLE or WS_TABSTOP or ES_LEFT or ES_PASSWORD or ES_AUTOHSCROLL"


class AsmTextArea(AsmTextBox):
    DEFAULT_WIDTH = 220
    DEFAULT_HEIGHT = 90
    def style(self): return "WS_CHILD or WS_VISIBLE or WS_TABSTOP or WS_VSCROLL or ES_LEFT or ES_MULTILINE or ES_AUTOVSCROLL"


class AsmCheckBox(BaseComponent):
    DEFAULT_WIDTH = 145
    DEFAULT_HEIGHT = 28
    def __init__(self, canvas, name, x, y, on_update_callback):
        super().__init__(canvas, name, x, y, "#795E26", "#D7BA7D", on_update_callback)
    def asm_class(self): return "BtnClass"
    def style(self): return "WS_CHILD or WS_VISIBLE or WS_TABSTOP or BS_AUTOCHECKBOX"


class AsmRadioButton(BaseComponent):
    DEFAULT_WIDTH = 145
    DEFAULT_HEIGHT = 28
    def __init__(self, canvas, name, x, y, on_update_callback):
        super().__init__(canvas, name, x, y, "#8E44AD", "#C586C0", on_update_callback)
    def asm_class(self): return "BtnClass"
    def style(self): return "WS_CHILD or WS_VISIBLE or WS_TABSTOP or BS_AUTORADIOBUTTON"


class AsmComboBox(BaseComponent):
    def available_events(self): return ["SelectionChange", "DropDown"]
    DEFAULT_WIDTH = 170
    DEFAULT_HEIGHT = 100
    def __init__(self, canvas, name, x, y, on_update_callback):
        super().__init__(canvas, name, x, y, "#264F78", "#3794FF", on_update_callback)
    def asm_class(self): return "ComboClass"
    def style(self): return "WS_CHILD or WS_VISIBLE or WS_TABSTOP or CBS_DROPDOWNLIST or WS_VSCROLL"


class AsmListBox(BaseComponent):
    def available_events(self): return ["SelectionChange", "DoubleClick"]
    DEFAULT_WIDTH = 170
    DEFAULT_HEIGHT = 110
    def __init__(self, canvas, name, x, y, on_update_callback):
        super().__init__(canvas, name, x, y, "#3C3C3C", "#9CDCFE", on_update_callback)
    def asm_class(self): return "ListClass"
    def ex_style(self): return "WS_EX_CLIENTEDGE"
    def style(self): return "WS_CHILD or WS_VISIBLE or WS_TABSTOP or WS_VSCROLL or LBS_NOTIFY"


class AsmGroupBox(BaseComponent):
    DEFAULT_WIDTH = 220
    DEFAULT_HEIGHT = 120
    def __init__(self, canvas, name, x, y, on_update_callback):
        super().__init__(canvas, name, x, y, "#333333", "#CE9178", on_update_callback)
    def asm_class(self): return "BtnClass"
    def style(self): return "WS_CHILD or WS_VISIBLE or BS_GROUPBOX"


class AsmPictureBox(BaseComponent):
    DEFAULT_WIDTH = 160
    DEFAULT_HEIGHT = 110
    def __init__(self, canvas, name, x, y, on_update_callback):
        super().__init__(canvas, name, x, y, "#4B4B4B", "#DCDCAA", on_update_callback)
    def asm_class(self): return "StaticClass"
    def style(self): return "WS_CHILD or WS_VISIBLE or SS_BLACKFRAME"


class AsmProgressBar(BaseComponent):
    def available_events(self): return []
    DEFAULT_WIDTH = 180
    DEFAULT_HEIGHT = 24
    def __init__(self, canvas, name, x, y, on_update_callback):
        super().__init__(canvas, name, x, y, "#0E639C", "#3794FF", on_update_callback)
    def asm_class(self): return "ProgressClass"
    def window_text_arg(self): return "NULL"
    def style(self): return "WS_CHILD or WS_VISIBLE"
    def post_create_code(self):
        return "    invoke SendMessage, eax, PBM_SETRANGE, 0, 00640000h\n    invoke SendMessage, eax, PBM_SETPOS, 50, 0\n"


class AsmSlider(BaseComponent):
    def available_events(self): return ["Change"]
    DEFAULT_WIDTH = 180
    DEFAULT_HEIGHT = 35
    def __init__(self, canvas, name, x, y, on_update_callback):
        super().__init__(canvas, name, x, y, "#6A9955", "#B5CEA8", on_update_callback)
    def asm_class(self): return "TrackbarClass"
    def window_text_arg(self): return "NULL"
    def style(self): return "WS_CHILD or WS_VISIBLE or WS_TABSTOP or TBS_AUTOTICKS"


class AsmDateTimePicker(BaseComponent):
    def available_events(self): return ["Change"]
    DEFAULT_WIDTH = 180
    DEFAULT_HEIGHT = 28
    def __init__(self, canvas, name, x, y, on_update_callback):
        super().__init__(canvas, name, x, y, "#804000", "#CE9178", on_update_callback)
    def asm_class(self): return "DateTimeClass"
    def window_text_arg(self): return "NULL"
    def style(self): return "WS_CHILD or WS_VISIBLE or WS_TABSTOP or DTS_SHORTDATEFORMAT"


class AsmPanel(BaseComponent):
    DEFAULT_WIDTH = 220
    DEFAULT_HEIGHT = 130
    def __init__(self, canvas, name, x, y, on_update_callback):
        super().__init__(canvas, name, x, y, "#2D2D30", "#007ACC", on_update_callback)
    def asm_class(self): return "StaticClass"
    def style(self): return "WS_CHILD or WS_VISIBLE or SS_ETCHEDFRAME"


class AsmHorizontalLine(BaseComponent):
    def available_events(self): return []
    DEFAULT_WIDTH = 200
    DEFAULT_HEIGHT = 3
    MIN_HEIGHT = 3
    def __init__(self, canvas, name, x, y, on_update_callback):
        super().__init__(canvas, name, x, y, "#858585", "#FFFFFF", on_update_callback)
    def preview_text(self): return ""
    def asm_class(self): return "StaticClass"
    def window_text_arg(self): return "NULL"
    def style(self): return "WS_CHILD or WS_VISIBLE or SS_ETCHEDHORZ"
