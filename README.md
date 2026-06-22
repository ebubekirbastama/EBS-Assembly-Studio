# EBS Visual Assembly Studio

Visual Studio benzeri sürükle-bırak Form Designer ve MASM32 Assembly IDE.

EBS Visual Assembly Studio, Win32 uygulamalarını görsel olarak tasarlayıp otomatik olarak Assembly (MASM32) kaynak koduna dönüştüren açık kaynak bir geliştirme ortamıdır.

---

## Özellikler

### Form Designer

* Sürükle & Bırak Tasarım
* Mouse ile Nesne Taşıma
* Mouse ile Nesne Boyutlandırma
* Grid Hizalama Sistemi
* Canlı Form Önizleme
* Özellikler (Properties) Penceresi

### Desteklenen Kontroller

* Button
* Label
* TextBox
* PasswordBox
* TextArea
* CheckBox
* RadioButton
* ComboBox
* ListBox
* GroupBox
* PictureBox
* ProgressBar
* Slider
* DateTimePicker
* Panel
* HorizontalLine

### Event Sistemi

Visual Studio benzeri Event Yönetimi:

* Click
* Change
* SelectionChange
* DoubleClick
* MouseEnter
* MouseLeave
* KeyPress

Event oluşturulduğunda ilgili Assembly prosedürü otomatik oluşturulur.

Örnek:

```asm
btnLogin_Click PROC

    invoke MessageBox,\
           NULL,\
           chr$("Giriş Başarılı"),\
           chr$("Bilgi"),\
           MB_OK

    ret

btnLogin_Click ENDP
```

---

## Kod Üretici

Tasarım ekranında oluşturulan tüm bileşenler otomatik olarak:

* Win32 API
* MASM32
* Native Windows EXE

koduna dönüştürülür.

Desteklenen API'ler:

* CreateWindowEx
* MessageBox
* SendMessage
* SetWindowText
* GetWindowText
* ShowWindow
* UpdateWindow

---

## Derleme

### Gereksinimler

* Windows 10 / 11
* Python 3.10+
* MASM32 SDK

MASM32 varsayılan kurulum yolu:

```text
C:\masm32
```

### Çalıştırma

```bash
python asm_ide.py
```

### Derleme

IDE içerisinden:

```text
DERLE VE ÇALIŞTIR
```

butonuna basmanız yeterlidir.

---

## Yol Haritası

### v1.1

* MenuStrip
* ToolBar
* StatusBar
* TreeView
* ListView
* TabControl

### v1.2

* Event Code Editor
* Assembly Syntax Highlight
* Project Explorer
* Resource Manager

### v2.0

* Visual Studio Benzeri Designer
* Çoklu Form Desteği
* DLL Oluşturma
* x64 Desteği
* FASM Desteği

---

## Ekran Görüntüsü

```text
Toolbox          Form Designer          Properties
-------------------------------------------------
Button           [ Tasarım Alanı ]      Name
TextBox          [ Live Preview ]       Size
ComboBox                                 Events
```

---

## Katkıda Bulunma

Pull Request gönderebilir veya Issue açabilirsiniz.

---

## Lisans

MIT License

---

## Geliştirici

Yusuf Küçük

GitHub:
https://github.com/ebubekirbastama/EBS-Assembly-Studio

Proje:
EBS Visual Assembly Studio
