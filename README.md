# AuraFarm (Équipe GPS²)

**Système d'aide à la décision agro-climatique pour le Togo — Hackathon « Climat & Innovation » 2026 (Togolaises In Science, Défi 1)**

> *« Cerveau connecté, dernier kilomètre sans internet »*

---

## 🌾 Contexte & Défi

Au Togo, plus de 70% de la production vivrière repose sur une agriculture pluviale soumise à des saisons de plus en plus erratiques. Les petits producteurs font face à deux risques majeurs :
1. **Le faux départ de saison** : semer trop tôt suite à une pluie isolée, conduisant à la perte irréversible des semences lors de la séquence sèche suivante.
2. **Le choix variétal inadapté** : semer une variété dont le cycle ou les besoins hydriques ne correspondent ni au sol local ni à la durée effective de la saison.

### Contraintes Réelles du Terrain (Non Négociables)
* **Aucun internet pour le producteur** : téléphones à touches 2G, pas d'application pour smartphone, pas de navigateur.
* **Analphabétisme & Plurilinguisme** : langues locales dominantes (éwé, kabiyè, mina, français).
* **Téléphones partagés & réseau intermittent**.
* **Gratuité pour le paysan** : appels sortants automatisés (IVR), rappel après « bip » (appel manqué), sessions USSD sans surtaxe.

---

## 🏛️ Architecture : Cerveau Connecté, Dernier Kilomètre 2G

```
+---------------------------------------------------------------------------------+
|                                SERVEUR CLOUD                                    |
|                                                                                 |
|  [ Ingestion Quotidienne ]                                                      |
|   - CHIRPS / IMERG (Pluie)      ---> [ Data Freshness Guard ]                  |
|   - ECMWF / Open-Meteo (Prévisions)     (Règle sécurité si > 48h)              |
|   - SoilGrids / SRTM (Sol/Pente)                                                |
|   - Remontées Pluviomètres Villageois                                           |
|                                         |                                       |
|                                         v                                       |
|  [ Moteur Agronomique & Alertes ]                                               |
|   - Simulation de stress hydrique (AquaCrop-OSPy)                               |
|   - Filtrage disponibilité semencière ITRA locale                               |
|   - Détecteur de faux départ de saison                                          |
|                                         |                                       |
|                                         v                                       |
|  [ Base Pré-calculée Journalière ]                                              |
|   - Fiche par village et culture (latence lecture < 50ms)                       |
+---------------------------------------------------------------------------------+
                                          |
                        +-----------------+-----------------+
                        |                                   |
                        v                                   v
             [ Canaux 2G Producteurs ]             [ Relais & Coopératives ]
        - Appel Vocal Sortant IVR (30-45s)      - Application PWA locale
          (Éwé, Kabiyè, Mina, Français)         - Bulletins hebdomadaires
        - USSD Interactif (*384*228#)             imprimables pour Radios
        - SMS d'alerte / Déclencheur « Bip »      Communautaires
```

---

## 🚀 Démarrage Rapide

### Prérequis
* Python 3.11+ (ou Docker)
* SQLite (inclus) ou PostgreSQL

### Installation
```bash
git clone https://github.com/gps2-aurafarm/aurafarm.git
cd aurafarm

# Créer un environnement virtuel
python -m venv venv
# Linux / macOS
source venv/bin/activate
# Windows
.\venv\Scripts\Activate.ps1

# Installer les dépendances
pip install -r requirements.txt
```

### Lancement du Serveur & du Simulateur
```bash
# Lancer l'API FastAPI et le serveur de diffusion
python -m uvicorn src.api.main:app --reload --port 8000
```
* **Tableau de bord PWA & Supervision LIVE** : `http://localhost:8000/dashboard`
* **Simulateur Téléphone 2G (USSD & Audio)** : `http://localhost:8000/ussd-simulator`
* **Studio d'Évaluation Vocale Terroir** : `http://localhost:8000/audio-eval`
* **Cartographie & Météo des 5 Régions** : `http://localhost:8000/zones-overview`
* **Enregistrement Audio Locutrices** : `http://localhost:8000/audio-recorder`
* **Documentation OpenAPI Interactive** : `http://localhost:8000/docs`
* **Script de Démonstration Jury (3 min)** : Voir [`DEMO_SCRIPT_3MIN.md`](file:///C:/Users/HP/Documents/AURAFARM/DEMO_SCRIPT_3MIN.md)

### Exécution des Tests
```bash
# Exécution complète de la suite de tests (pytest)
python -m pytest tests/ --ignore=tests/e2e -v
```

---

## 📁 Structure du Projet

```
AURAFARM/
├── data/
│   ├── villages_togo.csv        # 12 villages sentinelles sur les 5 régions du Togo
│   ├── varieties_togo.csv       # Variétés maïs, sorgho, niébé homologuées ITRA
│   ├── soil_profiles.json       # Propriétés hydro-pédologiques (SoilGrids)
│   └── audio_phrase_bank.csv    # Banque de phrases modulaires en 4 langues
├── src/
│   ├── core/                    # Modèles, config, hachage HMAC et base SQLite
│   ├── data_ingestion/          # Connecteurs CHIRPS/ECMWF, météo stochastique & profils zones
│   ├── agro_climate/            # Bilan hydrique, Hargreaves-Samani ET0 & simulations What-If
│   ├── crop_models/             # Scoring de résilience variétale (ITRA)
│   ├── alerts/                  # Détecteur de début de saison & risque de faux départ
│   ├── channels/                # Moteurs USSD (*384*228#), IVR, audio 2G & SMS
│   ├── api/                     # Endpoints FastAPI pour webhooks, flux live et PWA
│   └── dashboard/               # Vues HTML/Jinja2, fiches d'audit & bulletins radios
├── static/
│   ├── auracharts.js            # Moteur autonome de graphiques SVG hors-ligne (zéro CDN)
│   └── fiche.css                # Styles des fiches de décision traçables
├── tests/                       # Suite exhaustive de tests unitaires et d'intégration
├── DEMO_SCRIPT_3MIN.md          # Script chronométré pour la présentation au jury
├── ASSUMPTIONS.md               # Cadre complet des hypothèses agro-climatiques
├── LICENSES.md                  # Attribution des données ouvertes
└── README.md
```

---

## 📜 Conformité & Protection des Données (Loi Togolaise 2019-014)
* **Minimisation stricte** : Aucun nom de famille n'est collecté.
* **Pseudonymisation** : Hachage SHA-256 avec sel cryptographique de tous les numéros de téléphone.
* **Consentement libre et éclairé** : Opt-in explicite dès le premier contact.

