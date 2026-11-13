#define AppName "Xiaobai Bot"
[Setup]
AppName={#AppName}
AppVersion=0.1.0
AppPublisher=TechABJ / 理工阿白菌
DefaultDirName={autopf}\XiaobaiBot
DefaultGroupName=Xiaobai Bot
LicenseFile=..\LICENSE
OutputDir=..\dist
OutputBaseFilename=XiaobaiBot-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
[Files]
Source: "..\dist\XiaobaiBot.exe"; DestDir: "{app}"
Source: "..\LICENSE"; DestDir: "{app}"
Source: "..\NOTICE"; DestDir: "{app}"
[Icons]
Name: "{group}\Xiaobai Bot"; Filename: "{app}\XiaobaiBot.exe"
[Run]
Filename: "{app}\XiaobaiBot.exe"; Description: "Open Xiaobai Bot"; Flags: postinstall nowait skipifsilent
