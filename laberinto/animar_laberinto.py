import os
import csv
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- CONFIGURACIÓN ---
ARCHIVO_C = "laberinto.c"
EJECUTABLE_C = "laberinto.exe" if os.name == "nt" else "./laberinto"
CSV_LABERINTO = "laberinto_150x150.csv"
TXT_HISTORIA = "historia_laberinto.txt"

class AplicacionLaberintoAG:
    def __init__(self, root):
        self.root = root
        self.root.title("Algoritmo Genético - Navegación en Laberinto 150x150")
        self.root.geometry("1280x820")
        self.root.configure(bg="#f4f6f9")

        self.laberinto = self.cargar_csv()
        self.hitos_evolucion = []
        self.indice_actual = 0
        self.animando = False

        self.origen_r, self.origen_c = 1, 147
        self.destino_r, self.destino_c = 147, 147

        self.crear_interfaz()
        self.compilar_c_si_necesario()
        self.dibujar_vista_previa()

    def cargar_csv(self):
        if not os.path.exists(CSV_LABERINTO):
            messagebox.showerror("Error", f"No se encontró el archivo {CSV_LABERINTO}")
            self.root.destroy()
            return None
        lista = []
        with open(CSV_LABERINTO, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    lista.append([int(val) for val in row if val != ''])
        return np.array(lista)

    def crear_interfaz(self):
        # --- BARRA SUPERIOR DE CONTROLES ---
        panel_controles = tk.Frame(self.root, bg="#2c3e50", pady=10, padx=15)
        panel_controles.pack(side=tk.TOP, fill=tk.X)

        # Origen (Fila, Col)
        tk.Label(panel_controles, text="Origen (Fila, Col):", bg="#2c3e50", fg="#2ecc71", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 4))
        self.spin_or_r = tk.Spinbox(panel_controles, from_=0, to=149, width=4, font=("Arial", 10))
        self.spin_or_r.delete(0, tk.END)
        self.spin_or_r.insert(0, "1")
        self.spin_or_r.pack(side=tk.LEFT, padx=2)

        self.spin_or_c = tk.Spinbox(panel_controles, from_=0, to=149, width=4, font=("Arial", 10))
        self.spin_or_c.delete(0, tk.END)
        self.spin_or_c.insert(0, "147")
        self.spin_or_c.pack(side=tk.LEFT, padx=(2, 12))

        # Destino (Fila, Col)
        tk.Label(panel_controles, text="Destino (Fila, Col):", bg="#2c3e50", fg="#3498db", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 4))
        self.spin_de_r = tk.Spinbox(panel_controles, from_=0, to=149, width=4, font=("Arial", 10))
        self.spin_de_r.delete(0, tk.END)
        self.spin_de_r.insert(0, "147")
        self.spin_de_r.pack(side=tk.LEFT, padx=2)

        self.spin_de_c = tk.Spinbox(panel_controles, from_=0, to=149, width=4, font=("Arial", 10))
        self.spin_de_c.delete(0, tk.END)
        self.spin_de_c.insert(0, "147")
        self.spin_de_c.pack(side=tk.LEFT, padx=(2, 12))

        # Selector rápido de esquinas
        tk.Label(panel_controles, text="Presets:", bg="#2c3e50", fg="white", font=("Arial", 9)).pack(side=tk.LEFT, padx=(0, 4))
        self.combo_presets = ttk.Combobox(panel_controles, values=[
            "Sup-Der (1,147) ➔ Inf-Der (147,147)",
            "Sup-Izq (1,1) ➔ Inf-Der (147,147)",
            "Inf-Izq (147,1) ➔ Sup-Der (1,147)",
            "Sup-Izq (1,1) ➔ Inf-Izq (147,1)"
        ], width=30, state="readonly")
        self.combo_presets.current(0)
        self.combo_presets.bind("<<ComboboxSelected>>", self.aplicar_preset)
        self.combo_presets.pack(side=tk.LEFT, padx=(0, 12))

        # Botones de acción
        btn_ejecutar = tk.Button(panel_controles, text="▶ Ejecutar", command=self.ejecutar_busqueda, bg="#27ae60", fg="white", font=("Arial", 10, "bold"), padx=10, relief=tk.FLAT, cursor="hand2")
        btn_ejecutar.pack(side=tk.LEFT, padx=4)

        btn_pausa = tk.Button(panel_controles, text="⏯ Pausar / Reanudar", command=self.alternar_pausa, bg="#f39c12", fg="white", font=("Arial", 10, "bold"), padx=10, relief=tk.FLAT, cursor="hand2")
        btn_pausa.pack(side=tk.LEFT, padx=4)

        btn_final = tk.Button(panel_controles, text="⏭ Ir a Ruta Final", command=self.ir_al_final, bg="#2980b9", fg="white", font=("Arial", 10, "bold"), padx=10, relief=tk.FLAT, cursor="hand2")
        btn_final.pack(side=tk.LEFT, padx=4)

        # --- CONTENEDOR PRINCIPAL ---
        contenedor = tk.Frame(self.root, bg="#f4f6f9")
        contenedor.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Lienzo de Matplotlib (Izquierda)
        self.fig, self.ax = plt.subplots(figsize=(8.5, 7.5), dpi=100)
        self.fig.patch.set_facecolor("#ffffff")
        self.canvas = FigureCanvasTkAgg(self.fig, master=contenedor)
        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.mpl_connect("button_press_event", self.clic_en_mapa)

        # Panel lateral de información (Derecha)
        panel_info = tk.Frame(contenedor, width=340, bg="white", bd=1, relief=tk.SOLID, padx=15, pady=12)
        panel_info.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        panel_info.pack_propagate(False)

        tk.Label(panel_info, text="EVOLUCIÓN DEL LABERINTO", bg="white", fg="#2c3e50", font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 8))
        
        self.lbl_estado = tk.Label(panel_info, text="Estado: Listo", bg="#ecf0f1", fg="#2c3e50", font=("Arial", 10, "bold"), padx=8, pady=6)
        self.lbl_estado.pack(fill=tk.X, pady=4)

        # Tarjeta destacada y grande para la Generación
        frame_gen = tk.Frame(panel_info, bg="#eef5fc", bd=1, relief=tk.SOLID, padx=10, pady=8)
        frame_gen.pack(fill=tk.X, pady=6)
        self.lbl_gen = tk.Label(frame_gen, text="GENERACIÓN: -", bg="#eef5fc", fg="#1a5276", font=("Arial", 16, "bold"))
        self.lbl_gen.pack(anchor="center")

        self.lbl_coords = tk.Label(panel_info, text="Trayecto: -", bg="white", fg="#34495e", font=("Arial", 10, "bold"))
        self.lbl_coords.pack(anchor="w", pady=4)

        self.lbl_pasos = tk.Label(panel_info, text="Longitud de Ruta: - pasos", bg="white", fg="#34495e", font=("Arial", 11, "bold"))
        self.lbl_pasos.pack(anchor="w", pady=4)

        self.lbl_costo = tk.Label(panel_info, text="Costo / Penalización: -", bg="white", fg="#c0392b", font=("Arial", 12, "bold"))
        self.lbl_costo.pack(anchor="w", pady=4)

        # Nota explicativa del Costo 0
        nota_frame = tk.Frame(panel_info, bg="#fff8e1", bd=1, relief=tk.SOLID, padx=8, pady=6)
        nota_frame.pack(fill=tk.X, pady=8)
        tk.Label(nota_frame, text="Nota sobre el Costo:\n• Costo > 10,000: Aún no toca la meta.\n• Costo = 0: ¡Llegó al destino! Se retira\n  la penalización por callejón sin salida.", bg="#fff8e1", fg="#7f6000", font=("Arial", 9), justify=tk.LEFT).pack(anchor="w")


        
        # --- SIMBOLOGÍA CON COLORES REALES DIBUJADOS ---
        leyenda_frame = tk.Frame(panel_info, bg="#f8f9fa", bd=1, relief=tk.SOLID, padx=10, pady=8)
        leyenda_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        
        tk.Label(leyenda_frame, text="Simbología del Laberinto:", bg="#f8f9fa", fg="#2c3e50", font=("Arial", 9, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        items_leyenda = [
            ("#2ecc71", "Inicio (Origen)", "circulo", 1, 0),
            ("#3498db", "Meta (Destino)", "circulo", 1, 1),
            ("#f39c12", "Frente Avance", "circulo", 2, 0),
            ("#e74c3c", "Mejor Ruta", "linea", 2, 1),
        ]

        for color, texto, forma, fila, col in items_leyenda:
            item = tk.Frame(leyenda_frame, bg="#f8f9fa")
            item.grid(row=fila, column=col, sticky="w", padx=(0, 12), pady=2)
            
            cv = tk.Canvas(item, width=18, height=18, bg="#f8f9fa", highlightthickness=0)
            cv.pack(side=tk.LEFT, padx=(0, 5))
            if forma == "circulo":
                cv.create_oval(3, 3, 15, 15, fill=color, outline="#2c3e50", width=1)
            else:
                cv.create_line(2, 9, 16, 9, fill=color, width=4)
            
            tk.Label(item, text=texto, bg="#f8f9fa", fg="#2c3e50", font=("Arial", 9, "bold")).pack(side=tk.LEFT)

    def aplicar_preset(self, event=None):
        idx = self.combo_presets.current()
        presets = [
            (1, 147, 147, 147),
            (1, 1, 147, 147),
            (147, 1, 1, 147),
            (1, 1, 147, 1)
        ]
        or_r, or_c, de_r, de_c = presets[idx]
        self.actualizar_spinboxes(or_r, or_c, de_r, de_c)

    def actualizar_spinboxes(self, or_r, or_c, de_r, de_c):
        for sp, val in [(self.spin_or_r, or_r), (self.spin_or_c, or_c), (self.spin_de_r, de_r), (self.spin_de_c, de_c)]:
            sp.delete(0, tk.END)
            sp.insert(0, str(val))

    def clic_en_mapa(self, event):
        if event.xdata is None or event.ydata is None:
            return
        col = int(round(event.xdata))
        fila = int(round(event.ydata))
        if 0 <= fila < 150 and 0 <= col < 150:
            if self.laberinto[fila][col] == 1:
                messagebox.showwarning("Pared detectada", f"La celda ({fila}, {col}) es un muro (1). Haz clic en un pasillo blanco (0).")
                return
            if event.button == 1:  # Clic izquierdo -> Origen
                self.actualizar_spinboxes(fila, col, int(self.spin_de_r.get()), int(self.spin_de_c.get()))
            elif event.button == 3:  # Clic derecho -> Destino
                self.actualizar_spinboxes(int(self.spin_or_r.get()), int(self.spin_or_c.get()), fila, col)
            self.dibujar_vista_previa()

    def dibujar_vista_previa(self):
        or_r, or_c = int(self.spin_or_r.get()), int(self.spin_or_c.get())
        de_r, de_c = int(self.spin_de_r.get()), int(self.spin_de_c.get())
        self.ax.clear()
        self.ax.imshow(self.laberinto, cmap='binary', origin='upper')
        self.ax.plot(or_c, or_r, 'o', color='#2ecc71', markersize=9, markeredgecolor='black')
        self.ax.plot(de_c, de_r, 'o', color='#3498db', markersize=9, markeredgecolor='black')
        self.ax.set_title(f"Puntos seleccionados: ({or_r},{or_c}) ➔ ({de_r},{de_c})\nPresiona '▶ Ejecutar' para iniciar", fontsize=11, fontweight="bold")
        self.ax.axis("off")
        self.canvas.draw()

    def compilar_c_si_necesario(self):
        if os.path.exists(ARCHIVO_C):
            cmd = ["gcc", ARCHIVO_C, "-o", "laberinto.exe" if os.name == "nt" else "laberinto"]
            subprocess.run(cmd, check=True)

    def ejecutar_busqueda(self):
        self.animando = False
        try:
            self.origen_r = int(self.spin_or_r.get())
            self.origen_c = int(self.spin_or_c.get())
            self.destino_r = int(self.spin_de_r.get())
            self.destino_c = int(self.spin_de_c.get())
        except ValueError:
            messagebox.showerror("Error", "Ingresa coordenadas numéricas válidas entre 0 y 149.")
            return

        if not (0 <= self.origen_r < 150 and 0 <= self.origen_c < 150 and 0 <= self.destino_r < 150 and 0 <= self.destino_c < 150):
            messagebox.showerror("Error", "Las coordenadas deben estar entre 0 y 149.")
            return

        if self.laberinto[self.origen_r][self.origen_c] == 1:
            messagebox.showwarning("Pared en Origen", f"La celda de origen ({self.origen_r}, {self.origen_c}) es una pared (1). Elige un pasillo blanco (0).")
            return

        if self.laberinto[self.destino_r][self.destino_c] == 1:
            messagebox.showwarning("Pared en Destino", f"La celda de destino ({self.destino_r}, {self.destino_c}) es una pared (1). Elige un pasillo blanco (0).")
            return

        self.lbl_estado.config(text=" CALCULANDO EN C...", bg="#fff3cd", fg="#856404")
        self.root.update()

        subprocess.run([
            EJECUTABLE_C,
            str(self.origen_r), str(self.origen_c),
            str(self.destino_r), str(self.destino_c)
        ], check=True)

        self.hitos_evolucion = []
        mejor_dist = float('inf')

        with open(TXT_HISTORIA, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("GEN:"):
                    partes = line.split("|")
                    gen = int(partes[0].split(":")[1])
                    llego = int(partes[1].split(":")[1])
                    pasos = int(partes[2].split(":")[1])
                    dist = int(partes[3].split(":")[1])
                    camino_str = partes[4].split(":")[1]
                    camino = [int(x) for x in camino_str.split(",") if x] if camino_str else []

                    if dist < mejor_dist:
                        mejor_dist = dist
                        self.hitos_evolucion.append({
                            'gen': gen, 'llego': llego, 'pasos': pasos,
                            'dist': dist, 'camino': camino
                        })

        self.indice_actual = 0
        self.animando = True
        self.avanzar_animacion()

    def avanzar_animacion(self):
        if not self.animando or not self.hitos_evolucion:
            return

        data = self.hitos_evolucion[self.indice_actual]
        es_ultimo = (self.indice_actual == len(self.hitos_evolucion) - 1)
        self.dibujar_laberinto(data, es_final=es_ultimo)

        if not es_ultimo:
            self.indice_actual += 1
            # Velocidad adaptativa según cuántos hitos haya
            delay = 350 if len(self.hitos_evolucion) > 25 else 650
            self.root.after(delay, self.avanzar_animacion)
        else:
            self.animando = False

    def alternar_pausa(self):
        if self.indice_actual < len(self.hitos_evolucion) - 1:
            self.animando = not self.animando
            if self.animando:
                self.avanzar_animacion()

    def ir_al_final(self):
        self.animando = False
        if self.hitos_evolucion:
            self.indice_actual = len(self.hitos_evolucion) - 1
            self.dibujar_laberinto(self.hitos_evolucion[self.indice_actual], es_final=True)

    def dibujar_laberinto(self, data, es_final=False):
        self.ax.clear()
        self.ax.imshow(self.laberinto, cmap='binary', origin='upper')

        camino = data['camino']
        if camino:
            y_coords = [c // 150 for c in camino]
            x_coords = [c % 150 for c in camino]
            self.ax.plot(x_coords, y_coords, color='#e74c3c', linewidth=1.8, alpha=0.95)
            self.ax.plot(x_coords[-1], y_coords[-1], 'o', color='#f39c12', markersize=6)

        # Marcadores de inicio (verde) y meta (azul)
        self.ax.plot(self.origen_c, self.origen_r, 'o', color='#2ecc71', markersize=9, markeredgecolor='black')
        self.ax.plot(self.destino_c, self.destino_r, 'o', color='#3498db', markersize=9, markeredgecolor='black')

        titulo_estado = f"SOLUCIÓN FINAL (Gen {data['gen']})" if es_final else f"Generación {data['gen']} — Mejora {self.indice_actual + 1}/{len(self.hitos_evolucion)}"
        self.ax.set_title(f"Laberinto 150x150: ({self.origen_r},{self.origen_c}) ➔ ({self.destino_r},{self.destino_c})\n{titulo_estado}", fontsize=11, fontweight="bold", pad=8)
        self.ax.axis("off")
        self.fig.tight_layout()
        self.canvas.draw()

        # --- ACTUALIZAR PANEL DERECHO ---
        if data['llego'] == 1:
            self.lbl_estado.config(text="¡META ALCANZADA!" if not es_final else "RUTA ÓPTIMA ENCONTRADA", bg="#d4edda", fg="#155724")
        else:
            self.lbl_estado.config(text="EXPLORANDO PASILLOS...", bg="#f8d7da", fg="#721c24")

        self.lbl_gen.config(text=f"GENERACIÓN: {data['gen']}")
        self.lbl_coords.config(text=f"Trayecto: ({self.origen_r},{self.origen_c}) ➔ ({self.destino_r},{self.destino_c})")
        self.lbl_pasos.config(text=f"Longitud de Ruta: {data['pasos']} pasos")
        self.lbl_costo.config(text=f"Costo / Penalización: {data['dist']}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AplicacionLaberintoAG(root)
    root.mainloop()