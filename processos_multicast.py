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
        ByteEnumField("tipe", 0, {0:"MSG", 1:"ACK", 2:"START"}),
        IntField("message_id", 0),
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

ready = False
num_process = len(process)

def deal_with_msg(msg, id, clock, msg_queue, ack_queue, last_message_id, sock):
    #print(f"-> Pacote recebido do <<P{msg.src_process}>>")
    #print(f"\n->tipo:{msg.tipe}\n->id:{msg.message_id}\n->src_process:{msg.src_process}\n->dst_process:{msg.dst_process}\n->clock:{clock[0]}\n->timestamp:{msg.timestamp}\n->ack_timestamp:{msg.ack_timestamp}")
    
    last_message_id[0] = max(last_message_id[0], msg.message_id)
    clock[0] = max(clock[0], msg.timestamp) + 1
    
    if msg.tipe == 0 and msg.dst_process == id:
        #print(f"\n-> clock do recebimento da mensagem {msg.message_id}: {clock[0]}")
        key = (msg.message_id, msg.dst_process)
        pending_ack = ack_queue.pop(key, set())
        pending_ack.add(id)
        #print(f"key:{key}")
        #print(f"pending_ack:{pending_ack}")
        
        updated = False
        for i, (timestamp, message_id, src, dst, text, acks) in enumerate(msg_queue):
            if (message_id, dst) == key:
                acks.update(pending_ack) 
                msg_queue[i] = (timestamp, message_id, msg.src_process, dst, msg.text, acks)
                updated = True
                break

        if not updated:
            msg_queue.append((clock[0], msg.message_id, msg.src_process, msg.dst_process, msg.text, pending_ack))
        
        msg_queue.sort(key=lambda x: (x[0], x[1]))
        
        for pid, (host, port) in process.items():
            if pid == id:
                #print(f"\n-> clock do recebimento do ack de <<P{id}>> da mensagem {msg.message_id}: {clock[0]}")
                continue
            ack = message(tipe=1, message_id=msg.message_id, timestamp=clock[0], src_process=id, dst_process=pid, ack_timestamp=msg.timestamp)
            sock.sendto(bytes(ack), (host, port))
            
    elif msg.tipe == 1 and msg.dst_process == id:
        #print(f"\n-> clock do recebimento do ack de <<P{msg.src_process}>> da mensagem {msg.message_id}: {clock[0]}")
        key = (msg.message_id, msg.dst_process)
        #print(f"\n->chave do ack: {key}\n")
        
        found_message = False
        if len(msg_queue) > 0:
            for i, (timestamp, message_id, src, dst, text, acks) in enumerate(msg_queue):
                #print(f"-> chave do for: {(last_message_id[0], dst)}")
                if (message_id, dst) == key:
                    acks.add(msg.src_process)  
                    msg_queue[i] = (timestamp, message_id, src, dst, text, acks)
                    found_message = True
                    #print(f"->src:{msg.src_process}\n->current_msq_queue:{msg_queue[i]}")
                    break
                
        if not found_message:
            ack_queue.setdefault(key, set()).add(msg.src_process)
            
            placeholder_exist = False
            for _, message_id, _, dst, _, _ in msg_queue:
                if (message_id, dst) == key:
                    placeholder_exist = True
                    break

            if not placeholder_exist:
                current_acks = ack_queue[key]
                msg_queue.append((clock[0], msg.message_id, None, id, None, current_acks))
                msg_queue.sort(key=lambda x: (x[0], x[1]))
    
    elif msg.tipe == 2 and msg.dst_process == id:
        global ready
        ready += True
        print("Comecando...")
        print("")
        print("")
            
    while len(msg_queue) > 0:
        print("")
        print(f"-> Fila atual em <<P{id}>>: {[ (timestamp, message_id, src, dst, text, list(acks)) for timestamp, message_id, src, dst, text, acks in msg_queue ]}")
        timestamp, message_id, src, dst, text, acks = msg_queue[0]
        if len(acks) == num_process:  
            print(f"\n!!! Mensagem {message_id} entrege em <<P{id}>>: \"{text}\" de <<P{src}>>")
            msg_queue.pop(0)
        else:
            break        

def tr_receive_msg(id, port, clock, msg_queue, ack_queue, last_message_id):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    while True:
        data, addr = sock.recvfrom(4096)
        pkt = message(data)
        deal_with_msg(pkt, id, clock, msg_queue, ack_queue, last_message_id, sock)


def tr_send_msg(id, clock, latency, last_message_id):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    if id != 4:
        while not ready:
            time.sleep(0.1)
    else:
        input("")
        for pid, (host, port) in process.items():
            pkt = message(tipe=2, message_id=[0], timestamp=clock[0], src_process=id, dst_process=pid, text="begin")
            sock.sendto(bytes(pkt), (host, port))
        time.sleep(0.1)
    
    #print("saimo IRRAAAA")
    #print("")

    while clock[0] < 100:
        sent_counter[0] += 1
        text = f"Msg {sent_counter} do P {id}"
        clock[0] += 1
        last_message_id[0] += 1
        message_id = last_message_id[0]
        #print(f"-> clock do envio da mensagem {message_id}: {clock[0]}")
        for pid, (host, port) in process.items():
            pkt = message(tipe=0, message_id=message_id, timestamp=clock[0], src_process=id, dst_process=pid, text=text)
            sock.sendto(bytes(pkt), (host, port))
            time.sleep(latency)
            
        
        
if __name__ == "__main__":
    id = int(sys.argv[1])
    host, port = process[id]

    clock = [0] 
    last_message_id = [0] 
    sent_counter = [0] 
    msg_queue = []
    ack_queue = {}
    
    if len(sys.argv) > 2:
        latency = float(sys.argv[2])
    else:
        latency = 0.0
    
    print(f"Processo: <<P{id}>> rodando em {host}:{port}")
    
    # uma thread para tratar o recebimento dos pacotes
    th = threading.Thread(target=tr_receive_msg, args=(id, port, clock, msg_queue, ack_queue, last_message_id), daemon=True)
    th.start()
    
    # outra thread para tratar o envio dos pacotes
    tr_send_msg(id, clock, latency, last_message_id)