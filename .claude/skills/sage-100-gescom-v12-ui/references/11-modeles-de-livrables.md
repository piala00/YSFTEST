# 11 — Modèles réutilisables

## Modèle 1 : inventaire des menus

| Niveau 1 | Niveau 2 | Fonction | Type d'écran | Source | Édition / option | Validé sur V12 ? |
|---|---|---|---|---|---|---|
| Structure | Articles | Ouvrir la liste | Liste | DOC-V12 | Selon matrice | À observer |
| Traitement | Documents des ventes | Facture | Liste + document | DOC-V12 | Selon matrice | À observer |

## Modèle 2 : description exhaustive d'une fenêtre

```markdown
# Fiche UI-GESCOM-XXX — Nom de l'écran

## Contexte
- Produit / version / édition / modules :
- Utilisateur / profil / déploiement :
- Chemin de navigation :
- Source, capture, date :

## Composition
- Titre de fenêtre :
- Bandeau supérieur :
- Barre d'outils locale :
- Liste/grille : colonnes, tri et filtres :
- Onglets :
  - Onglet 1 : champs, type de contrôle, valeurs, obligatoire/optionnel :
  - Onglet 2 : champs, type de contrôle, valeurs, obligatoire/optionnel :
- Sous-onglets réellement observés :
- Barre / pied :
- Boutons et raccourcis :

## Interactions
| Déclencheur | Préconditions | Résultat visible | Impact métier | Droits |
|---|---|---|---|---|

## Observations
- États grisés, masqués, conditionnels :
- Messages d'erreur et validation :
- Personnalisation utilisateur :
- Inconnues et hypothèses :
```

## Modèle 3 : comparaison interface réelle vs maquette

```markdown
# Comparatif UI
| ID | Élément | Sage V12 observé | Maquette | Conforme ? | Capture | Correction |
|---|---|---|---|---|---|---|
```

## Modèle 4 : parcours utilisateurs

```text
Profil métier :
Objectif :
Déclencheur :
Chemin de menus :
Fenêtre d'arrivée :
Sélections / champs nécessaires :
Actions disponibles :
Validation et résultat attendu :
Erreurs et alertes :
Restrictions :
Captures vérificatives :
```

## Modèle 5 : réponse à « où trouver une commande ? »

1. **Chemin documenté** : `Menu > Sous-menu > Fonction` ou « emplacement à confirmer ».
2. **Rôle** : à quoi sert la fonction.
3. **Conditions** : édition/option, permission, statut du document.
4. **Si introuvable** : vérifier la personnalisation et les droits.
5. **Degré de certitude** : DOC-V12, OBSERVÉ, ERG-CLASSIQUE ou INDICATIF.
