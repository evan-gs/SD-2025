#Projeto feito por Gabriel Evangelista Gonçalves da Silva - RA 802791 e Gabriel Andrade - RA 815407

#!/usr/bin/env python3

from scapy.all import Packet, ByteEnumField, IntField
from colorama import Fore, Style
import sys
import socket
import time
import threading

# Classe de protocolo personalizada para envio de eleição e confirmação
class message(Packet):
    name = "Message"
    fields_desc = [
        ByteEnumField("ptype", 0, {0:"ELECTION"}),
        ByteEnumField("tipe", 0, {0:"ELECTION", 1:"OK"}),
        IntField("src_process", 0),
        IntField("dst_process", 0),
    ]

# Classe de protocolo personalizada para envio de heartbeat
class heartbeat(Packet):
    name = "HeartBeat"
    fields_desc = [
        ByteEnumField("ptype", 1, {1:"HEARTBEAT"}),
        ByteEnumField("tipe", 0, {0:"RU OK?", 1:"YES"}),
        IntField("src_process", 0),
        IntField("dst_process", 0),
    ]

# Dicionário dos processos com endereço de loopback e porta
process = {
    1: ("127.0.0.1", 65001),
    2: ("127.0.0.1", 65002),
    3: ("127.0.0.1", 65003),
    4: ("127.0.0.1", 65004),
    5: ("127.0.0.1", 65005)
}

num_process = len(process)

def deal_with_msg(msg, id, process_up, sock):   
    if isinstance(msg, heartbeat):
        if msg.tipe == 0: 
            pkt = heartbeat(tipe=1, src_process=id, dst_process=msg.src_process)  
            sock.sendto(bytes(pkt), process[msg.src_process])
        elif msg.tipe == 1: 
            process_up[msg.src_process] = True

    elif isinstance(msg, message):
        # sua parte aqui Evan
        i = 0
    

def tr_receive_msg(id, port, process_up):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    while True:
        data, addr = sock.recvfrom(4096)
        ptype = data[0]
        if ptype == 0:   # pacote Message
            pkt = message(data)
        else:            # pacote Heartbeat
            pkt = heartbeat(data)
        deal_with_msg(pkt, id, process_up, sock)

def tr_send_msg(id, process_up):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(Fore.YELLOW + Style.BRIGHT + f"\n-> <<P{id}>> <-\n" + Style.RESET_ALL)
    time.sleep(60)
    # Envia uma mensagem para o cordenador se não responder ele está morto e precisa iniciar uma eleição
    # !!! Pergunta: Ele tem que enviar a mensagem para o cordenador mesmo? Ele não consegue saber pelo process_up?
    
    #for pid, (host, port) in process.items():
    #    if pid != id:
    #        pkt = message(tipe=0, src_process=id, dst_process=pid)
    #        sock.sendto(bytes(pkt), (host, port))

def tr_send_heartbeat(id, process_up):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    for pid in process_up:
        if pid != id:
            host, port = process[pid]
            pkt = heartbeat(tipe=0, src_process=id, dst_process=pid)
            sock.sendto(bytes(pkt), (host, port))
                
    time.sleep(5)
           
    while True:
        print(Style.BRIGHT + "### Status dos processos ###" + Style.RESET_ALL)
        for pid in process_up:
            if process_up[pid]:
                print(Fore.GREEN + Style.BRIGHT + f"<<P{pid}>> está vivo" + Style.RESET_ALL)
            else:
                print(Fore.RED + Style.BRIGHT + f"<<P{pid}>> está morto" + Style.RESET_ALL)
        print(Style.BRIGHT + "############################\n" + Style.RESET_ALL)      
        
        time.sleep(5)
        
        for pid in process_up:
            if pid != id and process_up[pid]:
                host, port = process[pid]
                pkt = heartbeat(tipe=0, src_process=id, dst_process=pid)
                sock.sendto(bytes(pkt), (host, port))

if __name__ == "__main__":
    id = int(sys.argv[1])
    host, port = process[id]

    process_up = {pid: False for pid in range(1, num_process + 1) if pid != id}          
    
    print(f"Processo: <<P{id}>> rodando em {host}:{port}")
    
    # uma thread para tratar o recebimento dos pacotes
    threading.Thread(target=tr_receive_msg, args=(id, port, process_up), daemon=True).start()
    
    # uma thread para tratar o envio dos heartbeats
    threading.Thread(target=tr_send_heartbeat, args=(id, process_up), daemon=True).start()

    # outra thread para tratar o envio dos pacotes
    tr_send_msg(id, process_up)
