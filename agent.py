#!/usr/bin/env python3
import os, sys, time, subprocess, shutil, webbrowser, threading
import tkinter as tk
from tkinter import ttk
from flask import Flask, request, jsonify
from flask_cors import CORS
from pyngrok import ngrok
import pyautogui
import pyperclip

app = Flask(__name__)
CORS(app)

@app.after_request
def add_cors(r):
    r.headers["Access-Control-Allow-Origin"] = "*"
    r.headers["Access-Control-Allow-Headers"] = "*"
    r.headers["Access-Control-Allow-Methods"] = "*"
    return r

@app.route("/ping")
def ping():
    return jsonify({"status": "ok", "version": "2.0.0", "name": "Robot Agent"})

@app.route("/execute", methods=["POST", "OPTIONS"])
def execute():
    if request.method == "OPTIONS":
        return jsonify({}), 200
    data = request.json
    steps = data.get("steps", [])
    variables = data.get("variables", {})
    results = []

    def resolve(text):
        if not isinstance(text, str): return text
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
            elif t == "mouse_click":
                pyautogui.click(int(p.get("x", 0)), int(p.get("y", 0)))
                results.append({"step_index": i, "status": "success", "message": f"Click en {p.get('x')},{p.get('y')}"})
            elif t == "mouse_move":
                pyautogui.moveTo(int(p.get("x", 0)), int(p.get("y", 0)))
                results.append({"step_index": i, "status": "success", "message": "Ratón movido"})
            elif t == "type_text":
                pyautogui.typewrite(p.get("text", ""), interval=0.05)
                results.append({"step_index": i, "status": "success", "message": "Texto escrito"})
            elif t == "press_key":
                pyautogui.press(p.get("key", ""))
                results.append({"step_index": i, "status": "success", "message": f"Tecla pulsada: {p.get('key')}"})
            elif t == "screenshot":
                img = pyautogui.screenshot()
                path = p.get("path", "screenshot.png")
                img.save(path)
                results.append({"step_index": i, "status": "success", "message": f"Captura guardada: {path}"})
            elif t == "wait":
                time.sleep(float(p.get("seconds", 1)))
                results.append({"step_index": i, "status": "success", "message": "Espera completada"})
            else:
                results.append({"step_index": i, "status": "success", "message": f"Paso '{t}' procesado"})
        except Exception as e:
            results.append({"step_index": i, "status": "error", "message": str(e)})

    return jsonify({"success": True, "step_results": results})


def start_flask():
    app.run(host="0.0.0.0", port=5000, use_reloader=False)


def main():
    # Start Flask in background
    t = threading.Thread(target=start_flask, daemon=True)
    t.start()
    time.sleep(1)

    # Start ngrok
    tunnel = ngrok.connect(5000)
    url = tunnel.public_url.replace("http://", "https://")

    # Copy to clipboard
    try:
        pyperclip.copy(url)
    except:
        pass

    # Simple GUI window
    root = tk.Tk()
    root.title("Robot Agent")
    root.geometry("420x220")
    root.resizable(False, False)
    root.configure(bg="#0f1117")

    tk.Label(root, text="🤖 Robot Agent", font=("Helvetica", 16, "bold"),
             bg="#0f1117", fg="#22d3ee").pack(pady=(20, 5))
    tk.Label(root, text="Tu agente está activo. Copia la URL en la app:",
             font=("Helvetica", 10), bg="#0f1117", fg="#94a3b8").pack()

    url_var = tk.StringVar(value=url)
    entry = tk.Entry(root, textvariable=url_var, font=("Courier", 9),
                     bg="#1e293b", fg="#22d3ee", bd=0, relief="flat",
                     width=45, justify="center")
    entry.pack(pady=10, padx=20)
    entry.config(state="readonly")

    def copy_url():
        pyperclip.copy(url)
        btn.config(text="✅ Copiada!")
        root.after(2000, lambda: btn.config(text="📋 Copiar URL"))

    btn = tk.Button(root, text="📋 Copiar URL", command=copy_url,
                    bg="#22d3ee", fg="#0f1117", font=("Helvetica", 10, "bold"),
                    relief="flat", padx=20, pady=6, cursor="hand2")
    btn.pack()

    tk.Label(root, text="⚡ No cierres esta ventana mientras uses el agente",
             font=("Helvetica", 8), bg="#0f1117", fg="#475569").pack(pady=(10, 0))

    root.mainloop()


if __name__ == "__main__":
    main()
