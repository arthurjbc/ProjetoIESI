import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import os
from datetime import date, timedelta

class ZPLGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerador de Etiquetas ZPL")
        self.root.geometry("500x350")
        
        self.file_path = tk.StringVar()
        
        self._setup_ui()

    def _setup_ui(self):
        tk.Label(self.root, text="Gerador de ZPL Massivo", font=("Arial", 16, "bold")).pack(pady=10)

        frame_input = tk.Frame(self.root)
        frame_input.pack(pady=10, padx=20, fill="x")
        
        tk.Label(frame_input, text="Selecione a planilha (.xlsx ou .csv):").pack(anchor="w")
        
        entry_frame = tk.Frame(frame_input)
        entry_frame.pack(fill="x", pady=5)
        
        tk.Entry(entry_frame, textvariable=self.file_path, width=40).pack(side="left", fill="x", expand=True)
        tk.Button(entry_frame, text="Buscar...", command=self.select_file).pack(side="left", padx=5)

        tk.Button(self.root, text="GERAR ETIQUETAS", bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), 
                  command=self.generate_zpl, height=2).pack(pady=20, fill="x", padx=50)

        tk.Button(self.root, text="Imprimir (Mock)", command=self.mock_print_function).pack(pady=5)
        
        # Área de Status
        self.status_label = tk.Label(self.root, text="Aguardando arquivo...", fg="gray")
        self.status_label.pack(side="bottom", pady=10)

    def select_file(self):
        filename = filedialog.askopenfilename(
            title="Selecione a planilha",
            filetypes=[("Arquivos Excel", "*.xlsx"), ("Arquivos CSV", "*.csv")]
        )
        if filename:
            self.file_path.set(filename)
            self.status_label.config(text="Arquivo selecionado.", fg="blue")

    def mock_print_function(self):
        """
        Função Mock solicitada: Não faz nada real, apenas simula o clique.
        """
        if not self.file_path.get():
            messagebox.showwarning("Aviso", "Nenhuma etiqueta gerada ou arquivo selecionado para impressão.")
            return
            
        print("Botão de impressão acionado (MOCK). Nenhuma ação enviada para impressora.")
        messagebox.showinfo("Impressão", "Comando de impressão enviado (Simulação).")

    def generate_zpl(self):
        input_file = self.file_path.get()
        
        if not input_file:
            messagebox.showerror("Erro", "Por favor, selecione um arquivo primeiro.")
            return

        try:
            # Cria a pasta de saída
            output_folder = "etiquetas_geradas"
            os.makedirs(output_folder, exist_ok=True)
            
            # Leitura do arquivo (detecta se é excel ou csv)
            if input_file.endswith('.csv'):
                df = pd.read_csv(input_file)
            else:
                df = pd.read_excel(input_file)
            
            required_cols = ['nome_paciente', 'exame', 'data_nascimento']
            df.columns = [c.lower().replace(' ', '_') for c in df.columns]
            
            missing = [col for col in required_cols if col not in df.columns]
            if missing:
                messagebox.showerror("Erro de Formato", f"A planilha deve conter as colunas: {required_cols}\nFaltando: {missing}")
                return
            
            generated_count = 0
            current_date = date.today().strftime("%d-%m-%Y")
            for index, row in df.iterrows():
                row_id = index + 1 # ID baseado na linha
                
                nome = str(row.get('nome_paciente', ''))
                exame = str(row.get('exame', ''))
                nasc = str(row.get('data_nascimento', ''))
                
                zpl_content = f"""
^XA
^PW400
^LL240
^CI28

^FO10,10^A0N,25,25^FD{nome.capitalize()}^FS
^FO10,40^A0N,20,20^FDID: {row_id}  DN: {nasc[:10]}^FS
^FO10,65^A0N,20,20^FDData: {current_date[:10]}^FS

^FO10,100^GB380,0,2^FS 

^FO10,110^A0N,30,25^FDTIPO: SANGUE^FS
^FO10,155^FB380,2,0,L,0^A0N,25,25^FD{exame.capitalize()}^FS

^FO15,180^BY2,2,30^BCN,30,N,N,N^FD{nome.capitalize()}{row_id}^FS

^XZ
"""
                safe_name = "".join([c for c in nome if c.isalpha() or c.isdigit() or c==' ']).strip()
                filename = f"{output_folder}/etiqueta_{row_id}_{safe_name}.zpl"
                
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(zpl_content.strip())
                
                generated_count += 1

            self.status_label.config(text=f"Sucesso! {generated_count} etiquetas geradas.", fg="green")
            messagebox.showinfo("Concluído", f"{generated_count} arquivos ZPL foram salvos na pasta '{output_folder}'.")
            
        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Ocorreu um erro ao processar:\n{str(e)}")

root = tk.Tk()
app = ZPLGeneratorApp(root)
root.mainloop()