#!/usr/bin/env python3

from scapy.all import *
from scapy import IP, UDP
import sys
import time
import threading

# Classe de protocolo personalizada para envio de mensagem e clock lógico
class message(Packet):
    name = "Message"
    fiels_desc = [
        ByteEnumField("tipe", 0, {0:"MSG", 1:"ACK"}),
        IntField("timestamp", 0),
        IntField("src_process", 0),
        IntField("dst_process", 0),
        IntField("src_timestamp", 0),
        IntField("dst_timestamp", 0), 
        StrField("text", "")
    ]

# Dicionário dos processos com endereço de loopback e porta
process = {
    1: ("127.0.0.1", 65001),
    2: ("127.0.0.1", 65002),
    3: ("127.0.0.1", 65003),
    4: ("127.0.0.1", 65004)
}

num_process = len(process)

def deal_with_msg():
    return 0 

def tr_receive_msg(id, port, clock, msg_queue):
    def handle_msg(pkt):
        clock = deal_with_msg(pkt, id, clock, msg_queue)
        
    sniff(filter=f"udp and port {port}", prn=handle_msg)


def tr_send_msg(id, clock, msg_queue):
    while True:
        text = input("")
        clock += 1 # pode deixar += id para desincronizar
        for pid, (host, port) in process.items():
            pkt = Message(tipe=0, timestamp=clock, src_process=id, dst_process=pid, text=text)
            send(IP(dst=host)/UDP(dport=port)/pkt)
        
        
if __name__ == "__main__":
    id = int(sys.argv[1])
    host, port = process[id]

    clock = 0
    msg_queue = []
    
    print(f"Processo: <<P{id}>> rodando em {host}:{port}")
    
    th = threading.Thread(target=tr_receive_msg, args=(id, port, clock, msg_queue))
    th.start()
    
    tr_send_msg(id, clock, msg_queue)