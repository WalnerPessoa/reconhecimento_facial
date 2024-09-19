import gpiod
import time

# Inicializar o chip de GPIO
chip = gpiod.Chip('gpiochip0')

# Acessar a linha da GPIO 21
line = chip.get_line(21)

# Configurar a linha como saída
# No lugar de `line_request()`, usamos o método correto `request`
line.request(consumer="my_gpio", type=gpiod.LINE_REQ_DIR_OUT)

# Ligar a GPIO (nível alto)
line.set_value(1)
print("GPIO 21 ligado")
time.sleep(5)

# Desligar a GPIO (nível baixo)
line.set_value(0)
print("GPIO 21 desligado")

# Liberar a linha da GPIO
line.release()
