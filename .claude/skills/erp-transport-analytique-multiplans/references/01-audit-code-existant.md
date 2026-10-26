# Audit ciblé du code source fourni (observation, pas correctif)

Source inspectée : `ERP_OHADA_Transport_Code_Source_MAJ_7_Chiffres_Deux_Modules.zip`, dossier `ERP-OHADA-Transport/logiciel/`. Revalider ces observations sur la branche active avant de modifier.

| Constat dans le code | Localisation | Impact |
|---|---|---|
| `SectionAnalytique` possède `plan` en texte libre, `code`, `intitule`, `actif`; pas de référentiel fort des dix plans dans ce modèle. | `apps/comptabilite/models.py` | Les noms de plans peuvent diverger; « Agences » et « Gares » sont déjà distincts et doivent être réconciliés logiquement. |
| `LigneEcriture.section` est une `ForeignKey` unique vers SectionAnalytique, avec un autre lien `vehicule`. | `apps/comptabilite/models.py` | Une écriture ne peut pas stocker correctement 10 dimensions analytiques avec fractions par section du même plan. |
| `balance_analytique` agrège les lignes validées par `section` et comptes 6/7. | `apps/comptabilite/services.py` | Une seule ventilation de section; pas de sélection Plan→Section→États multicritères. |
| États véhicules/propriétaires reposent sur `ligne.vehicule` et contrats. | `apps/transport/analytique.py`, `apps/transport/views.py` | Partiellement opérationnels; préserver et intégrer au moteur sans régression. |
| Navigation comptabilité analytique privilégie les véhicules et propriétaires, et n'offre qu'une balance de sections. | `apps/core/navigation.py` (`ANALYTIQUE`) | Aucun accès complet à 10 plans ni aux journaux/grands livres de chaque section. |
| Les fenêtres de périodes sont différentes : `PeriodeForm` (`date_debut/date_fin`) et vues transport `du/au`, par défaut exercice entier. | `apps/comptabilite/forms.py`, `apps/transport/views.py`, `templates/transport/_filtres_analytiques.html` | Consultation mensuelle/journalière peu fluide et incohérente; uniformiser tout en maintenant compatibilité des liens. |
| `Gare.save()` crée une section plan `Gares` et `Vehicule.save()` plan `Véhicules`; `init_erp` crée des sections `Agences`. | `apps/transport/models.py`, `apps/core/management/commands/init_erp.py` | Agence administrative et gare physique sont des dimensions/hiérarchies distinctes : ne pas fusionner leurs historiques au hasard. |
| Les URLs anal. sont limitées à véhicules, propriétaires, balance sections, ventilation. | `apps/comptabilite/urls_analytique.py` | Ajouter le routage générique vers état par plan et section. |

## Obligations d'audit complémentaire

- Lire les requêtes exactes `apps/reporting/views.py` et `apps/transport/reporting.py` pour vérifier que les KPI monétaires proviennent des écritures validées; si les KPI proviennent d'opérations non comptabilisées, les distinguer comme « opérationnels/provisoires ».
- Vérifier les droits réels, l'isolation entreprise/site, la synchronisation de ces nouveaux objets et la clôture d'exercice.
- Contrôler la sémantique des types de lignes 6/7, les traitements de comptes de tiers, annulations, TVA et transferts; le détail de l'imputation OHADA exige une matrice validée par le comptable.
- Ne pas prétendre que les dix plans contiennent déjà des données comptables valides simplement parce qu'on peut afficher leurs noms.
