"""Kelebek Sınav Dağıtım Programı - başlatıcı. Çalıştırmak için: python kelebek_baslat.py"""
import sys

try:
    from kelebek.arayuz import calistir
except ImportError as e:
    print("Eksik paket:", e)
    print("Kurmak için:  pip install -r requirements.txt")
    input("Kapatmak için Enter'a basın...")
    sys.exit(1)

if __name__ == "__main__":
    calistir()
