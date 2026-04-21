#!/usr/bin/env python3
import ssl
import os
import subprocess
import shutil
import webbrowser
import time
import sys

# Fix SSL on Mac
ssl._create_default_https_context = ssl._create_unverified_context

from flask import Flask, request, jsonify
from flask_cors import CORS
from pyngrok import ngrok, conf

app = Flask(__name__)
CORS(app, origins="*", allow_headers=["Content-Type", "ngrok-skip-browser-warning"])

@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    return response

@app.route("/ping", methods=["GET", "OPTIONS"])
def ping():
    return jsonify({"status": "ok", "version": "1.0.0", "name": "Mi Agente Local"})

@app.route("/execute", methods=["POST", "OPTIONS"])
def execute():
    if request.method == "OPTIONS":
        return jsonify({}), 200
    data = request.json
    steps = data.get("steps", [])
    variables = data.get("variables", {})
    results = []

    def resolve(text):
        if not isinstance(text, str):
            return text
        for k, v in variables.items():
            text = text.replace("{" + k + "}", str(v))
        return text

    for i, step in enumerate(steps):
        t = step.get("type", "")
        p = {k: resolve(v) for k, v in step.get("params", {}).items()}
        try:
            if t == "create_folder":
                os.makedirs(p.get("path", ""), exist_ok=True)
                results.append({"step_index": i, "status": "success", "message": f"Carpeta creada: {p.get('path')}"})
            elif t == "open_url":
                webbrowser.open(p.get("url", ""))
                results.append({"step_index": i, "status": "success", "message": f"URL abierta: {p.get('url')}"})
            elif t == "run_command":
                out = subprocess.check_output(p.get("command", ""), shell=True, text=True, timeout=30)
                results.append({"step_index": i, "status": "success", "message": out.strip()[:500]})
            elif t == "copy_file":
                shutil.copy2(p.get("source", ""), p.get("destination", ""))
                results.append({"step_index": i, "status": "success", "message": "Archivo copiado"})
            elif t == "move_file":
                shutil.move(p.get("source", ""), p.get("destination", ""))
                results.append({"step_index": i, "status": "success", "message": "Archivo movido"})
            elif t == "delete_file":
                path = p.get("path", "")
                if os.path.isfile(path): os.remove(path)
                elif os.path.isdir(path): shutil.rmtree(path)
                results.append({"step_index": i, "status": "success", "message": "Eliminado"})
            elif t == "open_application":
                subprocess.Popen(p.get("app_path", ""), shell=True)
                results.append({"step_index": i, "status": "success", "message": "Aplicación abierta"})
            elif t == "wait":
                time.sleep(float(p.get("seconds", 1)))
                results.append({"step_index": i, "status": "success", "message": "Espera completada"})
            else:
                results.append({"step_index": i, "status": "success", "message": f"Paso '{t}' procesado"})
        except Exception as e:
            results.append({"step_index": i, "status": "error", "message": str(e)})

    return jsonify({"success": True, "step_results": results})

if __name__ == "__main__":
    print("🌐 Iniciando túnel ngrok...")
    tunnel = ngrok.connect(5000)
    url = tunnel.public_url
    if url.startswith("http://"):
        url = url.replace("http://", "https://")

    print("\n" + "="*60)
    print("✅ TU AGENTE ESTÁ LISTO")
    print("="*60)
    print(f"\n🔗 URL DEL AGENTE:\n\n   {url}\n")
    print("👆 Copia esta URL y pégala en la app > Ajustes > URL del Agente")
    print("="*60 + "\n")

    try:
        import pyperclip
        pyperclip.copy(url)
        print("📋 URL copiada al portapapeles!")
    except:
        pass

    print("⚡ Agente ejecutándose... (No cierres esta ventana)\n")
    app.run(host="0.0.0.0", port=5000)
