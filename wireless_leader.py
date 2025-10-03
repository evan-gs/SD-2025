#Projeto feito por Gabriel Evangelista Gonçalves da Silva - RA 802791 e Gabriel Andrade - RA 815407

#!/usr/bin/env python3

from scapy.all import Packet, ByteEnumField, IntField, StrField
from colorama import Fore, Style
import sys
import socket
import time
import threading

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

# Classe de protocolo personalizada para envio de eleição e confirmação de resultado
class message(Packet):
    name = "Message"
    fields_desc = [
        ByteEnumField("ptype", 1, {0:"ELECTION"}),
        ByteEnumField("tipe", 0, {0:"ELECTION", 1:"OK", 2:"ALLHAIL"}),
        IntField("src_process", 0),
        IntField("dst_process", 0),
        IntField("highest_process", 0),
        IntField("highest_capacity", 0)
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

def deal_with_msg(msg, id, sock, leader, election_happening, connections, capacity):   
    if isinstance(msg, graph):
        if msg.tipe == 0: 
            print(Fore.YELLOW + Style.BRIGHT + f"\n-> <<NOVO GRAFO>> <-\n" + Style.RESET_ALL)
            connections = []
            str_connections = msg.connections.split()
            for node in str_connections:
                connections.append(int(node))
            capacity[0] = msg.capacity
            print(connections)
            print(capacity)
    elif isinstance(msg, message):
        pass

def tr_receive_msg(id, port, leader, election_happening, connections, capacity):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    while True:
        try:
            data, addr = sock.recvfrom(4096)
        except ConnectionResetError:
            continue
        ptype = data[0]
        if ptype == 0:   # pacote Message
            pkt = graph(data)
        else:            # pacote Heartbeat
            pkt = message(data)
        deal_with_msg(pkt, id, sock, leader, election_happening, connections, capacity)

def tr_send_msg(id, leader, election_happening, connections, capacity):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(Fore.YELLOW + Style.BRIGHT + f"\n-> <<P{id}>> <-\n" + Style.RESET_ALL)

    while True:
        print(Fore.RED + Style.BRIGHT + f"\n-> <<ENTER PARA INICIAR UMA ELEIÇÃO>> <-\n" + Style.RESET_ALL)
        input("")

        host, port = process[pid]
        pkt = message(tipe=0, src_process=id, dst_process=pid)
        sock.sendto(bytes(pkt), (host, port))
        is_lowest = False

if __name__ == "__main__":
    id = int(sys.argv[1])
    host, port = process[id]
          
    leader = [0]
    election_happening = [False]
    node_connections = []
    node_capacity = [0]
    
    print(f"Processo: <<P{id}>> rodando em {host}:{port}")
    
    # uma thread para tratar o recebimento dos pacotes
    threading.Thread(target=tr_receive_msg, args=(id, port, leader, election_happening, node_connections, node_capacity), daemon=True).start()

    # outra thread para tratar o envio dos pacotes
    tr_send_msg(id, leader, election_happening, node_connections, node_capacity)
