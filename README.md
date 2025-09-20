# Slideshow
Als Container in Docker stellt er eine Weboberfläche zur verfügung Auf der man .zip Datein mit Bildern Hochladen kann.
Diese werden in der History gespeichert und können als Diashow abgespielt werden.

# Funktionen
<img width="1916" height="400" alt="Menü" src="https://github.com/user-attachments/assets/af823916-75f5-431b-a3b2-e8d06af9d7fc" />

- Ganz Links die Möglichkeit .zip Datein hochzuladen.
- Hochgeladene .zip Datein werden als Eine Show gespeichert und können umbenannt werden.
  Durch das Klicken auf die Show in Blau, wird die Diashow gestartet.
- Einstellen der Zeit pro Bild.
- Ganz Rechts ist es möglich Kasa Smart Plugs anzusteuern.
  Gibt man die IP Adresse eines Eingerichteten Smart Plugs ein wird dieser
  in der Angegebenen Offline Zeit ausgeschaltet und automatisch wieder eingeschaltet.


# Deploy Container
Bei Portainer als git Repo:
- Local container -> Stacks -> Add stack
- Repository auswählen
- Bei URL: https://github.com/LeonHolli/Slideshow.git
- Deploy Stack
- *ERSETZE DIE SERVERADRESSE*
- Website ist nun erreichbar unter http://[SERVERADRESSE]:9080

# Einrichten eines PI als Diashow Bildschirm
- Raspberry mit Desktop OS
- Chromium installieren (falls nicht vorhanden)
  ```
  sudo apt update
  sudo apt install -y chromium-browser
  ```
- Autostart-Ordner anlegen
  ```
  mkdir -p ~/.config/autostart
  nano ~/.config/autostart/kiosk.desktop
  ```
- In die geöffnete Datei (*ERSETZE DIE SERVERADRESSE*):
  ```
  [Desktop Entry]
  Type=Application
  Name=TouchGUI
  Exec=chromium-browser --noerrdialogs --kiosk http://[SERVERADRESSE]:9080/ --incognito --disable-restore-session-state
  StartupNotify=false
  ```
- Falls Autologin nicht aktiv:
  ```
  sudo raspi-config
  ```
  - 1 System Options -> S5 Boot / Auto Login
  - Console und Desktop Autonlogin auf Yes
  - Beende raspi-config und Neustart
  ```
  sudo reboot
  ```
  - Automatische Login und start in Vollbild Chromium
