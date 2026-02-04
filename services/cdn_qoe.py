from ortools.linear_solver import pywraplp
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

ESTADOS = ["AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO"]

RTT_MATRIX = [
        #AC    AL    AM     AP     BA     CE     DF     ES     GO     MA     MG     MS     MT     PA     PB    PE    PI     PR     RJ     RN    RO     RR     RS     SC    SE    SP     TO
        [0.00, 0.00, 0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00, 0.00, 0.00,  0.00,  0.00,  0.00, 7.02,  0.00,  0.00,  0.00, 0.00, 0.00,  0.00],  #AC
        [0.00, 0.00, 0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00, 3.36, 0.00,  0.00,  0.00,  0.00, 0.00,  0.00,  0.00,  0.00, 5.27, 0.00,  0.00],  #AL 
        [0.00, 0.00, 0.00,  14.70, 0.00,  0.00,  35.00, 0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00, 0.00, 0.00,  0.00,  0.00,  0.00, 0.00,  43.30, 0.00,  0.00, 0.00, 0.00,  0.00],  #AM
        [0.00, 0.00, 14.90, 0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  13.80, 0.00, 0.00, 0.00,  0.00,  0.00,  0.00, 0.00,  0.00,  0.00,  0.00, 0.00, 0.00,  0.00],  #AP
        [0.00, 0.00, 0.00,  0.00,  0.00,  12.50, 17.60, 12.40, 0.00,  0.00,  19.20, 0.00,  0.00,  0.00,  9.73, 0.00, 23.30, 0.00,  0.00,  0.00, 0.00,  0.00,  0.00,  0.00, 4.37, 0.00,  0.00],  #BA
        [0.00, 0.00, 0.00,  0.00,  12.40, 0.00,  29.80, 0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00, 0.00, 7.35,  0.00,  0.00,  7.56, 0.00,  90.70, 0.00,  0.00, 0.00, 45.90, 0.00],  #CE
        [0.00, 0.00, 34.90, 0.00,  17.70, 29.70, 0.00,  0.00,  3.13,  22.30, 10.20, 0.00,  15.30, 0.00,  0.00, 0.00, 0.00,  0.00,  23.80, 0.00, 0.00,  0.00,  0.00,  0.00, 0.00, 16.80, 8.94],  #DF
        [0.00, 0.00, 0.00,  0.00,  12.40, 0.00,  0.00,  0.00,  0.00,  0.00,  31.20, 0.00,  0.00,  0.00,  0.00, 0.00, 0.00,  0.00,  57.60, 0.00, 0.00,  0.00,  0.00,  0.00, 0.00, 0.00,  0.00],  #ES
        [0.00, 0.00, 0.00,  0.00,  0.00,  0.00,  3.10,  0.00,  0.00,  0.00,  0.00,  14.90, 12.50, 0.00,  0.00, 0.00, 0.00,  0.00,  0.00,  0.00, 0.00,  0.00,  0.00,  0.00, 0.00, 0.00,  0.00],  #GO
        [0.00, 0.00, 0.00,  0.00,  0.00,  0.00,  22.10, 0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  10.80, 0.00, 0.00, 6.40,  0.00,  0.00,  0.00, 0.00,  0.00,  0.00,  0.00, 0.00, 0.00,  0.00],  #MA
        [0.00, 0.00, 0.00,  0.00,  19.10, 0.00,  10.20, 31.10, 0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00, 0.00, 0.00,  0.00,  9.65,  0.00, 0.00,  0.00,  0.00,  0.00, 0.00, 8.09,  0.00],  #MG
        [0.00, 0.00, 0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  14.80, 0.00,  0.00,  0.00,  8.94,  0.00,  0.00, 0.00, 0.00,  21.80, 0.00,  0.00, 0.00,  0.00,  0.00,  0.00, 0.00, 0.00,  0.00],  #MS
        [0.00, 0.00, 0.00,  0.00,  0.00,  0.00,  15.30, 0.00,  12.60, 0.00,  0.00,  9.07,  0.00,  0.00,  0.00, 0.00, 0.00,  0.00,  0.00,  0.00, 14.10, 0.00,  0.00,  0.00, 0.00, 0.00,  0.00],  #MT
        [0.00, 0.00, 0.00,  13.80, 0.00,  0.00,  0.00,  0.00,  0.00,  10.80, 0.00,  0.00,  0.00,  0.00,  0.00, 0.00, 0.00,  0.00,  0.00,  0.00, 0.00,  0.00,  0.00,  0.00, 0.00, 0.00,  15.70], #PA
        [0.00, 0.00, 0.00,  0.00,  9.76,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00, 2.62, 0.00,  0.00,  0.00,  2.90, 0.00,  0.00,  0.00,  0.00, 0.00, 0.00,  0.00],  #PB
        [0.00, 3.32, 0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  2.59, 0.00, 0.00,  0.00,  0.00,  0.00, 0.00,  0.00,  0.00,  0.00, 0.00, 0.00,  0.00],  #PE
        [0.00, 0.00, 0.00,  0.00,  23.30, 7.33,  0.00,  0.00,  0.00,  6.27,  0.00,  0.00,  0.00,  0.00,  0.00, 0.00, 0.00,  0.00,  0.00,  0.00, 0.00,  0.00,  0.00,  0.00, 0.00, 0.00,  0.00],  #PI
        [0.00, 0.00, 0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  22.60, 0.00,  0.00,  0.00, 0.00, 0.00,  0.00,  0.00,  0.00, 0.00,  0.00,  9.31,  4.20, 0.00, 5.19,  0.00],  #PR
        [0.00, 0.00, 0.00,  0.00,  0.00,  0.00,  23.70, 57.60, 0.00,  0.00,  9.68,  0.00,  0.00,  0.00,  0.00, 0.00, 0.00,  0.00,  0.00,  0.00, 0.00,  0.00,  0.00,  0.00, 0.00, 7.41,  0.00],  #RJ
        [0.00, 0.00, 0.00,  0.00,  0.00,  7.53,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  2.90, 0.00, 0.00,  0.00,  0.00,  0.00, 0.00,  0.00,  0.00,  0.00, 0.00, 0.00,  0.00],  #RN
        [6.75, 0.00, 0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  14.10, 0.00,  0.00, 0.00, 0.00,  0.00,  0.00,  0.00, 0.00,  0.00,  0.00,  0.00, 0.00, 0.00,  0.00],  #RO
        [0.00, 0.00, 9.70,  0.00,  0.00,  90.70, 0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00, 0.00, 0.00,  0.00,  0.00,  0.00, 0.00,  0.00,  0.00,  0.00, 0.00, 0.00,  0.00],  #RR
        [0.00, 0.00, 0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00, 0.00, 0.00,  9.35,  0.00,  0.00, 0.00,  0.00,  0.00,  5.82, 0.00, 14.20, 0.00],  #RS
        [0.00, 0.00, 0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00, 0.00, 0.00,  4.20,  0.00,  0.00, 0.00,  0.00,  5.85,  0.00, 0.00, 0.00,  0.00],  #SC
        [0.00, 4.79, 0.00,  0.00,  4.12,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00, 0.00, 0.00,  0.00,  0.00,  0.00, 0.00,  0.00,  0.00,  0.00, 0.00, 0.00,  0.00],  #SE
        [0.00, 0.00, 0.00,  0.00,  0.00,  45.80, 16.60, 0.00,  0.00,  0.00,  8.07,  0.00,  0.00,  0.00,  0.00, 0.00, 0.00,  5.16,  7.39,  0.00, 0.00,  0.00,  14.10, 0.00, 0.00, 0.00,  0.00],  #SP
        [0.00, 0.00, 0.00,  0.00,  0.00,  0.00,  8.91,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  15.70, 0.00, 0.00, 0.00,  0.00,  0.00,  0.00, 0.00,  0.00,  0.00,  0.00, 0.00, 0.00,  0.00],  #TO
    ]

