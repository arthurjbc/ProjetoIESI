from geradorZPL import root, carregar_tela_login
import shutil

root.title("Sistema de Etiquetas - Login")
root.geometry("1024x768")

carregar_tela_login()

root.mainloop()

with open(".env", 'w') as f:
    f.write("")
import shutil

caminhoWin = "C:/Users/"

shutil.rmtree("etiquetas_geradas")
