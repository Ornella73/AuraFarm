# AuraFarm — Cadre des Hypothèses & Limites Scientifiques (ASSUMPTIONS.md)

Ce document répertorie l'ensemble des hypothèses de modélisation, règles de décision, calibrations agronomiques et limites techniques du MVP AuraFarm. Conformément aux principes de transparence du projet, aucune estimation n'est présentée comme une certitude absolue aux producteurs ou aux agents.

---

## 1. Climatologie et Régimes Pluviométriques du Togo

### 1.1 Zonage Agro-écologique
Le Togo est divisé en deux grands régimes pluviométriques :
* **Régime Bimodal (Sud - Régions Maritime et Plateaux)** :
  * Deux saisons des pluies :
    * Grande saison : mi-mars à mi-juillet.
    * Petite saison : septembre à mi-novembre.
  * Période de transition sèche : fin juillet à août.
* **Régime Unimodal (Nord - Régions Centrale, Kara et Savanes)** :
  * Une seule saison des pluies continue : de mai/juin à octobre.
  * Période sèche marquée : novembre à avril (harmattan).

### 1.2 Règle de Détection du Début de Saison (« Critère Sivakumar / AGRHYMET adapté »)
* **Critère d'alerte SEMER (par défaut pour le MVP)** :
  * Cumul de précipitations $\ge 20\text{ mm}$ sur 3 jours consécutifs après la date plancher de la zone.
  * Absence de séquence sèche supérieure à 7 jours consécutifs dans les 30 jours suivants (estimée via prévision 7–14 jours + climatologie locale).
* **Faux départ de saison** :
  * Pluie isolée $\ge 15\text{ mm}$ suivie immédiatement d'une prévision de séquence sèche $\ge 7\text{ jours}$.
  * Statut émis : `ATTENDRE` ou `RISQUE` avec conseil explicite de ne pas semer prématurément.

---

## 2. Pédologie et Rétention en Eau des Sols

Les profils de sols sont issus des cartes SoilGrids (ISRIC 250m) et iSDAsoil (30m) pour l'Afrique de l'Ouest :
* **Sols ferrallitiques (« Terres de barre » - Région Maritime)** :
  * Texture sablo-argileuse en surface, argileuse en profondeur.
  * Capacité de rétention d'eau moyenne à bonne (100–130 mm/m).
  * Risque : battance et ruissellement lors de fortes averses soudaines.
* **Sols ferrugineux tropicaux (Plateaux, Centrale, Kara)** :
  * Drainage rapide, teneur variable en gravillons/concrétions.
  * Rétention modérée (70–100 mm/m).
