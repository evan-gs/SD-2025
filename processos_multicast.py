#!/usr/bin/env python3

from scapy.all import IP, UDP, send, sniff, Packet, ByteEnumField, IntField, StrField
import sys
import socket
import time
import threading

# Classe de protocolo personalizada para envio de mensagem e clock lógico
class message(Packet):
    name = "Message"
    fields_desc = [
        ByteEnumField("tipe", 0, {0:"MSG", 1:"ACK"}),
        IntField("timestamp", 0),
        IntField("src_process", 0),
        IntField("dst_process", 0),
        IntField("ack_timestamp", 0),
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

def deal_with_msg(msg, id, clock, msg_queue, ack_queue, sock):
    print(f"-> Pacote recebido do <<P{msg.src_process}>>")
    print(f"\n->tipo:{msg.tipe}\n->src_process:{msg.src_process}\n->dst_process:{msg.dst_process}\n->clock:{clock[0]}\n->timestamp:{msg.timestamp}\n->ack_timestamp:{msg.ack_timestamp}")
    
    if msg.tipe == 0:
        clock[0] = max(clock[0], msg.timestamp) + 1
        key = (msg.timestamp, msg.dst_process)
        pending_ack = ack_queue.pop(key, set())
        pending_ack.add(id)
        print(key)
        print(pending_ack)
        msg_queue.append((msg.timestamp, msg.src_process, msg.dst_process, msg.text, pending_ack))
        msg_queue.sort()
        for pid, (host, port) in process.items():
            if pid == id:
                continue
            ack = message(tipe=1, timestamp=clock[0], src_process=id, dst_process=pid, ack_timestamp=msg.timestamp)
            sock.sendto(bytes(ack), (host, port))
            
    elif msg.tipe == 1:
        clock[0] = max(clock[0], msg.timestamp) + 1
        key = (msg.ack_timestamp, msg.dst_process)
        print(f"\n->chave do ack: {key}\n")
        for i, (timestamp, src, dst, text, acks) in enumerate(msg_queue):
            print(f"-> chave do for: {(timestamp, dst)}\n src:{src}")
            if (timestamp, dst) == key:
                acks.add(msg.src_process)  
                msg_queue[i] = (timestamp, src, dst, text, acks)
                break
            else:
                ack_queue.setdefault(key, set()).add(msg.src_process)
            
    while len(msg_queue) > 0:
        print(f"-> Fila atual em <<P{id}>>: {[ (timestamp, src, dst, text, list(acks)) for timestamp, src, dst, text, acks in msg_queue ]}")
        timestamp, src, dst, text, acks = msg_queue[0]
        if len(acks) == num_process:  
            print(f"-> Mensagem entrege em <<P{id}>>: \"{text}\" de <<P{src}>>")
            msg_queue.pop(0)
        else:
            break        

def tr_receive_msg(id, port, clock, msg_queue, ack_queue):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    while True:
        data, addr = sock.recvfrom(4096)
        pkt = message(data)
        deal_with_msg(pkt, id, clock, msg_queue, ack_queue, sock)


def tr_send_msg(id, clock, latency):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        text = input("")
        clock[0] += id
        msg_clock = clock[0]
        print(f"-> clock: {clock[0]}")
        for pid, (host, port) in process.items():
            pkt = message(tipe=0, timestamp=msg_clock, src_process=id, dst_process=pid, text=text)
            sock.sendto(bytes(pkt), (host, port))
            time.sleep(latency)
            
        
        
if __name__ == "__main__":
    id = int(sys.argv[1])
    host, port = process[id]

    clock = [0]
    msg_queue = []
    ack_queue = {}
    
    if len(sys.argv) > 2:
        latency = float(sys.argv[2])
    else:
        latency = 0.0
    
    print(f"Processo: <<P{id}>> rodando em {host}:{port}")
    
    # uma thread para tratar o recebimento dos pacotes
    th = threading.Thread(target=tr_receive_msg, args=(id, port, clock, msg_queue, ack_queue), daemon=True)
    th.start()
    
    # outra thread para tratar o envio dos pacotes
    tr_send_msg(id, clock, latency)