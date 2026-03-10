#!/usr/bin/env python3
########################################################################
# Filename    : generateur_code.py
# Description : Génère un code aléatoire pour l'utilisateur
########################################################################
import random
import json
import os
from datetime import datetime

CODE_FILE = "/tmp/code_actif.json"   # fichier temporaire pour partager le code

def generer_code(longueur=4):
    """Génère un code numérique aléatoire."""
    return ''.join([str(random.randint(0, 9)) for _ in range(longueur)])

def sauvegarder_code(nom, code):
    """Sauvegarde le nom et le code dans un fichier temporaire."""
    data = {
        "nom":   nom,
        "code":  code,
        "heure": datetime.now().strftime("%H:%M:%S")
    }
    with open(CODE_FILE, 'w') as f:
        json.dump(data, f)

def demarrer():
    print("=" * 40)
    print("   🚪  SYSTÈME DE CONTRÔLE D'ACCÈS")
    print("=" * 40)

    nom = input("\n👤 Entrez votre nom : ").strip()

    if not nom:
        print("❌ Nom invalide. Relancez le programme.")
        return

    code = generer_code()
    sauvegarder_code(nom, code)

    print("\n" + "=" * 40)
    print(f"  Bonjour, {nom} !")
    print(f"  🔑 Votre code d'accès : {code}")
    print(f"  ⏱️  Entrez ce code sur le keypad.")
    print("=" * 40 + "\n")

    # Lance porte.py automatiquement après
    os.system("python3 /home/angelbert/PROJET_PI/PORTE/porte.py")

if __name__ == '__main__':
    demarrer()
