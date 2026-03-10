#!/usr/bin/env python3
import Keypad
from gpiozero import AngularServo, LED
import time
import threading
import json
import os
import paho.mqtt.client as mqtt

from lcd_driver import lcd_init, lcd_print, lcd_clear, lcd_off
from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import Device

Device.pin_factory = PiGPIOFactory()

# ─── Configuration MQTT ──────────────────────────────────────────────
MQTT_BROKER = "100.x.x.x"  # IP Tailscale du serveur
MQTT_PORT = 1883

# Topics MQTT
TOPIC_STATE = "homeassistant/lock/porte/state"
TOPIC_COMMAND = "homeassistant/lock/porte/set"
TOPIC_AVAILABLE = "homeassistant/lock/porte/available"

# ─── Configuration matérielle ────────────────────────────────────────
ROWS = 4
COLS = 4
keys = ['1','2','3','A', '4','5','6','B', '7','8','9','C', '*','0','#','D']
rowsPins = [18, 23, 24, 25]
colsPins = [10, 22, 27, 17]

SERVO_GPIO = 12
myCorrection = 0.0
maxPW = (2.5 + myCorrection) / 1000
minPW = (0.5 - myCorrection) / 1000
UNLOCK_DELAY = 2 * 60

servo = AngularServo(SERVO_GPIO, initial_angle=0, min_angle=0, max_angle=180,
                     min_pulse_width=minPW, max_pulse_width=maxPW)

LED_GPIO = 16
led = LED(LED_GPIO)
led.off()

LCD_ADDRESS = 0x27
lcd = lcd_init(LCD_ADDRESS)

# ─── Configuration MQTT ──────────────────────────────────────────────
mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connecté au broker MQTT")
        client.subscribe(TOPIC_COMMAND)
        client.publish(TOPIC_AVAILABLE, "online", retain=True)
        publish_state("LOCKED")
    else:
        print(f"❌ Échec connexion MQTT: {rc}")

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"📨 MQTT reçu: {payload}")
    
    if msg.topic == TOPIC_COMMAND:
        if payload == "UNLOCK":
            unlock_servo(mqtt_triggered=True)
        elif payload == "LOCK":
            lock_servo(mqtt_triggered=True)

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.will_set(TOPIC_AVAILABLE, "offline", retain=True)

try:
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
    print("🔌 Connexion MQTT en cours...")
except Exception as e:
    print(f"❌ Erreur MQTT: {e}")

# ─── Fonctions MQTT ──────────────────────────────────────────────────
def publish_state(state):
    mqtt_client.publish(TOPIC_STATE, state, retain=True)
    print(f"📤 État: {state}")

# ─── Code généré ─────────────────────────────────────────────────────
CODE_FILE = "/tmp/code_actif.json"

def lire_code():
    if not os.path.exists(CODE_FILE):
        return "Invité", "1234"
    with open(CODE_FILE, 'r') as f:
        data = json.load(f)
    return data["nom"], data["code"]

# ─── Variables ───────────────────────────────────────────────────────
input_buffer = ""
servo_locked = True
lock_timer = None
nom_global, code_global = lire_code()

def unlock_servo(mqtt_triggered=False):
    global servo_locked, lock_timer
    
    servo.angle = 90
    led.on()
    servo_locked = False
    
    lcd_clear(lcd)
    lcd_print(lcd, "Bonjour", 1)
    lcd_print(lcd, nom_global[:16], 2)
    time.sleep(2)
    lcd_clear(lcd)
    lcd_print(lcd, "Porte ouverte", 1)
    lcd_print(lcd, "2 min...", 2)
    
    print(f"✅ Porte ouverte {'(MQTT)' if mqtt_triggered else '(Keypad)'}")
    publish_state("UNLOCKED")
    
    if lock_timer and lock_timer.is_alive():
        lock_timer.cancel()
    
    lock_timer = threading.Timer(UNLOCK_DELAY, fermeture_auto)
    lock_timer.daemon = True
    lock_timer.start()

def lock_servo(mqtt_triggered=False):
    global servo_locked, lock_timer
    
    if lock_timer and lock_timer.is_alive():
        lock_timer.cancel()
    
    servo.angle = 0
    led.off()
    servo_locked = True
    
    lcd_clear(lcd)
    lcd_print(lcd, "Porte fermee", 1)
    lcd_print(lcd, "MQTT" if mqtt_triggered else "Manuel", 2)
    time.sleep(2)
    lcd_clear(lcd)
    lcd_print(lcd, "Entrez le", 1)
    lcd_print(lcd, "code :", 2)
    
    print(f"🔒 Porte fermée {'(MQTT)' if mqtt_triggered else '(Manuel)'}")
    publish_state("LOCKED")

def fermeture_auto():
    global servo_locked
    servo.angle = 0
    led.off()
    servo_locked = True
    
    lcd_clear(lcd)
    lcd_print(lcd, "Porte fermee", 1)
    lcd_print(lcd, "Auto", 2)
    time.sleep(2)
    lcd_clear(lcd)
    lcd_print(lcd, "Entrez code", 1)
    
    print("🔒 Fermeture auto")
    publish_state("LOCKED")

def loop():
    global input_buffer, nom_global, code_global
    
    keypad = Keypad.Keypad(keys, rowsPins, colsPins, ROWS, COLS)
    keypad.setDebounceTime(50)
    
    lcd_clear(lcd)
    lcd_print(lcd, "Systeme pret", 1)
    lcd_print(lcd, "Entrez code", 2)
    
    print(f"👤 Utilisateur: {nom_global}")
    print("🔢 En attente...")
    
    while True:
        key = keypad.getKey()
        
        if key != keypad.NULL:
            if key == '*':
                input_buffer = ""
                lcd_clear(lcd)
                lcd_print(lcd, "Reset", 1)
                print("\n🔄 Reset")
                continue
            
            input_buffer += key
            lcd_clear(lcd)
            lcd_print(lcd, "Code:", 1)
            lcd_print(lcd, '*' * len(input_buffer), 2)
            
            if len(input_buffer) >= len(code_global):
                if input_buffer == code_global:
                    if servo_locked:
                        unlock_servo()
                    else:
                        lock_servo()
                else:
                    lcd_clear(lcd)
                    lcd_print(lcd, "Incorrect", 1)
                    time.sleep(2)
                    lcd_clear(lcd)
                    lcd_print(lcd, "Entrez code", 1)
                    print("❌ Code incorrect")
                
                input_buffer = ""

if __name__ == '__main__':
    print("🚪 Système démarré")
    lcd_clear(lcd)
    lcd_print(lcd, "Demarrage...", 1)
    try:
        loop()
    except KeyboardInterrupt:
        print("\n🛑 Arrêt")
        servo.angle = 0
        led.off()
        mqtt_client.publish(TOPIC_AVAILABLE, "offline", retain=True)
        mqtt_client.disconnect()
        lcd_clear(lcd)
        lcd_off(lcd)
