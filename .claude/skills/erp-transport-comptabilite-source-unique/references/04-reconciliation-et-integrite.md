# 04 — Rapprochements obligatoires et garde-fous

## Conservation financière

Pour toute ligne de GL éligible à une répartition analytique, à statut validé :

`Montant_GL_eligible = Somme_des_ventilations_analytiques_actives + Montant_non_ventilé`

Sur le périmètre de même **société, exercice, période, devise, convention de signe et ensemble de comptes éligibles**.

Ne pas exiger que le chiffre d'affaires du **véhicule** soit égal au chiffre d'affaires **total société** : une partie des revenus peut ne pas relever des véhicules, certains comptes ne sont pas éligibles. Il faut un état de rapprochement explicite `source GL éligible → affecté → non affecté` et un rapprochement GL total de contrôle plus large.

## Contrôles de qualité

- Analyse orpheline (`gl_line_id` absent) : blocage de publication et alerte ; ne pas fabriquer un justificatif ou un GL artificiel.
- Source GL non comptabilisée : analyse financière définitive interdite, statut « en attente de comptabilisation ».
- Source GL contrepassée : marqueur et projection corrective ; les deux écritures restent visibles.
- Allocation active dépassant / insuffisante : blocage du statut “réconcilié” ; ligne GL non ventilée listée clairement.
- Mauvaise société, période, devise, véhicule, propriétaire à date : blocage et piste d'audit.
- Doublon de projection après resynchronisation : idempotence sur événement, GL line, version d'allocation.
- Durée de contrat : rattacher au contrat réellement actif à la date d'exploitation ; ne pas reconstruire le passé d'après le propriétaire courant.
- Période clôturée : pas d'édition silencieuse ; ajustement dans une période ouverte selon politique comptable.
- Écritures non monétaires : kilomètres, nombre de voyageurs, sièges, colis restent séparés des totaux financiers et clairement identifiés.

## Consultation

Chaque tableau Véhicule et Propriétaire offre un drill-down :

`Montant récapitulatif → rubrique → véhicule/voyage → allocation → écriture GL comptabilisée → compte/journal/tiers → document source`.

La direction peut consulter un registre des écarts compta/analytique, ventilations manquantes, agences non synchronisées et comptes sans attribution véhicule. Les anomalies non résolues rendent le rapport « provisoire », sans supprimer les données GL.

## Autorisations et clôture

Rapprochement à effectuer lors de la clôture de caisse/journée, du départ clôturé et de la fin de période comptable selon granularité choisie. Les chiffres “définitifs” exigent : écritures GL validées, projections idempotentes appliquées, règles de ventilation vérifiées, réconciliation réussie, agences attendues synchronisées et clôture approuvée.
