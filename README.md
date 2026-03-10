# 🚪 Système de Contrôle d'Accès Intelligent avec Home Assistant

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2025.x-blue.svg)

Système de verrouillage intelligent pour porte d'entrée, contrôlé par clavier matriciel 4x4 et intégré avec Home Assistant via MQTT.

![Photo du système](docs/images/systeme_complet.jpg)

## ✨ Fonctionnalités

- 🔐 **Déverrouillage par code PIN** via clavier matriciel 4x4
- 🌐 **Contrôle à distance** via Home Assistant (web/mobile)
- 📱 **Interface MQTT** pour intégration domotique
- 🔒 **Verrouillage automatique** après 2 minutes
- 💡 **Indication visuelle** par LED
- 📟 **Affichage LCD 16x2** avec messages
- 🎯 **Génération de codes aléatoires** quotidiens

## 🛠️ Matériel requis

### Composants principaux

| Composant | Quantité | Description |
|-----------|----------|-------------|
| Raspberry Pi | 1 | 3B+ ou supérieur recommandé |
| Servo-moteur | 1 | AngularServo 0-180° |
| LCD I2C 16x2 | 1 | Adresse 0x27 |
| Clavier matriciel | 1 | 4x4 (16 touches) |
| LED | 1 | Indication d'état |
| Résistances | Diverses | Pour LED et pull-up |

### Branchements GPIO
```
Servo     → GPIO 12
LED       → GPIO 16
LCD I2C   → SDA/SCL (I2C)
Clavier:
  Rows    → GPIO 18, 23, 24, 25
  Cols    → GPIO 10, 22, 27, 17
```

## 📋 Schéma de connexion
```
┌─────────────────────────────────────────┐
│         Raspberry Pi 4                  │
│                                         │
│  GPIO 12 ─────────────► Servo Motor    │
│  GPIO 16 ─────────────► LED            │
│  SDA/SCL ─────────────► LCD I2C         │
│  GPIO 18,23,24,25 ───► Keypad (Rows)   │
│  GPIO 10,22,27,17 ───► Keypad (Cols)   │
└─────────────────────────────────────────┘
```

## 🚀 Installation

### 1. Prérequis système
```bash
# Mettre à jour le système
sudo apt-get update
sudo apt-get upgrade -y

# Installer les dépendances
sudo apt-get install -y python3-pip git i2c-tools pigpio
sudo systemctl enable pigpiod
sudo systemctl start pigpiod

# Activer I2C
sudo raspi-config
# Interface Options → I2C → Enable
```

### 2. Cloner le projet
```bash
git clone https://github.com/FILSTOGNO/PROJET_PORTE_HOMEASSISTANT.git
cd PROJET_PORTE_HOMEASSISTANT
```

### 3. Installer les dépendances Python
```bash
pip3 install -r requirements.txt --break-system-packages
```

### 4. Configuration
```bash
# Copier le fichier de configuration
cp config/config.example.json config/config.json

# Éditer avec vos paramètres
nano config/config.json
```

## ⚙️ Configuration Home Assistant

### 1. Installer Mosquitto MQTT Broker
```bash
docker run -d \
  --name mosquitto \
  --restart unless-stopped \
  --network host \
  -v /path/to/mosquitto/config:/mosquitto/config \
  eclipse-mosquitto
```

### 2. Ajouter la configuration dans `configuration.yaml`
```yaml
mqtt:
  broker: localhost
  port: 1883
  
  lock:
    - name: "Porte Entrée"
      unique_id: "porte_entree_pi"
      state_topic: "homeassistant/lock/porte/state"
      command_topic: "homeassistant/lock/porte/set"
      availability_topic: "homeassistant/lock/porte/available"
      payload_lock: "LOCK"
      payload_unlock: "UNLOCK"
      state_locked: "LOCKED"
      state_unlocked: "UNLOCKED"
```

### 3. Redémarrer Home Assistant
```bash
docker restart homeassistant
```

## 🎮 Utilisation

