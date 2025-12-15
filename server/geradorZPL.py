import json
import os
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import tkinter as tk
from tkinter import filedialog, messagebox

# Importa a função que retorna o dicionário
from geradorJSON import gerar_json 

# --- CONFIGURAÇÕES GERAIS (50mm x 30mm) ---
# Considerando impressora 203 DPI (8 dots/mm)
LARGURA_DOTS = 400
ALTURA_DOTS = 240

def carregar_fonte(tamanho=20, bold=False):
    """Tenta carregar fontes do sistema, fallback para padrão."""
    try:
        if bold:
            return ImageFont.truetype("arialbd.ttf", tamanho)
        return ImageFont.truetype("arial.ttf", tamanho)
    except IOError:
        return ImageFont.load_default()

def gerar_zpl_string(paciente, exame_atual, index_exame):
    """
    Gera o código ZPL puro para uma etiqueta de 50x30mm.
    """
    nome_abrev = paciente['nome'][:25] 
    exame_abrev = exame_atual[:25]
    
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

^FO5,180^BY2,2,30^BCN,30,N,N,N^FD{paciente['id']}-{paciente['nome']}^FS

^XZ
"""
    return zpl

def gerar_imagem_pillow(paciente, exame_atual, index_exame, filename):
    """
    Gera uma imagem PNG simulando a etiqueta com código de barras real.
    """
    img = Image.new('RGB', (LARGURA_DOTS, ALTURA_DOTS), 'white')
    draw = ImageDraw.Draw(img)
    
    font_nome = carregar_fonte(28, bold=True)
    font_texto = carregar_fonte(22)
    font_destaque = carregar_fonte(26, bold=True)
    
    # --- Desenhando na Imagem ---
    draw.text((10, 10), f"{paciente['nome'][:28]}", fill="black", font=font_nome)
    draw.text((10, 45), f"ID: {paciente['id']}   DN: {paciente['data_n']}", fill="black", font=font_texto)
    draw.text((10, 75), f"Data: {paciente['data'][:10]}", fill="black", font=font_texto)
    draw.line([(10, 105), (390, 105)], fill="black", width=2)
    draw.text((10, 115), f"EXAME ({index_exame + 1}/{paciente['qtd_lem']})", fill="black", font=font_destaque)
    draw.text((10, 150), exame_atual, fill="black", font=font_texto)
    
    # --- Geração do Código de Barras Real ---
    try:
        dados_barcode = f"{paciente['id']}-{paciente['nome']}"
        CODE128 = barcode.get_barcode_class('code128')
        writer = ImageWriter()
        my_barcode = CODE128(dados_barcode, writer=writer)
        
        options = {
            'module_width': 0.25,
            'module_height': 8.0,
            'quiet_zone': 1.0, 
            'font_size': 0,
            'text_distance': 0,
            'write_text': False
        }
        
        barcode_img = my_barcode.render(options)
        
        largura_maxima = 380
        if barcode_img.width > largura_maxima:
            ratio = largura_maxima / barcode_img.width
            nova_altura = int(barcode_img.height * ratio)
            barcode_img = barcode_img.resize((largura_maxima, nova_altura), Image.Resampling.LANCZOS)
        
        pos_x = (LARGURA_DOTS - barcode_img.width) // 2
        pos_y = 150 
        
        img.paste(barcode_img, (pos_x, pos_y))

    except Exception as e:
        print(f"Erro ao gerar barcode para imagem: {e}")
        draw.rectangle([(10, 190), (390, 230)], fill="black")
        draw.text((20, 200), "ERRO BARCODE", fill="white", font=carregar_fonte(15))

    img.save(filename)

def processar_dados():
    """Obtém o dicionário direto da função e gera as etiquetas."""
    
    output_dir = "etiquetas_geradas"
    output_dir_png = "etiquetasPNG"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if not os.path.exists(output_dir_png):
        os.makedirs(output_dir_png)

    try:
        # --- ALTERAÇÃO PRINCIPAL AQUI ---
        # Chama a função importada para obter o dicionário diretamente
        dados = gerar_json() 
        
        if not dados:
            messagebox.showwarning("Aviso", "A função gerar_json retornou dados vazios.")
            return

        contador_arquivos = 0

        # Itera sobre cada paciente (Chaves "1", "2", etc.)
        for key, paciente in dados.items():
            
            lembretes = paciente.get("lembretes", [])
            
            # Itera sobre cada lembrete (exame) do paciente
            for i, exame in enumerate(lembretes):
                safe_nome = paciente['nome'].replace(" ", "_")
                # Remove caracteres proibidos em nomes de arquivo se necessário
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

        messagebox.showinfo("Concluído", f"Processamento finalizado!\n{contador_arquivos} etiquetas geradas.")

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao processar dados: {str(e)}")

# --- GUI Principal ---
root = tk.Tk()
root.title("Gerador de Etiquetas em Lote (50x30mm)")
root.geometry("400x200")

frame = tk.Frame(root, padx=20, pady=20)
frame.pack(expand=True)

# Botão atualizado para chamar a nova função
btn_processar = tk.Button(frame, text="Gerar Etiquetas (Direto)", command=processar_dados, bg="#4CAF50", fg="white")
btn_processar.pack(fill=tk.X, pady=10)

lbl_info = tk.Label(frame, text="\nLê diretamente de 'gerar_json()'\nSaída: .ZPL e .PNG", fg="gray")
lbl_info.pack(pady=5)

root.mainloop()