# CERBERUSB 🐺🔌

**Borne de décontamination USB** — détection automatique, scan antivirus et
neutralisation des clés USB infectées, sur Raspberry Pi.

Projet réalisé dans le cadre d'un Master Cybersécurité et d'une mission
d'alternance chez Enedis.

---

## Le principe

1. Clé USB branchée → montage automatique en lecture seule (`ro,noexec,nosuid,nodev`)
2. Scan ClamAV du contenu
3. Clé saine → écran vert. Clé infectée → écran rouge avec option de formatage

Aucun fichier de la clé n'est jamais exécuté : le montage est verrouillé en
lecture seule avec `noexec,nosuid,nodev` pendant toute la durée de l'analyse.

## Fonctionnalités

- 🔌 **Détection à chaud** du branchement/débranchement via `pyudev` (udev),
  filtrée pour ne réagir qu'aux périphériques réellement sur bus USB
- 🛡️ **Scan antivirus** avec ClamAV (`clamscan`), base virale mise à jour
  automatiquement (`freshclam`, via un timer systemd quotidien)
- 🔒 **Montage sécurisé** en lecture seule, sans exécution ni privilèges
- 🧹 **Formatage confirmé** de la clé infectée (FAT32), avec re-vérification
  que le périphérique est bien un support USB avant toute action destructive
- 🖥️ **Interface tactile Kivy** en plein écran (mode kiosque), 4 écrans :
  attente, scan en cours, clé saine, clé infectée
- 📝 **Traçabilité** : logs de chaque scan et détection dans `/var/log/borne-usb`
- 🔌 **Air-gap friendly** : conçu pour fonctionner isolé du réseau une fois
  déployé (la mise à jour ClamAV échoue silencieusement sans réseau)

## Stack technique

| Couche          | Choix              | Pourquoi                                        |
|-----------------|--------------------|--------------------------------------------------|
| OS              | Raspberry Pi OS Lite | Pas de bureau superflu, empreinte minimale      |
| Détection USB   | `pyudev`             | Accès direct aux événements udev, léger         |
| Antivirus       | ClamAV               | Open source, base virale maintenue, scriptable  |
| Interface       | Kivy                 | Support tactile natif, léger sur Pi 3            |
| Orchestration   | Python 3 / systemd    | Démarrage automatique, redémarrage en cas de crash |

## Architecture du dépôt

```
borne-usb/
├── main.py                     # orchestration : udev → scan → UI → formatage
├── usb_monitor.py               # détection USB (pyudev)
├── scanner.py                    # montage RO + scan ClamAV
├── formatter.py                  # formatage sécurisé avec confirmation
├── config.py                     # configuration centralisée
├── ui/
│   ├── app.py                    # application Kivy (mode kiosque)
│   └── screens/
│       ├── idle.py                # écran d'attente
│       ├── scanning.py            # écran "scan en cours"
│       ├── clean.py               # écran vert — clé saine
│       └── infected.py            # écran rouge — clé infectée
├── borne-usb.service              # service systemd de l'application
├── freshclam-update.service/.timer # mise à jour quotidienne de la base virale
├── DEPLOY.md                      # procédure de mise en service, pas à pas
└── requirements.txt
```

## Démarrage rapide

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
sudo ./venv/bin/python3 main.py
```

Pour le déploiement complet sur Raspberry Pi (flash de la carte SD,
dépendances système, services systemd), voir **[DEPLOY.md](DEPLOY.md)**.

## Sécurité — contraintes de conception

Ce projet est pensé pour un usage en environnement sensible (poste de
sécurité industrielle) :

- la clé USB n'est **jamais montée en écriture ni en exécution** pendant
  l'analyse
- le formatage **ne peut pas** être déclenché sans confirmation explicite de
  l'utilisateur, et re-vérifie que le périphérique ciblé est bien un support
  USB avant toute opération destructive
- la borne est conçue pour fonctionner **sans connexion réseau permanente**
  (mise à jour de la base virale en tâche planifiée, tolérante à l'absence
  de réseau)
- chaque scan est journalisé pour permettre un audit a posteriori

## Matériel

- Raspberry Pi 3
- Écran tactile 3,5″
- Boîtier imprimé en 3D (conception CAO sous Fusion 360)
