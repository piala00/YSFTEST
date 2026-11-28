# Organisation du dossier des licences (atelier éditeur)

Décidé avec le propriétaire (2026-11-04). But : un seul dossier « atelier », deux identités
séparées automatiquement (Développeur / Clients), et un classement par société sous Clients.

## Structure cible (l'outil la crée automatiquement)

```
<Atelier>\                      ← dossier unique choisi une fois
├── Developpeur\                ← identité DÉVELOPPEUR (créée auto, clé ≠ production)
│   ├── coffre.dat, parametres.dat, identite-role.txt = dev
│   └── LICENCE-DEVELOPPEUR-*.erplic
└── Clients\                    ← identité CLIENTS / production (créée auto)
    ├── coffre.dat, parametres.dat, identite-role.txt = clients
    ├── registre-licences.csv   ← registre global des clients (reste à la racine Clients)
    ├── <Société A>\            ← un sous-dossier PAR SOCIÉTÉ (créé auto à l'émission)
    │   ├── <licence>.erplic    ← UN SEUL fichier : la licence autorise l'installation
    │   ├── parametres.dat      ← identité publique (pour le paquet client)
    │   ├── <licence>-LIRE-MOI.txt
    │   └── <devis/facture>      ← quand la grille tarifaire sera en place (P1)
    └── <Société B>\
```

## Règles
- Les deux sous-dossiers `Developpeur\` et `Clients\` sont **créés automatiquement** sous l'atelier.
- Les boutons « Créer identité Développeur / Clients » créent dans le sous-dossier correspondant
  (clés **différentes** : dev ≠ clients ≠ production).
- Émettre une **licence client** crée/utilise `Clients\<Société>\` et y place la licence (+ notice,
  + devis plus tard). Le **registre** reste à la racine `Clients\`.
- Émettre une **licence développeur** va dans `Developpeur\`.
- **Un seul fichier** pour le client : la licence `.erplic` autorise l'installation (pas de clé
  d'installation séparée — décision du 2026-11-04).

## Atelier PORTABLE et AUTO-RECONNU (demande 2026-11-04)
L'atelier est **autonome et portable** : tout ce dont l'outil a besoin vit dedans
(coffres = clés privées **chiffrées**, `parametres.dat` = clés publiques, registres,
dossiers par société, licences). Un marqueur `atelier.json` à la racine le rend
**auto-reconnaissable**.

Usage visé : je **copie le dossier entier** (clé USB, autre poste), j'ouvre l'outil sur
**n'importe quelle machine**, je **sélectionne le dossier** → l'outil détecte l'atelier et
**charge automatiquement** les identités Développeur et Clients (il suffit de saisir le mot
de passe du coffre pour signer). Aucune reconfiguration.

Sécurité : le coffre reste **chiffré par mot de passe** ; le transporter sur une clé USB est
donc protégé (sans le mot de passe, la clé privée est inexploitable). La clé publique
(`parametres.dat`) n'est pas secrète.

## Migration de l'identité de production existante (ne JAMAIS la perdre)
Si l'atelier (ou un ancien dossier) contient déjà un `coffre.dat` à sa racine (cas actuel :
`C:\Users\…\ERP-OHADA-Licences\coffre.dat`), l'outil **déplace** ce coffre + `parametres.dat` +
`registre-licences.csv` dans `Clients\`, en **gardant une copie de sécurité**, pour qu'il devienne
l'identité Clients sans recréer de clé (les licences déjà émises restent valides).

## À implémenter (outil `deploy/licences/licences.py`)
1. Helpers atelier (sous-dossiers Developpeur/Clients) + préparation automatique.
2. Émission client dans un sous-dossier par société ; registre à la racine Clients.
3. GUI : champ « Dossier propriétaire » = atelier ; boutons d'identité ciblant les sous-dossiers ;
   émission routée vers la bonne identité/sous-dossier.
4. Migration sûre d'un coffre de production existant vers `Clients\`.
5. Tests (unitaires + parcours interface xvfb) et recompilation de l'outil.
