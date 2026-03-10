#!/usr/bin/env python3
########################################################################
# Filename    : lcd_driver.py
# Description : Driver pour LCD 16x2 I2C
########################################################################
import smbus
import time

# Constantes LCD
LCD_CHR = 1
LCD_CMD = 0
LCD_LINE_1 = 0x80
LCD_LINE_2 = 0xC0
LCD_BACKLIGHT = 0x08
ENABLE = 0b00000100

def lcd_init(address=0x27, bus=1):
    """Initialise le LCD et retourne un objet lcd."""
    lcd = {
        "address": address,
        "bus": smbus.SMBus(bus)
    }
    _lcd_byte(lcd, 0x33, LCD_CMD)
    _lcd_byte(lcd, 0x32, LCD_CMD)
    _lcd_byte(lcd, 0x06, LCD_CMD)
    _lcd_byte(lcd, 0x0C, LCD_CMD)
    _lcd_byte(lcd, 0x28, LCD_CMD)
    lcd_clear(lcd)
    time.sleep(0.05)
    return lcd

def _lcd_byte(lcd, bits, mode):
    bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
    bits_low  = mode | ((bits << 4) & 0xF0) | LCD_BACKLIGHT
    lcd["bus"].write_byte(lcd["address"], bits_high)
    _lcd_toggle_enable(lcd, bits_high)
    lcd["bus"].write_byte(lcd["address"], bits_low)
    _lcd_toggle_enable(lcd, bits_low)

def _lcd_toggle_enable(lcd, bits):
    time.sleep(0.0005)
    lcd["bus"].write_byte(lcd["address"], (bits | ENABLE))
    time.sleep(0.0005)
    lcd["bus"].write_byte(lcd["address"], (bits & ~ENABLE))
    time.sleep(0.0005)

def lcd_clear(lcd):
    """Efface l'écran."""
    _lcd_byte(lcd, 0x01, LCD_CMD)
    time.sleep(0.05)

def lcd_print(lcd, message, line=1):
    """Affiche un message sur la ligne 1 ou 2 (centré automatiquement)."""
    message = message.center(16)          # centre sur 16 caractères
    _lcd_byte(lcd, LCD_LINE_1 if line == 1 else LCD_LINE_2, LCD_CMD)
    for char in message:
        _lcd_byte(lcd, ord(char), LCD_CHR)

def lcd_off(lcd):
    """Éteint le rétroéclairage."""
    lcd["bus"].write_byte(lcd["address"], 0x00)
