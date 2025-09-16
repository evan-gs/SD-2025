# Projeto feito por 
 - Gabriel Evangelista Gonçalves da Silva - RA 802791
 - Gabriel Andrade - RA 815407

### Multicast Totalmente Ordenado
Sistema de multicast com ordenação total entre múltiplos processos.

### Pré-requisitos
Python 3.11.x

Scapy (pip install scapy)

### Como Executar
Execução Básica (4 processos)

Abra 4 terminais e execute em cada um:

```bash
# Terminal 1
python3 processos_multicast.py 1

# Terminal 2
python3 processos_multicast.py 2

# Terminal 3
python3 processos_multicast.py 3

# Terminal 4
python3 processos_multicast.py 4
```

### Execução com Latência

```bash
# Processo 1 com latência de 0.5 segundos
python3 processos_multicast.py 1 0.5

# Processo 2 com latência de 1 segundo
python3 processos_multicast.py 2 1
```

### Uso
Digite mensagens em qualquer processo e pressione Enter.
