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
        ByteEnumField("tipe", 0, {0:"ELECTION", 1:"OK", 2:"ALLHAIL"}),
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

def deal_with_msg(msg, id, process_up, sock, received_heartbeat_ok, received_election_ok, leader, election_happening):   
    if isinstance(msg, heartbeat):
        if msg.tipe == 0: 
            #avisa que é o leader se o processo tava morto
            if leader[0] == id and not process_up[msg.src_process]:
                pkt = message(tipe=2, src_process=id, dst_process=msg.src_process)  
                sock.sendto(bytes(pkt), process[msg.src_process])
            else:
                pkt = heartbeat(tipe=1, src_process=id, dst_process=msg.src_process)  
                sock.sendto(bytes(pkt), process[msg.src_process])
            process_up[msg.src_process] = True
            received_heartbeat_ok[msg.src_process] = True
        elif msg.tipe == 1: 
            process_up[msg.src_process] = True
            received_heartbeat_ok[msg.src_process] = True

    elif isinstance(msg, message):
        if msg.tipe == 0:
            election_happening = True
            #primeiro manda o ack pra acabar a participação do processo q iniciou a eleição
            pkt = message(tipe=1, src_process=id, dst_process=msg.src_process)
            sock.sendto(bytes(pkt), process[msg.src_process])

            #repete o processo de eleição, primeiro enviando mensagem para candidatos apropriados
            for pid in process_up:
                if pid < id and process_up[pid]:
                    host, port = process[pid]
                    pkt = message(tipe=0, src_process=id, dst_process=pid)
                    sock.sendto(bytes(pkt), (host, port))

            #pra ver se ele recebeu resposta
            was_bullied = False
            for i in range(10):
                if was_bullied:
                    break
                for pid in received_election_ok:
                    if pid < id and received_election_ok[pid] and process_up[pid]:
                        was_bullied = True
                        break
                time.sleep(0.1)

            #caso nenhum menor tenha respondido, ele vira o lider e avisa todo mundo viv
            if not was_bullied:
                leader[0] = id
                for pid in process_up:
                    if process_up[pid]:
                        host, port = process[pid]
                        pkt = message(tipe=2, src_process=id, dst_process=pid)
                        sock.sendto(bytes(pkt), process[msg.src_process])
                print(Fore.BLUE + Style.BRIGHT + f"\n-> <<EU, P{leader[0]}, sou o líder supremo>> <-\n" + Style.RESET_ALL)
                election_happening = False

            #reseta a variavel para futuras eleicoes
            for pid in received_election_ok:
                received_election_ok[pid] = False

            
        elif msg.tipe == 1:
            #só regristra o ack pra usar no processo de eleição
            received_heartbeat_ok[msg.src_process] = True
            received_election_ok[msg.src_process] = True

        elif msg.tipe == 2:
            #só salva o novo lider
            leader[0] = msg.src_process
            process_up[msg.src_process] = True
            received_heartbeat_ok[msg.src_process] = True
            print(Fore.BLUE + Style.BRIGHT + f"\n-> <<P{leader[0]} é o líder supremo>> <-\n" + Style.RESET_ALL)
            election_happening = False
    

def tr_receive_msg(id, port, process_up, received_heartbeat_ok, received_election_ok, leader, election_happening):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    while True:
        data, addr = sock.recvfrom(4096)
        ptype = data[0]
        if ptype == 0:   # pacote Message
            pkt = message(data)
        else:            # pacote Heartbeat
            pkt = heartbeat(data)
        deal_with_msg(pkt, id, process_up, sock, received_heartbeat_ok, received_election_ok, leader, election_happening)

