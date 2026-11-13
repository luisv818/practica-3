import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import networkx as nx

# --- CONFIGURACIÓN DE ARCHIVOS ---
ARCHIVO_C = "genericoCiudades_2.c"
EJECUTABLE_C = "genericoCiudades.exe" if os.name == "nt" else "./genericoCiudades"
ARCHIVO_HISTORIA = "historia_evolutiva.txt"

NOMBRES_CIUDADES = [
    "Tijuana", "Rosarito", "Tecate", "Ensenada", "Mexicali", 
    "San Luis Rio Colorado", "San Felipe", "San Quintin", "Guerrero negro", "Santa Rosalia", 
    "Mulege", "Ciudad Constitucion", "San Carlos", "La Paz", "San Jose del Cabo", 
    "Cabo San Lucas", "Sonoyta", "Puerto Penasco", "Caborca", "Santa Ana", 
    "Nogales", "Cananea", "Agua Prieta", "Hermosillo", "Guaymas", 
    "Ciudad Obregon", "Moctezuma", "Yecora", "Janos", "Ciudad Juarez", 
    "Villa Ahumada", "Flores Magon", "Sueco", "Ciudad Cuauhtemoc", "Chihuahua", 
    "Ojinaga", "Delicias", "Ciudad Jimenez", "Parral"
]

POSICIONES_GEOGRAFICAS = {
    0: (-117.03, 32.51),  # Tijuana
    1: (-117.05, 32.36),  # Rosarito
    2: (-116.62, 32.57),  # Tecate
    3: (-116.60, 31.86),  # Ensenada
    4: (-115.45, 32.62),  # Mexicali
    5: (-114.77, 32.45),  # San Luis Rio Colorado
    6: (-114.84, 31.02),  # San Felipe
    7: (-115.94, 30.56),  # San Quintin
    8: (-114.05, 27.96),  # Guerrero negro
    9: (-112.26, 27.34),  # Santa Rosalia
    10: (-111.98, 26.89), # Mulege
    11: (-111.67, 25.03), # Ciudad Constitucion
    12: (-112.11, 24.79), # San Carlos
    13: (-110.31, 24.14), # La Paz
    14: (-109.70, 23.06), # San Jose del Cabo
    15: (-109.91, 22.89), # Cabo San Lucas
    16: (-112.85, 31.86), # Sonoyta
    17: (-113.53, 31.32), # Puerto Penasco
    18: (-112.16, 30.71), # Caborca
    19: (-111.12, 30.54), # Santa Ana
    20: (-110.94, 31.30), # Nogales
    21: (-110.30, 30.98), # Cananea
    22: (-109.54, 31.32), # Agua Prieta
    23: (-110.96, 29.07), # Hermosillo
    24: (-110.89, 27.92), # Guaymas
    25: (-109.93, 27.48), # Ciudad Obregon
    26: (-109.68, 29.80), # Moctezuma
    27: (-108.92, 28.37), # Yecora
    28: (-108.19, 30.88), # Janos
    29: (-106.42, 31.69), # Ciudad Juarez
    30: (-106.51, 30.61), # Villa Ahumada
    31: (-106.96, 29.94), # Flores Magon
    32: (-106.39, 29.91), # Sueco
    33: (-106.86, 28.40), # Ciudad Cuauhtemoc
    34: (-106.06, 28.63), # Chihuahua
    35: (-104.41, 29.56), # Ojinaga
    36: (-105.47, 28.19), # Delicias
    37: (-104.92, 27.13), # Ciudad Jimenez
    38: (-105.66, 26.93)  # Parral
}

ARISTAS_CON_PESO = [
    (0, 1, 20), (0, 2, 52), (1, 3, 85), (2, 3, 100), (2, 4, 135),
    (4, 5, 80), (4, 6, 197), (3, 6, 246), (3, 7, 185), (7, 8, 425),
    (6, 8, 394), (8, 9, 220), (9, 10, 63), (10, 11, 283), (11, 12, 61),
    (11, 13, 210), (13, 15, 157), (13, 14, 201), (14, 15, 38),
    (5, 16, 203), (16, 17, 98), (16, 18, 149), (17, 18, 176), (18, 19, 107),
    (19, 20, 107), (19, 21, 125), (19, 23, 171), (20, 21, 99), (21, 22, 86),
    (22, 28, 160), (22, 26, 199), (23, 24, 135), (23, 26, 178), (23, 27, 278),
    (24, 25, 130), (26, 27, 257), (28, 29, 212), (28, 31, 173), (29, 30, 125),
    (30, 31, 93), (30, 32, 85), (31, 32, 60), (31, 33, 211), (32, 34, 158),
    (27, 33, 309), (33, 34, 105), (34, 35, 379), (34, 36, 87), (34, 38, 225),
    (36, 37, 139), (37, 38, 215)
]

