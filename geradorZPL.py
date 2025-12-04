import json
import os
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import tkinter as tk
from tkinter import filedialog, messagebox

# --- CONFIGURAÇÕES GERAIS (50mm x 30mm) ---
# Considerando impressora 203 DPI (8 dots/mm)
# Largura: 50mm * 8 = 400 dots
# Altura: 30mm * 8 = 240 dots
LARGURA_DOTS = 400
ALTURA_DOTS = 240

def carregar_fonte(tamanho=20, bold=False):
    """Tenta carregar fontes do sistema, fallback para padrão."""
    try:
        if bold:
            return ImageFont.truetype("arialbd.ttf", tamanho)
        return ImageFont.truetype("arial.ttf", tamanho)
    except IOError:
        # Fallback se não tiver Arial
        return ImageFont.load_default()

def gerar_zpl_string(paciente, exame_atual, index_exame):
    """
    Gera o código ZPL puro para uma etiqueta de 50x30mm.
    """
    # Tratamento de Strings para evitar quebra de layout ZPL
    nome_abrev = paciente['nome'][:25] # Limita caracteres
    exame_abrev = exame_atual[:25]
    
    # ^XA: Inicio
    # ^PW400: Largura de impressão
    # ^LL240: Comprimento da etiqueta
    # ^CI28: Encoding UTF-8 (para acentos)
    zpl = f"""
^XA
^PW{LARGURA_DOTS}
^LL{ALTURA_DOTS}
^CI28

^FO10,10^A0N,25,25^FD{nome_abrev}^FS
^FO10,40^A0N,20,20^FDID: {paciente['id']}  DN: {paciente['data_n']}^FS
^FO10,65^A0N,20,20^FDData: {paciente['data'][:10]}^FS

^FO10,100^GB380,0,2^FS 

^FO10,110^A0N,10,10^FDTIPO: SANGUE^FS
^FO10,120^A0N,30,30^FDEXAME ({index_exame + 1}/{paciente['qtd_lem']})^FS
^FO10,155^FB380,2,0,L,0^A0N,25,25^FD{exame_abrev}^FS

^FO20,180^BY2,2,30^BCN,30,N,N,N^FD{paciente['id']}-{paciente['nome']}^FS

^XZ
"""
    return zpl

def gerar_imagem_pillow(paciente, exame_atual, index_exame, filename):
    """
    Gera uma imagem PNG simulando a etiqueta com código de barras real.
    """
    # Cria canvas branco
    img = Image.new('RGB', (LARGURA_DOTS, ALTURA_DOTS), 'white')
    draw = ImageDraw.Draw(img)
    
    # Fontes
    font_nome = carregar_fonte(28, bold=True)
    font_texto = carregar_fonte(22)
    font_destaque = carregar_fonte(26, bold=True)
    
    # --- Desenhando na Imagem ---
    
    # Linha 1: Nome
    draw.text((10, 10), f"{paciente['nome'][:28]}", fill="black", font=font_nome)
    
    # Linha 2: ID e DN
    draw.text((10, 45), f"ID: {paciente['id']}   DN: {paciente['data_n']}", fill="black", font=font_texto)
    
    # Linha 3: Data do pedido
    draw.text((10, 75), f"Data: {paciente['data'][:10]}", fill="black", font=font_texto)
    
    # Linha Divisória
    draw.line([(10, 105), (390, 105)], fill="black", width=2)
    
    # Linha 4: Título do Exame e Contador
    draw.text((10, 115), f"EXAME ({index_exame + 1}/{paciente['qtd_lem']})", fill="black", font=font_destaque)
    
    # Linha 5: Nome do Exame
    draw.text((10, 150), exame_atual, fill="black", font=font_texto)
    
    # --- Geração do Código de Barras Real ---
    try:
        # Dados do barcode: ID e Nome concatenados conforme solicitado
        dados_barcode = f"{paciente['id']}-{paciente['nome']}"
        
        # Usando Code128
        CODE128 = barcode.get_barcode_class('code128')
        writer = ImageWriter()
        
        # Instancia o barcode
        my_barcode = CODE128(dados_barcode, writer=writer)
        
        # Opções para ajustar o tamanho na etiqueta pequena
        options = {
            'module_width': 0.25,  # Barras mais finas
            'module_height': 8.0,  # Altura das barras
            'quiet_zone': 1.0,     # Margem branca menor
            'font_size': 0,        # Sem texto dentro do barcode (já temos texto na etiqueta)
            'text_distance': 0,
            'write_text': False
        }
        
        # Renderiza para um objeto PIL Image
        barcode_img = my_barcode.render(options)
        
        # Verifica se o código de barras ficou maior que a largura da etiqueta (com margens)
        largura_maxima = 380
        if barcode_img.width > largura_maxima:
            ratio = largura_maxima / barcode_img.width
            nova_altura = int(barcode_img.height * ratio)
            barcode_img = barcode_img.resize((largura_maxima, nova_altura), Image.Resampling.LANCZOS)
        
        # Centraliza e cola na parte inferior
        pos_x = (LARGURA_DOTS - barcode_img.width) // 2
        pos_y = 150 # Posição Y ajustada para o rodapé
        
        img.paste(barcode_img, (pos_x, pos_y))

    except Exception as e:
        print(f"Erro ao gerar barcode para imagem: {e}")
        # Fallback visual em caso de erro
        draw.rectangle([(10, 190), (390, 230)], fill="black")
        draw.text((20, 200), "ERRO BARCODE", fill="white", font=carregar_fonte(15))

    img.save(filename)

