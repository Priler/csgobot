# -*- coding: utf-8 -*-
"""
ULTIMATE HYBRID CS BOT v9.0
Combines autonomous chat learning with professional YOLO detection
Merges: v8.0 Chat Learning Bot + Priler/csgobot YOLO Architecture
Author: Hybrid Development
"""

import subprocess
import sys
import os
import time
import threading
import random
import re
import pickle
import json
import ctypes
import logging
import multiprocessing
import signal
from ctypes import windll, wintypes
from typing import Dict, List, Optional, Tuple
from collections import deque
from dataclasses import dataclass, field
from enum import Enum

# ==================== Auto-install dependencies ====================
def check_and_install_dependencies():
    packages = {
        'psutil': 'psutil',
        'pywin32': 'win32gui',
        'keyboard': 'keyboard',
        'mouse': 'mouse',
        'Pillow': 'PIL',
        'opencv-python': 'cv2',
        'numpy': 'numpy',
        'pyautogui': 'pyautogui',
        'pynput': 'pynput',
        'requests': 'requests',
        'ultralytics': 'ultralytics',
        'torch': 'torch',
    }
    missing = []
    for pip_name, import_name in packages.items():
        try:
            if pip_name == 'Pillow':
                from PIL import Image
            elif pip_name == 'pywin32':
                import win32gui
            else:
                __import__(import_name.replace('-', '_'))
        except ImportError:
            missing.append(pip_name)
    if missing:
        print(f"[SETUP] Installing {len(missing)} packages...")
        for pkg in missing:
            try:
                subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', pkg, '--quiet', '--disable-pip-version-check'],
                    capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW
                )
            except:
                pass
    print("[SETUP] Dependencies ready.")

if not getattr(sys, 'frozen', False):
    check_and_install_dependencies()

# ==================== Logging setup ====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("HybridCSBot")

# ==================== Imports ====================
import psutil
import win32gui
import win32process
import win32api
import win32con
import win32ui
import keyboard
import mouse

try:
    from PIL import Image
    PIL_OK = True
except:
    PIL_OK = False

try:
    import cv2
    import numpy as np
    CV_OK = True
except:
    CV_OK = False

try:
    from pynput import keyboard as pynput_keyboard
    from pynput import mouse as pynput_mouse
    PYNPUT_OK = True
except:
    PYNPUT_OK = False

try:
    from ultralytics import YOLO
    YOLO_OK = True
except:
    YOLO_OK = False

user32 = windll.user32

# ==================== Enums ====================
class Team(Enum):
    CT = "ct"
    T = "t"

