# 🌾 SCRIPT DE DÉMONSTRATION JURY (3 MINUTES CHRONO)
## Projet AuraFarm — Hackathon « Climat & Innovation » 2026
**Équipe GPS² (Togolaises In Science) • "Cerveau connecté, dernier kilomètre sans internet"**

---

### Résumé Visuel du Parcours Démo
| Minute | Phase | Support Écran | Action Clé |
|---|---|---|---|
| **0:00 – 0:45** | Problème & Réalité Paysanne | Diapo / Discours | Évocation des faux départs et contrainte 2G |
| **0:45 – 1:45** | Démonstration 2G Télécom | `/ussd-simulator` & `/audio-eval` | Composition `*384*228#`, Option 1 en < 500 ms, voix terroir 2G |
| **1:45 – 2:30** | Moteur Agro-Climatique & Traçabilité | `/dashboard` (Onglets 1 & 5) | Liaison temps réel LIVE, fiche d'audit, sliders What-If |
| **2:30 – 3:00** | Conformité Légale & Impact | `/dashboard` & architecture | Loi 2019-014 (HMAC-SHA256), partenariat ICAT/ITRA/ANAMET |

---

## ⏱️ 0:00 – 0:45 — L'Urgence & La Réalité Paysanne au Togo

**Présentatrice :**
> « Honorables membres du jury,
> 
> Au Togo, l'agriculture pluviale fait vivre plus de 65 % de la population active. Mais avec le dérèglement climatique, le premier danger d'un producteur de maïs dans la région des Plateaux ou des Savanes n'est pas le manque de travail : c'est le **faux départ de saison**.
> 
> Une première pluie abondante tombe en mars. Le paysan sème tout son capital de semences. Dix jours plus tard, une pause sèche imprévue s'installe : les germes meurent, l'engrais est perdu, et la famille est ruinée pour l'année.
> 
> Pourquoi les applications modernes échouent-elles ? Parce que **85 % des petits producteurs en zone rurale n'ont ni smartphone, ni connexion 4G, ni forfait data dans leur champ**.
> 
> Notre réponse avec **AuraFarm** repose sur un principe radical : **"Cerveau connecté, dernier kilomètre sans internet"** ! »

---

## ⏱️ 0:45 – 1:45 — Le Dernier Kilomètre : USSD & Voix Terroir 2G

**Action à l'écran :** Ouvrir [`/ussd-simulator`](http://localhost:8000/ussd-simulator) en plein écran sur le combiné 2G virtuel.

**Présentatrice :**
> « Voici le téléphone basique à touches d'un producteur de Kovié dans le Zio. Pas d'application à installer, pas de crédit data nécessaire.
> 
> Le producteur compose simplement le code USSD gratuit : **`*384*228#`** et appuie sur Appel. »

*(Cliquer sur le bouton vert **"Appeler"**)*

> « Observez la rapidité : en moins de 300 millisecondes, le menu GSM 03.38 apparaît dans la langue du producteur.
> 
> Nous avons restructuré le menu pour aller à l'essentiel : **Option 1 — Dois-je semer ?** »

*(Taper `1` puis cliquer sur **"Envoyer"**)*

> « L'avis tombe immédiatement : **"SEMER : Humidité du sol suffisante (> 45 mm). Variété recommandée : TZEE-W-Pop 85j."**
> Tout est conforme au strict standard de 160 caractères des réseaux 2G togolais (Togocom / Moov).
> 
> Et pour un producteur analphabète ? Il lui suffit de faire un simple bip manqué gratuit, ou de sélectionner l'Option 6. »

**Action à l'écran :** Ouvrir [`/audio-eval`](http://localhost:8000/audio-eval) ou activer la lecture vocale.

> « Écoutez : le système déclenche un rappel vocal automatique dans sa langue maternelle — en **Éwé**, en **Kabiyè** ou en **Mina** — avec notre filtre exclusif reproduisant le haut-parleur 2G GSM (bande passante 300–3400 Hz, compression 8 kHz) audité par des locuteurs natifs. »

*(Cliquer sur **"Écouter l'Extrait Vocal"** pour faire entendre la consigne)*

---

## ⏱️ 1:45 – 2:30 — Le Cerveau Connecté : Traçabilité & Simulation What-If