### Lancer le système
```bash
cd PROJET_PORTE_HOMEASSISTANT
python3 src/porte_mqtt.py
```

### Lancer au démarrage (systemd)
```bash
# Créer le service
sudo nano /etc/systemd/system/porte-smart.service
```

Contenu :
```ini
[Unit]
Description=Système de Porte Intelligente
After=network.target pigpiod.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/PROJET_PORTE_HOMEASSISTANT
ExecStart=/usr/bin/python3 /home/pi/PROJET_PORTE_HOMEASSISTANT/src/porte_mqtt.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Activer le service :
```bash
sudo systemctl daemon-reload
sudo systemctl enable porte-smart.service
sudo systemctl start porte-smart.service
sudo systemctl status porte-smart.service
```

## 📱 Interface Home Assistant

### Aperçu du dashboard

![Dashboard Home Assistant](docs/images/screenshot_homeassistant.png)

### Actions disponibles

- 🔓 **Déverrouiller** : Ouvre la porte via servo
- 🔒 **Verrouiller** : Ferme la porte
- 📊 **État** : Affiche l'état actuel (locked/unlocked)
- 🔋 **Disponibilité** : Indique si le Raspberry Pi est connecté

## 🔧 Configuration avancée

### Modifier le délai de verrouillage automatique

Dans `src/porte_mqtt.py` :
```python
UNLOCK_DELAY = 2 * 60  # 2 minutes (en secondes)
```

### Changer le code PIN
```bash
# Générer un nouveau code
python3 src/generateur_code.py

# Le code est stocké dans /tmp/code_actif.json
cat /tmp/code_actif.json
```

### Personnaliser les messages LCD

Dans `src/porte_mqtt.py`, modifiez les fonctions :
```python
lcd_print(lcd, "Votre message", 1)  # Ligne 1
lcd_print(lcd, "Ligne 2", 2)        # Ligne 2
```

## 📊 Architecture MQTT
```
Topics utilisés:
├── homeassistant/lock/porte/state         (LOCKED/UNLOCKED)
├── homeassistant/lock/porte/set           (Commandes)
├── homeassistant/lock/porte/available     (online/offline)
└── homeassistant/lock/porte/code_entered  (Dernier code saisi)
```

## 🐛 Dépannage

### Le servo ne bouge pas
```bash
# Vérifier que pigpiod tourne
sudo systemctl status pigpiod

# Redémarrer si nécessaire
sudo systemctl restart pigpiod
```

### LCD n'affiche rien
```bash
# Vérifier l'adresse I2C
sudo i2cdetect -y 1

# Devrait montrer 0x27
```

### MQTT ne se connecte pas
```bash
# Tester la connexion
mosquitto_pub -h VOTRE_IP -t "test" -m "hello"

# Vérifier les logs
docker logs mosquitto
```

## 🤝 Contribution

Les contributions sont les bienvenues ! 

1. Forkez le projet
2. Créez une branche (`git checkout -b feature/amelioration`)
3. Committez vos changements (`git commit -am 'Ajout fonctionnalité'`)
4. Pushez (`git push origin feature/amelioration`)
5. Créez une Pull Request

## 📄 License

Ce projet est sous license MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 👤 Auteur

**Angelbert Fankepa**

- GitHub: [FILSTOGNO](https://github.com/FILSTOGNO)
- Website: [fankepa.com](https://fankepa.com)

## 🙏 Remerciements

- [Home Assistant](https://www.home-assistant.io/) pour la plateforme domotique
- [Eclipse Mosquitto](https://mosquitto.org/) pour le broker MQTT
- La communauté Raspberry Pi

## 📸 Galerie

### Système complet
![Vue d'ensemble](docs/images/vue_ensemble.jpg)

### Clavier matriciel
![Keypad](docs/images/keypad.jpg)

### Écran LCD
![LCD](docs/images/lcd_display.jpg)

---

⭐ **Si ce projet vous a aidé, n'oubliez pas de mettre une étoile !** ⭐
