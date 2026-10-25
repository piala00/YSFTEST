# Échanges entre agences hors ligne et consolidation au siège

Chaque agence (gare) travaille **seule**, sur son propre ordinateur serveur, même sans Internet ni électricité
fiable. Les données circulent par **fichiers** (.erpx) envoyés avec les moyens du moment : **WhatsApp, Telegram**,
courriel, clé USB. Le **siège** reçoit les fichiers de toutes les agences et **consolide la comptabilité**.

Conception : `SPEC_ECHANGES_AGENCES.md` (skill `erp-ohada-retour-revue-conditionnements-consolidation`), mise en
œuvre dans `apps/echanges`.

## Mise en place (une fois)

1. **Au siège** : Fichier › *Échanges entre agences* › « Ce poste est le siège ».
2. **Au siège** : déclarer chaque agence (code DLA, nom, ville). Elle reçoit un **n° d'ordre** qui donne son compte
   de liaison **185NN**, le même dans tous les dossiers (18501 le siège, 18502 la première agence…).
3. **Au siège** : créer les gares (en indiquant leur agence), lignes, tarifs, véhicules et chauffeurs.
4. **Au siège** : « Fichier d'installation » de l'agence. Ce fichier contient la **clé secrète** de l'agence : le
   remettre **en main propre** ou par message privé, jamais dans un groupe.
5. **Dans l'agence** (après `1-INSTALLER.bat`, activité Transport) : Fichier › *Échanges entre agences* ›
   « Installer cette agence » avec ce fichier. L'agence reçoit les gares, lignes, tarifs, véhicules et agences.

## Au quotidien

| Qui | Quand | Quoi |
|---|---|---|
| Agence | à chaque départ de car, et en fin de journée | « Préparer le fichier à envoyer » → envoyer le fichier au siège par WhatsApp/Telegram (en document) |
| Siège | à réception | « Importer les fichiers reçus » (plusieurs à la fois, dans n'importe quel ordre) |
| Siège | après import | « Préparer le fichier » pour chaque agence → l'envoyer |
| Agence | à réception | importer le fichier du siège : nouveaux tarifs, colis à remettre, remises faites ailleurs |

Un fichier importé deux fois ne fait rien de plus. Un fichier modifié, abîmé ou destiné à un autre site est refusé
avec un message clair. Un fichier manquant est signalé (« faits n° 12 à 15 pas encore reçus : demandez le renvoi »).

## Ce qui circule

| Fait | Agence → siège | Siège → agences |
|---|---|---|
| Écritures comptables validées | oui (consolidation) | non |
| Billets, dépenses de véhicules | oui (états consolidés) | non |
| Départs, colis, courriers, fret | oui | à l'agence de départ et à l'agence d'arrivée |
| Remise d'un colis, arrivée d'un car | oui | à l'agence d'expédition |
| Agences, gares, lignes, tarifs, véhicules, chauffeurs | oui (si créés en agence) | à toutes les agences |

Le siège ne refait jamais une opération : il reprend les écritures **telles que l'agence les a passées**, dans un
journal propre à l'agence (CA-DLA, VT-DLA…), avec la section analytique de la gare ou de l'agence.

## Colis entre deux agences

1. Douala enregistre le colis (port payé ou dû, contre-remboursement éventuel) et le charge sur le car.
2. Le fichier de Douala part au siège, qui transmet le colis à Yaoundé.
3. À l'arrivée du car, Yaoundé constate l'arrivée et **remet le colis contre le code de retrait** ; elle encaisse le
   port dû (son produit) et le contre-remboursement, **dû à Douala** : crédit du compte de liaison de Douala (185 Douala).
4. Douala apprend la remise par le siège et **reverse** le contre-remboursement à l'expéditeur : débit du compte de
   liaison de Yaoundé (185 Yaoundé).
5. Au siège, les comptes de liaison se compensent (total des 185 = 0) ; la caisse et les produits sont exacts.

Seule l'agence qui a créé un départ, un billet ou un colis peut le modifier ; l'agence d'arrivée peut seulement
constater l'arrivée et remettre l'envoi.

## Sécurité

- Chaque agence a sa **clé** (connue d'elle et du siège) ; chaque fichier est signé (HMAC-SHA256 sur le manifeste,
  empreintes SHA-256 des données). Un fichier signé n'est **pas chiffré** : il circule par des canaux de la société.
- Contenu limité à trois fichiers (manifest.json, events.jsonl, auth.json) ; tout autre contenu, chemin ou taille
  anormale est refusé. Aucun code, SQL ou sauvegarde n'est jamais importé par ce moyen.

## Commande (automatisation, Claude Code sur le poste)

```
python manage.py echanges siege --code SIEGE --nom "Siège"
python manage.py echanges agence --code DLA --nom "Agence de Douala" --ville Douala
python manage.py echanges installation --agence DLA --dossier D:\ECHANGES
python manage.py echanges installer D:\ECHANGES\ERP-INSTALLATION-SIEGE-vers-DLA-….erpx
python manage.py echanges exporter --dossier D:\ECHANGES            (au siège : un fichier par agence)
python manage.py echanges importer D:\ECHANGES\*.erpx
python manage.py echanges etat
```

## Essai

`python manage.py test apps.echanges` : trois **bases séparées** (siège, Douala, Yaoundé) qui ne communiquent que par
fichiers. Le scénario couvre l'installation des agences, la vente de billets, un colis en port dû avec
contre-remboursement, son relais, sa remise à Yaoundé, le reversement à Douala, la consolidation (liaisons à 0), un rejeu
sans effet et un fichier altéré refusé. Le scénario se lance aussi à la main : `python -m apps.echanges.scenario DOSSIER`.

## Reste à faire

- **Envoi automatique** quand Internet est disponible (robot Telegram ou dépôt HTTPS) ; aujourd'hui, l'envoi est manuel.
- **Transmission directe d'agence à agence** (sans attendre le siège) pour les colis, si le car arrive avant le fichier ;
  en attendant, l'agence d'arrivée attend le fichier du siège pour remettre l'envoi.
- **Gestion commerciale** (factures, règlements, stocks entre agences) : les écritures remontent déjà ; les pièces et
  mouvements de stock suivront avec les transferts entre dépôts.
- **États consolidés** dédiés au siège (balance par agence, fraîcheur des données sur chaque état).
