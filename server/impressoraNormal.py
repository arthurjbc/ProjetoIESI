#ATENÇÃO é preciso criar um venv, depois instale: pip install pywin32


import win32print
import win32api
import os
import time
# escolher qual impressora a gente vai querer usar
lista_impressoras = win32print.EnumPrinters(4)
impressora = lista_impressoras[0]

win32print.SetDefaultPrinter(impressora[2])
caminho = r"D:\caminho\pasta" #alterar
lista_arquivos = os.listdir(caminho)

# mandar imprimir todos os arquivos de uma pasta
for arquivo in lista_arquivos:
    win32api.ShellExecute(0, "print", arquivo, None, caminho, 0)
    time.sleep(5)