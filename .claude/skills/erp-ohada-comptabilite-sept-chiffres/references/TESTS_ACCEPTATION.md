# Critères d'acceptation — contrôle avant livraison

## Plan de comptes (Commercial et Transport)

- [ ] Nouveau dossier avec comptes `4111000` / `7010000` selon les racines attendues et **exactement sept chiffres** pour les comptes de l'entreprise.
- [ ] Un compte court saisi dans le parcours normal est normalisé correctement (zéros à droite).
- [ ] La migration d'un dossier existant est **désactivée par défaut** (simulation sans écriture).
- [ ] La simulation refuse toute collision (`4111` + `4111000`) sans changement.
- [ ] La simulation/l'application refusent un numéro plus long que sept chiffres et tout numéro non conforme ; aucune mise à jour partielle.
- [ ] Conversion vérifiée sur copie avec sauvegarde : nombre de comptes et de lignes d'écriture inchangé, IDs et liens de comptes inchangés, totaux débit/crédit et soldes identiques.
- [ ] Dossier miroir connecté à Sage : conversion bloquée jusqu'à une bascule contrôlée.
- [ ] Paramétrage multi-société/multi-base : aucune renumérotation d'un autre dossier.

## Accueil / navigation

- [ ] Web et bureau : deux cartes affichées séparément, `Comptabilité générale` et `Comptabilité analytique`.
- [ ] Les deux cartes mènent à des modules fonctionnels, sans écran vide ni lien cassé.
- [ ] Les permissions fonctionnent sur l'interface **et** sur les URLs/API.
- [ ] Le module analytique ne crée pas de pièces ou d'écritures monétaires en double.
- [ ] Le client Windows analytique ouvre ses états web sur le même serveur et avec une gestion de session sûre.

## Analytique commerciale

- [ ] Accueil analytique par section ; produits/charges/résultat cohérents avec écritures **validées**.
- [ ] Sections non affectées détectées explicitement.
- [ ] Aucune liste de véhicules ou propriétaires comme états principaux pour `COMMERCE`.

## Analytique transport

- [ ] États principaux : `Véhicules` et `Propriétaires de véhicules` ; les filtres agence/ligne/voyage/Classe/​VIP n'ajoutent pas de nouvelles rubriques principales.
- [ ] Les véhicules `Classique` et `VIP` sont distingués selon leur classification réelle.
- [ ] Résultat d'exploitation d'un véhicule et somme due au propriétaire demeurent deux indicateurs distincts.
- [ ] Les périodes de contrat et les changements de propriétaire sont respectés.

## Régression et bilan

- [ ] Facturation, règlement, rapprochement, lettrage, balance, grand-livre, bilan et compte de résultat identiques à données constantes.
- [ ] `python manage.py check` et suites de tests `apps.comptabilite` et `apps.transport` : résultats consignés et anomalies documentées.
- [ ] Aucun identifiant ni secret ajouté aux sources.
- [ ] Aucune action destructive ou déploiement en production sans accord explicite et sauvegarde.