def normalizar_matriz_min_max(matriz):
    matriz = np.asarray(matriz)    
    min_val = np.min(matriz)
    max_val = np.max(matriz)
    if max_val == min_val:
        return np.zeros(matriz.shape)
    matriz_normalizada = (matriz - min_val) / (max_val - min_val)
    return matriz_normalizada

def normalizar_vetor(vetor):
    vetor = np.asarray(vetor, dtype=float)
    norma = np.linalg.norm(vetor)
    if norma == 0:
        return vetor
    vetor_normalizado = vetor / norma
    return vetor_normalizado

def create_aij(a, nrttm):
    aij = [[0.0 for _ in range(27)] for _ in range(27)]
    num_nodes = len(RTT_MATRIX)
    
    for i in range (num_nodes):
        for j in range(num_nodes):
            aij[i][j] = float((a * nrttm[i][j]))

    return aij

def desenhar_grafo_qoe(matriz_rtt, estados, todos_caminhos, melhor_caminho, melhor_destino_idx, origem_idx, qoe, nome_arquivo="grafo_resultado_qoe.png"):

    G = nx.DiGraph()
    for i in range(len(estados)):
        G.add_node(i, label=estados[i])
    for i in range(len(matriz_rtt)):
        for j in range(len(matriz_rtt[i])):
            if matriz_rtt[i][j] > 0:
                G.add_edge(i, j)

    pos = nx.spring_layout(G, k=0.35, iterations=50, seed=42)
    plt.figure(figsize=(24, 18))
    plt.title("Visualização do Caminho Ótimo de QoE", size=20)
    
    # Desenho base do grafo
    nx.draw_networkx_edges(G, pos, alpha=0.1, edge_color="gray", arrows=False)
    if todos_caminhos:
        nx.draw_networkx_edges(G, pos, edgelist=todos_caminhos, edge_color="cornflowerblue", width=2.0, alpha=0.6)
    if melhor_caminho:
        nx.draw_networkx_edges(G, pos, edgelist=melhor_caminho, edge_color="red", width=3.5, arrows=True, arrowsize=20)

    if melhor_caminho:
        edge_labels = { (i, j): f"{matriz_rtt[i][j]:.2f}ms" for i, j in melhor_caminho }
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='black', font_size=8, bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))

    node_colors = ["limegreen" if node == origem_idx else "red" if node == melhor_destino_idx else "skyblue" for node in G.nodes()]
    
    node_sizes = [2500 if node == melhor_destino_idx else 1500 for node in G.nodes()]

    labels = {}
    for i, estado in enumerate(estados):
        if i == melhor_destino_idx:
            labels[i] = f"{estado}\nQoE:\n{qoe:.5f}"
        else:
            labels[i] = estado
            
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes)
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=9, font_weight="bold")

    plt.margins(0.1)
    #print("\nExibindo o grafo em uma nova janela...")
    #plt.show()


