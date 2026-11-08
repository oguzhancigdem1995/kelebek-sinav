; Kelebek Sınav Dağıtımı - Inno Setup betiği (kurulum sihirbazı)
[Setup]
AppId={{6E4B1C52-8A57-4C0D-9D55-0A1B2C3D4E5F}
AppName=Kelebek
AppVersion=1.2
AppPublisher=Kelebek
DefaultDirName={autopf}\Kelebek
DefaultGroupName=Kelebek
DisableProgramGroupPage=yes
OutputDir=..\cikti
OutputBaseFilename=Kelebek_Kurulum
SetupIconFile=..\assets\kelebek.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\Kelebek.exe

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaüstüne kısayol oluştur"; GroupDescription: "Ek görevler:"

[Files]
Source: "..\dist\Kelebek\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion createallsubdirs

[Icons]
Name: "{autoprograms}\Kelebek"; Filename: "{app}\Kelebek.exe"
Name: "{autodesktop}\Kelebek"; Filename: "{app}\Kelebek.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Kelebek.exe"; Description: "Programı şimdi başlat"; Flags: nowait postinstall skipifsilent
