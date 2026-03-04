# 🧾 Invoice OCR System — Sistema OCR de Facturas

Sistema automatizado para el procesamiento de facturas de proveedores mediante OCR. Recibe documentos escaneados vía carpeta de red Samba, extrae datos automáticamente y los publica en una interfaz web con exportación a Excel.

## ✨ Características

- 📥 **Carpeta compartida Samba** — Solo accesible desde la red interna (`192.168.10.0/24`)
- 🔍 **OCR con Tesseract** — Procesa PDF, JPG, PNG, TIFF en español e inglés
- 📝 **Extracción automática** — Número de factura, fecha, proveedor, monto total
- 📂 **Renombrado automático** — Los archivos pasan a llamarse `Factura XXXX.pdf`
- 📊 **Excel automático** — Cada factura agrega una fila formateada al archivo `.xlsx`
- 🌐 **Interfaz web moderna** — Panel con estadísticas, tabla de facturas y logs en tiempo real
- 🔁 **Servicio systemd** — Arranque automático y supervisión permanente

## 🏗️ Arquitectura

```
Escáner (red LAN)
      │
      ▼
\\servidor\Facturas  (Samba)
      │
      ▼
/srv/facturas/escaneadas/
      │
      ▼ (watchdog)
ocr_processor.py
  ├── Tesseract OCR (spa+eng)
  ├── Extracción con regex
  ├── Renombrado → /srv/facturas/procesadas/
  └── Excel → /srv/facturas/facturas.xlsx
      │
      ▼
web/app.py (Flask)
      │
      ▼
Nginx :80 → http://192.168.10.14/
```

## 📁 Estructura del Proyecto

```
factura-ocr/
├── ocr_processor.py        # Script principal OCR + watchdog
├── web/
│   ├── app.py              # Aplicación Flask
│   └── templates/
│       └── index.html      # Interfaz web
├── smb.conf                # Configuración Samba
├── nginx-facturas.conf     # Configuración Nginx
├── ocr-facturas.service    # Systemd: OCR processor
├── web-facturas.service    # Systemd: Web app
├── requirements.txt        # Dependencias Python
└── README.md
```

## 🚀 Instalación en Servidor (Ubuntu 22.04)

### 1. Paquetes del sistema

```bash
apt-get update
apt-get install -y tesseract-ocr tesseract-ocr-spa \
    samba samba-common poppler-utils imagemagick \
    python3-pip python3-venv nginx inotify-tools
```

### 2. Dependencias Python

```bash
pip3 install -r requirements.txt
```

### 3. Crear estructura de directorios

```bash
mkdir -p /srv/facturas/{escaneadas,procesadas,web/static,web/templates}
chmod 755 /srv/facturas/escaneadas /srv/facturas/procesadas
```

### 4. Subir archivos al servidor

```bash
scp ocr_processor.py root@192.168.10.14:/srv/facturas/
scp -r web/ root@192.168.10.14:/srv/facturas/
```

### 5. Configurar Samba

```bash
cp smb.conf /etc/samba/smb.conf
systemctl restart smbd nmbd
systemctl enable smbd nmbd
```

### 6. Configurar Nginx

```bash
cp nginx-facturas.conf /etc/nginx/sites-available/facturas.conf
ln -s /etc/nginx/sites-available/facturas.conf /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx && systemctl enable nginx
```

### 7. Configurar servicios systemd

```bash
cp ocr-facturas.service /etc/systemd/system/
cp web-facturas.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable ocr-facturas web-facturas
systemctl start ocr-facturas web-facturas
```

## 🖥️ Uso

### Acceso a la interfaz web

```
http://192.168.10.14/
```

### Carpeta compartida (para el escáner)

| Sistema | Ruta |
|---------|------|
| Windows | `\\192.168.10.14\Facturas` |
| macOS | `smb://192.168.10.14/Facturas` (Finder: ⌘+K) |
| Linux | `smb://192.168.10.14/Facturas` |

### Flujo automático

1. El escáner guarda el archivo en `\\servidor\Facturas`
2. El sistema detecta el nuevo archivo automáticamente
3. Tesseract OCR extrae el texto del documento
4. Se identifican los datos con expresiones regulares
5. El archivo se renombra a `Factura XXXX.pdf` y se mueve a `procesadas/`
6. Los datos se agregan al Excel y aparecen en la web

## ⚙️ Administración

```bash
# Ver estado de servicios
systemctl status ocr-facturas web-facturas nginx smbd

# Ver logs en tiempo real
journalctl -u ocr-facturas -f
journalctl -u web-facturas -f

# Reiniciar servicios
systemctl restart ocr-facturas web-facturas

# Ver Excel en el servidor
ls -la /srv/facturas/facturas.xlsx

# Ver log del OCR
tail -f /srv/facturas/ocr.log
```

## 🔧 Configuración

### Formatos de archivo soportados

| Formato | Extensión |
|---------|-----------|
| PDF | `.pdf` |
| JPEG | `.jpg`, `.jpeg` |
| PNG | `.png` |
| TIFF | `.tiff`, `.tif` |
| BMP | `.bmp` |

### Variables en `ocr_processor.py`

| Variable | Valor por defecto | Descripción |
|----------|-------------------|-------------|
| `SCAN_DIR` | `/srv/facturas/escaneadas` | Carpeta de entrada |
| `PROCESSED_DIR` | `/srv/facturas/procesadas` | Carpeta de salida |
| `EXCEL_PATH` | `/srv/facturas/facturas.xlsx` | Archivo Excel |
| `TESSERACT_LANG` | `spa+eng` | Idiomas OCR |

## 📦 Dependencias

| Paquete | Versión | Uso |
|---------|---------|-----|
| `pytesseract` | ≥0.3.10 | Interfaz Python para Tesseract |
| `Pillow` | ≥9.0 | Procesamiento de imágenes |
| `pdf2image` | ≥1.16 | Conversión PDF → imagen |
| `openpyxl` | ≥3.0 | Lectura/escritura Excel |
| `Flask` | ≥2.2 | Framework web |
| `watchdog` | ≥3.0 | Monitor de sistema de archivos |

## 🔒 Seguridad

- La carpeta Samba **solo es accesible desde** `192.168.10.0/24`
- Nginx actúa como **reverse proxy** (Flask no expuesto directamente)
- El acceso a la web no requiere autenticación (red interna)

## 📄 Licencia

MIT License — Libre para uso interno y comercial.
