import json
import os
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import tkinter as tk
from tkinter import filedialog, messagebox
from impressoraZPL import imprimir_zpl

from geradorJSON import gerar_json 

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
    """Gera o código ZPL puro para uma etiqueta de 50x30mm."""
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

^FO15,180^BY2,2,30^BCN,30,N,N,N^FD{paciente['id']}-{paciente['nome']}^FS

^XZ
"""
    return zpl

def gerar_imagem_pillow(paciente, exame_atual, index_exame, filename):
    """Gera uma imagem PNG simulando a etiqueta."""
    img = Image.new('RGB', (LARGURA_DOTS, ALTURA_DOTS), 'white')
    draw = ImageDraw.Draw(img)
    
    font_nome = carregar_fonte(28, bold=True)
    font_texto = carregar_fonte(22)
    font_destaque = carregar_fonte(26, bold=True)
    
    draw.text((10, 10), f"{paciente['nome'][:28]}", fill="black", font=font_nome)
    draw.text((10, 45), f"ID: {paciente['id']}   DN: {paciente['data_n']}", fill="black", font=font_texto)
    draw.text((10, 75), f"Data: {paciente['data'][:10]}", fill="black", font=font_texto)
    draw.line([(10, 105), (390, 105)], fill="black", width=2)
    draw.text((10, 115), f"EXAME ({index_exame + 1}/{paciente['qtd_lem']})", fill="black", font=font_destaque)
    draw.text((10, 150), exame_atual, fill="black", font=font_texto)
    
    try:
        dados_barcode = f"{paciente['id']}-{paciente['nome']}"
        CODE128 = barcode.get_barcode_class('code128')
        writer = ImageWriter()
        my_barcode = CODE128(dados_barcode, writer=writer)
        
        options = {
            'module_width': 0.25, 'module_height': 8.0, 'quiet_zone': 1.0, 
            'font_size': 0, 'text_distance': 0, 'write_text': False
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
        print(f"Erro ao gerar barcode: {e}")
        draw.rectangle([(10, 190), (390, 230)], fill="black")
        draw.text((20, 200), "ERRO BARCODE", fill="white", font=carregar_fonte(15))

    img.save(filename)

def processar_dados():
    """Lógica principal de geração de etiquetas."""
    output_dir = "etiquetas_geradas"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        dados = gerar_json() 
        if dados == {}:
            messagebox.showwarning("Aviso", "A função gerar_json retornou dados vazios.")
            return

        contador_arquivos = 0
        for key, paciente in dados.items():
            lembretes = paciente.get("lembretes", [])
            for i, exame in enumerate(lembretes):
                safe_nome = paciente['nome'].replace(" ", "_")
                base_name = f"{paciente['id']}_{safe_nome}_{i+1}"
                path_zpl = os.path.join(output_dir, f"{base_name}.zpl")

                zpl_content = gerar_zpl_string(paciente, exame, i)
                with open(path_zpl, "w", encoding="utf-8") as zpl_file:
                    zpl_file.write(zpl_content)
                
                contador_arquivos += 1

        messagebox.showinfo("Concluído", f"Processamento finalizado!\n{contador_arquivos} etiquetas geradas.")

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao processar dados: {str(e)}")

def mock_impressao():
    print("Enviando para impressora...")
    messagebox.showinfo("Impressão", "Comando enviado para impressora (Mock).")


def salvar_no_env(login, senha):
    """Salva as credenciais no arquivo .env"""
    try:
        with open(".env", 'w') as f:
            f.write(f"login='{login}'\n")
            f.write(f"senha='{senha}'\n")
        return True
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível salvar o arquivo .env: {e}")
        return False

def tentar_login():
    usuario = entry_usuario.get()
    senha = entry_senha.get()

    if not usuario or not senha:
        messagebox.showwarning("Atenção", "Preencha usuário e senha.")
        return

    # Salva no .env
    sucesso = salvar_no_env(usuario, senha)
    
    if sucesso:
        # Destrói o frame de login e carrega o principal
        frame_login.destroy()
        carregar_tela_principal()

def carregar_tela_principal():
    """Constrói a interface principal do gerador de etiquetas."""
    frame_principal = tk.Frame(root, padx=20, pady=20)
    frame_principal.pack(expand=True, fill=tk.BOTH)

    lbl_titulo = tk.Label(frame_principal, text="Painel de Etiquetas", font=("Arial", 16, "bold"))
    lbl_titulo.pack(pady=20)

    btn_gerar = tk.Button(frame_principal, text="Gerar Etiquetas (ZPL)", command=processar_dados, 
                          bg="#2196F3", fg="white", font=("Arial", 12), height=2)
    btn_gerar.pack(fill=tk.X, pady=10)

    btn_imprimir = tk.Button(frame_principal, text="Imprimir Etiquetas", command=imprimir_zpl, 
                             bg="#4CAF50", fg="white", font=("Arial", 12), height=2)
    btn_imprimir.pack(fill=tk.X, pady=10)

    lbl_info = tk.Label(frame_principal, text="Logado com sucesso. Configurações salvas em .env", fg="gray")
    lbl_info.pack(side=tk.BOTTOM, pady=10)

def carregar_tela_login():
    """Constrói a interface de login."""
    global frame_login, entry_usuario, entry_senha
    
    frame_login = tk.Frame(root, padx=40, pady=40)
    frame_login.pack(expand=True)

    lbl_titulo = tk.Label(frame_login, text="Acesso ao Sistema", font=("Arial", 14, "bold"))
    lbl_titulo.pack(pady=(0, 20))

    tk.Label(frame_login, text="Usuário:", anchor="w").pack(fill=tk.X)
    entry_usuario = tk.Entry(frame_login, font=("Arial", 11))
    entry_usuario.pack(fill=tk.X, pady=(0, 10))

    tk.Label(frame_login, text="Senha:", anchor="w").pack(fill=tk.X)
    entry_senha = tk.Entry(frame_login, show="*", font=("Arial", 11))
    entry_senha.pack(fill=tk.X, pady=(0, 20))

    btn_entrar = tk.Button(frame_login, text="Entrar", command=tentar_login, 
                           bg="#007ACC", fg="white", font=("Arial", 11, "bold"), height=2)
    btn_entrar.pack(fill=tk.X)

root = tk.Tk()