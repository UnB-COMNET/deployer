import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from ortools.linear_solver import pywraplp
import subprocess
import re

IP_TO_ESTADO_CLIENTE = {
    "192.168.0.2": "SP"
}

IP_TO_ESTADO_SERVIDOR = {
    "192.168.0.1": "ES"
}

ESTADOS = ["ES", "MG", "RJ", "SP"]

# State -> DPID mapping 
DEVICE_MAP = {
    "ES": "of:0000000000000001",
    "MG": "of:0000000000000002",
    "RJ": "of:0000000000000003",
    "SP": "of:0000000000000004"
}

RTT_MATRIX = [[0.0 for _ in ESTADOS] for _ in ESTADOS]

def normalizar_matriz_min_max(matriz):
    matriz = np.asarray(matriz)    
    min_val = np.min(matriz); max_val = np.max(matriz)
    if max_val == min_val: return np.zeros(matriz.shape)
    return (matriz - min_val) / (max_val - min_val)

def normalizar_vetor(vetor):
    vetor = np.asarray(vetor, dtype=float)
    norma = np.linalg.norm(vetor)
    return vetor / norma if norma != 0 else vetor

def create_aij(a, nrttm):
    num_nodes = len(ESTADOS)
    aij = [[0.0 for _ in range(num_nodes)] for _ in range(num_nodes)]
    for i in range(num_nodes):
        for j in range(num_nodes):
            aij[i][j] = float(a * nrttm[i][j])
    return aij

# Brief: Lê o link-latencies do ONOS e popula a RTT_MATRIX global
def get_dynamic_latencies():
    global RTT_MATRIX
    # Zera a matriz para não usar lixo de execuções passadas
    RTT_MATRIX = [[0.0 for _ in ESTADOS] for _ in ESTADOS]
    
    try:
        # Usando 'c1' como confirmado no seu docker ps
        cmd = "docker exec -t c1 /home/onos/apache-karaf-4.2.14/bin/client -u karaf -p karaf 'link-latencies'"
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8")
        
        pattern = r"src=(of:[a-f0-9]+)/\d+, dst=(of:[a-f0-9]+)/\d+.*--- (\d+)ms"
        matches = re.finditer(pattern, output)
        rev_map = {v: k for k, v in DEVICE_MAP.items()}
        
        for m in matches:
            src_st = rev_map.get(m.group(1))
            dst_st = rev_map.get(m.group(2))
            lat = float(m.group(3))
            if src_st and dst_st:
                RTT_MATRIX[ESTADOS.index(src_st)][ESTADOS.index(dst_st)] = lat
                
    except Exception as e:
        print(f"\n [AVISO] Falha ao ler ONOS: {e}")
        print(" [AVISO] Injetando topologia de Fallback para o Solver não crashar...")
        
        # PLANO B: Topologia base (ES-MG, ES-RJ, MG-SP, RJ-SP) 
        # Valores simulados para o caso do Docker falhar no Deployer
        def add_link(u, v, lat):
            RTT_MATRIX[ESTADOS.index(u)][ESTADOS.index(v)] = lat
            RTT_MATRIX[ESTADOS.index(v)][ESTADOS.index(u)] = lat

        add_link("ES", "MG", 10.0)
        add_link("ES", "RJ", 20.0) # Gargalo que criamos no main.py
        add_link("MG", "SP", 10.0)
        add_link("RJ", "SP", 10.0)

def solve_shortest_path_with_constraints(source_uf: str, target_ufs: list[str], tx: list[float]):
    get_dynamic_latencies() # Atualiza a matriz antes de resolver
    
    # PASSO 1: PARAMETRIZAÇÃO
    solver = pywraplp.Solver.CreateSolver("SCIP")
    num_nodes = len(RTT_MATRIX)
    source = ESTADOS.index(source_uf)
    targets = [ESTADOS.index(uf) for uf in target_ufs]
    
    nrttm = normalizar_matriz_min_max(RTT_MATRIX)
    ntx = normalizar_vetor(tx)
    a, b = 0.75, 0.25
    
    best_qoe = float("inf")
    best_path, best_target = None, None
    all_edges = set()

    for t in range(len(targets)):
        # PASSO 2: VARIÁVEIS
        x = {}
        for i in range(num_nodes):
            for j in range(num_nodes):
                if RTT_MATRIX[i][j] > 0:
                    x[i, j] = solver.IntVar(0, 1, f"x_{i}_{j}")

        # PASSO 3: RESTRIÇÃO
        for v in range(num_nodes):
            if v == source: constraint = solver.Constraint(-1, -1)  # fluxo sai da origem
            elif v == targets[t]: constraint = solver.Constraint(1, 1)  # fluxo entra no destino
            else: constraint = solver.Constraint(0, 0)

            # Adiciona coeficientes das variáveis que entram e saem do nó v
            for i in range(num_nodes):
                if (i, v) in x: constraint.SetCoefficient(x[i, v], 1)  # fluxo entra
            for j in range(num_nodes):
                if (v, j) in x: constraint.SetCoefficient(x[v, j], -1)  # fluxo sai

        # PASSO 4: FUNCAO OBJETIVO
        aij = create_aij(a, nrttm)
        obj = solver.Objective()
        for (i, j), var in x.items():
            obj.SetCoefficient(var, aij[i][j])
        obj.SetOffset(-b * ntx[t])
        obj.SetMinimization()

        # PASSO 5: Resolver o problema
        if solver.Solve() == pywraplp.Solver.OPTIMAL:
            qoe = solver.Objective().Value()
            path = [(i, j) for (i, j), var in x.items() if var.solution_value() > 0]
            all_edges.update(path)
            if qoe < best_qoe:
                best_qoe, best_target, best_path = qoe, targets[t], path
        solver.Clear()

    return source, best_target, best_qoe, best_path, list(all_edges)
