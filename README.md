# Keep_Tracking
Keep Tracking : traceur GPS discret pour motos et scooters, avec récupération d'énergie par vibrations piézoélectriques, alerte antivol par LoRaWAN et application mobile. Projet INSA Centre Val de Loire 2026-2027.
# Keep Tracking : traceur GPS pour deux-roues

Projet INSA Centre Val de Loire, année 2026-2027, encadré par M. Duclos.

## Équipe

| Membre | Responsabilité |
|---|---|
| Alae | Analyse fonctionnelle et intégration |
| Bachir | Hardware et firmware |
| Yassine | Serveur et interface |
| Nidal | Safety case (QHSE) |
| Wissal | Fiabilité FIDES |

## 1. Contexte et problème

Les vols de motos et de scooters augmentent, et la majorité des deux-roues volés ne seraient jamais retrouvés (chiffre à sourcer). Les traceurs existants (Monimoto, Invoxia, GeoRide, PAJ) imposent un abonnement, une batterie à recharger ou à remplacer, ou un branchement sur la batterie de la moto.

## 2. Objectif

Concevoir un traceur GPS pour deux-roues qui soit :

- discret, pour ne pas être repéré par un voleur ;
- autonome en énergie, avec une récupération par vibrations qui prolonge l'autonomie de la batterie interne ;
- simple à installer, sans câblage sur la moto ;
- vendu environ 300 DH (environ 28 €), sans abonnement.

## 3. Solution proposée

Une carte électronique qui dort presque tout le temps. Quand la moto bouge, l'accéléromètre réveille la carte, qui prend un fix GPS et envoie une trame par LoRaWAN. Trois types de trames :

- **START** : début de mouvement
- **STOP** : arrêt, avec la dernière position
- **HEARTBEAT** : signe de vie toutes les 6 à 12 heures

Le propriétaire reçoit une alerte sur son téléphone et consulte la position dans l'application.

## 4. Marché et positionnement

- Cible initiale : les motards de Salé, Kénitra et Rabat.
- Cible secondaire : fabricants de motos installés au Maroc (intégration en série).
- Positionnement : seul acteur « prix bas, sans abonnement » sur la cartographie de l'étude de marché.
- Chiffres de marché : mondiaux (environ 4 Md$ en 2025, croissance de 12 à 17 % par an). Aucune donnée marocaine n'a encore été recherchée.

## 5. Modèle d'entreprise

SARL soumise à l'IS, basée à Kénitra. Prix visé : 300 DH, sans abonnement. Le coût réel de production, de distribution et d'infrastructure reste à chiffrer.

## 6. Architecture technique

### Hardware

| Fonction | Composant proposé |
|---|---|
| MCU et radio LoRa | STM32WLE5 |
| GNSS | u-blox MAX-M10S |
| Détection de mouvement | LIS2DW12 |
| Récupération piézo | LTC3588-1 et supercondensateur |
| Alimentation | Batterie Li-ion 2000 mAh, BQ24074, TPS63900 |
| Autres | Jauge MAX17048, protection batterie, USB-C |

Principe énergétique : le piézo n'est jamais branché directement sur la batterie. Son énergie passe par une protection, un redressement et un supercondensateur, puis soulage la batterie.

### Firmware

Machine à états : veille, mouvement, fix GPS, envoi, veille. Le GNSS est coupé hors acquisition et le MCU n'est réveillé que par l'accéléromètre.

### Serveur

Carte, passerelle LoRaWAN, network server (ChirpStack ou The Things Stack), broker MQTT, API backend, base PostgreSQL/PostGIS, notifications (push, SMS, e-mail). Fonctions : authentification, association carte / moto / propriétaire, décodage des trames, historique, règles d'alerte.

### Interface

Application mobile : carte avec la dernière position, mode garé / roulage, alerte push, historique des trajets, état de la batterie.

## 7. Analyse fonctionnelle (Alae)

- Besoin : le motard veut retrouver sa moto ou être alerté en cas de vol.
- Fonctions principales : détecter un déplacement anormal, localiser, alerter, afficher.
- Fonctions contraintes : discrétion, autonomie, résistance aux vibrations, à l'eau et à la chaleur, coût de 300 DH, conformité radio et données.
- Livrables : bête à cornes, pieuvre, cahier des charges chiffré, FAST.

## 8. Sécurité (Nidal) et fiabilité (Wissal)

**Safety case** : batterie Li-ion (surcharge, emballement thermique), haute tension du piézo, supercondensateur, environnement moto, défaillances fonctionnelles (pas d'alerte, fausse alerte, pas de réseau), cybersécurité et vie privée, conformité (radio 868 MHz, CEM, transport de la batterie).

**Fiabilité FIDES** : profil de mission de la moto, taux de défaillance de chaque composant de la BOM, points faibles et mesures correctives.

## 9. Répartition détaillée des tâches

### Alae : analyse fonctionnelle et intégration
- [ ] Bête à cornes
- [ ] Diagramme pieuvre
- [ ] Fonctions principales et contraintes
- [ ] Cahier des charges chiffré
- [ ] FAST
- [ ] Intégration des tests des trois blocs
- [ ] Dossier final et soutenance

### Bachir : hardware et firmware
- [ ] Mesure du piézo sur une moto
- [ ] Schéma et routage du PCB
- [ ] Budget énergétique et coût de la carte
- [ ] Prototype et tests
- [ ] Boîtier discret
- [ ] Firmware (veille, fix GPS, trames START / STOP / HEARTBEAT)

### Yassine : serveur et interface
- [ ] Réception et décodage des trames LoRaWAN
- [ ] Base de données et API
- [ ] Règles d'alerte et notifications
- [ ] Sécurité des échanges et des données
- [ ] Application mobile (carte, historique, batterie)
- [ ] Mode garé / roulage

### Nidal : safety case
- [ ] Identification et évaluation des dangers
- [ ] AMDEC
- [ ] Mesures de maîtrise des risques
- [ ] Conformité (radio, CEM, données, transport batterie)
- [ ] Plan de tests et preuves

### Wissal : fiabilité FIDES
- [ ] Profil de mission
- [ ] Taux de défaillance par composant
- [ ] Points faibles et mesures
- [ ] Synthèse pour le dossier

## 10. Points ouverts

1. **Transmission** : le rapport marché parle de LTE-M/2G, le rapport matériel de LoRaWAN (choix retenu ici). À vérifier : couverture au Maroc, réglementation de la bande 863-870 MHz, financement des passerelles.
2. **Recharge par vibration** : une recharge significative est peu probable sans mesures. À prouver sur prototype avant de l'afficher comme argument commercial.
3. **Prix de 300 DH** : à confronter au coût de production à 100 et 1000 unités.
4. **Mode garé** : la carte n'a pas de Bluetooth et ne distingue pas le propriétaire d'un voleur. À décider tôt (firmware, serveur, application).
5. **Temps réel ou événements** : le design actuel envoie des événements, pas un suivi continu.
6. **Marché marocain** : nombre de motos, vols, concurrents locaux, prix acceptable.
7. **Définition d'« invisible »** : taille, boîtier, emplacement.

## 11. Étapes

1. Valider le choix de transmission et rédiger le cahier des charges.
2. Mesurer le piézo et calculer le budget énergétique.
3. Concevoir le schéma et le PCB, puis réaliser un prototype.
4. Développer en parallèle le firmware, le serveur et l'application (MVP).
5. Mener l'analyse de risques, la fiabilité FIDES et les tests.
6. Intégrer, tester sur moto et préparer le dossier final.