def solve_shortest_path_with_constraints():
    solver = pywraplp.Solver.CreateSolver("SCIP")
    
    if not solver:
        raise Exception("SCIP solver not available")

    # PASSO 1: PARAMETRIZAÇÃO
    # 4 BA, 18 RJ
    source = 4
    num_targets = 4
    targets = [16, 7, 6, 5] #PI ES 
    tx = [300.56, 461.94, 363.73, 476.26]
    num_nodes = len(RTT_MATRIX)

    best_qoe = float("inf")
    best_path = None
    best_target = None

    nrttm = normalizar_matriz_min_max(RTT_MATRIX)
    ntx = normalizar_vetor(tx)
    a = 0.75
    b = 0.25
    
    all_optimal_edges = set()

    for t in range(num_targets):
        # PASSO 2: VARIÁVEIS
        x = {}
        for i in range(num_nodes):
            for j in range(num_nodes):
                if RTT_MATRIX[i][j] > 0:
                    x[i, j] = solver.IntVar(0, 1, f"x_{i}_{j}")

        # PASSO 3: RESTRIÇÃO
        for v in range(num_nodes):
            constraint = solver.Constraint(0, 0)
            if v == source:
                constraint = solver.Constraint(-1, -1)  # fluxo sai da origem
            elif v == targets[t]:
                constraint = solver.Constraint(1, 1)  # fluxo entra no destino
            else:
                constraint = solver.Constraint(0, 0)

            # Adiciona coeficientes das variáveis que entram e saem do nó v
            for i in range(num_nodes):
                if (i, v) in x:
                    constraint.SetCoefficient(x[i, v], 1)  # fluxo entra
            for j in range(num_nodes):
                if (v, j) in x:
                    constraint.SetCoefficient(x[v, j], -1)  # fluxo sai

        # PASSO 4: FUNCAO OBJETIVO
        aij = create_aij(a, nrttm)
        objective = solver.Objective()
        for (i, j), var in x.items():
            objective.SetCoefficient(var, aij[i][j])
        objective.SetOffset(-b * ntx[t])
        objective.SetMinimization()

        # PASSO 5: Resolver o problema
        status = solver.Solve()
        if status == pywraplp.Solver.OPTIMAL:
            qoe = solver.Objective().Value()

            path = [(i, j) for (i, j), var in x.items() if var.solution_value() > 0]
            all_optimal_edges.update(path)

            print(f"Caminho ótimo para destino {ESTADOS[targets[t]]}:")
            rtt_path = 0
            for i, j in path:
                print(f"{ESTADOS[i]} -> {ESTADOS[j]} (RTT = {aij[i][j]:.2})")
                rtt_path = rtt_path + aij[i][j]
            print(f"RTT Caminho: {rtt_path:.3f} ms")
            print(f"Indice de QoE do caminho: {qoe:.5f}")
            print("=====\n")

            if qoe < best_qoe:
                best_qoe = qoe
                best_target = targets[t]
                best_path = [(i, j) for (i, j), var in x.items() if var.solution_value() > 0]

        solver.Clear()

    return source, best_target, best_qoe, best_path, list(all_optimal_edges)

if __name__ == "__main__":
    source, target, qoe, path, all_edges = solve_shortest_path_with_constraints()

    if path:
            print("\n--- RESULTADO FINAL ---")
            print(f"Origem: {ESTADOS[source]}")
            print(f"Melhor destino: {ESTADOS[target]}")
            print(f"Melhor Índice de QoE (custo mínimo): {qoe:.5f}")
            
            rtt_total_do_melhor_caminho = 0
            print("Melhor Caminho e RTTs:")
            for i, j in path:
                rtt_trecho = RTT_MATRIX[i][j]
                rtt_total_do_melhor_caminho += rtt_trecho
                print(f"  {ESTADOS[i]} -> {ESTADOS[j]} (RTT = {rtt_trecho} ms)")
            print(f"RTT Total do Melhor Caminho: {rtt_total_do_melhor_caminho:.2f} ms")

            desenhar_grafo_qoe(
                matriz_rtt=RTT_MATRIX,
                estados=ESTADOS,
                todos_caminhos=all_edges,
                melhor_caminho=path,
                melhor_destino_idx=target,
                origem_idx=source,
                qoe=qoe
            )

def run_qoe():
    source, target, qoe, path, all_edges = solve_shortest_path_with_constraints()
    return source, target, qoe, path, all_edges
