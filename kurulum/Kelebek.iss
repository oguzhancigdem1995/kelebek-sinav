; Kelebek Sınav Dağıtımı - Inno Setup betiği (kurulum sihirbazı)
[Setup]
AppId={{6E4B1C52-8A57-4C0D-9D55-0A1B2C3D4E5F}
AppName=Kelebek
AppVersion=2.0
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
Source: "MicrosoftEdgeWebview2Setup.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall; Check: WebView2Gerekli
Source: "..\dist\Kelebek\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion createallsubdirs

[Icons]
Name: "{autoprograms}\Kelebek"; Filename: "{app}\Kelebek.exe"
Name: "{autodesktop}\Kelebek"; Filename: "{app}\Kelebek.exe"; Tasks: desktopicon

[Run]
Filename: "{tmp}\MicrosoftEdgeWebview2Setup.exe"; Parameters: "/silent /install"; StatusMsg: "Microsoft Edge WebView2 bileşeni kuruluyor..."; Flags: waituntilterminated; Check: WebView2Gerekli
Filename: "{app}\Kelebek.exe"; Description: "Programı şimdi başlat"; Flags: nowait postinstall skipifsilent

[Code]
function WebView2Var: Boolean;
var s: String;
begin
  Result := RegQueryStringValue(HKLM, 'SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', s) and (s <> '') and (s <> '0.0.0.0');
  if not Result then
    Result := RegQueryStringValue(HKCU, 'Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', s) and (s <> '') and (s <> '0.0.0.0');
end;

function WebView2Gerekli: Boolean;
begin
  Result := not WebView2Var;
end;
