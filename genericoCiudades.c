#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <stdbool.h>

#define NUM_CIUDADES 39
#define MAX_PASOS 50
#define TAM_POBLACION 20
#define MAX_GENERACIONES 20
#define TASA_CRUCE 0.8
#define TASA_MUTACION 0.15
#define PENALIZACION_SIN_SALIDA 10000

// Lista con los nombres de todas las ciudades mapeadas de la imagen
const char *NOMBRES_CIUDADES[NUM_CIUDADES] = {
    "Tijuana", "Rosarito", "Tecate", "Ensenada", "Mexicali", 
    "San Luis Rio Colorado", "San Felipe", "San Quintin", "Guerrero negro", "Santa Rosalia", 
    "Mulege", "Ciudad Constitucion", "San Carlos", "La Paz", "San Jose del Cabo", 
    "Cabo San Lucas", "Sonoyta", "Puerto Penasco", "Caborca", "Santa Ana", 
    "Nogales", "Cananea", "Agua Prieta", "Hermosillo", "Guaymas", 
    "Ciudad Obregon", "Moctezuma", "Yecora", "Janos", "Ciudad Juarez", 
    "Villa Ahumada", "Flores Magon", "Sueco", "Ciudad Cuauhtemoc", "Chihuahua", 
    "Ojinaga", "Delicias", "Ciudad Jimenez", "Parral"
};

// Matriz de adyacencia (distancias en Km)
int grafo[NUM_CIUDADES][NUM_CIUDADES];

// Estructura de un individuo (cromosoma)
typedef struct {
    int camino[MAX_PASOS]; // Lista de IDs de ciudades
    int longitud;          // Cantidad de ciudades en la ruta
    int distancia_total;   // Distancia acumulada en Km
    double fitness;        // Valor de aptitud
} Individuo;

// --- ESTRUCTURA DE CONEXIONES (SEGÚN LA IMAGEN) ---
void inicializar_grafo() {
    for (int i = 0; i < NUM_CIUDADES; i++) {
        for (int j = 0; j < NUM_CIUDADES; j++) {
            grafo[i][j] = 0;
        }
    }

    // Estructura auxiliar para registrar las aristas
    struct Arista { int u; int v; int d; } aristas[] = {
        {0, 1, 20}, {0, 2, 52}, {1, 3, 85}, {2, 3, 100}, {2, 4, 135},
        {4, 5, 80}, {4, 6, 197}, {3, 6, 246}, {3, 7, 185}, {7, 8, 425},
        {6, 8, 394}, {8, 9, 220}, {9, 10, 63}, {10, 11, 283}, {11, 12, 61},
        {11, 13, 210}, {13, 15, 157}, {13, 14, 201}, {14, 15, 38},
        {5, 16, 203}, {16, 17, 98}, {16, 18, 149}, {17, 18, 176}, {18, 19, 107},
        {19, 20, 107}, {19, 21, 125}, {19, 23, 171}, {20, 21, 99}, {21, 22, 86},
        {22, 28, 160}, {22, 26, 199}, {23, 24, 135}, {23, 26, 178}, {23, 27, 278},
        {24, 25, 130}, {26, 27, 257}, {28, 29, 212}, {28, 31, 173}, {29, 30, 125},
        {30, 31, 93}, {30, 32, 85}, {31, 32, 60}, {31, 33, 211}, {32, 34, 158},
        {27, 33, 309}, {33, 34, 105}, {34, 35, 379}, {34, 36, 87}, {34, 38, 225},
        {36, 37, 139}, {37, 38, 215}
    };

    int num_aristas = sizeof(aristas) / sizeof(aristas[0]);
    for (int i = 0; i < num_aristas; i++) {
        grafo[aristas[i].u][aristas[i].v] = aristas[i].d;
        grafo[aristas[i].v][aristas[i].u] = aristas[i].d; // Grafo no dirigido
    }
}