# ==================== SendInput Controller ====================
class SendInput:
    INPUT_KEYBOARD = 1
    INPUT_MOUSE = 0
    MOUSEEVENTF_MOVE = 0x0001
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    KEYEVENTF_KEYDOWN = 0x0000
    KEYEVENTF_KEYUP = 0x0002

    VK = {
        'A': 0x41, 'B': 0x42, 'C': 0x43, 'D': 0x44, 'E': 0x45,
        'F': 0x46, 'G': 0x47, 'R': 0x52, 'S': 0x53, 'W': 0x57,
        'SPACE': 0x20, 'ENTER': 0x0D, 'ESC': 0x1B, 'TAB': 0x09,
        'SHIFT': 0x10, 'CTRL': 0x11, 'ALT': 0x12,
        '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34, '5': 0x35,
        'B': 0x42, 'Q': 0x51, 'X': 0x58, 'Z': 0x5A,
    }

    MOUSE = {'left': (0x0002, 0x0004), 'right': (0x0008, 0x0010)}
    _initialized = False

    @classmethod
    def setup(cls):
        if cls._initialized:
            return
        class MI(ctypes.Structure):
            _fields_ = [('dx', wintypes.LONG), ('dy', wintypes.LONG),
                        ('mouseData', wintypes.DWORD), ('dwFlags', wintypes.DWORD),
                        ('time', wintypes.DWORD), ('dwExtraInfo', ctypes.POINTER(wintypes.ULONG))]
        class KI(ctypes.Structure):
            _fields_ = [('wVk', wintypes.WORD), ('wScan', wintypes.WORD),
                        ('dwFlags', wintypes.DWORD), ('time', wintypes.DWORD),
                        ('dwExtraInfo', ctypes.POINTER(wintypes.ULONG))]
        class DataUnion(ctypes.Union):
            _fields_ = [('mi', MI), ('ki', KI)]
        class InputStruct(ctypes.Structure):
            _fields_ = [('type', wintypes.DWORD), ('data', DataUnion)]
        cls.MI, cls.KI, cls.InputStruct = MI, KI, InputStruct
        cls._initialized = True

    @classmethod
    def key(cls, key: str, press: bool = True):
        cls.setup()
        vk = cls.VK.get(key.upper(), 0)
        inp = cls.InputStruct()
        inp.type = cls.INPUT_KEYBOARD
        inp.data.ki.wVk = vk
        inp.data.ki.dwFlags = cls.KEYEVENTF_KEYDOWN if press else cls.KEYEVENTF_KEYUP
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

    @classmethod
    def mouse_move(cls, dx: int, dy: int):
        cls.setup()
        inp = cls.InputStruct()
        inp.type = cls.INPUT_MOUSE
        inp.data.mi.dx = dx
        inp.data.mi.dy = dy
        inp.data.mi.dwFlags = cls.MOUSEEVENTF_MOVE
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

    @classmethod
    def click(cls, button: str = 'left', duration: float = 0.02):
        cls.setup()
        d, u = cls.MOUSE.get(button, cls.MOUSE['left'])
        inp = cls.InputStruct()
        inp.type = cls.INPUT_MOUSE
        inp.data.mi.dwFlags = d
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
        time.sleep(duration)
        inp.data.mi.dwFlags = u
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

    @classmethod
    def press(cls, key: str):
        cls.key(key, True)
        time.sleep(0.02)
        cls.key(key, False)

# ==================== Window Capture ====================
class WindowCapture:
    def __init__(self, hwnd: int = None):
        self.hwnd = hwnd
        self.w, self.h, self.x, self.y = 1920, 1080, 0, 0

    def capture(self):
        if not self.hwnd or not PIL_OK:
            return None
        try:
            l, t, r, b = win32gui.GetWindowRect(self.hwnd)
            self.w, self.h = r - l, b - t
            self.x, self.y = l, t
            hdc = win32gui.GetWindowDC(self.hwnd)
            mdc = win32ui.CreateDCFromHandle(hdc)
            sdc = mdc.CreateCompatibleDC()
            bm = win32ui.CreateBitmap()
            bm.CreateCompatibleBitmap(mdc, self.w, self.h)
            sdc.SelectObject(bm)
            sdc.BitBlt((0, 0), (self.w, self.h), mdc, (0, 0), win32con.SRCCOPY)
            info = bm.GetInfo()
            data = bm.GetBitmapBits()
            img = Image.frombuffer('RGB', (info['bmWidth'], info['bmHeight']), data, 'raw', 'BGRX')
            win32gui.DeleteObject(bm.GetHandle())
            sdc.DeleteDC()
            mdc.DeleteDC()
            win32gui.ReleaseDC(self.hwnd, hdc)
            return img
        except:
            return None

