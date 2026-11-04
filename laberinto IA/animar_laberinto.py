import os
import csv
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

# --- CONFIGURACION ---
CSV_LABERINTO = "laberinto_150x150.csv"
TXT_HISTORIA = "historia_laberinto.txt"
GIF_SALIDA = "evolucion_laberinto.gif"
PAUSA_ESTANCAMIENTO = 50

# cargar el laberinto
if not os.path.exists(CSV_LABERINTO):
    print(f"Error: No se encontró {CSV_LABERINTO}")
    exit(1)

laberinto_lista = []
with open(CSV_LABERINTO, "r") as f:
    reader = csv.reader(f)
    for row in reader:
        if row:
            laberinto_lista.append([int(val) for val in row if val != ''])

laberinto = np.array(laberinto_lista)

# leer historia de C filtrando solo las mejoras de ruta
if not os.path.exists(TXT_HISTORIA):
    print(f"Error: No se encontró {TXT_HISTORIA}")
    exit(1)

historia_mejoras = []
mejor_distancia_historica = float('inf')
origen_idx, destino_idx = 1 * 150 + 1, 147 * 150 + 147

with open(TXT_HISTORIA, "r") as f:
    for line in f:
        line = line.strip()
        if line.startswith("ORIGEN:"):
            partes = line.split("|")
            origen_idx = int(partes[0].split(":")[1])
            destino_idx = int(partes[1].split(":")[1])
        elif line.startswith("GEN:"):
            partes = line.split("|")
            gen = int(partes[0].split(":")[1])
            llego = int(partes[1].split(":")[1])
            pasos = int(partes[2].split(":")[1])
            dist = int(partes[3].split(":")[1])
            camino_str = partes[4].split(":")[1]
            camino = [int(x) for x in camino_str.split(",") if x] if camino_str else []
            
            if dist < mejor_distancia_historica:
                mejor_distancia_historica = dist
                historia_mejoras.append({
                    'gen': gen, 'llego': llego, 'pasos': pasos, 
                    'dist': dist, 'camino': camino
                })

if not historia_mejoras:
    print("No hay rutas registradas.")
    exit(0)

frames_filtrados = [historia_mejoras[0]]
consecutivos_iguales = 0

for i in range(1, len(historia_mejoras)):
    if historia_mejoras[i]['dist'] == historia_mejoras[i-1]['dist']:
        consecutivos_iguales += 1
    else:
        consecutivos_iguales = 0
    
    frames_filtrados.append(historia_mejoras[i])
    if consecutivos_iguales >= PAUSA_ESTANCAMIENTO:
        break

# RENDERIZADO CON PANEL LATERAL
fig, (ax_lab, ax_info) = plt.subplots(1, 2, figsize=(12, 7), gridspec_kw={'width_ratios': [2.5, 1]})
fig.subplots_adjust(wspace=0.1)

origen_r, origen_c = origen_idx // 150, origen_idx % 150
destino_r, destino_c = destino_idx // 150, destino_idx % 150

def actualizar(frame_idx):
    ax_lab.clear()
    ax_info.clear()
    
    data = frames_filtrados[frame_idx]
    
    # RENDERING DEL LABERINTO
    ax_lab.imshow(laberinto, cmap='binary', origin='upper')

    camino = data['camino']
    if camino:
        y_coords = [c // 150 for c in camino]
        x_coords = [c % 150 for c in camino]
        ax_lab.plot(x_coords, y_coords, color='red', linewidth=1.5, alpha=0.9, label='Mejor Ruta')
        ax_lab.plot(x_coords[-1], y_coords[-1], 'o', color='orange', markersize=5, label='Frente de avance')

    # marcadores de inicio y fin
    ax_lab.plot(origen_c, origen_r, 'go', markersize=8, label=f'Inicio ({origen_r},{origen_c})')
    ax_lab.plot(destino_c, destino_r, 'bo', markersize=8, label=f'Fin ({destino_r},{destino_c})')

    ax_lab.set_title(f"Evolución del Laberinto 150x150", fontsize=12, fontweight='bold')
    ax_lab.axis('off')

    # RENDERING DEL PANEL INFORMATIVO
    ax_info.axis('off')
    
    estado_txt = "SI (EXITO)" if data['llego'] == 1 else "NO (EN PROCESO)"
    color_txt = "darkgreen" if data['llego'] == 1 else "darkred"
    
    info_text = (
        "=== METRICAS Y ESTADO ===\n\n"
        f"Generacion: {data['gen']}\n\n"
        f"¿Llego al destino?: {estado_txt}\n\n"
        f"Longitud de Ruta: {data['pasos']} pasos\n\n"
        f"Costo / Distancia: {data['dist']}"
    )
    
    ax_info.text(0.05, 0.95, info_text, transform=ax_info.transAxes, fontsize=10,
                verticalalignment='top', bbox=dict(boxstyle='round,pad=0.8', facecolor='#f0f0f0', alpha=0.9),
                color=color_txt, fontweight='bold')
    
    # simbologia renderizada dentro del panel lateral derecho
    handles, labels = ax_lab.get_legend_handles_labels()
    ax_info.legend(handles, labels, loc='lower left', bbox_to_anchor=(0.05, 0.1), fontsize=9, title="Simbología", title_fontsize=10)

# configurar 1 segundo de retraso (1 fps)
ani = animation.FuncAnimation(fig, actualizar, frames=len(frames_filtrados), interval=1000, repeat=True)

print(f"[+] Generando GIF '{GIF_SALIDA}' con panel lateral independiente...")
ani.save(GIF_SALIDA, writer='pillow', fps=1)
print(f"[+] GIF generado con exito")