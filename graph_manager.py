#Projeto feito por Gabriel Santos de Andrade - RA 815407
# Gabriel Evangelista Gonçalves da Silva - RA 802791

#!/usr/bin/env python3

from scapy.all import Packet, ByteEnumField, IntField, StrField
from colorama import Fore, Style
import socket

# Classe de protocolo personalizada para iniciar grafo de conexões
class graph(Packet):
    name = "graph"
    fields_desc = [
        ByteEnumField("ptype", 0, {0:"NEWGRAPH"}),
        ByteEnumField("tipe", 0, {0:"INFO"}),
        IntField("dst_process", 0),
        IntField("capacity", 0),
        StrField("connections", "")
    ]

# Dicionário dos processos com endereço de loopback e porta
process = {
    1: ("127.0.0.1", 65001),
    2: ("127.0.0.1", 65002),
    3: ("127.0.0.1", 65003),
    4: ("127.0.0.1", 65004),
    5: ("127.0.0.1", 65005),
    6: ("127.0.0.1", 65006),
    7: ("127.0.0.1", 65007),
    8: ("127.0.0.1", 65008),
    9: ("127.0.0.1", 65009),
    10: ("127.0.0.1", 65010)
}

num_process = len(process)

def send_msg():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Cada iteração aqui é uma topologia diferente. Podemos ficar mudando em tempo real nos processos, embora não haja failsafe ainda se fizermos isso no meio de uma eleição
    while True:
        try:
            print(Fore.YELLOW + Style.BRIGHT + f"\n-> <<ESCOLHA UMA OPÇÃO>> <-\n" + Style.RESET_ALL)
            print("1 - Configuração manual do grafo")
            print("2 - Configuração automática do grafo")
            opcao = input("Digite 1 ou 2: ")
            
            if opcao == "2":
                # Configuração automática - topologia fornecida
                node_connections = {
                    1: [2, 3],
                    2: [1, 4],
                    3: [1, 4, 5],
                    4: [2, 3, 6, 7],
                    5: [3, 6, 8],
                    6: [4, 5, 8, 9],
                    7: [4, 10],
                    8: [5, 6, 9],
                    9: [6, 8, 10],
                    10: [7, 9]
                }
                
                # Converter as conexões para strings (igual ao código manual)
                for pid in node_connections:
                    node_connections[pid] = [str(x) for x in node_connections[pid]]
                
                node_capacity = {
                    1: 4, 2: 4, 3: 6, 4: 4, 5: 3,
                    6: 1, 7: 8, 8: 2, 9: 4, 10: 5
                }
                
                print(Fore.YELLOW + Style.BRIGHT + f"\n-> <<CONFIGURAÇÃO AUTOMÁTICA APLICADA>> <-\n" + Style.RESET_ALL)
                
            else:
                # Configuração manual - código original mantido
                node_capacity = {cap: 0 for cap in range(1, num_process + 1)}
                node_connections = {node: [] for node in range(1, num_process + 1)}
                
                for pid in node_connections:
                    node_connections[pid].clear()
                print(Fore.YELLOW + Style.BRIGHT + f"\n-> <<DIGITE EM UMA LINHA AS NOVAS CAPACIDADES, CASO QUEIRA MUDAR O GRAFO>> <-\n" + Style.RESET_ALL)
                capacity = input("")
                for pid in range(1, 10):
                    first_node, second_node = capacity.split(" ", 1)
                    node_capacity[pid] = int(first_node)
                    capacity = second_node
                node_capacity[10] = int(capacity)

                print(Fore.YELLOW + Style.BRIGHT + f"\n-> <<DIGITE, POR LINHA, CADA CONEXÃO DO GRAFO. DIGITE 'q' PARA ENVIAR>> <-\n" + Style.RESET_ALL)
                while (connection := input("")) != "q":
                    first_node, second_node = connection.split()
                    a = int(first_node)
                    b = int(second_node)

                    node_connections[a].append(second_node)
                    node_connections[b].append(first_node)

                print(Fore.YELLOW + Style.BRIGHT + f"\n-> <<CONEXÕES INSERIDAS>> <-\n" + Style.RESET_ALL)
            
            # Envio para todos os processos (comum para ambas as opções)
            for pid in process:
                #Prepara os dados para envio
                msg_connections = " ".join(node_connections[pid])
                #print(node_capacity[pid])
                #print(msg_connections)

                # !!!MAIS IMPORTANTE!!!
                # envia a capacidade como um inteiro, conexões como uma string a ser tratada
                # !!!MAIS IMPORTANTE!!!
                host, port = process[pid]
                pkt = graph(tipe=0, dst_process=pid, capacity=node_capacity[pid], connections=msg_connections)
                sock.sendto(bytes(pkt), (host, port))
                
        except ValueError:
            print(Fore.YELLOW + Style.BRIGHT + f"\n-> <<ERRO! INSIRA CORRETAMENTE OS VALORES (NÚMEROS INTEIROS)>> <-\n" + Style.RESET_ALL)
        except KeyError:
            print(Fore.YELLOW + Style.BRIGHT + f"\n-> <<ERRO! INSIRA CONEXÕES POSSÍVEIS NOS 10 NÓS (APENAS VALORES DE 1 A 10)>> <-\n" + Style.RESET_ALL)
    

if __name__ == "__main__":
    # inicia o envio de grafos para os processos
    send_msg()