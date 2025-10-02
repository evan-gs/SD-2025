#Projeto feito por Gabriel Evangelista Gonçalves da Silva - RA 802791 e Gabriel Andrade - RA 815407

#!/usr/bin/env python3

from scapy.all import Packet, ByteEnumField, IntField
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

