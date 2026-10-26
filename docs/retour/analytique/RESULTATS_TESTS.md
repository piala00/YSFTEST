# Résultats des tests — comptabilité analytique

Date : 26/10/2026. Environnement : Linux, Python 3.13, Django 6.1.2, SQLite (bases de test créées puis détruites).

```
python manage.py test
Ran 293 tests in 121.636s
OK
```

## Tests propres à l'analytique (apps/transport/tests.py, PlanAnalytiqueCompletTests)

Jeu de données : la commande `simulation` jouée sur 2 jours (8 cars, 5 camions, 30 salariés, données fictives).

| Test | Vérifie | Cas du skill |
|---|---|---|
| test_chaque_axe_se_rapproche_de_la_comptabilite_generale | les 9 axes existent ; sur chacun, éléments + non affecté = générale ; produits entièrement attribués aux gares, véhicules, activités | 1, 5 |
| test_etats_detailles_d_un_element | les 7 états d'une gare s'affichent ; le croisé par véhicule redonne le résultat de la gare ; CSV = lignes du grand-livre ; non affecté ; axe inconnu → 404 | 2, 8, 15 |
| test_periodes_rapides | semaine, mois précédent, trimestre, dates libres, période précédente | 10 |
| test_services_periodes_journal_et_reporting_identique | paie hors véhicule sur la section du service ; axe Services rapproché ; **reporting = état analytique au franc près** ; Du > Au refusé ; ←/→ ; N-1 (29 février) ; mois choisi ; journal des imputations ; classement | 10, 11 |
| test_societe_de_commerce_sections_seulement | commerce : ni véhicules ni propriétaires, ses plans de sections seulement | — |

Autres tests liés : DeuxModulesComptablesTests (transport et core), ComptabiliteAnalytiqueTests, ComparaisonsTransportTests
(reporting passé sur le moteur, inchangés et verts), RemunerationsProprietairesTests, CompteDuCamionTests.

## Vérification manuelle

Dossier de simulation de septembre (copie) : plan, axe Gares, gare de Yaoundé (exploitation, croisé par véhicule),
véhicule (évolution, comparaison) affichés dans le navigateur (captures faites, non jointes au dépôt).
Gare de Yaoundé : produits 117 183 000, charges 44 305 800 ; somme des 41 véhicules = 72 877 200 = résultat de la gare.

## Non testé

Cas du skill 4 (changement de contrat en cours de mois : couvert par les tests propriétaires existants, pas par un test
du plan), 6 (ventilation fractionnée : absente), 7 (contrepassation : le moteur ne lit que les validées), 12 (agence
hors connexion sur les états), 13 (propriétaire-fournisseur : tests propriétaires existants), 14 (droits par gare :
absents), 16 (simulation complète 60 cars : faite manuellement le 26/10, pas en test automatique).
