try:
    import sys
    import os

    print("Instalation des module nescaire pour le Dumper:")

    if sys.platform.startswith("win"):
        os.system("python -m pip install --upgrade pip")
        os.system("python -m pip install -r requirements.txt")
        os.system("python Lycone.py")

except Exception as e:
    print(e)
    os.system("pause")