class AplicacionRutasAG:
    def __init__(self, root):
        self.root = root
        self.root.title("Algoritmo Genético - Buscador de Rutas entre Ciudades")
        self.root.geometry("1280x800")
        self.root.configure(bg="#f4f6f9")

        self.G = nx.Graph()
        for i, nombre in enumerate(NOMBRES_CIUDADES):
            self.G.add_node(i, label=nombre)
        for u, v, w in ARISTAS_CON_PESO:
            self.G.add_edge(u, v, weight=w)

        self.hitos_evolucion = []
        self.indice_actual = 0
        self.animando = False
        self.origen_idx = 0
        self.destino_idx = 34

        self.crear_interfaz()
        self.compilar_c_si_necesario()
        self.dibujar_mapa_inicial()

    def crear_interfaz(self):
        # --- BARRA SUPERIOR DE CONTROLES ---
        panel_controles = tk.Frame(self.root, bg="#2c3e50", pady=10, padx=15)
        panel_controles.pack(side=tk.TOP, fill=tk.X)

        tk.Label(panel_controles, text="Ciudad Origen:", bg="#2c3e50", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        self.combo_origen = ttk.Combobox(panel_controles, values=[f"{i}: {n}" for i, n in enumerate(NOMBRES_CIUDADES)], width=24, state="readonly")
        self.combo_origen.current(0)
        self.combo_origen.pack(side=tk.LEFT, padx=(0, 15))

        tk.Label(panel_controles, text="Ciudad Destino:", bg="#2c3e50", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        self.combo_destino = ttk.Combobox(panel_controles, values=[f"{i}: {n}" for i, n in enumerate(NOMBRES_CIUDADES)], width=24, state="readonly")
        self.combo_destino.current(34)
        self.combo_destino.pack(side=tk.LEFT, padx=(0, 15))

        btn_ejecutar = tk.Button(panel_controles, text="▶ Ejecutar Búsqueda", command=self.ejecutar_busqueda, bg="#27ae60", fg="white", font=("Arial", 10, "bold"), padx=12, relief=tk.FLAT, cursor="hand2")
        btn_ejecutar.pack(side=tk.LEFT, padx=5)

        btn_pausa = tk.Button(panel_controles, text="⏯ Pausar / Reanudar", command=self.alternar_pausa, bg="#f39c12", fg="white", font=("Arial", 10, "bold"), padx=10, relief=tk.FLAT, cursor="hand2")
        btn_pausa.pack(side=tk.LEFT, padx=5)

        btn_final = tk.Button(panel_controles, text="⏭ Ir a Ruta Final", command=self.ir_al_final, bg="#2980b9", fg="white", font=("Arial", 10, "bold"), padx=10, relief=tk.FLAT, cursor="hand2")
        btn_final.pack(side=tk.LEFT, padx=5)

        # --- CONTENEDOR PRINCIPAL ---
        contenedor = tk.Frame(self.root, bg="#f4f6f9")
        contenedor.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Lienzo de Matplotlib (Izquierda)
        self.fig, self.ax = plt.subplots(figsize=(9, 7), dpi=100)
        self.fig.patch.set_facecolor("#ffffff")
        self.canvas = FigureCanvasTkAgg(self.fig, master=contenedor)
        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Panel lateral de información (Derecha)
        panel_info = tk.Frame(contenedor, width=330, bg="white", bd=1, relief=tk.SOLID, padx=15, pady=12)
        panel_info.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        panel_info.pack_propagate(False)

        tk.Label(panel_info, text="RESULTADOS DE EVOLUCIÓN", bg="white", fg="#2c3e50", font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 8))
        
        self.lbl_estado = tk.Label(panel_info, text="Estado: Esperando...", bg="#ecf0f1", fg="#2c3e50", font=("Arial", 10, "bold"), padx=8, pady=6)
        self.lbl_estado.pack(fill=tk.X, pady=4)

        # Tarjeta destacada y grande para la Generación
        frame_gen = tk.Frame(panel_info, bg="#eef5fc", bd=1, relief=tk.SOLID, padx=10, pady=8)
        frame_gen.pack(fill=tk.X, pady=6)
        self.lbl_gen = tk.Label(frame_gen, text="GENERACIÓN: -", bg="#eef5fc", fg="#1a5276", font=("Arial", 16, "bold"))
        self.lbl_gen.pack(anchor="center")

        self.lbl_pasos = tk.Label(panel_info, text="Pasos: -", bg="white", fg="#34495e", font=("Arial", 11, "bold"))
        self.lbl_pasos.pack(anchor="w", pady=4)

        self.lbl_km = tk.Label(panel_info, text="Distancia Total: - Km", bg="white", fg="#c0392b", font=("Arial", 13, "bold"))
        self.lbl_km.pack(anchor="w", pady=4)

        tk.Label(panel_info, text="Secuencia de Ciudades:", bg="white", fg="#2c3e50", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10, 4))
        
        self.txt_ruta = tk.Text(panel_info, height=14, width=34, bg="#f8f9fa", fg="#2c3e50", font=("Consolas", 9), relief=tk.FLAT, padx=8, pady=8)
        self.txt_ruta.pack(fill=tk.BOTH, expand=True)

        # --- SIMBOLOGÍA CON COLORES REALES DIBUJADOS ---
        leyenda_frame = tk.Frame(panel_info, bg="#f8f9fa", bd=1, relief=tk.SOLID, padx=10, pady=8)
        leyenda_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        
        tk.Label(leyenda_frame, text="Simbología del Mapa:", bg="#f8f9fa", fg="#2c3e50", font=("Arial", 9, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        items_leyenda = [
            ("#2ecc71", "Ciudad Origen", "circulo", 1, 0),
            ("#3498db", "Ciudad Destino", "circulo", 1, 1),
            ("#f39c12", "Ciudad en Ruta", "circulo", 2, 0),
            ("#e74c3c", "Carretera Elegida", "linea", 2, 1),
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

    def compilar_c_si_necesario(self):
        if os.path.exists(ARCHIVO_C):
            cmd = ["gcc", ARCHIVO_C, "-o", "genericoCiudades.exe" if os.name == "nt" else "genericoCiudades"]
            subprocess.run(cmd, check=True)

    def dibujar_mapa_inicial(self):
        self.origen_idx = self.combo_origen.current()
        self.destino_idx = self.combo_destino.current()
        self.ax.clear()

        nx.draw_networkx_edges(self.G, POSICIONES_GEOGRAFICAS, ax=self.ax, edge_color="#d0d7de", width=1.5)
        edge_labels = nx.get_edge_attributes(self.G, 'weight')
        nx.draw_networkx_edge_labels(self.G, POSICIONES_GEOGRAFICAS, edge_labels=edge_labels, font_size=6, font_color="#7f8c8d", ax=self.ax)
        nx.draw_networkx_nodes(self.G, POSICIONES_GEOGRAFICAS, ax=self.ax, node_color="#bdc3c7", node_size=180)

        nx.draw_networkx_nodes(self.G, POSICIONES_GEOGRAFICAS, nodelist=[self.origen_idx], node_color="#2ecc71", node_size=420, ax=self.ax)
        nx.draw_networkx_nodes(self.G, POSICIONES_GEOGRAFICAS, nodelist=[self.destino_idx], node_color="#3498db", node_size=420, ax=self.ax)

        pos_etiquetas = {k: (v[0], v[1] + 0.18) for k, v in POSICIONES_GEOGRAFICAS.items()}
        labels = {i: NOMBRES_CIUDADES[i] for i in range(len(NOMBRES_CIUDADES))}
        nx.draw_networkx_labels(self.G, pos_etiquetas, labels=labels, font_size=7, font_weight="bold", font_color="#2c3e50", ax=self.ax)

        self.ax.set_title("Selecciona Origen y Destino y presiona '▶ Ejecutar Búsqueda'", fontsize=11, fontweight="bold", pad=10)
        self.ax.axis("off")
        self.fig.tight_layout()
        self.canvas.draw()

    def ejecutar_busqueda(self):
        self.animando = False
        self.origen_idx = self.combo_origen.current()
        self.destino_idx = self.combo_destino.current()

        if self.origen_idx == self.destino_idx:
            messagebox.showwarning("Aviso", "Selecciona una ciudad de origen y destino diferentes.")
            return

        subprocess.run([EJECUTABLE_C, str(self.origen_idx), str(self.destino_idx)], check=True)

        self.hitos_evolucion = []
        mejor_km = float('inf')

        with open(ARCHIVO_HISTORIA, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("GEN:"):
                    partes = line.split("|")
                    gen = int(partes[0].split(":")[1])
                    llego = int(partes[1].split(":")[1])
                    pasos = int(partes[2].split(":")[1])
                    km = int(partes[3].split(":")[1])
                    camino_str = partes[4].split(":")[1]
                    camino = [int(x) for x in camino_str.split(",") if x] if camino_str else []

                    if km < mejor_km:
                        mejor_km = km
                        self.hitos_evolucion.append({
                            'gen': gen, 'llego': llego, 'pasos': pasos,
                            'km': km, 'camino': camino
                        })

        self.indice_actual = 0
        self.animando = True
        self.avanzar_animacion()

    def avanzar_animacion(self):
        if not self.animando or not self.hitos_evolucion:
            return

        data = self.hitos_evolucion[self.indice_actual]
        es_ultimo = (self.indice_actual == len(self.hitos_evolucion) - 1)
        self.dibujar_mapa(data, es_final=es_ultimo)

        if not es_ultimo:
            self.indice_actual += 1
            self.root.after(700, self.avanzar_animacion)
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
            self.dibujar_mapa(self.hitos_evolucion[self.indice_actual], es_final=True)

    def dibujar_mapa(self, data, es_final=False):
        self.ax.clear()

        nx.draw_networkx_edges(self.G, POSICIONES_GEOGRAFICAS, ax=self.ax, edge_color="#d0d7de", width=1.5)
        edge_labels = nx.get_edge_attributes(self.G, 'weight')
        nx.draw_networkx_edge_labels(self.G, POSICIONES_GEOGRAFICAS, edge_labels=edge_labels, font_size=6, font_color="#7f8c8d", ax=self.ax)
        nx.draw_networkx_nodes(self.G, POSICIONES_GEOGRAFICAS, ax=self.ax, node_color="#bdc3c7", node_size=180)

        camino = data['camino']
        if len(camino) > 1:
            aristas_ruta = [(camino[i], camino[i+1]) for i in range(len(camino)-1)]
            nx.draw_networkx_edges(self.G, POSICIONES_GEOGRAFICAS, edgelist=aristas_ruta, edge_color="#e74c3c", width=3.5, ax=self.ax)
            nx.draw_networkx_nodes(self.G, POSICIONES_GEOGRAFICAS, nodelist=camino, node_color="#f39c12", node_size=260, ax=self.ax)

        nx.draw_networkx_nodes(self.G, POSICIONES_GEOGRAFICAS, nodelist=[self.origen_idx], node_color="#2ecc71", node_size=420, ax=self.ax)
        nx.draw_networkx_nodes(self.G, POSICIONES_GEOGRAFICAS, nodelist=[self.destino_idx], node_color="#3498db", node_size=420, ax=self.ax)

        pos_etiquetas = {k: (v[0], v[1] + 0.18) for k, v in POSICIONES_GEOGRAFICAS.items()}
        labels = {i: NOMBRES_CIUDADES[i] for i in range(len(NOMBRES_CIUDADES))}
        nx.draw_networkx_labels(self.G, pos_etiquetas, labels=labels, font_size=7, font_weight="bold", font_color="#2c3e50", ax=self.ax)

        titulo_estado = f"RUTA ÓPTIMA FINAL (Gen {data['gen']})" if es_final else f"Generación {data['gen']} — Mejora {self.indice_actual + 1}/{len(self.hitos_evolucion)}"
        self.ax.set_title(f"{NOMBRES_CIUDADES[self.origen_idx]} ➔ {NOMBRES_CIUDADES[self.destino_idx]}\n{titulo_estado}", fontsize=12, fontweight="bold", pad=10)
        self.ax.axis("off")
        self.fig.tight_layout()
        self.canvas.draw()

        # --- ACTUALIZAR PANEL DERECHO ---
        if data['llego'] == 1:
            self.lbl_estado.config(text=" DESTINO ALCANZADO" if not es_final else " RUTA FINAL CONSOLIDADA", bg="#d4edda", fg="#155724")
        else:
            self.lbl_estado.config(text=" BUSCANDO CAMINO...", bg="#f8d7da", fg="#721c24")

        self.lbl_gen.config(text=f"GENERACIÓN: {data['gen']}")
        tramos = max(0, data['pasos'] - 1)
        self.lbl_pasos.config(text=f"Pasos: {tramos} tramos ({data['pasos']} ciudades)")
        self.lbl_km.config(text=f"Distancia Total: {data['km']} Km")

        self.txt_ruta.delete("1.0", tk.END)
        for idx, ciudad_id in enumerate(camino):
            prefijo = "[INICIO] " if idx == 0 else ("[META] " if ciudad_id == self.destino_idx else f" {idx}. ")
            self.txt_ruta.insert(tk.END, f"{prefijo}{NOMBRES_CIUDADES[ciudad_id]}\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = AplicacionRutasAG(root)
    root.mainloop()