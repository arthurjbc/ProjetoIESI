import win32print
import os

# --- CONFIGURAÇÃO ---
# Nome da impressora ZEBRA ou de etiquetas (Use o nome exato)
nome_impressora = r"\\printers.cin.ufpe.br\NomeDaZebra"  #nome compartilhado da impressora Zebra na rede ALTERAR
pasta_arquivos = r"D:\caminho\pasta"  #alterar
# --------------------

def enviar_zpl_para_impressora(nome_imp, arquivo_path):
    try:
        # 1. Abre a conexão com a impressora
        hPrinter = win32print.OpenPrinter(nome_imp)
        
        # 2. Lê o arquivo ZPL como binário (bytes)
        with open(arquivo_path, "rb") as f:
            dados_zpl = f.read()

        # 3. Inicia o trabalho de impressão em modo RAW
        try:
            hJob = win32print.StartDocPrinter(hPrinter, 1, ("Imprimindo Etiqueta ZPL", None, "RAW"))
            win32print.StartPagePrinter(hPrinter)
            
            # 4. Envia os bytes diretos
            win32print.WritePrinter(hPrinter, dados_zpl)
            
            win32print.EndPagePrinter(hPrinter)
            win32print.EndDocPrinter(hPrinter)
            print(f"Sucesso: {arquivo_path} enviado.")
            
        finally:
            # Garante que fecha a conexão mesmo se der erro
            win32print.ClosePrinter(hPrinter)

    except Exception as e:
        print(f"Erro ao imprimir {arquivo_path}: {e}")

# --- BLOCO PRINCIPAL ---
# Verifica se a impressora existe primeiro
try:
    # Testa se conseguimos conectar na impressora
    # Se der erro aqui, o nome está errado ou sem permissão
    h = win32print.OpenPrinter(nome_impressora)
    win32print.ClosePrinter(h)
    print(f"Impressora '{nome_impressora}' conectada!")
    
    arquivos = os.listdir(pasta_arquivos)
    for arquivo in arquivos:
        # Filtra apenas arquivos de texto ou .zpl
        if arquivo.endswith(".txt") or arquivo.endswith(".zpl"):
            caminho_completo = os.path.join(pasta_arquivos, arquivo)
            enviar_zpl_para_impressora(nome_impressora, caminho_completo)

except Exception as e:
    print(f"Não foi possível conectar na impressora: {e}")