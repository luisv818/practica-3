import os
import matplotlib.pyplot as plt
import networkx as nx
from PIL import Image

#CONFIGURACION
# Guarda la imagen cada X generaciones (ejemplo: 50)
INTERVALO_X = 50  
CARPETA_SALIDA = "mejores_rutas"

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

aristas = [
    (0, 1), (0, 2), (1, 3), (2, 3), (2, 4), (4, 5), (4, 6), (3, 6), (3, 7), (7, 8),
    (6, 8), (8, 9), (9, 10), (10, 11), (11, 12), (11, 13), (13, 15), (13, 14), (14, 15),
    (5, 16), (16, 17), (16, 18), (17, 18), (18, 19), (19, 20), (19, 21), (19, 23), (20, 21), (21, 22),
    (22, 28), (22, 26), (23, 24), (23, 26), (23, 27), (24, 25), (26, 27), (28, 29), (28, 31), (29, 30),
    (30, 31), (30, 32), (31, 32), (31, 33), (32, 34), (27, 33), (33, 34), (34, 35), (34, 36), (34, 38),
    (36, 37), (37, 38)
]

# Construccion del grafo
G = nx.Graph()
for i, nombre in enumerate(NOMBRES_CIUDADES):
    G.add_node(i, label=nombre)
G.add_edges_from(aristas)
pos = nx.spring_layout(G, seed=42)

origen_idx, destino_idx = 0, 34
historia = []

# Leer archivo generado por C
with open("historia_evolutiva.txt", "r") as f:
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
            km = int(partes[3].split(":")[1])
            camino_str = partes[4].split(":")[1]
            camino = [int(x) for x in camino_str.split(",") if x] if camino_str else []
            historia.append({
                'gen': gen, 'llego': llego, 'pasos': pasos, 
                'km': km, 'camino': camino
            })

os.makedirs(CARPETA_SALIDA, exist_ok=True)

# Buscar y dibujar unicamente el avance de la MEJOR RUTA
mejor_km_historico = float('inf')
mejor_data = None

def guardar_grafica_ruta(data, nombre_archivo, titulo_extra=""):
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # Grafo base
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color='lightgray', node_size=250)
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color='gainsboro', width=1.5)
    
    labels = {i: NOMBRES_CIUDADES[i] for i in range(len(NOMBRES_CIUDADES))}
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=6, ax=ax)

    # Nodos Origen y Destino
    nx.draw_networkx_nodes(G, pos, nodelist=[origen_idx], node_color='green', node_size=400, ax=ax)
    nx.draw_networkx_nodes(G, pos, nodelist=[destino_idx], node_color='blue', node_size=400, ax=ax)

    # Trazar la Mejor Ruta
    camino = data['camino']
    if len(camino) > 1:
        edges_camino = [(camino[i], camino[i+1]) for i in range(len(camino)-1)]
        nx.draw_networkx_edges(G, pos, edgelist=edges_camino, edge_color='red', width=3, ax=ax)
        nx.draw_networkx_nodes(G, pos, nodelist=camino, node_color='orange', node_size=300, ax=ax)

    estado_txt = "SÍ (ÉXITO)" if data['llego'] == 1 else "NO"
    color_txt = "green" if data['llego'] == 1 else "red"
    
    info = (
        f"Generación: {data['gen']}\n"
        f"¿Llegó al destino?: {estado_txt}\n"
        f"Ciudades en ruta: {data['pasos']}\n"
        f"Distancia Total: {data['km']} Km"
    )
    
    ax.set_title(f"Mejor Ruta Encontrada {titulo_extra}", fontsize=12, fontweight='bold')
    ax.text(0.02, 0.95, info, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.9),
            color=color_txt, fontweight='bold')
    ax.axis('off')

    plt.savefig(nombre_archivo, bbox_inches='tight', dpi=150)
    plt.close(fig)

# Filtrar las mejores rutas que superaron a las anteriores
for data in historia:
    if data['km'] < mejor_km_historico:
        mejor_km_historico = data['km']
        mejor_data = data
        
        # 1. Guardar/Sobrescribir la imagen de la "Mejor Ruta Actual"
        guardar_grafica_ruta(mejor_data, "mejor_ruta_actual.png", f"(Generación {data['gen']})")
        print(f"[+] Nueva mejor ruta encontrada en Gen {data['gen']}: {data['km']} Km")

    # 2. Guardar imagen periodica cada INTERVALO_X generaciones con la mejor ruta alcanzada hasta esa generación
    if data['gen'] == 1 or data['gen'] % INTERVALO_X == 0 or data['gen'] == len(historia):
        archivo_periodico = os.path.join(CARPETA_SALIDA, f"mejor_ruta_gen_{data['gen']:04d}.png")
        guardar_grafica_ruta(mejor_data, archivo_periodico, f"hasta Gen {data['gen']}")

print("\n[+] Proceso finalizado:")
print(" 1. La imagen 'mejor_ruta_actual.png' contiene la ruta óptima final alcanzada.")
print(f" 2. En la carpeta '{CARPETA_SALIDA}/' se guardaron las imágenes del avance cada {INTERVALO_X} generaciones.")

#Creacion de GIF
ruta_carpeta = "/workspaces/practica-3/mejores_rutas" 
formatos_validos = (".png", ".jpg", ".jpeg")

archivos = [
    f for f in os.listdir(ruta_carpeta) if f.lower().endswith(formatos_validos)
]

archivos.sort()

imagenes = []
for archivo in archivos:
  ruta_completa = os.path.join(ruta_carpeta, archivo)
  imagenes.append(Image.open(ruta_completa))

if imagenes:
  imagen_principal = imagenes[0]
  imagen_principal.save(
      "animacion_carpeta.gif",
      save_all=True,
      append_images=imagenes[1:],
      duration=500,  # 500 milisegundos
      loop=0,  # 0 para bucle infinito
  )
  print(
      f"GIF creado con exito usando {len(imagenes)} imagenes de la carpeta"
  )
else:
  print("No se encontraron imagenes validas en la carpeta")