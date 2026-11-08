; Kelebek Sınav Dağıtımı - Inno Setup betiği (kurulum sihirbazı)
[Setup]
AppId={{6E4B1C52-8A57-4C0D-9D55-0A1B2C3D4E5F}
AppName=Kelebek Sınav Dağıtımı
AppVersion=1.1
AppPublisher=Kelebek
DefaultDirName={autopf}\KelebekSinav
DefaultGroupName=Kelebek Sınav Dağıtımı
DisableProgramGroupPage=yes
OutputDir=..\cikti
OutputBaseFilename=KelebekSinav_Kurulum
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\KelebekSinav.exe

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaüstüne kısayol oluştur"; GroupDescription: "Ek görevler:"

[Files]
Source: "..\dist\KelebekSinav\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion createallsubdirs

[Icons]
Name: "{autoprograms}\Kelebek Sınav Dağıtımı"; Filename: "{app}\KelebekSinav.exe"
Name: "{autodesktop}\Kelebek Sınav Dağıtımı"; Filename: "{app}\KelebekSinav.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\KelebekSinav.exe"; Description: "Programı şimdi başlat"; Flags: nowait postinstall skipifsilent