// Función para obtener vecinos válidos de una ciudad
int obtener_vecinos(int ciudad, int vecinos[]) {
    int count = 0;
    for (int i = 0; i < NUM_CIUDADES; i++) {
        if (grafo[ciudad][i] > 0) {
            vecinos[count++] = i;
        }
    }
    return count;
}

// Genera una caminata aleatoria desde origen a destino
void generar_camino_aleatorio(Individuo *ind, int origen, int destino) {
    ind->camino[0] = origen;
    ind->longitud = 1;
    int actual = origen;

    bool visitado[NUM_CIUDADES] = {false};
    visitado[origen] = true;

    while (actual != destino && ind->longitud < MAX_PASOS) {
        int vecinos[NUM_CIUDADES];
        int num_vecinos = obtener_vecinos(actual, vecinos);

        // Filtrar vecinos no visitados
        int no_visitados[NUM_CIUDADES];
        int count_no_visitados = 0;
        for (int i = 0; i < num_vecinos; i++) {
            if (!visitado[vecinos[i]]) {
                no_visitados[count_no_visitados++] = vecinos[i];
            }
        }

        if (count_no_visitados > 0) {
            int siguiente = no_visitados[rand() % count_no_visitados];
            ind->camino[ind->longitud++] = siguiente;
            visitado[siguiente] = true;
            actual = siguiente;
        } else {
            // Callejón sin salida
            break;
        }
    }
}

// Calcular la distancia total y fitness
void evaluar_individuo(Individuo *ind, int destino) {
    ind->distancia_total = 0;
    bool camino_valido = true;

    for (int i = 0; i < ind->longitud - 1; i++) {
        int u = ind->camino[i];
        int v = ind->camino[i + 1];
        if (grafo[u][v] > 0) {
            ind->distancia_total += grafo[u][v];
        } else {
            camino_valido = false;
            break;
        }
    }

    // Penalización si no llega al destino final
    if (ind->camino[ind->longitud - 1] != destino || !camino_valido) {
        ind->distancia_total += PENALIZACION_SIN_SALIDA;
    }

    ind->fitness = 1.0 / (ind->distancia_total + 1.0);
}

// Selección por Torneo
Individuo seleccion_torneo(Individuo poblacion[], int k) {
    int mejor_idx = rand() % TAM_POBLACION;
    for (int i = 1; i < k; i++) {
        int idx = rand() % TAM_POBLACION;
        if (poblacion[idx].fitness > poblacion[mejor_idx].fitness) {
            mejor_idx = idx;
        }
    }
    return poblacion[mejor_idx];
}

// Cruce basado en punto/ciudad común
void cruce(Individuo p1, Individuo p2, Individuo *h1, Individuo *h2, int destino) {
    // Buscar si comparten alguna ciudad intermedia
    int coincidencia_p1 = -1, coincidencia_p2 = -1;

    for (int i = 1; i < p1.longitud - 1; i++) {
        for (int j = 1; j < p2.longitud - 1; j++) {
            if (p1.camino[i] == p2.camino[j]) {
                coincidencia_p1 = i;
                coincidencia_p2 = j;
                break;
            }
        }
        if (coincidencia_p1 != -1) break;
    }

    if (coincidencia_p1 != -1 && ((double)rand() / RAND_MAX) < TASA_CRUCE) {
        // Generar Hijo 1: Parte inicial de P1 + Parte final de P2
        h1->longitud = 0;
        for (int i = 0; i <= coincidencia_p1; i++) {
            h1->camino[h1->longitud++] = p1.camino[i];
        }
        for (int j = coincidencia_p2 + 1; j < p2.longitud; j++) {
            if (h1->longitud < MAX_PASOS) {
                h1->camino[h1->longitud++] = p2.camino[j];
            }
        }

        // Generar Hijo 2: Parte inicial de P2 + Parte final de P1
        h2->longitud = 0;
        for (int j = 0; j <= coincidencia_p2; j++) {
            h2->camino[h2->longitud++] = p2.camino[j];
        }
        for (int i = coincidencia_p1 + 1; i < p1.longitud; i++) {
            if (h2->longitud < MAX_PASOS) {
                h2->camino[h2->longitud++] = p1.camino[i];
            }
        }
    } else {
        *h1 = p1;
        *h2 = p2;
    }
}

