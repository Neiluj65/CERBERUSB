# Mise en service — du Raspberry Pi nu à la borne opérationnelle

Neuf étapes, dans l'ordre, pour flasher, configurer et démarrer la borne de
décontamination USB sur le Raspberry Pi 3. Suivez-les une par une — la
plupart des blocages viennent d'une étape sautée, pas d'un bug de code.

Matériel/config visés : Raspberry Pi 3, Raspberry Pi OS Lite 64-bit, écran
tactile 3,5″, borne air-gapée après installation.

## 1. Préparer la carte SD

Flashez **Raspberry Pi OS Lite (64-bit)** avec le Raspberry Pi Imager. Avant
de lancer le flash, ouvrez le menu des options avancées (icône ⚙️) et
préconfigurez :

- un hostname (ex. `borne-usb`)
- SSH activé
- un utilisateur et mot de passe
- le Wi-Fi, **temporairement**, uniquement pour l'installation

> ⚠️ Le Wi-Fi n'est là que pour installer les paquets. Coupez-le une fois la
> borne opérationnelle — c'est une contrainte de sécurité du projet, pas une
> option.

## 2. Se connecter au Pi

Depuis votre PC, une fois le Pi démarré et sur le même réseau :

```bash
ssh <user>@borne-usb.local
```

## 3. Installer les dépendances système

Mise à jour du système puis paquets nécessaires à Python, Kivy et ClamAV :

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y python3-pip python3-venv git clamav clamav-freshclam \
    libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
    libmtdev-dev xclip xsel dosfstools
```

Les librairies SDL2 sont requises pour que Kivy s'installe et s'affiche
correctement sur le Pi.

## 4. Mettre à jour la base virale (premier import)

Avant de couper le réseau définitivement, il faut au moins une base virale
à jour :

```bash
sudo systemctl stop clamav-freshclam
sudo freshclam
```

## 5. Transférer le code sur le Pi

Depuis votre PC :

```bash
scp -r "c:\Users\B86885\borne-usb" <user>@borne-usb.local:/home/<user>/borne-usb
```

Alternative si le code est poussé sur un dépôt distant : `git clone`
directement sur le Pi.

## 6. Installer le projet

```bash
sudo mkdir -p /opt/borne-usb
sudo cp -r ~/borne-usb/* /opt/borne-usb/
cd /opt/borne-usb
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

## 7. Premier test à la main

Avant tout service systemd — testez chaque brique séparément, dans l'ordre.

```bash
# 1. la détection USB seule — le test le plus important
sudo ./venv/bin/python3 usb_monitor.py
```

> ✓ Branchez une clé USB : la console doit afficher
> `[INSERTION] UsbDeviceInfo(...)`. Si rien ne s'affiche ici, rien d'autre ne
> fonctionnera — c'est le point de départ à déboguer.

```bash
# 2. le scan seul (device_node vu à l'étape précédente)
sudo ./venv/bin/python3 scanner.py /dev/sda1

# 3. l'application complète
sudo ./venv/bin/python3 main.py
```

L'écran tactile 3,5″ doit afficher l'écran d'accueil bleu foncé « en attente
de clé ».

## 8. Installer les services systemd

Une fois le test manuel concluant, faire tourner la borne et la mise à jour
ClamAV en permanence :

```bash
sudo cp borne-usb.service freshclam-update.service freshclam-update.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl disable clamav-freshclam
sudo systemctl enable --now freshclam-update.timer
sudo systemctl enable --now borne-usb.service
```

## 9. Vérifier les logs

```bash
journalctl -u borne-usb -f
```

À garder ouvert pendant les premiers essais réels avec une clé — c'est ici
que remonteront les erreurs de montage, de scan ou d'affichage.
