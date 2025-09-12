#!/usr/bin/env python3

from scapy.all import *
import sys
import time
import threading

# Classe personalizada para mensagem e clock lógico
class mensagem(Packet):
    name = "Mensagem"
    fiels_desc = [
        ByteEnumField("tipo", 0, {0:"MSG", 1:"ACK"}),
        IntField("timestamp", 0),
        IntField("src_process", 0),
        IntField("dst_process", 0),
        IntField("src_timestamp", 0),
        IntField("dst_timestamp", 0), 
        StrField("mensagem", "")
    ]

# Dicionário dos processos com endereço de loopback e porta
processos = {
    1: ("127.0.0.1", 65001),
    2: ("127.0.0.1", 65002),
    3: ("127.0.0.1", 65003),
    4: ("127.0.0.1", 65004)
}

num_processos = len(processos)

id = int(sys.argv[1])
src, port = processos[id]

clock = 0 
fila = []