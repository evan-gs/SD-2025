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
        ByteEnumField("tipe", 0, {0:"REQ", 1:"REL", 2:"ACK", 3:"NACK", 4:"BUSY"}),
        IntField("timestamp", 0),
        IntField("resource", 0),
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
num_resources = 2
required_key = 0

def deal_with_msg(msg, id, clock, ack_queue, sock, resource_state):    
    clock[0] = max(clock[0], msg.timestamp) + 1
    global required_key
    
    if msg.tipe == 0 and msg.dst_process == id:        
        for pid, (host, port) in process.items():
            if pid == id:
                continue

            elif msg.timestamp < clock[0] or (msg.timestamp == clock[0] and msg.src_process < id):
                ack = message(tipe=2, src_process=id, dst_process=msg.src_process, resource=msg.resource)
                sock.sendto(bytes(ack), (host, port))
                
            elif msg.timestamp > clock[0] or (msg.timestamp == clock[0] and msg.src_process > id):
                ack = message(tipe=3, src_process=id, dst_process=msg.src_process, resource=msg.resource)
                sock.sendto(bytes(ack), (host, port))

            print("veio request")
            
    elif msg.tipe == 1 and msg.dst_process == id:
        #descobre se recurso tá aberto e request pra processo que estava o usando
        resource_state[msg.resource] = False
        print(f"recurso {msg.resource+1} livre")
        if required_key != 0:
            for pid, (host, port) in process.items():
                if pid == msg.src_process:
                    pkt = message(tipe=0, timestamp=clock[0], resource=required_key, src_process=id, dst_process=msg.src_process)
                    sock.sendto(bytes(pkt), (host, port))

            
    elif msg.tipe == 2 and msg.dst_process == id:
        #adiciona acks por recurso pedido
        ack_queue[msg.resource].append(msg.src_process)
        print(f"veio ack de {msg.src_process}")
        
    elif msg.tipe == 3 and msg.dst_process == id:
        #só recebe o nack, e a lista de acks não muda. sem necessidade de tratar o nack
        print("tomei nack")

    elif msg.tipe == 4 and msg.dst_process == id:
        #limpa o queue uma vez que não há forma de pegar aquele recurso mais
        resource_state[msg.resource] = True
        print(f"processo {msg.src_process} tá usando o recurso {msg.resource+1}")
            
    for i, queue in enumerate(ack_queue.values()):
        if len(queue) >= (num_process - 1):
            queue.clear()
            required_key = 0
            resource_state[i] = True
            for pid, (host, port) in process.items():
                if pid == id:
                    continue
                ack = message(tipe=4, src_process=id, dst_process=pid, resource=i)
                sock.sendto(bytes(ack), (host, port))
            print(f"utilizando recurso {i}")
            time.sleep(3)        
            resource_state[i] = False
            for pid, (host, port) in process.items():
                if pid == id:
                    continue
                ack = message(tipe=1, src_process=id, dst_process=pid, resource=i)
                sock.sendto(bytes(ack), (host, port))
            print(f"recurso {i} liberado")

def tr_receive_msg(id, port, clock, ack_queue, resource_state):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    while True:
        data, addr = sock.recvfrom(4096)
        pkt = message(data)
        deal_with_msg(pkt, id, clock, ack_queue, sock, resource_state)


def tr_send_msg(id, clock):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    global required_key
    while True:
        required = int(input(f"Escolha um recurso entre (1, {num_resources}): "))
        clock[0] += 1
        required_key = required
        for pid, (host, port) in process.items():
            pkt = message(tipe=0, timestamp=clock[0], resource=required, src_process=id, dst_process=pid)
            sock.sendto(bytes(pkt), (host, port))
            
        
if __name__ == "__main__":
    id = int(sys.argv[1])
    host, port = process[id]

    required_key = 0
    clock = [0] 
    ack_queue = {ack: [] for ack in range(1, num_resources + 1)}          
    resource_state = {resource: False for resource in range(1, num_resources+1)}
    
    print(f"Processo: <<P{id}>> rodando em {host}:{port}")
    
    # uma thread para tratar o recebimento dos pacotes
    th = threading.Thread(target=tr_receive_msg, args=(id, port, clock, ack_queue, resource_state), daemon=True)
    th.start()
    
    # outra thread para tratar o envio dos pacotes
    tr_send_msg(id, clock)
