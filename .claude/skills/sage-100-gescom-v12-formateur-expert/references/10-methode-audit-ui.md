# 10 — Méthode de relevé, audit et éventuelle reproduction de l'UI

## Objectif

Construire une documentation fiable, éventuellement exploitable pour développer un logiciel similaire **sans copier automatiquement le code ni promettre une conformité visuelle parfaite**.

## Phase A — Reconnaissance

1. Relever `Aide > À propos`, ou la fenêtre équivalente, pour obtenir la **version exacte**, sans supposer que le menu porte ce nom.
2. Déterminer édition, déploiement, licence, options et droits utilisateur.
3. Capturer l'écran principal et chaque menu horizontal déroulé (sept captures recommandées).
4. Capturer la barre d'outils, la barre latérale et les menus contextuels ; relever uniquement ce qui existe visuellement.
5. Comparer les points observés au découpage officiel V12.10 ; conserver l'origine de chaque élément.

## Phase B — Inventaire des listes et fiches

Pour **Structure > Articles / Clients / Fournisseurs / Dépôts / Collaborateurs**, relever :
- liste : colonnes, filtres, tri, recherche, menus et options de sortie ;
- fiche : titre, champs d'identification, onglets réels, champs par onglet ;
- interactions : clic simple/double, bouton droit, tabulation, validation, erreurs ;
- états : droits, restrictions, zones grisées, champs requis.

## Phase C — Documents et états

Documenter séparément :
- Ventes : devis, commandes, préparations, BL, retours, factures, avoirs.
- Achats : demandes, commandes, BL, factures, retours et avoirs.
- Stocks : entrées, sorties, transferts, inventaires et dépréciations.
- Règlements, besoins, mises à jour comptables.
- États : critères, période, aperçu, colonnes, impression, export et tableaux de bord.

## Phase D — Reproduction (uniquement si demandée)

1. Définir le **support de la future interface** (Python natif, web, etc.) ; ne pas transformer implicitement une demande de documentation en génération de code.
2. Créer l'arborescence de navigation avant les formulaires.
3. Définir des composants réutilisables : barre de menus, barre d'outils, table, filtre, fiche, onglets, modale, notifications.
4. Conserver une matrice traçable : `élément Sage → écran cible → état de réalisation → capture de référence → test`.
5. Prendre en charge navigation clavier, redimensionnement, droits, messages, tri, impression et accessibilité.
6. Séparer la couche de présentation, le service métier et la source de données. Lors de l'intégration Sage : SQL en lecture seule pour le reporting ; utiliser des API/objets métiers autorisés pour les écritures.
7. Tester chaque écran contre des captures autorisées ; distinguer **fidélité visuelle**, **équivalence de fonction** et **exactitude métier**.

## Modèle de registre d'écarts

| ID | Fenêtre | Observation | Référence | Attendu | Gravité | Action |
|---|---|---|---|---|---|---|
| UI-001 | Exemple : liste clients | Colonne masquée | Capture utilisateur | Colonne visible | Moyenne | Vérifier personnalisation |

Ne jamais présenter un exemple fictif comme un bug réel.

## Phases de validation

- **Couverture** : menus / sous-menus identifiés.
- **Précision** : onglets, contrôles, libellés et commandes capturés.
- **Disponibilité** : éditions et droits renseignés.
- **Navigation** : tous les chemins vérifiés.
- **État** : actions désactivées / visibles analysées.
- **Sécurité** : aucune opération destructive exécutée pendant l'audit.
- **Documentation** : notes de version et captures liées.
