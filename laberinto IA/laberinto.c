#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <stdbool.h>



#define N 150                       // El laberinto es de 150 x 150
#define NUM_CELDAS (N * N)          // Cada celda libre 
#define MAX_PASOS 3000
#define TAM_POBLACION 15
#define MAX_GENERACIONES 10000
#define TASA_CRUCE 0.8
#define TASA_MUTACION 0.3
#define PENALIZACION_SIN_SALIDA 10000
 
// Laberinto leido del CSV: 1 = pared, 0 = camino libre
int laberinto[N][N]; 

// Estructura de un individuo (cromosoma)
typedef struct {
    int camino[MAX_PASOS]; // Lista de IDs de ciudades
    int longitud;          // Cantidad de ciudades en la ruta
    int distancia_total;   // Distancia acumulada en Km
    double fitness;        // Valor de aptitud
} Individuo;

 
// LEER EL LABERINTO DESDE EL CSV 
void inicializar_laberinto(const char *archivo) {
    FILE *f = fopen(archivo, "r");
    if (f == NULL) {
        printf("No se pudo abrir %s\n", archivo);
        exit(1);
    }
    int fila = 0, col = 0, c;
    while ((c = fgetc(f)) != EOF && fila < N) {
        if (c == '0' || c == '1') {
            laberinto[fila][col++] = c - '0';
        } else if (c == '\n') {
            fila++;
            col = 0;
        }
    }
    fclose(f);
}


// Función para obtener vecinos válidos de una celda
int obtener_vecinos(int celda, int vecinos[]) {
    int fila = celda / N, col = celda % N;
    int df[4] = {-1, 1, 0, 0};
    int dc[4] = {0, 0, -1, 1};
    int count = 0;
    for (int k = 0; k < 4; k++) {
        int nf = fila + df[k], nc = col + dc[k];
        if (nf >= 0 && nf < N && nc >= 0 && nc < N && laberinto[nf][nc] == 0) {
            vecinos[count++] = nf * N + nc;
        }
    }
    return count;
}

int distancia(int u, int v) {
    int fila_u = u / N, col_u = u % N;
    int fila_v = v / N, col_v = v % N;
    return abs(fila_u - fila_v) + abs(col_u - col_v); // Distancia Manhattan
}

// Genera una caminata aleatoria desde origen a destino
void generar_camino_aleatorio(Individuo *ind, int origen, int destino) {
    ind->camino[0] = origen;
    ind->longitud = 1;
    int actual = origen;

    bool visitado[NUM_CELDAS] = {false};
    memset(visitado, 0, sizeof(visitado));
    visitado[origen] = true;

    int pasos = 0; // limite de intentos para no ciclar eternamente
   
    while (actual != destino && pasos < 200 * NUM_CELDAS && ind->longitud < MAX_PASOS) {
        pasos++;
        int vecinos[4];
        int num_vecinos = obtener_vecinos(actual, vecinos);

        // Filtrar vecinos no visitados
        int no_visitados[4];
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
        /*} else if (ind->longitud > 1) {
            // Callejon sin salida: retroceder un paso
            ind->longitud--;
            actual = ind->camino[ind->longitud - 1]; 
            */
        } else {
            break; // no hay más opciones
        }
    }
    
}

// Calcular la distancia total y fitness
void evaluar_individuo(Individuo *ind, int destino) {
    ind->distancia_total = 0; // Cada paso cuenta como 1 unidad de distancia
    int ultimo = ind->camino[ind->longitud - 1]; 
    bool callejon_sin_salida = (ultimo != destino);
    
    if (ultimo != destino) {
        ind->distancia_total += PENALIZACION_SIN_SALIDA + 10*distancia(ultimo, destino); // Penalización si no llega al destino
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


void eliminar_ciclos(Individuo *ind, int destino) { //Cortar ciclos en el camino del individuo, apartir de la primera ciudad repetida, se regenera el camino desde la ultima ciudad hasta el destino
    int i = 0;
    while (i < ind->longitud) {
        int ultima = i;
        for (int j = ind->longitud - 1; j > i; j--) {
            if (ind->camino[j] == ind->camino[i]) {
                ultima = j;
                break;
            }
        }
        if (ultima != i) {
            int saltos = ultima - i;
            for (int k = ultima; k < ind->longitud; k++) {
                ind->camino[k - saltos] = ind->camino[k];
            }
            ind->longitud -= saltos;
        }
        i++;
    }

    int actual = ind->camino[ind->longitud - 1];
        Individuo subcamino;
        generar_camino_aleatorio(&subcamino, actual, destino);

        for (int i = 1; i < subcamino.longitud; i++) {
            if (ind->longitud < MAX_PASOS) {
                ind->camino[ind->longitud++] = subcamino.camino[i];
            }
        }
}


int main() {
    srand((unsigned int)time(NULL));
    inicializar_laberinto("laberinto_150x150.csv");


    //DEFINIR ORIGEN Y DESTINO
    int origen = 1 * N + 1;   
    int destino = 147 * N + 147; 

    printf("=== ALGORITMO GENETICO: LABERINTO 150x150 ===\n");
    printf("Origen: (%d,%d)\n", origen / N, origen % N);
    printf("Destino: (%d,%d)\n\n", destino / N, destino % N);

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

            eliminar_ciclos(&h1, destino);   //nuevo
            eliminar_ciclos(&h2, destino);   //nuevo

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

        if ((gen + 1) % 1000 == 0 || gen == 0) {
            printf("Generacion %d - Mejor Distancia: %d Km - Numero de pasos: %d\n", gen + 1, mejor_absoluto.distancia_total, mejor_absoluto.longitud);
            printf("\n");
        }
    }

    // 3. Mostrar Resultados Finales
    printf("\n================ RESULTADO OPTIMO ================\n");
    printf("Distancia Total: %d Km\n", mejor_absoluto.distancia_total);
    printf("Ruta Encontrada (%d pasos):\n", mejor_absoluto.longitud);

    for (int i = 0; i < mejor_absoluto.longitud; i++) {
        printf(" -> (%d,%d) ", mejor_absoluto.camino[i] / N, mejor_absoluto.camino[i] % N);
    }
    printf("\n==================================================\n");

    return 0;
}