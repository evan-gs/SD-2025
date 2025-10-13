# Projeto feito por 
 - Gabriel Evangelista Gonçalves da Silva - RA 802791
 - Gabriel Andrade - RA 815407

### Eleição de Líder em Redes sem Fio

### Pré-requisitos
Python 3.11.x

Scapy (pip install scapy)
Colorama (pip install colorama)

### Como Executar
Execução Básica (11 processos)

Abra 1- terminais e execute em cada um:

```bash
# Terminal 1
python3 wireless_leader.py 1

# Terminal 2
python3 wireless_leader.py 2

# Terminal 3
python3 wireless_leader.py 3

# Terminal 4
python3 wireless_leader.py 4

# Terminal 5
python3 wireless_leader.py 5

# Terminal 6
python3 wireless_leader.py 6

# Terminal 7
python3 wireless_leader.py 7

# Terminal 8
python3 wireless_leader.py 8

# Terminal 9
python3 wireless_leader.py 9

# Terminal 10
python3 wireless_leader.py 10

# Terminal 11
python3 graph_manager

```
### Versão de execução com delay

```bash
# 
python3 wireless_leader.py -d <delay> <1-10>

exemplo -> python3 wireless_leader.py -d 3 1

```
Assim o processo 1 enviará mensagens para os seus vizinhos após 3 segundos nas eleições

Insira as conexões entre cada nó pelo terminal do graph manager, primeiro descrevendo a capacidade de cada nó e depois suas conexões como x y em cada linha, e digite q para encerrar a descrição do grafo
Exemplo abaixo descreve o grafo presente nos slides:
```bash
4 6 3 2 1 4 2 8 5 4
1 2
1 10
2 3
2 7
3 4
3 5
4 5
4 6
5 6
5 7
6 9
7 8
7 10
8 9

```
