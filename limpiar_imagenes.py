import shutil
import os

ruta = "data/images_procesadas"

if os.path.exists(ruta):
    for elemento in os.listdir(ruta):
        ruta_completa = os.path.join(ruta, elemento)
        
        if os.path.isdir(ruta_completa):
            shutil.rmtree(ruta_completa)
        else:
            os.remove(ruta_completa)

    print("Carpeta images_procesadas limpiada.")
else:
    print("La carpeta no existe.")