**Action à l'écran :** Basculer immédiatement sur l'onglet [`/dashboard`](http://localhost:8000/dashboard).

**Présentatrice :**
> « Pendant que le paysan recevait sa réponse sur son téléphone à touches, que s'est-il passé côté supervision ?
> 
> Regardez le bandeau supérieur **LIVE** : en direct, l'événement télécom USSD que nous venons de composer vient de remonter sur la tour de contrôle des agents ICAT et des coopératives avec mise en surbrillance de la fiche du village !
> 
> Chaque fiche est **100 % traçable** :
> 1. **Entrées vérifiées** : Pluviométrie satellitaire CHIRPS v3 consolidée avec les pluviomètres paysans, température ECMWF et texture de sol SoilGrids.
> 2. **Bilan hydrique journalier** : Calcul physique de l'évapotranspiration Hargreaves-Samani et du réservoir en eau du sol (RAW/TAW).
> 3. **Règle de décision explicite** : Vous voyez exactement le seuil franchi et la probabilité de poche sèche à 21 jours. »

**Action à l'écran :** Cliquer sur l'onglet **« Analyse & Simulations »** (Onglet 5).

> « Mieux encore : nos ingénieurs et agronomes ont accès à un moteur de simulation What-If interactif sans aucune dépendance externe, propulsé par notre moteur vectoriel SVG embarqué.
> 
> Si je simule une baisse de 30 % des précipitations... »

*(Déplacer le slider Précipitations vers la gauche à 0.70x ou cliquer sur le preset **"Faux départ"**)*

> « ... instantanément, les courbes de réserve hydrique, les fenêtres de semis et le diagramme tornado recalculent l'impact agro-climatique en moins de 100 millisecondes ! »

---

## ⏱️ 2:30 – 3:00 — Réglementation, Impact & Déploiement

**Présentatrice :**
> « Pour conclure, AuraFarm n'est pas une simple maquette, c'est une architecture prête pour le passage à l'échelle :
> 
> 1. **Protection stricte des données personnelles** : Conformité totale avec la **Loi Togolaise N° 2019-014**. Aucun numéro de téléphone n'est stocké en clair : nous utilisons une pseudonymisation irréversible HMAC-SHA256 avec sel cryptographique et recueil de consentement obligatoire.
> 2. **Multi-canal inclusif** : USSD 2G, IVR vocal en 4 langues, SMS de secours, et bulletins pour les radios communautaires rurales générés automatiquement.
> 3. **Ancrage institutionnel** : Paramétré sur les 5 régions économiques du Togo, en liaison directe avec l'ICAT pour l'encadrement agricole et l'ITRA pour la résilience variétale.
> 
> AuraFarm transforme la donnée satellite en une décision simple dans la poche de chaque paysan togolais, sans qu'il ait besoin d'un seul mégaoctet d'internet.
> 
> Merci, et nous attendons vos questions ! »

---

## 🎯 Réponses Clés aux Questions Fréquentes du Jury (Q&A)

### Q1 : « Que se passe-t-il si la connexion satellite ou l'API météo tombe en panne ? »
**Réponse :** 
> « AuraFarm applique une politique de résilience stricte à trois niveaux :
> 1. Les fiches du jour sont pré-calculées chaque nuit dans SQLite locale : les canaux USSD et IVR ne font **aucun appel réseau externe en direct**.
> 2. Si l'API satellite est indisponible, le système bascule sur la persistance locale et les relevés des pluviomètres paysans avec un badge visuel orange "Fallback".
> 3. Si les données ont plus de 48 heures, l'alerte de sécurité "PÉRIMÉE" s'enclenche automatiquement pour interdire tout mauvais conseil. »

### Q2 : « Pourquoi avoir développé votre propre moteur de graphiques SVG plutôt qu'une librairie React ou un CDN ? »
**Réponse :** 
> « Dans les bureaux de préfecture de l'ICAT à Dapaong, Kara ou Notsé, l'internet est instable voire absent. AuraFarm fonctionne en **PWA 100 % autonome hors-ligne**. Aucune dépendance externe CDN n'est requise. Notre script `auracharts.js` pèse moins de 15 Ko et s'exécute directement dans le navigateur du conseiller agricole. »

### Q3 : « Comment gérez-vous les coûts télécoms pour le paysan ? »
**Réponse :** 
> « L'accès est **100 % gratuit pour le paysan**. Soit via le numéro vert USSD subventionné dans le cadre des plans d'adaptation climatique nationaux, soit via le mécanisme de bip manqué (missed-call) où notre serveur IVR rappelle immédiatement le producteur. »