// Mutación: Regenera un tramo del camino desde un punto aleatorio
void mutar(Individuo *ind, int destino) {
    if (((double)rand() / RAND_MAX) < TASA_MUTACION && ind->longitud > 2) {
        int punto_mutacion = 1 + rand() % (ind->longitud - 1);
        ind->longitud = punto_mutacion;
        
        // Regenerar recorrido desde el punto mutado hacia el destino
        int actual = ind->camino[punto_mutacion - 1];
        Individuo subcamino;
        generar_camino_aleatorio(&subcamino, actual, destino);

        for (int i = 1; i < subcamino.longitud; i++) {
            if (ind->longitud < MAX_PASOS) {
                ind->camino[ind->longitud++] = subcamino.camino[i];
            }
        }
    }
}

int main() {
    srand((unsigned int)time(NULL));
    inicializar_grafo();

    // DEFINIR CIUDAD ORIGEN Y DESTINO
    // Ejemplo: 0 = Tijuana, 34 = Chihuahua (o 15 = Cabo San Lucas)
    int origen = 0;   // Tijuana
    int destino = 34; // Chihuahua

    printf("=== ALGORITMO GENETICO: RUTA DE CARRETERAS ===\n");
    printf("Origen: %s\n", NOMBRES_CIUDADES[origen]);
    printf("Destino: %s\n\n", NOMBRES_CIUDADES[destino]);

    Individuo poblacion[TAM_POBLACION];
    Individuo nueva_poblacion[TAM_POBLACION];

    // 1. Inicializar Población
    for (int i = 0; i < TAM_POBLACION; i++) {
        generar_camino_aleatorio(&poblacion[i], origen, destino);
        evaluar_individuo(&poblacion[i], destino);
    }

    Individuo mejor_absoluto = poblacion[0];

    // 2. Ciclo Evolutivo
    for (int gen = 0; gen < MAX_GENERACIONES; gen++) {
        int idx_mejor_gen = 0;

        for (int i = 0; i < TAM_POBLACION; i++) {
            if (poblacion[i].fitness > poblacion[idx_mejor_gen].fitness) {
                idx_mejor_gen = i;
            }
        }

        if (poblacion[idx_mejor_gen].fitness > mejor_absoluto.fitness) {
            mejor_absoluto = poblacion[idx_mejor_gen];
        }

        // Crear nueva generación
        for (int i = 0; i < TAM_POBLACION; i += 2) {
            Individuo p1 = seleccion_torneo(poblacion, 3);
            Individuo p2 = seleccion_torneo(poblacion, 3);

            Individuo h1, h2;
            cruce(p1, p2, &h1, &h2, destino);

            mutar(&h1, destino);
            mutar(&h2, destino);

            evaluar_individuo(&h1, destino);
            evaluar_individuo(&h2, destino);

            nueva_poblacion[i] = h1;
            if (i + 1 < TAM_POBLACION) {
                nueva_poblacion[i + 1] = h2;
            }
        }

        // Copiar nueva población
        for (int i = 0; i < TAM_POBLACION; i++) {
            poblacion[i] = nueva_poblacion[i];
        }

        if ((gen + 1) % 50 == 0 || gen == 0) {
            printf("Generacion %d - Mejor Distancia: %d Km\n", gen + 1, mejor_absoluto.distancia_total);
        }
    }

    // 3. Mostrar Resultados Finales
    printf("\n================ RESULTADO OPTIMO ================\n");
    printf("Distancia Total: %d Km\n", mejor_absoluto.distancia_total);
    printf("Ruta Encontrada (%d ciudades):\n", mejor_absoluto.longitud);

    for (int i = 0; i < mejor_absoluto.longitud; i++) {
        printf(" -> %s", NOMBRES_CIUDADES[mejor_absoluto.camino[i]]);
    }
    printf("\n==================================================\n");

    return 0;
}