# ==================== Vision Processor ====================
class VisionProcessor:
    def __init__(self, use_yolo=False, yolo_model_path=None):
        self.prev_enemies = []
        self.use_yolo = use_yolo and YOLO_OK
        self.yolo_model = None
        
        if self.use_yolo and yolo_model_path:
            try:
                self.yolo_model = YOLO(yolo_model_path)
                logger.info(f"[VISION] YOLO model loaded: {yolo_model_path}")
            except Exception as e:
                logger.warning(f"[VISION] Failed to load YOLO model: {e}. Falling back to color detection.")
                self.use_yolo = False

    def detect_enemies(self, screen) -> List[Dict]:
        if screen is None:
            return []
        
        if self.use_yolo and self.yolo_model:
            return self._detect_enemies_yolo(screen)
        else:
            return self._detect_enemies_color(screen)

    def _detect_enemies_yolo(self, screen) -> List[Dict]:
        enemies = []
        try:
            results = self.yolo_model(screen, conf=0.5, verbose=False)
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    
                    x, y, w, h = x1, y1, x2 - x1, y2 - y1
                    enemies.append({
                        'x': x + w // 2, 'y': y + h // 2,
                        'w': w, 'h': h,
                        'distance': max(10, 100 * 50 / max(w, h)),
                        'confidence': conf,
                        'class': cls,
                    })
        except Exception as e:
            logger.debug(f"[VISION] YOLO detection error: {e}")
            return self._detect_enemies_color(screen)
        
        return enemies

    def _detect_enemies_color(self, screen) -> List[Dict]:
        if not CV_OK or screen is None:
            return []
        enemies = []
        try:
            arr = np.array(screen)
            hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV)
            mask1 = cv2.inRange(hsv, np.array([0, 100, 100]), np.array([10, 255, 255]))
            mask2 = cv2.inRange(hsv, np.array([160, 100, 100]), np.array([180, 255, 255]))
            mask3 = cv2.inRange(hsv, np.array([20, 100, 100]), np.array([30, 255, 255]))
            mask = cv2.bitwise_or(cv2.bitwise_or(mask1, mask2), mask3)
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > 200:
                    x, y, w, h = cv2.boundingRect(cnt)
                    aspect_ratio = w / max(h, 1)
                    if 0.2 < aspect_ratio < 4.0:
                        enemies.append({
                            'x': x + w // 2, 'y': y + h // 2,
                            'w': w, 'h': h,
                            'distance': max(10, 100 * 50 / max(w, h)),
                            'confidence': min(1.0, area / 600),
                        })
        except Exception as e:
            logger.debug(f"[VISION] Color detection error: {e}")
        return enemies

    def predict_position(self, enemies: List[Dict], dt: float = 0.1) -> List[Dict]:
        predicted = []
        for idx, e in enumerate(enemies):
            if idx < len(self.prev_enemies):
                prev = self.prev_enemies[idx]
                dx = e['x'] - prev['x']
                dy = e['y'] - prev['y']
                predicted_x = e['x'] + dx * dt * 60
                predicted_y = e['y'] + dy * dt * 60
            else:
                predicted_x = e['x']
                predicted_y = e['y']
            predicted.append({**e, 'pred_x': predicted_x, 'pred_y': predicted_y})
        self.prev_enemies = enemies.copy()
        return predicted

# ==================== Chat Learner ====================
class ChatLearner:
    def __init__(self, memory_file="chat_memory.pkl"):
        self.memory_file = memory_file
        self.memory = self.load_memory()

    def load_memory(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "rb") as f:
                    return pickle.load(f)
            except:
                pass
        return []

    def save_memory(self):
        try:
            with open(self.memory_file, "wb") as f:
                pickle.dump(self.memory, f)
        except:
            pass

    def process_chat_message(self, msg):
        msg_lower = msg.lower()
        bad_words = ['fuck', 'shit', 'bitch', 'nigger', 'faggot', 'cunt', 'хуй', 'пизда', 'блядь', 'ебать']
        if any(bad in msg_lower for bad in bad_words):
            return
        if "buy" in msg_lower or "купить" in msg_lower or "покупай" in msg_lower:
            self.memory.append(("buy", msg_lower))
        elif "attack" in msg_lower or "атака" in msg_lower or "стреляй" in msg_lower:
            self.memory.append(("attack", msg_lower))
        elif "sniper" in msg_lower or "снайпер" in msg_lower or "awp" in msg_lower:
            self.memory.append(("sniper", msg_lower))
        elif "defend" in msg_lower or "защита" in msg_lower or "оборон" in msg_lower:
            self.memory.append(("defend", msg_lower))
        elif "rush" in msg_lower or "рвем" in msg_lower or "бежим" in msg_lower:
            self.memory.append(("rush", msg_lower))
        if len(self.memory) > 500:
            self.memory.pop(0)

    def decide_action_from_chat(self):
        if not self.memory:
            return None
        actions = [m[0] for m in self.memory]
        return max(set(actions), key=actions.count)

