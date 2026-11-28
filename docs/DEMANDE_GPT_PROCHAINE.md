# Demande de recherche pour GPT — prochaine livraison (22/10/2026)

## Contexte en bref

Je développe un ERP OHADA (Django) qui reproduit l'interface et le fonctionnement de **Sage 100 V12** (Gestion
commerciale, Comptabilité), puis l'adapte au Cameroun. Il est déjà fonctionnel :
- documents, stock, règlements, comptabilisation SYSCOHADA ;
- droits par menu, fichiers liés, fenêtres de sélection, reprise SQL Sage en lecture seule.

Vos livraisons précédentes sont intégrées : menus et droits (lot 1), fiscalité Cameroun (lot 2), écrans et états
(lot 3), SQL et hébergement (étape 4), fenêtres de sélection, liaisons avec la comptabilité.

Il me manque surtout des **faits relevés sur V12** : beaucoup de vos sources sont le manuel 8.50 ou des aides sans
numéro de version.

## Règles (inchangées)

1. **Ne rien inventer.** Chaque fait cite sa source (URL, document, page) et sa version (V12.x, V10+, sans build, 8.50).
2. **Libellés exacts** de Sage (casse, accents, « Etat » sans accent dans la barre de menus).
3. **Séparer** le fait documenté, la déduction et l'inconnue. Ce qui n'est pas trouvé va dans `INCONNUES.csv`.
4. Pas de règle fiscale française transposée au Cameroun.
5. **Livraison** : un skill zippé par lot (`SKILL.md` + `references/*.csv` UTF-8, séparateur `;`), comme les précédents.

## Priorité 1 — Écrans que l'utilisateur voit tous les jours

### A. Fenêtres de sélection des états, relevées sur V12
Pour chaque état, donner :
- les critères : libellé, type, valeurs proposées ;
- la **valeur par défaut** ;
- les boutons (OK, Annuler, Plus, Différer… existent-ils encore en V12 ?).

États, par ordre de priorité :
1. Balance des comptes (P006), Echéancier (P007), Grand-livre des tiers (P009), Balance des tiers (P010), Justificatif
   de solde (P011) ;
2. Mouvements de stock (G066), Inventaire (G068), Statistiques clients et articles (G052, G064) ;
3. Confirmer en V12 la Balance âgée (P008) : « D'après la date d'écriture », délais 30 / 45 / 60, et les colonnes de
   l'état imprimé.

### B. Fiches V12 complètes
- Fiche **client / fournisseur** : onglets, champs dans l'ordre, valeurs par défaut. Inclure le **tiers payeur**,
  le compte collectif, la catégorie comptable et la catégorie tarifaire.
- Fiche **article** : mêmes informations.

### C. Documents d'achat et de stock V12
- En-tête, colonnes de la grille, pied.
- Existe-t-il un neuvième type de document d'achat ?
- Transformations depuis le bon de retour, le bon d'avoir financier et la demande d'achat.
- **Avoir financier d'achat** : comment Sage V12 répartit-il la correction de valeur sur le stock (par article, au
  prorata, sur le CMUP) ? Exemple chiffré si possible.

## Priorité 2 — Droits, utilisateurs et liaison comptable

### D. Libellés des droits en V12
Liste exacte de la liste déroulante des autorisations, par exemple « Autoriser », « Interdire la suppression »,
« Interdire l'écriture », « Interdire la lecture et l'écriture » / « Tout interdire ». Une commande interdite est-elle
**masquée ou grisée** ?

### E. Fichiers liés et utilisateurs (R15)
1. Emplacement et libellé exacts de « Fichier lié » dans À propos de votre société, en Gestion commerciale et en
   Comptabilité.
2. Liste des données partagées par le lien.
3. Sens exact d'un accès **« invité »** et d'un accès **« utilisateur »** :
   - l'invité ne fait-il que consulter ?
   - consomme-t-il une licence ?
4. Les droits d'un profil sont-ils stockés une seule fois pour tous les logiciels, ou séparément pour chacun ?

### F. Mise à jour comptable (Gestion commerciale V12)
- L'écran Traitement › Mise à jour comptable : options, sélection des documents, regroupement des écritures, journaux,
  date retenue, message en cas de période fermée.
- Une facture peut-elle être modifiée entre sa validation et sa mise à jour comptable ?
- Le droit « mise à jour comptable » est-il distinct du droit sur les factures ?

## Priorité 3 — Structure complète des menus (lot 1, suite)

1. **Découpage fonctionnel Comptabilité (S02, 9 pages)** : toutes les lignes, menu par menu, avec le chemin complet
   et la colonne d'édition (Essentials, Standard, Premium…).
2. **Gestion commerciale (S03)** : seulement les différences avec notre liste V11
   (`docs/AUDIT_SAGE_V12_GESCOM.md`), surtout Édition, Fenêtre et « ? ».

## Priorité 4 — Cameroun et SYSCOHADA (lot 2, suite)

1. **Plan SYSCOHADA révisé final** (JO OHADA du 15/02/2017) : une diffusion officielle téléchargeable.
2. **Correspondance comptes → rubriques** du bilan et du compte de résultat (système normal), en particulier :
   - les lignes AE à AH, AJ à AN, AR et AS ;
   - le code de l'écart de conversion passif.
3. **AIR et précompte** : assiette au moment de la facture ou du règlement, avec un exemple chiffré officiel.
4. **Mention exacte** sur la facture d'un non-assujetti à la TVA ou d'un contribuable à l'IGS, si un texte la fixe.
5. **Facture électronique** (art. 8 bis) : arrêté d'application, entreprises concernées, calendrier.

## Priorité 5 — Expérience utilisateur (R14)

Pour les fiches et listes de V12, relever :
- les colonnes par défaut et la personnalisation des listes ;
- les boutons Précédent / Suivant / Rechercher ;
- les **raccourcis clavier** ;
- les **messages** de blocage : encours, stock insuffisant, période clôturée ;
- la page d'accueil.

Pour chacun, donner le texte exact et les boutons.

---

## Retour sur la livraison du 22/10/2026 (`sage-reponses-claude-tous-les-lots`)

**Intégré :**
- Menu Fichier de la Comptabilité aligné sur la matrice S02 :
  - Paramètres société › Identification, Monnaie & Formats, Préférences, Exercices… ;
  - Lire les informations, Configuration système et partage ;
  - Outils › Sauvegarder / Restaurer ma société, Journal des événements légaux…
- Bilan : code **DY** pour l'écart de conversion passif (modèle DGI 2021).
- Reprise Sage : **CT_NumPayeur** → tiers payeur de l'ERP.
- Balance âgée : les délais 30 / 45 / 60 sont signalés comme historiques (8.50), pas comme défauts V12.
- Aucun calcul automatique d'AIR ou de précompte, aucune mention de non-assujetti imposée, aucune date de facture
  électronique : ces points restent non établis, comme vous l'indiquez.

**Pour la prochaine fois :**
1. **Gestion commerciale** : comparer S03 avec le fichier `docs/AUDIT_SAGE_V12_GESCOM.md`, joint cette fois à la
   demande.
2. **AIR et précompte** : une circulaire ou un avis de la DGI qui tranche l'assiette (HT ou TTC) et le moment
   (facture ou règlement) pour les achats locaux.
3. **Plan SYSCOHADA final** : le JO OHADA du 15/02/2017 complet, si une diffusion officielle est retrouvée.
4. **Arrêté du MINFI** sur le suivi électronique de la facturation (L 8 bis) : périmètre et calendrier.
