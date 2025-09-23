#Projeto feito por Gabriel Evangelista Gonçalves da Silva - RA 802791 e Gabriel Andrade - RA 815407

#!/usr/bin/env python3

from scapy.all import Packet, ByteEnumField, IntField
from colorama import Fore, Style
import sys
import socket
import time
import threading

# Classe de protocolo personalizada para envio de requests, comfirmação ou negação
class message(Packet):
    name = "Message"
    fields_desc = [
        ByteEnumField("tipe", 0, {0:"REQ", 1:"ACK", 2:"NACK"}),
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

# Dicionário dos processos com os recursos a serem requisitados
req_per_process = {
    1: [1,2,1], #[1,2,1] 
    2: [2,1,2], #[2,1,2]
    3: [1,2,1], #[1,2,1]
    4: [2,1,2]  #[2,1,2]
}

num_process = len(process)
num_resources = 2

def use_resource(resource, id, clock, sock, pending_requests, request_timestamp):
    print(Fore.BLUE + Style.BRIGHT + f"|| <<P{id}>> entrou no recurso {resource} com clock [{clock[0]}]" + Style.RESET_ALL)
    time.sleep(3)
    print(Fore.BLUE + Style.BRIGHT + f"|| <<P{id}>> liberou o recurso {resource} com clock [{clock[0]}]\n" + Style.RESET_ALL)
    resource_state[resource] = False
    for req in pending_requests[resource]:
        if req.src_process != id:
            ack = message(tipe=1, src_process=id, dst_process=req.src_process, resource=resource, timestamp=clock[0])
            sock.sendto(bytes(ack), process[req.src_process])
            print(f"<<P{id}>> || clock [{clock[0]}]: enviou ACK para P{req.src_process} para recurso {resource}")
    pending_requests[resource].clear()
    request_timestamp[resource] = None

def deal_with_msg(msg, id, clock, ack_queue, sock, resource_state, pending_requests, request_timestamp):    
    clock[0] = max(clock[0], msg.timestamp) + 1

    if msg.tipe == 0 and msg.dst_process == id:
        print(f"<<P{id}>> || clock [{clock[0]}]: recebeu REQ do <<P{msg.src_process}>> com timestamp <{msg.timestamp}> para o recurso <{msg.resource}>\n")
        
        my_request_timestamp = request_timestamp.get(msg.resource, None)
        
        if not resource_state[msg.resource] and (my_request_timestamp is None or msg.timestamp < my_request_timestamp or (msg.timestamp == my_request_timestamp and msg.src_process < id)): 
            ack = message(tipe=1, src_process=id, dst_process=msg.src_process, resource=msg.resource, timestamp=clock[0])
            sock.sendto(bytes(ack), process[msg.src_process])
            print(f"<<P{id}>> || clock [{clock[0]}]: enviou ACK para P{msg.src_process} para recurso {msg.resource}\n")
        else: 
            nack = message(tipe=2, src_process=id, dst_process=msg.src_process, resource=msg.resource, timestamp=clock[0])
            sock.sendto(bytes(nack), process[msg.src_process])
            pending_requests[msg.resource].append(msg)
            print(f"<<P{id}>> || clock [{clock[0]}]: enviou NACK para P{msg.src_process} para recurso {msg.resource}\n")

    elif msg.tipe == 1 and msg.dst_process == id:
        ack_queue[msg.resource].append(msg.src_process)

    elif msg.tipe == 2 and msg.dst_process == id:
        pending_requests[msg.resource].append(message(tipe=0, src_process=id, dst_process=msg.src_process, resource=msg.resource))

    for res, queue in ack_queue.items():
        if len(queue) == (num_process - 1) and not resource_state[res]:
            queue.clear()
            resource_state[res] = True
            threading.Thread(target=use_resource, args=(res, id, clock, sock, pending_requests, request_timestamp), daemon=True).start()

def tr_receive_msg(id, port, clock, ack_queue, resource_state, pending_requests, request_timestamp):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    while True:
        data, addr = sock.recvfrom(4096)
        pkt = message(data)
        deal_with_msg(pkt, id, clock, ack_queue, sock, resource_state, pending_requests, request_timestamp)

def tr_send_msg(id, clock, resource_state, requisitions, request_timestamp):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    req = req_per_process[id]
    time.sleep(3) 
    for i in range(requisitions):
        required = req[i] 
        if not resource_state[required]:
            clock[0] += 1
            request_timestamp[required] = clock[0]
            print(Fore.GREEN + Style.BRIGHT + f"\n-> <<P{id}>> requisitando recurso {required} no clock <{clock[0]}> <-\n" + Style.RESET_ALL)
            for pid, (host, port) in process.items():
                if pid != id:
                    pkt = message(tipe=0, timestamp=clock[0], resource=required, src_process=id, dst_process=pid)
                    sock.sendto(bytes(pkt), (host, port))
        else:
            print(f"\n!!! <<P{id}>> tentou solicitar um recurso que ele mesmo está usando !!!\n")
        time.sleep(5) 
    time.sleep(30)

if __name__ == "__main__":
    id = int(sys.argv[1])
    host, port = process[id]

    clock = [0] 
    ack_queue = {ack: [] for ack in range(1, num_resources + 1)}          
    resource_state = {resource: False for resource in range(1, num_resources+1)}
    pending_requests = {resource: [] for resource in range(1, num_resources+1)}
    request_timestamp = {res: None for res in range(1, num_resources+1)}
    
    print(f"Processo: <<P{id}>> rodando em {host}:{port}")
    
    # uma thread para tratar o recebimento dos pacotes
    th = threading.Thread(target=tr_receive_msg, args=(id, port, clock, ack_queue, resource_state, pending_requests, request_timestamp), daemon=True)
    th.start()
    
    # outra thread para tratar o envio dos pacotes
    tr_send_msg(id, clock, resource_state, 3, request_timestamp)
