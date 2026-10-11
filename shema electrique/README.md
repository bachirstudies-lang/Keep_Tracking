# Schéma électrique — Keep Tracking (rév. C)

Traceur GPS autonome pour deux-roues : GNSS u-blox MAX-M10S, LoRaWAN 868 MHz (STM32WLE5CCU6),
batterie Li-ion 1S + récupération d'énergie piézoélectrique (LTC3588-1).

## Ouvrir le projet

Ouvrir `keeptracker.kicad_pro` avec **KiCad 9** (bibliothèques projet incluses : `keeptracker.kicad_sym`,
`keeptracker.pretty`).

Le schéma est généré par script — ne pas modifier `keeptracker.kicad_sch` à la main :

```bash
python generate_schematic.py keeptracker.kicad_sch
```

## Contenu

| Fichier | Rôle |
|---|---|
| `keeptracker.kicad_sch` / `.kicad_pro` | Schéma et projet KiCad (classes de nets 50 Ω incluses) |
| `keeptracker_schematic.pdf` / `.png` | Schéma imprimable |
| `keeptracker_bom.csv` | Nomenclature (références, empreintes, MPN) |
| `keeptracker.net` | Netlist |
| `keeptracker_erc.rpt` | Rapport ERC : 0 erreur, 0 avertissement |
| `keeptracker.pretty/` | Empreintes projet : TPS22916 (DSBGA-4 YFP), antenne Abracon ACAG1204-868-T |

## Révision C — principales évolutions

- **Brochages vérifiés sur les datasheets constructeur** (STM32WLE5 UFQFPN48, TPS63900, MAX-M10S, LIS2DW12,
  BQ24074, LTC3588, MAX17048…).
- **Charge Li-ion** : ITERM du BQ24074 programmé à 60 mA (fin de charge correcte).
- **Pertes d'énergie réduites** : OR-ing des sources par 2 × LM66100 (blocage du courant inverse),
  équilibrage des supercondensateurs sans fuite (ALD910025), V_BCKP GNSS commuté, pull-ups 100 kΩ côté batterie.
- **Impédances maîtrisées** : lignes RF 50 Ω (CPWG 0,26 / 0,20 mm sur empilage JLC04161H-7628),
  couplage TCXO 220 Ω + 10 pF, accord d'antenne en Pi.
- **Front-end LoRa discret** : réseau d'adaptation repris de la carte Olimex BB-STM32WL rév. D1 (même MCU),
  switch SPDT XA17-G4K — **accord final à valider au VNA sur le PCB**.

## Points ouverts avant routage

- Choisir l'antenne GNSS (AE2) et créer son empreinte.
- Confirmer chez le distributeur les références de condensateurs RF ajoutées (2,4 pF et 3,0 pF, ±0,25 pF).
