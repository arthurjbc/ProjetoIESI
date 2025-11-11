import tkinter as tk
from tkinter import ttk, messagebox
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import os

# --- Funções Principais ---

def centralizar_texto(draw, texto, fonte, largura_imagem):
    """Calcula a posição x para centralizar o texto."""
    bbox = fonte.getbbox(texto)
    largura_texto = bbox[2] - bbox[0]
    return (largura_imagem - largura_texto) / 2

def tentar_carregar_fonte(tamanho=18):
    """Tenta carregar fontes comuns do sistema. Retorna a fonte padrão se falhar."""
    fontes_comuns = ["arial.ttf", "DejaVuSans.ttf", "helvetica.ttf"]
    for nome_fonte in fontes_comuns:
        try:
            return ImageFont.truetype(nome_fonte, tamanho)
        except IOError:
            continue
    print("Aviso: Nenhuma fonte TTF comum encontrada. Usando fonte padrão.")
    return ImageFont.load_default()

def gerar_etiqueta():
    """Função principal chamada pelo botão."""
    
    nome_paciente = entry_nome.get()
    nome_exame = entry_exame.get()

    if not nome_paciente or not nome_exame:
        messagebox.showerror("Erro", "Por favor, preencha todos os campos.")
        return

    # Combina os dados para o código de barras
    dados_barcode = f"{nome_paciente.upper()}"
    
    # Define os nomes dos arquivos
    barcode_temp_file = "temp_barcode.png"
    # Sanitiza o nome do arquivo para evitar erros
    base_filename = f"etiqueta_{nome_paciente.replace(' ', '_')}_{nome_exame.replace(' ', '_')}"
    png_filename = f"{base_filename}.png"
    zpl_filename = f"{base_filename}.txt" # NOVO: Nome do arquivo ZPL

    try:
        # --- 1. Geração do Código de Barras (Imagem) ---
        
        CODE128 = barcode.get_barcode_class('code128')
        writer_options = {'module_height': 10.0, 'font_size': 0, 'text_distance': 0, 'quiet_zone': 2.0, 'dpi': 300}
        meu_barcode = CODE128(dados_barcode, writer=ImageWriter())
        meu_barcode.save("temp_barcode", options=writer_options)

        # --- 2. Composição da Imagem Final (com Pillow) ---
        
        img_barcode = Image.open(barcode_temp_file)
        largura_barcode, altura_barcode = img_barcode.size

        padding = 30
        espaco_texto_extra = 100
        largura_total = largura_barcode + (padding * 2)
        altura_total = altura_barcode + espaco_texto_extra + (padding * 2)

        img_final = Image.new('RGB', (largura_total, altura_total), 'white')
        draw = ImageDraw.Draw(img_final)

        fonte_titulo = tentar_carregar_fonte(tamanho=24)
        fonte_subtexto = tentar_carregar_fonte(tamanho=20)

        pos_barcode_x = (largura_total - largura_barcode) // 2
        pos_barcode_y = padding
        img_final.paste(img_barcode, (pos_barcode_x, pos_barcode_y))

        texto_nome = f"Paciente: {nome_paciente}"
        pos_nome_x = centralizar_texto(draw, texto_nome, fonte_titulo, largura_total)
        pos_nome_y = pos_barcode_y + altura_barcode + 25
        draw.text((pos_nome_x, pos_nome_y), texto_nome, fill="black", font=fonte_titulo)

        texto_exame = f"Exame: {nome_exame}"
        pos_exame_x = centralizar_texto(draw, texto_exame, fonte_subtexto, largura_total)
        pos_exame_y = pos_nome_y + 40
        draw.text((pos_exame_x, pos_exame_y), texto_exame, fill="black", font=fonte_subtexto)

        # --- 3. Salvamento da Imagem ---
        img_final.save(png_filename)
        os.remove(barcode_temp_file) # Limpa o temporário

        # --- 4. NOVO: Geração do Arquivo ZPL (.txt) ---

        # Este template ZPL é para uma impressora de 203 dpi (como a ZD220)
        # ^CI28 - Habilita o encoding UTF-8 para acentos
        # ^FO(x,y) - Field Origin (posição X, Y)
        # ^BCN,100,N,N,N - Barcode Code128 (N=normal, 100 dots altura, N=sem texto legível)
        # ^A0N,35,35 - Fonte padrão (N=normal, 35x35 dots)
        # ^FD...^FS - Field Data (os dados) e Field Separator
        
        zpl_template = f"""
^XA
^PW500

^FO150,30
^BY2,3.0
^BCN,100,N,N,N,A
^FD{dados_barcode}^FS

^FO50,160
^AAN,36,20
^FDPaciente: {nome_paciente}^FS

^FO50,205
^AAN,36,20
^FDExame: {nome_exame}^FS

^XZ

"""
        # Salva o arquivo ZPL com encoding UTF-8 (importante para acentos)
        with open(zpl_filename, "w", encoding="utf-8") as f:
            f.write(zpl_template)

        # --- 5. Finalização ---

        messagebox.showinfo("Sucesso", 
                            f"Etiqueta gerada com sucesso!\n\n"
                            f"Imagem: {png_filename}\n"
                            f"ZPL: {zpl_filename}")
        
        entry_nome.delete(0, tk.END)
        entry_exame.delete(0, tk.END)
        entry_nome.focus()

    except Exception as e:
        messagebox.showerror("Erro na Geração", f"Ocorreu um erro: {e}")
        if os.path.exists(barcode_temp_file):
            os.remove(barcode_temp_file)


# --- Configuração da Interface Gráfica (Tkinter) ---

root = tk.Tk()
root.title("Gerador de Etiqueta de Exame")
root.geometry("400x200")

frame = ttk.Frame(root, padding="20")
frame.pack(expand=True, fill=tk.BOTH)

lbl_nome = ttk.Label(frame, text="Nome do Paciente:")
lbl_nome.pack(pady=(0, 5))
entry_nome = ttk.Entry(frame, width=50)
entry_nome.pack(pady=(0, 10))

lbl_exame = ttk.Label(frame, text="Nome do Exame:")
lbl_exame.pack(pady=(0, 5))
entry_exame = ttk.Entry(frame, width=50)
entry_exame.pack(pady=(0, 15))

btn_gerar = ttk.Button(frame, text="Gerar Etiqueta", command=gerar_etiqueta)
btn_gerar.pack(pady=10)

entry_nome.focus()
root.mainloop()