import gpiod
import sys
import time

# Verifica se o número da GPIO foi passado como argumento
if len(sys.argv) != 2:
    print("Número de GPIO não fornecido.")
    sys.exit(1)

# Obtém o número da GPIO passado pelo rec_facial_back.py
item = int(sys.argv[1])

# Inicializa o chip de GPIO
chip = gpiod.Chip('gpiochip0')
line = chip.get_line(item)

# Configura a linha da GPIO como saída
line.request(consumer="my_gpio", type=gpiod.LINE_REQ_DIR_OUT)

# Ativa a GPIO (nível alto)
line.set_value(1)
print(f"GPIO {item} ligada.")
time.sleep(2)  # Mantém a GPIO ligada por 5 segundos

# Desativa a GPIO (nível baixo)
line.set_value(0)
print(f"GPIO {item} desligada.")

# Libera a linha da GPIO
line.release()
