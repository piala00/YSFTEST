# Retour du propriétaire — édition Transport (02/11/2026)

> Constats faits par le propriétaire en testant l'ERP Transport installé sous Windows
> (OVERLINE TRANSPORT ET LOGISTIQUE). À traiter ; aucune idée ne doit être perdue.

## Déjà corrigé (02/11/2026)
- **Titres de fenêtre affichant du HTML brut** : sections collées par erreur dans `{% block title %}`
  de `rapport_journalier.html` (« 7. Points ouverts ») et `depart_detail.html` (« Avances de
  mission »). Corrigé (commit 410ce83) ; scan complet : plus aucun titre ne contient de HTML.

## Chantier A — Séparer Transport et Gestion commerciale (PRIORITAIRE, correctness)

**Constat.** Dans l'édition **Transport**, on peut encore atteindre la **Gestion commerciale** :
- Fichier › Paramètres société › Identification ouvre l'écran société **hébergé dans l'app
  Commerce** (`commercial:societe` → `/commercial/societe/`) → tout l'habillage « Gestion
  commerciale » (menu des ventes) surgit. Cause : le bandeau est choisi d'après le préfixe d'URL
  (`module_pour_chemin`), et `menu_fichier(..., "commercial:societe")` est utilisé par tous les
  modules (navigation.py lignes 734, 806, 894, 985).
- Pire : on peut **créer un document de vente** depuis le Transport → les routes commerciales sont
  réellement accessibles, pas seulement affichées.

**Objectif.** Sur l'édition Transport (licence « transport »), **aucun écran, menu ou route de la
Gestion commerciale ne doit être atteignable**. Transport et Commerce sont deux métiers distincts.

**Pistes de correction.**
1. Lier la visibilité ET l'accessibilité des modules à l'**édition de la licence** (transport),
   pas seulement à `societe.activite`. Sur édition transport : masquer `GESTION_COMMERCIALE` du
   portail/menu « Logiciels », et **bloquer les routes commerciales** (accès direct → « non
   disponible dans cette édition »).
2. L'écran **Identification / Paramètres société** (commun) doit s'ouvrir dans un shell **neutre
   « Administration du poste »** (comme Licence et Base de données) ou dans le shell Transport —
   jamais « Gestion commerciale ». Router l'écran société hors du préfixe `/commercial/`.
3. Vérifier qu'aucun autre lien transport ne pointe vers un écran commercial (audit des
   `commercial:*` atteignables depuis les menus transport).

## Chantier B — Ergonomie : barres et espace (navigateur)

**Constat.** En navigateur, l'espace vertical est précieux (les barres du navigateur en prennent
déjà). Le formulaire **Saisir un billet** n'a pas de place pour s'étirer ; le cadre est trop petit
alors que le formulaire est long.

**Demandes précises.**
1. **Barre du haut permanente et plus fine.** La barre « ERP OHADA · OVERLINE TRANSPORT ET
   LOGISTIQUE · Exercice 2026 » ne doit **pas changer** selon le module ; on **réduit sa hauteur**
   pour qu'elle soit fine. Quand on entre dans un module, **le nom du module s'y affiche**
   (« Module Billetterie ») avec les infos société/exercice — la barre reste la même.
2. **Barre d'outils masquable.** Les petits outils (icônes) entre la barre de menu du module et
   l'interface doivent pouvoir être **masqués** pour gagner de l'espace.
3. **Plus de hauteur pour les formulaires.** Les écrans de saisie (ex. *Saisir un billet*)
   doivent pouvoir **s'étirer vers le haut** / disposer de plus de place verticale ; revoir la
   hauteur utile pour une meilleure ergonomie en navigateur.

## Risque signalé par le propriétaire
Vu la **multitude d'options** du Transport, il peut rester d'**autres mélanges** Transport/Commerce
non encore repérés. Prévoir un **audit systématique** des liens et routes de l'édition Transport.
