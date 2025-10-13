#Projeto feito por Gabriel Santos de Andrade - RA 815407
# Gabriel Evangelista Gonçalves da Silva - RA 802791

#!/usr/bin/env python3

from scapy.all import Packet, ByteEnumField, IntField, StrField
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

# Classe de protocolo personalizada para envio de eleição e confirmação de resultado
class message(Packet):
    name = "Message"
    fields_desc = [
        ByteEnumField("ptype", 1, {1:"ELECTION"}),
        ByteEnumField("tipe", 0, {0:"ELECTION", 1:"OK", 2:"ALLHAIL", 3:"IGNORED"}),
        IntField("src_process", 0),
        IntField("dst_process", 0),
        IntField("lowest_process", 0),
        IntField("highest_capacity", 0),
        IntField("election_initiator", 0)
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

class ElectionState:
    def __init__(self):
        self.current_election = None  # {initiator, lowest_process, highest_capacity, pending_replies, received_from}
        self.leader = 0
        self.connections = []
        self.capacity = 0
        self.id = 0
        self.delay_time = 0  
        
def handle_election_message(msg, id, sock, election_state):
    initiator = msg.election_initiator
    current_lowest_process = msg.lowest_process
    current_highest_capacity = msg.highest_capacity
    sender = msg.src_process

    print(Fore.GREEN + f"P{id}: Recebeu ELEIÇÃO de P{sender} (Iniciador: P{initiator})" + Style.RESET_ALL)

    if election_state.current_election is not None:
        current_initiator = election_state.current_election['initiator']
        
        # Se é a mesma eleição (mesmo initiator) - IGNORA (loop na topologia)
        if current_initiator == initiator:
            print(Fore.RED + f"P{id}: IGNORADO - Já participando da MESMA eleição de P{initiator}" + Style.RESET_ALL)
            send_ignored_message(id, sock, sender, initiator)
            return
        
        # Se a nova eleição tem initiator MENOR que a atual - SUBSTITUI
        elif initiator < current_initiator:
            print(Fore.YELLOW + f"P{id}: Substituindo eleição anterior (P{current_initiator}) por nova (P{initiator}) - initiator menor" + Style.RESET_ALL)
        
        # Se a nova eleição tem initiator MAIOR que a atual - IGNORA
        else:
            print(Fore.RED + f"P{id}: IGNORADO - Já participando de eleição de P{current_initiator} (initiator menor)" + Style.RESET_ALL)
            send_ignored_message(id, sock, sender, initiator)
            return

    # Verifica se este nó tem capacidade maior que a atual
    if election_state.capacity > current_highest_capacity:
        current_lowest_process = id
        current_highest_capacity = election_state.capacity
        print(Fore.CYAN + f"P{id}: Atualizando maior nó para P{id} (Capacidade: {election_state.capacity} > {msg.highest_capacity})" + Style.RESET_ALL)
    # Em caso de empate na capacidade, usa o ID menor como critério de desempate
    elif election_state.capacity == current_highest_capacity and id < current_lowest_process:
        current_lowest_process = id
        current_highest_capacity = election_state.capacity
        print(Fore.CYAN + f"P{id}: Atualizando maior nó para P{id} (Empate de capacidade, ID menor)" + Style.RESET_ALL)

    # Define/atualiza a nova eleição atual
    election_state.current_election = {
        'initiator': initiator,
        'lowest_process': current_lowest_process,
        'highest_capacity': current_highest_capacity,
        'pending_replies': set(election_state.connections) - {sender},
        'received_from': sender
    }

    print(Fore.BLUE + f"P{id}: Vizinhos para contactar: {election_state.current_election['pending_replies']}" + Style.RESET_ALL)

    # Se não há vizinhos para enviar, responde imediatamente com OK
    if not election_state.current_election['pending_replies']:
        print(Fore.MAGENTA + f"P{id}: Sem vizinhos para enviar - Respondendo OK para P{sender}" + Style.RESET_ALL)
        send_ok_message(id, sock, election_state, election_state.current_election['received_from'])
        election_state.current_election = None
    else:
        if election_state.delay_time > 0:
            print(Fore.YELLOW + f"P{id}: Aguardando {election_state.delay_time} segundos antes de propagar eleição..." + Style.RESET_ALL)
            
            # Cria uma thread para enviar as mensagens após o delay
            def delayed_propagation():
                time.sleep(election_state.delay_time)
                if (election_state.current_election is not None and 
                    election_state.current_election['initiator'] == initiator):
                    print(Fore.YELLOW + f"P{id}: Propagando eleição após delay de {election_state.delay_time}s" + Style.RESET_ALL)
                    for neighbor in election_state.current_election['pending_replies']:
                        send_election_message(id, sock, neighbor, initiator, current_lowest_process, current_highest_capacity)
            
            threading.Thread(target=delayed_propagation, daemon=True).start()
        else:
            for neighbor in election_state.current_election['pending_replies']:
                send_election_message(id, sock, neighbor, initiator, current_lowest_process, current_highest_capacity)

def handle_ok_message(msg, id, sock, election_state):
    initiator = msg.election_initiator
    sender = msg.src_process

    # Se não estamos participando de uma eleição ou a eleição não é a mesma, ignora
    if election_state.current_election is None or election_state.current_election['initiator'] != initiator:
        print(Fore.RED + f"P{id}: OK de P{sender} ignorado - Não participando desta eleição" + Style.RESET_ALL)
        return

    print(Fore.BLUE + f"P{id}: Recebeu OK de P{sender} para eleição de P{initiator}" + Style.RESET_ALL)
    print(Fore.CYAN + f"P{id}: Maior nó recebido: P{msg.lowest_process} (Capacidade: {msg.highest_capacity})" + Style.RESET_ALL)

    if msg.highest_capacity > election_state.current_election['highest_capacity']:
        election_state.current_election['lowest_process'] = msg.lowest_process
        election_state.current_election['highest_capacity'] = msg.highest_capacity
        print(Fore.GREEN + f"P{id}: Atualizando maior nó global para P{msg.lowest_process} (Capacidade maior: {msg.highest_capacity})" + Style.RESET_ALL)
    
    elif (msg.highest_capacity == election_state.current_election['highest_capacity'] and 
          msg.lowest_process < election_state.current_election['lowest_process']):
        election_state.current_election['lowest_process'] = msg.lowest_process
        election_state.current_election['highest_capacity'] = msg.highest_capacity
        print(Fore.GREEN + f"P{id}: Atualizando maior nó global para P{msg.lowest_process} (Mesma capacidade, ID menor)" + Style.RESET_ALL)

    # Remove o vizinho da lista de pendentes
    election_state.current_election['pending_replies'].discard(sender)

    print(Fore.YELLOW + f"P{id}: Respostas pendentes: {election_state.current_election['pending_replies']}" + Style.RESET_ALL)

    # Se recebeu todas as respostas
    if not election_state.current_election['pending_replies']:
        if initiator == id:  # Iniciador da eleição
            # Eleição concluída
            election_state.leader = election_state.current_election['lowest_process']
            print(Fore.MAGENTA + Style.BRIGHT + 
                  f"P{id}: ELEIÇÃO CONCLUÍDA! Líder é P{election_state.leader} (Capacidade: {election_state.current_election['highest_capacity']})" + 
                  Style.RESET_ALL)
            
            # Anuncia o líder para todos os vizinhos
            for neighbor in election_state.connections:
                send_allhail_message(id, sock, neighbor, election_state.leader)
            
            election_state.current_election = None
        else:
            # Encaminha OK para quem enviou a eleição
            print(Fore.CYAN + f"P{id}: Encaminhando OK para P{election_state.current_election['received_from']} com P{election_state.current_election['lowest_process']}" + Style.RESET_ALL)
            send_ok_message(id, sock, election_state, election_state.current_election['received_from'])
            election_state.current_election = None

def handle_ignored_message(msg, id, sock, election_state):
    initiator = msg.election_initiator
    sender = msg.src_process

    print(Fore.RED + f"P{id}: Recebeu IGNORED de P{sender} para eleição de P{initiator}" + Style.RESET_ALL)

    # Se não participa desta eleição - IGNORA
    if election_state.current_election is None or election_state.current_election['initiator'] != initiator:
        return

    # Remove o vizinho da lista de pendentes
    election_state.current_election['pending_replies'].discard(sender)

    print(Fore.YELLOW + f"P{id}: Respostas pendentes após IGNORED: {election_state.current_election['pending_replies']}" + Style.RESET_ALL)

    # Se recebeu todas as respostas
    if not election_state.current_election['pending_replies']:
        if initiator == id:  # Sou o iniciador da eleição
            # Eleição concluída
            election_state.leader = election_state.current_election['lowest_process']
            print(Fore.MAGENTA + Style.BRIGHT + 
                  f"P{id}: ELEIÇÃO CONCLUÍDA! Líder é P{election_state.leader} (Capacidade: {election_state.current_election['highest_capacity']})" + 
                  Style.RESET_ALL)
            
            # Anuncia o líder para todos os vizinhos
            for neighbor in election_state.connections:
                send_allhail_message(id, sock, neighbor, election_state.leader)
            
            election_state.current_election = None
        else:
            # Encaminha OK para quem enviou a eleição
            print(Fore.CYAN + f"P{id}: Encaminhando OK para P{election_state.current_election['received_from']} com P{election_state.current_election['lowest_process']}" + Style.RESET_ALL)
            send_ok_message(id, sock, election_state, election_state.current_election['received_from'])
            election_state.current_election = None

def handle_allhail_message(msg, id, sock, election_state):
    leader = msg.lowest_process
    sender = msg.src_process
    
    if election_state.leader == leader:
        return
    
    # Atualiza o líder e anuncia apenas uma vez
    election_state.leader = leader
    print(Fore.RED + Style.BRIGHT + 
          f"P{id}: LÍDER ANUNCIADO! P{leader} é o novo líder" + 
          Style.RESET_ALL)

    for neighbor in election_state.connections:
        if neighbor != sender:  # Evita enviar de volta para quem enviou primeiro
            send_allhail_message(id, sock, neighbor, leader)
            print(Fore.MAGENTA + f"P{id}: Propagando ALLHAIL para P{neighbor}" + Style.RESET_ALL)

def send_election_message(id, sock, dst, initiator, lowest_process, highest_capacity):
    host, port = process[dst]
    pkt = message(tipe=0, src_process=id, dst_process=dst, 
                 lowest_process=lowest_process, highest_capacity=highest_capacity,
                 election_initiator=initiator)
    sock.sendto(bytes(pkt), (host, port))
    print(Fore.YELLOW + f"P{id}: Enviando ELEIÇÃO para P{dst}" + Style.RESET_ALL)

def send_ok_message(id, sock, election_state, dst):
    host, port = process[dst]
    pkt = message(tipe=1, src_process=id, dst_process=dst,
                 lowest_process=election_state.current_election['lowest_process'],
                 highest_capacity=election_state.current_election['highest_capacity'],
                 election_initiator=election_state.current_election['initiator'])
    sock.sendto(bytes(pkt), (host, port))
    print(Fore.CYAN + f"P{id}: Enviando OK para P{dst} com P{election_state.current_election['lowest_process']}" + Style.RESET_ALL)

def send_ignored_message(id, sock, dst, initiator):
    host, port = process[dst]
    pkt = message(tipe=3, src_process=id, dst_process=dst,
                 lowest_process=0, highest_capacity=0,
                 election_initiator=initiator)
    sock.sendto(bytes(pkt), (host, port))
    print(Fore.RED + f"P{id}: Enviando IGNORED para P{dst}" + Style.RESET_ALL)

def send_allhail_message(id, sock, dst, leader):
    host, port = process[dst]
    pkt = message(tipe=2, src_process=id, dst_process=dst,
                 lowest_process=leader, highest_capacity=0,
                 election_initiator=0)
    sock.sendto(bytes(pkt), (host, port))

def deal_with_msg(msg, id, sock, election_state):
    if isinstance(msg, graph):
        if msg.tipe == 0: 
            # recebe nova topologia, mas apenas as informações que ele deve ter acesso (nós adjacentes e sua capacidade)
            print(Fore.YELLOW + Style.BRIGHT + f"\n-> P{id}: NOVO GRAFO RECEBIDO <-" + Style.RESET_ALL)
            election_state.connections.clear()  # reseta toda vez antes de salvar nova topologia
            str_connections = msg.connections.split()
            for node in str_connections:
                election_state.connections.append(int(node))
            election_state.connections = sorted(set(election_state.connections))  # ordena e retira duplicatas, evitando input ruim no graphmanager.py
            election_state.capacity = msg.capacity
            print(Fore.CYAN + f"P{id}: Conexões: {election_state.connections}, Capacidade: {election_state.capacity}" + Style.RESET_ALL)

            # !!!MAIS IMPORTANTE!!!
            # string de conexões é tratada aqui pra ser salva na lista connections de inteiros ordenados.
            # !!!MAIS IMPORTANTE!!!
            
    elif isinstance(msg, message):
        if msg.tipe == 0:  # ELECTION message
            handle_election_message(msg, id, sock, election_state)
        elif msg.tipe == 1:  # OK message
            handle_ok_message(msg, id, sock, election_state)
        elif msg.tipe == 2:  # ALLHAIL message
            handle_allhail_message(msg, id, sock, election_state)
        elif msg.tipe == 3:  # IGNORED message
            handle_ignored_message(msg, id, sock, election_state)

def tr_receive_msg(id, port, election_state):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    while True:
        try:
            data, addr = sock.recvfrom(4096)
            ptype = data[0]
            if ptype == 0:   # pacote graph
                pkt = graph(data)
            else:            # pacote message
                pkt = message(data)
            deal_with_msg(pkt, id, sock, election_state)
        except ConnectionResetError:
            continue
        except Exception as e:
            print(f"Erro: {e}")

def tr_send_msg(id, election_state):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    while True:
        print(Fore.RED + Style.BRIGHT + f"\nP{id}: ENTER para iniciar eleição | Capacidade: {election_state.capacity}" + Style.RESET_ALL)
        input("")
        
        # Inicia nova eleição
        if election_state.current_election is not None:
            print(Fore.YELLOW + f"P{id}: Já existe uma eleição em andamento" + Style.RESET_ALL)
            continue
            
        print(Fore.MAGENTA + Style.BRIGHT + f"P{id}: INICIANDO ELEIÇÃO!" + Style.RESET_ALL)
        
        # Inicia estado para esta eleição
        election_state.current_election = {
            'initiator': id,
            'lowest_process': id,
            'highest_capacity': election_state.capacity,
            'pending_replies': set(election_state.connections),
            'received_from': None
        }
        
        print(Fore.BLUE + f"P{id}: Vizinhos para contactar: {election_state.current_election['pending_replies']}" + Style.RESET_ALL)
        
        # Se não há vizinhos - eu sou o líder (ditador)
        if not election_state.connections:
            election_state.leader = id
            print(Fore.MAGENTA + Style.BRIGHT + f"P{id}: ELEIÇÃO CONCLUÍDA! Sou o único nó - Líder é P{id}" + Style.RESET_ALL)
            election_state.current_election = None
            continue
            
        # Envia mensagem de eleição para todos os vizinhos
        for neighbor in election_state.connections:
            send_election_message(id, sock, neighbor, id, id, election_state.capacity)

if __name__ == "__main__":
    # Processa argumentos
    delay_time = 0
    
    # Verifica se há argumento de delay
    if "-d" in sys.argv:
        try:
            delay_idx = sys.argv.index("-d")
            delay_time = float(sys.argv[delay_idx + 1])
            # Remove o argumento -d e seu valor
            sys.argv.pop(delay_idx)
            sys.argv.pop(delay_idx)
        except (ValueError, IndexError):
            print(Fore.RED + "Erro: Argumento -d deve ser seguido por um número (segundos)" + Style.RESET_ALL)
            sys.exit(1)
    
    id = int(sys.argv[1])
    host, port = process[id]
    
    election_state = ElectionState()
    election_state.id = id
    election_state.delay_time = delay_time  # Novo campo para armazenar o delay
    
    print(f"Processo: P{id} rodando em {host}:{port}")
    
    # Informa sobre o modo de delay
    if delay_time > 0:
        print(Fore.YELLOW + f"MODO DELAY: Propagação com delay de {delay_time} segundos" + Style.RESET_ALL)
    else:
        print(Fore.GREEN + "MODO NORMAL: Propagação imediata" + Style.RESET_ALL)
    
    # Thread para receber mensagens
    threading.Thread(target=tr_receive_msg, args=(id, port, election_state), daemon=True).start()
    
    # Thread principal para enviar mensagens
    tr_send_msg(id, election_state)