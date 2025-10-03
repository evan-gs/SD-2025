#Projeto feito por Gabriel Evangelista Gonçalves da Silva - RA 802791 e Gabriel Andrade - RA 815407

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

    while True:
        try:
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
            while (connection := input("")) != "q": #possivelmente botar um regex pra evitar coisas diferentes de dois inteiros
                first_node, second_node = connection.split()
                a = int(first_node)
                b = int(second_node)

                node_connections[a].append(second_node)
                node_connections[b].append(first_node)

            print(Fore.YELLOW + Style.BRIGHT + f"\n-> <<CONEXÕES INSERIDAS>> <-\n" + Style.RESET_ALL)
            
            for pid in process:
                #Prepara os dados para envio
                msg_connections = " ".join(node_connections[pid])
                #print(node_capacity[pid])
                #print(msg_connections)

                host, port = process[pid]
                pkt = graph(tipe=0, dst_process=pid, capacity=node_capacity[pid], connections=msg_connections)
                sock.sendto(bytes(pkt), (host, port))
        except ValueError:
            print(Fore.YELLOW + Style.BRIGHT + f"\n-> <<ERRO! INSIRA CORRETAMENTE OS VALORES>> <-\n" + Style.RESET_ALL)
    

if __name__ == "__main__":
    node_capacity = {cap: 0 for cap in range(1, num_process + 1)}
    node_connections = {node: [] for node in range(1, num_process + 1)}

    # inicia o envio de grafos para os processos
    send_msg()
