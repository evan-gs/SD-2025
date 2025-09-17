#Projeto feito por Gabriel Evangelista Gonçalves da Silva - RA 802791 e Gabriel Andrade - RA 815407

#!/usr/bin/env python3

from scapy.all import Packet, ByteEnumField, IntField
import sys
import socket
import time
import threading

# Classe de protocolo personalizada para envio de requests, comfirmação ou negação
class message(Packet):
    name = "Message"
    fields_desc = [
        ByteEnumField("tipe", 0, {0:"REQ", 1:"ACK", 2:"NACK"}),
        IntField("src_process", 0),
        IntField("dst_process", 0),
    ]

# Dicionário dos processos com endereço de loopback e porta
process = {
    1: ("127.0.0.1", 65001),
    2: ("127.0.0.1", 65002),
    3: ("127.0.0.1", 65003),
    4: ("127.0.0.1", 65004)
}

num_process = len(process)

def deal_with_msg(msg, id, clock, req_queue, ack_queue, sock):    
    clock[0] = max(clock[0], msg.timestamp) + 1
    
    if msg.tipe == 0 and msg.dst_process == id:        
        for pid, (host, port) in process.items():
            if pid == id:
                continue
            ack = message(tipe=1, src_process=id, dst_process=pid)
            sock.sendto(bytes(ack), (host, port))
            
    elif msg.tipe == 1 and msg.dst_process == id:
        for _ in range(0):
            break
            
    elif msg.tipe == 2 and msg.dst_process == id:
        for _ in range(0):
            break
            
    while len(req_queue) > 0:
        if 1 == num_process:  
            req_queue.pop(0)
        else:
            break        

def tr_receive_msg(id, port, clock, req_queue, ack_queue):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    while True:
        data, addr = sock.recvfrom(4096)
        pkt = message(data)
        deal_with_msg(pkt, id, clock, req_queue, ack_queue, sock)


def tr_send_msg(id, clock):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        text = input("")
        clock[0] += 1
        #print(f"-> clock do envio da mensagem {message_id}: {clock[0]}")
        for pid, (host, port) in process.items():
            pkt = message(tipe=0, src_process=id, dst_process=pid)
            sock.sendto(bytes(pkt), (host, port))
            
        
        
if __name__ == "__main__":
    id = int(sys.argv[1])
    host, port = process[id]

    clock = [0] 
    req_queue = []
    ack_queue = {}
    
    print(f"Processo: <<P{id}>> rodando em {host}:{port}")
    
    # uma thread para tratar o recebimento dos pacotes
    th = threading.Thread(target=tr_receive_msg, args=(id, port, clock, req_queue, ack_queue), daemon=True)
    th.start()
    
    # outra thread para tratar o envio dos pacotes
    tr_send_msg(id, clock)
