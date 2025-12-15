from geradorZPL import root, carregar_tela_login
import shutil

root.title("Sistema de Etiquetas - Login")
root.geometry("1024x768")

carregar_tela_login()

def ao_fechar():
    with open(".env", 'w') as f:
        f.write("")
    try:
        shutil.rmtree("etiquetas_geradas")
    except:
        pass
    root.destroy()

root.protocol("WM_DELETE_WINDOW", ao_fechar)

root.mainloop()