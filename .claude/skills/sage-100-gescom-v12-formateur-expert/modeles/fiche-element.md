# Modèle — Fiche exhaustive d'un élément d'interface Sage V12

Copier cette fiche **une fois par menu, commande, fenêtre, onglet, champ, bouton ou colonne**.

```yaml
id: UI-GESCOM-V12-0001
nom_exact: ""
type: menu|sous-menu|fenetre|liste|onglet|sous-onglet|champ|colonne|bouton|icone|dialogue
chemin: "Fichier > ... > ..."
parent_id: ""
version_observee: "V12.__"
edition: "Essentials|Standard|Premium|autre"
options: []
deploiement: "sur site|heberge|partenaire"
profil_utilisateur: ""
libelle_infobulle: ""
ordre_visuel: null
capture_reference: ""
source_url: ""
source_date: ""
niveau_de_preuve: DOC-V12|DOC-PROC|ERG-CLASSIQUE|OBSERVE|HYPOTHESE
fonction: ""
champs_entree: []
valeurs_possibles_confirmees: []
prerequis: []
conditions_activation: []
effets_document: ""
effets_stock: ""
effets_tiers_reglement: ""
effets_comptabilite: ""
impacts_et_risques: []
droits_requis: ""
procedure_test: []
resultat_attendu: ""
resultat_observe: ""
erreurs_connues: []
points_a_verifier: []
date_derniere_verification: ""
```

## Comment renseigner correctement

- Si un onglet n'est pas visible sur une capture V12, laisser `nom_exact` vide ; noter le **groupe de fonction documentaire** séparément.
- Ne pas coder de formule de calcul métier non vérifiée comme si elle provenait de Sage.
- Pour une même commande qui change de comportement selon statut de pièce, créer **plusieurs variantes de test**.
- Une ligne doit avoir une preuve, une observation ou une mention explicite « à vérifier ».
- Pour un bouton à effets financiers/stock, ajouter avant/après et besoin de sauvegarde/validation.
