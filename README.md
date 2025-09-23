# Projeto feito por 
 - Gabriel Evangelista Gonçalves da Silva - RA 802791
 - Gabriel Andrade - RA 815407

### Multicast Totalmente Ordenado
Sistema de exclusão mútua entre múltiplos processos para utilização de recursos.

### Pré-requisitos
Python 3.11.x

Scapy (pip install scapy)

### Como Executar
Execução Básica (4 processos)

Abra 4 terminais e execute em cada um:

```bash
# Terminal 1
python3 exclusao_mutua.py 1

# Terminal 2
python3 exclusao_mutua.py 2

# Terminal 3
python3 exclusao_mutua.py 3

# Terminal 4
python3 exclusao_mutua.py 4
```

Os recursos serão liberados conforme o clock de cada processo, no código atual a ordem para os processos serias:
- Recurso 1: P1, P3, P2, P4, P1, P3 
- Recurso 2: P2, P4, P1, P3, P2, P4 