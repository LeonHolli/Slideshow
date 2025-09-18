# Slideshow
Als Container in Docker stellt er eine Weboberfläche zur verfügung Auf der man .zip Datein mit Bildern Hochladen kann.
Diese werden in der History gespeichert und können als Diashow abgespielt werden.

# Deploy Container
Bei Portainer als git Repo:
- Local container -> Stacks -> Add stack
- Repository auswählen
- Bei URL: https://github.com/LeonHolli/Slideshow.git
- Deploy Stack
- Website ist nun erreichbar unter http://[SERVERADRESSE]:8080

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
- In die geöffnete Datei:
  ```
  [Desktop Entry]
  Type=Application
  Name=TouchGUI
  Exec=chromium-browser --noerrdialogs --kiosk http://192.168.2.122:8080/ --incognito --disable-restore-session-state
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
