# Barèmes de remises, ristournes, soldes/promotions et commissions — conception (à valider)

**But :** se caler sur **ce que fait Sage 100 Gestion commerciale** avant de coder, puis le reproduire dans notre
logiciel. Aucune règle de calcul n'est inventée : les points marqués **[DOC-V12]** viennent de la compétence Sage ;
ceux marqués **[À VALIDER]** demandent votre décision ; **[DÉJÀ FAIT]** existe déjà chez nous.

## 1. Ce que fait Sage (compétence `sage100-gescom-v5-v12-expert`) [DOC-V12]

Dans **Structure › Barèmes**, Sage distingue trois familles :
- **Commissions des représentants** : taux de commission (par représentant, parfois par famille/article).
- **Rabais, remises, ristournes (RRR) clients et fournisseurs** : remises automatiques selon des critères.
- **Soldes et promotions clients et fournisseurs** : remises limitées dans le temps (période).

Le **prix d'une ligne** peut venir de plusieurs sources, dans un ordre que Sage calcule :
catégorie tarifaire → tarif d'exception → **escalier (remise selon quantité)** → **remise par famille** →
**promotions** → RFA (remise de fin d'année = ristourne). Sage avertit : **l'ordre exact et l'existence de chaque
règle dépendent de l'édition et de la version** ; à prouver sur un dossier de test, jamais à supposer.

Critères possibles d'un barème [DOC-V12] : **client ou catégorie tarifaire**, **article ou famille d'articles**,
**quantité** (escalier), **période** (soldes/promotions), **devise**.

## 2. Ce que notre logiciel a déjà [DÉJÀ FAIT]

- **Catégorie tarifaire** par client (`Tiers.categorie_tarifaire`) et **prix par catégorie** (`TarifCategorie`).
- `Article.prix_pour(tiers)` choisit déjà le prix : catégorie tarifaire, sinon prix de la fiche.
- **Remise ligne à ligne** manuelle (`LigneDocument.remise %`), avec prix net après remise.

Il manque donc exactement la branche **Barèmes** de Sage : les remises **automatiques** (par critères) et dans le
temps, et les commissions.

## 3. Modèle proposé (calé sur Sage) [À VALIDER]

Un seul modèle `Bareme`, simple et lisible, couvrant les trois familles via un champ **type** :

| Champ | Rôle | Exemple |
|---|---|---|
| type | `remise` (RRR immédiate) \| `promotion` (datée) \| `commission` | remise |
| sens | `client` \| `fournisseur` | client |
| catégorie tarifaire | critère (vide = toutes) | GROS |
| client | critère précis (vide = tous) | — |
| famille d'articles | critère (vide = toutes) | Boissons |
| article | critère précis (vide = tous) | — |
| quantité minimale | escalier (0 = sans seuil) | 10 |
| début / fin | période (vide = permanent) ; obligatoire pour `promotion` | 01→31/12 |
| taux % | remise ou commission | 5 % |
| représentant | pour `commission` seulement | — |

**Application sur un document** [À VALIDER], proposée pour rester prévisible (Sage est paramétrable) :
1. Le prix de base vient comme aujourd'hui (`prix_pour`).
2. Parmi les barèmes `remise`/`promotion` **actifs à la date** qui **correspondent** à la ligne (catégorie/client,
   famille/article, quantité ≥ seuil), on retient **le plus précis** (article > famille ; client > catégorie ;
   seuil le plus élevé atteint). **Un seul** s'applique — pas de cumul incontrôlé — et il remplit la remise de la
   ligne. **Une remise saisie à la main reste prioritaire** (le vendeur peut toujours forcer).
3. Les **commissions** ne touchent pas le prix : elles alimentent un **état des commissions** par représentant.

**Ce que je ne fais pas sans votre accord :**
- **Cumul de remises** (empiler plusieurs taux) : par défaut **non** (un seul barème, le plus précis). [À VALIDER]
- **RFA / ristourne de fin d'année** (avoir calculé sur le chiffre d'affaires annuel) : écriture comptable à la
  clé → **séparé, plus tard**, après validation du principe et des comptes avec l'expert-comptable. [À VALIDER]
- Aucun **taux** par défaut n'est inscrit : les barèmes sont créés par vous (règle AGENTS.md).

## 4. Décisions attendues de votre part

1. Le modèle unique `Bareme` ci-dessus vous convient-il, ou voulez-vous trois écrans séparés comme Sage
   (RRR / Soldes-promotions / Commissions) ?
2. **Un seul barème appliqué (le plus précis), sans cumul** — d'accord ? Sinon, quelle règle de cumul ?
3. Les **commissions représentants** : les fait-on maintenant (état par représentant) ou plus tard ?
4. La **RFA / ristourne de fin d'année** : plus tard, avec l'expert-comptable — d'accord ?

Dès votre validation, je code par étapes testées : modèle + migration additive, écran de saisie des barèmes,
application à la saisie des documents (avec priorité à la remise manuelle), et états (remises accordées,
commissions). Les montants comptables continueront de venir des écritures validées.

---
*Référence Sage : compétence `sage100-gescom-v5-v12-expert`, `references/04-menu-structure.md` et
`formations/02-referentiels-et-tarification.md` [DOC-V12]. L'ordre de calcul exact de Sage étant propre à chaque
version, notre ordre est explicite et documenté ci-dessus, non présenté comme identique à Sage.*
