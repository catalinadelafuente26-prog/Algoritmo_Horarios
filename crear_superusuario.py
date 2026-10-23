"""
crear_superusuario.py
Crea el usuario 'admin' (superusuario). Ejecutar una sola vez:
    python crear_superusuario.py
"""
import getpass
import database as db


def crear():
    db.inicializar_db()
    pwd = getpass.getpass("Contraseña para el superusuario 'admin' (mínimo 8 caracteres): ")
    pwd2 = getpass.getpass("Repite la contraseña: ")

    if len(pwd) < 8:
        print("La contraseña debe tener al menos 8 caracteres.")
        return
    if pwd != pwd2:
        print("Las contraseñas no coinciden.")
        return

    ok, mensaje = db.registrar_usuario("admin", pwd, "secretario", "Superusuario")
    print(mensaje)


if __name__ == "__main__":
    crear()