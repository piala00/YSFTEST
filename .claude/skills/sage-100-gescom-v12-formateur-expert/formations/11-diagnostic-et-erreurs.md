# Diagnostic et dépannage — Arbre de décision Sage 100 Gescom

## En premier : cerner précisément le symptôme

Demander ou relever : message intégral, écran, chemin, version V12.xx, édition, société, utilisateur, type/n° de pièce **anonymisé**, date, contexte, événement déclencheur, état avant/après ; comparer un profil autorisé et un profil concerné quand cela est possible. **Ne pas demander de mot de passe ni de base de production complète.**

## Diagnostic générique

1. **La fonction manque ?** édition/option → droits → personnalisation → contexte/status → sous-version. Voir `references/09-disponibilite-et-droits.md`.
2. **Un bouton est grisé ?** sélection correcte → état de pièce (validée, comptabilisée, clôturée) → permissions → prérequis obligatoires.
3. **Un montant diffère ?** article/tarif → remise/escompte/taxe → devise → période → type de document → source de l'état.
4. **Un stock diffère ?** dépôt → période → état avant/après → pièces stockantes → lot/série → inventaire → doublon/annulation/retour.
5. **Une créance diffère ?** facture → échéance → règlements imputés → avoirs → date d'arrêté → client/affectation → filtre.
6. **Une pièce ne passe pas en compta ?** validation → paramétrage catégorie/journal/compte/taxe → statut/pièce → journal d'erreur → connexion/module comptable.
7. **Une liste ne montre pas la pièce ?** dossier, exercice/période, document/type, statut, filtre utilisateur, recherche, autorisation, actualisation.
8. **Erreur SQL ou performance ?** sauvegardes, journaux applicatifs et SQL, réseau, comptes de service, permissions, espace disque et santé serveur ; ne pas transformer le diagnostic en correction SQL intrusive.

## Rapport de diagnostic obligatoire

```text
Symptôme constaté :
Périmètre (V12.xx / licence / société / profil) :
Reproduction dans un dossier test :
Preuves : captures, message, n° anonymisé, état avant/après :
Hypothèses (de la plus probable à la moins probable) :
Tests NON destructifs et résultats :
Cause établie / cause non démontrée :
Solution recommandée / impact / réversibilité :
Sauvegarde et validation requises avant modification :
Vérification post-correction :
Sources :
```

## Cas pratiques de diagnostic

- **Stock d'un article positif en A mais commande bloquée** : inspecter dépôt réellement affecté, disponibilité vs réel, allocations, option stock négatif, droits, état de pièce.
- **Facture en liste mais pas dans l'état des ventes** : examiner type, date, validation, filtres, souche, société ; vérifier si état cumule BL/facture/avoirs.
- **Règlement enregistré mais créance inchangée** : chercher mauvaise échéance, affectation non réalisée, date, dossier, client, état non actualisé ; ne pas supprimer le règlement aveuglément.
- **Utilisateur voit moins de commandes que l'admin** : rôles, restrictions de dépôt/tiers, responsables, filtres mémorisés, société active et personnalisation.
- **Prix différent après transformation** : politique tarifaire et règle Sage S11 avant de suspecter corruption.

## Escalade et sécurité

Sauvegarder et contacter l'administrateur/intégrateur Sage pour les erreurs d'intégrité, bases dégradées, réajustements, clôtures ou interventions sur données. Les preuves collectées doivent éviter les informations personnelles ou commerciales sensibles.
