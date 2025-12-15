import win32print

# Flag 6 = Procura Local (2) + Conexões de Rede (4)
# Isso garante que ele ache tudo que está mapeado no seu PC
flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS

lista_impressoras = win32print.EnumPrinters(flags)

print(f"Encontrei {len(lista_impressoras)} impressoras.")

for i, impressora in enumerate(lista_impressoras):
    # O item [2] é o nome da impressora
    print(f"Índice {i}: {impressora[2]}")