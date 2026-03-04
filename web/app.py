"""
Aplicación Web Flask para visualización de Facturas OCR
"""

import os
import json
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, send_file, jsonify, request, abort
import openpyxl

app = Flask(__name__)

PROCESSED_DIR = Path("/srv/facturas/procesadas")
EXCEL_PATH    = Path("/srv/facturas/facturas.xlsx")
LOG_PATH      = Path("/srv/facturas/ocr.log")


def get_facturas():
    """Lee facturas del Excel y retorna lista de dicts."""
    if not EXCEL_PATH.exists():
        return []
    try:
        wb = openpyxl.load_workbook(EXCEL_PATH)
        ws = wb.active
        facturas = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            if any(row):
                facturas.append({
                    "numero":     row[0] or "-",
                    "fecha":      row[1] or "-",
                    "proveedor":  row[2] or "-",
                    "total":      row[3] or 0,
                    "archivo":    row[4] or "",
                    "procesado":  row[5] or "-",
                })
        return facturas
    except Exception as e:
        return []


def get_stats(facturas):
    totales = [f["total"] for f in facturas if isinstance(f["total"], (int, float))]
    return {
        "total_facturas": len(facturas),
        "monto_total":    sum(totales),
        "monto_promedio": sum(totales) / len(totales) if totales else 0,
        "ultimo_escaneo": facturas[-1]["procesado"] if facturas else "-",
    }


@app.route("/")
def index():
    facturas = get_facturas()
    stats = get_stats(facturas)
    return render_template("index.html", facturas=facturas, stats=stats)


@app.route("/api/facturas")
def api_facturas():
    return jsonify(get_facturas())


@app.route("/api/stats")
def api_stats():
    return jsonify(get_stats(get_facturas()))


@app.route("/descargar/excel")
def descargar_excel():
    if not EXCEL_PATH.exists():
        abort(404)
    return send_file(EXCEL_PATH, as_attachment=True,
                     download_name="facturas.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.route("/ver/<filename>")
def ver_archivo(filename):
    """Visualiza/descarga un archivo procesado."""
    safe_name = Path(filename).name
    file_path = PROCESSED_DIR / safe_name
    if not file_path.exists():
        abort(404)
    suffix = file_path.suffix.lower()
    mimetype_map = {
        ".pdf":  "application/pdf",
        ".jpg":  "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png":  "image/png",
        ".tiff": "image/tiff",
        ".tif":  "image/tiff",
    }
    mime = mimetype_map.get(suffix, "application/octet-stream")
    return send_file(file_path, mimetype=mime)


@app.route("/logs")
def ver_logs():
    """Retorna las últimas 100 líneas del log."""
    if not LOG_PATH.exists():
        return jsonify({"lines": []})
    with open(LOG_PATH, "r") as f:
        lines = f.readlines()
    return jsonify({"lines": [l.rstrip() for l in lines[-100:]]})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