def tr_send_msg(id, process_up, leader, election_happening):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(Fore.YELLOW + Style.BRIGHT + f"\n-> <<P{id}>> <-\n" + Style.RESET_ALL)
    time.sleep(6)
    # Envia uma mensagem para o cordenador se não responder ele está morto e precisa iniciar uma eleição
    # !!! Pergunta: Ele tem que enviar a mensagem para o cordenador mesmo? Ele não consegue saber pelo process_up?
    # Resposta: Acho que saber pelo process up é meio "cheat?" ele só deveria reiniciar a eleição quando é reanimado
    
    #se o processo reanimou, ele volta a pedir eleição
    if not election_happening:
        print(Fore.BLUE + Style.BRIGHT + f"\n-> <<DIRETAS JÁ>> <-\n" + Style.RESET_ALL)
        is_lowest = True
        for pid in process_up:
            if pid < id and process_up[pid]:
                host, port = process[pid]
                pkt = message(tipe=0, src_process=id, dst_process=pid)
                sock.sendto(bytes(pkt), (host, port))
                is_lowest = False

        if is_lowest:
            for pid in process_up:
                host, port = process[pid]
                pkt = message(tipe=2, src_process=id, dst_process=pid)
                sock.sendto(bytes(pkt), (host, port))
            leader[0] = id
            print(Fore.BLUE + Style.BRIGHT + f"\n-> <<EU, P{leader[0]}, sou o líder supremo>> <-\n" + Style.RESET_ALL)
            election_happening = False
    
    #se o lider desapareceu pra ele, ele volta a pedir eleição
    while True:
        if leader[0] == 0 and not election_happening:
            print(Fore.BLUE + Style.BRIGHT + f"\n-> <<DIRETAS JÁ>> <-\n" + Style.RESET_ALL)
            is_lowest = True
            for pid in process_up:
                if pid < id and process_up[pid]:
                    host, port = process[pid]
                    pkt = message(tipe=0, src_process=id, dst_process=pid)
                    sock.sendto(bytes(pkt), (host, port))
                    is_lowest = False

            if is_lowest:
                for pid in process_up:
                    host, port = process[pid]
                    pkt = message(tipe=2, src_process=id, dst_process=pid)
                    sock.sendto(bytes(pkt), (host, port))
                leader[0] = id
                print(Fore.BLUE + Style.BRIGHT + f"\n-> <<EU, P{leader[0]}, sou o líder supremo>> <-\n" + Style.RESET_ALL)
        time.sleep(5)

def tr_send_heartbeat(id, process_up, received_heartbeat_ok, leader, election_happening):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    for pid in process_up:
        if pid != id:
            host, port = process[pid]
            pkt = heartbeat(tipe=0, src_process=id, dst_process=pid)
            sock.sendto(bytes(pkt), (host, port))

    time.sleep(5)
           
    while True:
        #print(leader[0])
        for pid in received_heartbeat_ok:
            if not received_heartbeat_ok[pid]:
                process_up[pid] = False
                if pid == leader[0]:
                    #print(Fore.BLUE + Style.BRIGHT + f"\n-> <<O LIDER MORREU!!!!!!!>> <-\n" + Style.RESET_ALL)
                    leader[0] = 0
            received_heartbeat_ok[pid] = False
            
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
    received_heartbeat_ok = {pid: False for pid in range(1, num_process + 1) if pid != id}
    received_election_ok = {pid: False for pid in range(1, num_process + 1) if pid != id}
    leader = [0] #todo processo deve saber quem é o lider, variavel = 0 quando n sabe 
    leader[0] = 0
    election_happening = False
    
    print(f"Processo: <<P{id}>> rodando em {host}:{port}")
    
    # uma thread para tratar o recebimento dos pacotes
    threading.Thread(target=tr_receive_msg, args=(id, port, process_up, received_heartbeat_ok, received_election_ok, leader, election_happening), daemon=True).start()
    
    # uma thread para tratar o envio dos heartbeats
    threading.Thread(target=tr_send_heartbeat, args=(id, process_up, received_heartbeat_ok, leader, election_happening), daemon=True).start()

    # outra thread para tratar o envio dos pacotes
    tr_send_msg(id, process_up, leader, election_happening)