def processar_json():
    """Lê o arquivo JSON e gera as etiquetas."""
    
    # 1. Selecionar arquivo
    filepath = filedialog.askopenfilename(title="Selecione o arquivo JSON", filetypes=[("JSON Files", "*.json")])
    if not filepath:
        return

    output_dir = "etiquetas_geradas"
    output_dir_png = "etiquetasPNG"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if not os.path.exists(output_dir_png):
        os.makedirs(output_dir_png)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            dados = json.load(f)

        contador_arquivos = 0

        # Itera sobre cada paciente (Chaves "1", "2", etc.)
        for key, paciente in dados.items():
            
            lembretes = paciente.get("lembretes", [])
            
            # Itera sobre cada lembrete (exame) do paciente
            for i, exame in enumerate(lembretes):
                safe_nome = paciente['nome'].replace(" ", "_")
                safe_exame = exame.replace(" ", "_")[:10]
                
                base_name = f"{paciente['id']}_{safe_nome}_{i+1}"
                path_zpl = os.path.join(output_dir, f"{base_name}.zpl")

                path_png = os.path.join(output_dir_png, f"{base_name}.png")

                # 1. Gerar ZPL
                zpl_content = gerar_zpl_string(paciente, exame, i)
                with open(path_zpl, "w", encoding="utf-8") as zpl_file:
                    zpl_file.write(zpl_content)

                # 2. Gerar Imagem
                gerar_imagem_pillow(paciente, exame, i, path_png)
                
                contador_arquivos += 1

        messagebox.showinfo("Concluído", f"Processamento finalizado!\n{contador_arquivos} etiquetas geradas na pasta '{output_dir}'.")

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao processar JSON: {str(e)}")

# --- GUI Principal ---
root = tk.Tk()
root.title("Gerador de Etiquetas em Lote (50x30mm)")
root.geometry("400x200")

frame = tk.Frame(root, padx=20, pady=20)
frame.pack(expand=True)

btn_processar = tk.Button(frame, text="Selecionar JSON e Gerar Etiquetas", command=processar_json, bg="#4CAF50", fg="white")
btn_processar.pack(fill=tk.X, pady=10)

lbl_info = tk.Label(frame, text="\nFormatos: .ZPL e .PNG", fg="gray")
lbl_info.pack(pady=5)

root.mainloop()