# ==================== Game Detector ====================
class GameDetector:
    SUPPORTED_GAMES = {
        'cs2.exe': 'CS2',
        'csgo.exe': 'CSGO',
        'hl2.exe': 'CSS',
    }

    @staticmethod
    def detect_game():
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            proc = psutil.Process(pid)
            name = proc.name().lower()
            for exe, gtype in GameDetector.SUPPORTED_GAMES.items():
                if exe.lower() == name:
                    return gtype, hwnd
        except:
            pass
        return None, None

# ==================== Weapon DB ====================
class WeaponDB:
    WEAPONS = {
        'ak47': {'name': 'AK-47', 'damage': 36, 'price': 2700},
        'm4a1': {'name': 'M4A1-S', 'damage': 38, 'price': 3100},
        'awp': {'name': 'AWP', 'damage': 115, 'price': 4750},
        'deagle': {'name': 'Desert Eagle', 'damage': 63, 'price': 700},
    }

    @classmethod
    def get(cls, name: str):
        return cls.WEAPONS.get(name.lower())

# ==================== Main Hybrid Bot ====================
class HybridCSBot:
    def __init__(self, use_yolo=False, yolo_model_path=None):
        self.running = False
        self.paused = False
        self.game_type = None
        self.hwnd = None
        self.capture = None
        self.vision = VisionProcessor(use_yolo=use_yolo, yolo_model_path=yolo_model_path)
        self.chat_learner = ChatLearner()
        self.current_weapon = None
        self.money = 0
        self.round_number = 0
        self.stats = {'frames': 0, 'shots': 0, 'kills': 0}
        self.movement_keys = {'w': False, 'a': False, 's': False, 'd': False}
        self.keyboard_listener = None
        self.bot_thread = None

    def start_keyboard_listener(self):
        if not PYNPUT_OK:
            return
        def on_key_event(key):
            try:
                k = key.char.lower() if hasattr(key, 'char') else str(key)
                if k in self.movement_keys:
                    self.movement_keys[k] = True
            except:
                pass
        def on_release(key):
            try:
                k = key.char.lower() if hasattr(key, 'char') else str(key)
                if k in self.movement_keys:
                    self.movement_keys[k] = False
            except:
                pass
        self.keyboard_listener = pynput_keyboard.Listener(on_press=on_key_event, on_release=on_release)
        self.keyboard_listener.start()

    def detect_and_init(self):
        self.game_type, self.hwnd = GameDetector.detect_game()
        if self.hwnd:
            self.capture = WindowCapture(self.hwnd)
            logger.info(f"[BOT] Detected game: {self.game_type}")
            return True
        return False

    def auto_buy(self):
        if self.money > 4750:
            SendInput.press('4')
            time.sleep(0.1)
            SendInput.press('ENTER')
        elif self.money > 3100:
            SendInput.press('3')
            time.sleep(0.1)
            SendInput.press('ENTER')
        elif self.money > 2700:
            SendInput.press('1')
            time.sleep(0.1)
            SendInput.press('ENTER')
        elif self.money > 700:
            SendInput.press('2')
            time.sleep(0.1)
            SendInput.press('ENTER')

    def follow_chat_advice(self):
        recommendation = self.chat_learner.decide_action_from_chat()
        if recommendation == "buy":
            self.auto_buy()
        elif recommendation == "attack" or recommendation == "rush":
            SendInput.press('w')
            time.sleep(0.05)
            SendInput.press('d')
        elif recommendation == "defend":
            SendInput.press('s')
            time.sleep(0.05)
            SendInput.press('a')
        elif recommendation == "sniper":
            SendInput.press('4')
            time.sleep(0.1)
            SendInput.press('ENTER')

    def choose_map_and_mode(self):
        modes = ["Deathmatch", "ArmsRace", "GunGame", "Casual"]
        maps = ["de_dust2", "de_inferno", "de_mirage", "de_nuke", "de_overpass"]
        selected_mode = random.choice(modes)
        selected_map = random.choice(maps)
        logger.info(f"[BOT] Mode: {selected_mode}, Map: {selected_map}")
        return selected_mode, selected_map

    def simulate_chat_read(self):
        messages = [
            "buy awp pls", "rush a", "defend b", "attack mid",
            "снайпер купи", "рвем через а", "защищаем б"
        ]
        msg = random.choice(messages)
        self.chat_learner.process_chat_message(msg)
        logger.info(f"[CHAT] Learned: {msg}")

    def combat_loop(self):
        logger.info("[BOT] Combat loop started")
        while self.running:
            if self.paused:
                time.sleep(0.05)
                continue

            screen = self.capture.capture() if self.capture else None
            if screen is None:
                time.sleep(0.1)
                continue

            self.stats['frames'] += 1

            enemies = self.vision.detect_enemies(screen)
            enemies = self.vision.predict_position(enemies)

            if enemies:
                enemies.sort(key=lambda e: e.get('distance', 999))
                target = enemies[0]
                pred_x = target.get('pred_x', target['x'])
                pred_y = target.get('pred_y', target['y'])
                dx = pred_x - 960
                dy = pred_y - 540
                SendInput.mouse_move(int(dx * 0.7), int(dy * 0.7))
                SendInput.click()
                self.stats['shots'] += 1
                time.sleep(0.05)
            else:
                if random.random() < 0.02:
                    key = random.choice(['w', 'a', 's', 'd'])
                    SendInput.press(key)
                time.sleep(0.01)

            if self.stats['frames'] % 100 == 0:
                self.simulate_chat_read()
                self.follow_chat_advice()

            if self.stats['frames'] % 500 == 0:
                SendInput.press('r')

    def toggle(self):
        if self.running:
            logger.info("[BOT] Stopping...")
            self.running = False
            if self.keyboard_listener:
                try:
                    self.keyboard_listener.stop()
                except:
                    pass
        else:
            logger.info("[BOT] Starting...")
            if not self.detect_and_init():
                logger.error("[BOT] No CS2/CS:GO found! Start the game first.")
                return
            self.running = True
            self.start_keyboard_listener()
            self.choose_map_and_mode()
            self.bot_thread = threading.Thread(target=self.combat_loop, daemon=True)
            self.bot_thread.start()

# ==================== Run ====================
if __name__ == "__main__":
    print("=" * 60)
    print("  ULTIMATE HYBRID CS BOT v9.0")
    print("  Combines Chat Learning + YOLO Detection")
    print("  F8 - Start/Stop | F - Pause | ESC - Exit")
    print("=" * 60)
    print("\n[INFO] Start CS2/CS:GO first, then press F8\n")

    # Set to True to use YOLO detection (if model available)
    USE_YOLO = False
    YOLO_MODEL_PATH = "./yolov8/best.pt"

    bot = HybridCSBot(use_yolo=USE_YOLO, yolo_model_path=YOLO_MODEL_PATH)

    keyboard.add_hotkey('F8', bot.toggle)
    keyboard.add_hotkey('F', lambda: setattr(bot, 'paused', not bot.paused))

    try:
        keyboard.wait('esc')
    except:
        pass

    bot.running = False
    bot.chat_learner.save_memory()
    logger.info(f"\n[BOT] Stopped. Stats: {bot.stats}")
