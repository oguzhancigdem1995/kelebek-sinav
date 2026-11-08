@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [1/3] Gerekli paketler kuruluyor...
python -m pip install -r requirements.txt pyinstaller || goto hata
echo [2/3] Uygulama derleniyor...
python -m PyInstaller --noconfirm --windowed --name KelebekSinav --collect-all pdfplumber --collect-all pdfminer --collect-all reportlab --collect-all python_calamine --add-data "fonts;fonts" kelebek_baslat.py || goto hata
set ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe
if not exist "%ISCC%" set ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe
if not exist "%ISCC%" (
  echo Inno Setup bulunamadi. jrsoftware.org adresinden Inno Setup 6 kurup bu dosyayi yeniden calistirin.
  echo Simdilik programi dist\KelebekSinav\KelebekSinav.exe ile acabilirsiniz.
  pause
  exit /b 1
)
echo [3/3] Kurulum sihirbazi olusturuluyor...
"%ISCC%" kurulum\KelebekSinav.iss || goto hata
echo Bitti: cikti\KelebekSinav_Kurulum.exe
pause
exit /b 0
:hata
echo Bir hata olustu.
pause
exit /b 1