* **Sols hydro-morphes et vertiques (Plaines des Savanes, berges de l'Oti et du Mono)** :
  * Forte teneur en argile, rétention élevée, mais risque d'engorgement/asphyxie racinaire en cas d'excès d'eau.

*Note de transparence* : En l'absence d'analyse de sol parcellaire au niveau du producteur, le modèle prend par défaut la médiane du canton/village issue de SoilGrids.

---

## 3. Paramètres Variétaux (Catalogue ITRA / IITA / ICRISAT)

Toutes les variétés modélisées existent dans les réseaux semenciers togolais officiels et coopératives de base. Aucune variété fictive ou génétiquement modifiée n'est prise en compte.

| Espèce | Variété | Cycle (jours) | Besoin hydrique (mm) | Sensibilité stress floraison | Tolérance sécheresse | Source calibration |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Maïs** | `TZEE-W-SR` | 80–85 | 350–450 | Élevée (jour 45–55) | Très bonne (extra-précoce) | ITRA / IITA |
| **Maïs** | `Sotubaka` | 95–105 | 450–550 | Moyenne-Élevée | Bonne (intermédiaire) | ITRA |
| **Maïs** | `TZB-SR` | 110–120 | 550–700 | Élevée | Modérée (nécessite longue saison) | ITRA / IITA |
| **Sorgho** | `Sorvato 28` | 105–115 | 350–450 | Faible à Moyenne | Excellente | ITRA |
| **Sorgho** | `Chokwe` | 120–135 | 400–500 | Modérée (photopériodique) | Très bonne | ITRA / ICRISAT |
| **Niébé** | `TVx 3236` | 65–75 | 250–350 | Faible | Excellente (racines profondes) | ITRA / IITA |
| **Niébé** | `IT99K-573-1-1` | 60–70 | 220–300 | Faible | Extra-résistante | ITRA / IITA |

*Règle stricte d'adéquation* : Une variété n'est jamais recommandée si les semenciers de la zone sont en rupture de stock déclarée (`disponibilite_locale = False`).

---

## 4. Règle de Sécurité : Obsolescence des Données (`Data Freshness Guard`)

* Latence nominale CHIRPS satellite : 24 à 48 h.
* Latence nominale Prévisions ECMWF/GFS : 12 h.
* **RÈGLE CRITIQUE DE SAUVEGARDE** :
  * Si la dernière observation de pluie disponible date de **plus de 48 heures** ET qu'aucune observation terrain villageoise n'a été saisie dans les dernières 24 heures :
  * Le système **INTERDIT FORMELLEMENT** l'émission de la recommandation `SEMER`.
  * Le système force la bascule vers le statut : `ATTENDRE_CONSULTER_AGENT`.
  * Le message transmis sur tous les canaux (IVR, USSD, SMS) devient :
    > *« Attention : Données météo locales en cours d’actualisation. Ne prenez pas de risque, consultez votre agent d'encadrement ICAT/ITRA avant de semer. »*

---

## 5. Niveaux de Confiance et Gestion de l'Incertitude

Chaque conseil diffusé est qualifié par l'un des trois niveaux :
1. **SÛR (Confiance Forte)** : Concordance totale pluie observée + prévisions 7j + historique local.
2. **ASSEZ SÛR (Confiance Modérée)** : Légère divergence entre modèles de prévision ou sol à rétention limite.
3. **INCERTAIN (Confiance Faible)** : Transition saisonnière hésitante, risque élevé de sécheresse post-semis. Prescription d'attendre ou de validation par le relais humain.

---

## 6. Protection des Données Personnelles (Loi Togolaise n° 2019-014)

1. **Minimisation** : Seuls sont collectés : numéro de téléphone (MSISDN), village/canton de rattachement, langue préférée, culture suivie. Aucun nom de famille n'est requis.
2. **Pseudonymisation & Hachage** : Les numéros de téléphone ne sont jamais consignés en clair dans les logs d'application (remplacés par un hash HMAC SHA-256 tronqué).
3. **Consentement explicite (Opt-in)** :
   * Lors du premier contact vocal : « Tapez 1 pour recevoir les alertes gratuites d’AuraFarm ».
   * Sur l’USSD : acceptation préalable des conditions de service.
4. **Droit d'accès et de retrait** : Tout producteur peut se désinscrire gratuitement à tout moment via le menu USSD (« Option 9 : Se désinscrire ») ou par simple demande à son agent de vulgarisation.

---

## 7. Modélisation Biophysique & Bilan Hydrique (Steps E2, E3, E7)

### 7.1 Évapotranspiration de Référence Hargreaves-Samani (1985)
Adaptée aux zones tropicales sans station météo complète :
$$ET_0 = 0.0023 \cdot R_a \cdot (T_{\text{mean}} + 17.8) \cdot \sqrt{T_{\text{max}} - T_{\text{min}}}$$
Où :
* $R_a$ est le rayonnement solaire extraterrestre journalier calculé selon la latitude du village (ex: $6.13^\circ\text{N}$ pour le Littoral à $10.86^\circ\text{N}$ pour Dapaong).
* $T_{\text{max}}$, $T_{\text{min}}$, $T_{\text{mean}}$ en degrés Celsius issus d'Open-Meteo / ECMWF ou des générateurs stochastiques calibrés.

### 7.2 Réservoir en Eau Facilement Utilisable (RAW / TAW)
* **TAW (Total Available Water)** : $TAW = \text{TAW}_{\text{spécifique}} \times \text{profondeur enracinement (m)}$
  * Terres de barre du Sud : $\approx 110\text{ mm/m}$ sur $0.60\text{ m} \to 66\text{ mm}$.
  * Sols ferrugineux du Nord : $\approx 85\text{ mm/m}$ sur $0.50\text{ m} \to 42.5\text{ mm}$.
* **RAW (Readily Available Water)** :
  $$RAW = p \cdot TAW$$
  Avec $p = 0.55$ pour le maïs et le sorgho au stade germination/levée.
* **Bilan Journalier du Stock ($S_t$)** :
  $$S_t = \min(TAW, \max(0, S_{t-1} + P_t - K_c \cdot ET_{0,t}))$$
  Avec $K_c = 0.40$ au stade initial des semis (FAO-56).
* Si $S_t < RAW \times 0.5$, un stress hydrique de levée est détecté.

### 7.3 Simulation Post-Semis sur 21 Jours & Alerte Faux Départ
* Tout avis `SEMER` simule les 21 jours suivant la date candidate.
* Si le modèle détecte une séquence continue sans pluie $\ge 8\text{ jours}$ faisant chuter le stock sous $0.20 \times RAW$, le risque de faux départ passe à `RISQUE` et le semis est déconseillé.

---

## 8. Spécifications Télécoms & Pipeline Audio 2G (Steps E6, E9, E10)

### 8.1 Contrainte GSM 03.38 pour l'USSD
* Tout écran USSD doit respecter rigoureusement la limite maximale de **160 caractères** dans l'alphabet GSM 03.38 7-bit standard.
* Aucun caractère spécial hors table (remplacement automatique des lettres accentuées ou caractères Unicode non reconnus par les combinés 2G d'entrée de gamme).

### 8.2 Spécifications Voix Terroir 2G
* **Échantillonnage** : 8 000 Hz / 16 000 Hz, mono PCM 16-bit.
* **Filtre Téléphonique** : Passe-bande Butterworth 300 Hz – 3 400 Hz simulant les codecs vocaux GSM FR/AMR.
* **Normalisation de Crête** : -1.0 dBFS pour éliminer la saturation sur petits haut-parleurs.
* **Suppression des Silences** : Détection de seuil d'énergie (< -40 dBFS) en début et fin d'enregistrement.
* **Validation Locuteurs Natifs** : Protocole d'évaluation humaine en 4 critères (/5) sur `/audio-eval` (clarté, naturel, authenticité d'accent, taux de compréhension immédiate).


