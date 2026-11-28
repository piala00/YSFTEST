# 06 — Mise à jour additive, tests et retour Claude → ChatGPT

## Ordre impératif
1. Sauvegarder le projet, auditer schéma/tables/rôles/paiements/projections et confronter avec ce Skill. Relever les conflits sémantiques (ex. `partner` utilisé simultanément pour supplier/owner).
2. Définir migrations additives à clé de rôle + contrats versionnés + soldes dérivés. Documenter équivalences et migration des tiers existants sans les reclassifier automatiquement.
3. Tester le modèle de rémunération : fixe garanti, variable, fixe+variable et avance imputable. Les schémas GL demeurent configurables/validés.
4. Implémenter gestion de droit fixe, calcul et validation de droits variables, compte auxiliaire propriétaire, demandes de retraits, comptabilisation et états comptables/analytique/reporting.
5. Proposer la **reconstruction de la simulation mensuelle** de huit agences et 15 véhicules partenaires AVEC droits fixes sur un échantillon de contrats, plutôt que de modifier uniquement des états CSV déjà équilibrés ; comparer balance GA avant/après, journaux, compte propriétaire, résultats analytiques, paie des 300 salariés inchangée.
6. Fournir validation du scénario autonome : `python .claude/skills/erp-transport-partenaires-proprietaires/scripts/validate_exemple.py`.

## Tests minimum
- Une personne avec rôles OWNER + SUPPLIER garde deux sous-comptes indépendants et deux permissions séparées.
- Un propriétaire sans contrat de travail n'apparaît pas dans la paie salariale pour son fixe.
- Montant fixe garanti dû même si marge insuffisante, sauf clause contractuelle d'exception ; pas de variable arbitraire si marge négative.
- Cas fixe+variable : pas de double charge au paiement ; contrôles de base après le fixe, arrondis, taxes et pièces.
- Cas fixe=avance : pas de charge fixe + charge variable en doublon ; gestion avance supérieure au dû.
- Demande de retrait 100 000 avec solde disponible 180 000 : autorisation conditionnelle ; nouvelle demande 90 000 après règlement si reste seulement 80 000 : refus.
- Aucune écriture analytique monétaire sans `source_gl_line_id` vers `POSTED` ; reconstituer balance / relevé.
- Annulation, remboursement, changement de contrat/propriétaire, coupure Internet et concurrence inter-agences : intégrité et audit.
- Totaux et état « provisoire » si journée/contrat/agence non clôturé ou non synchronisé.

## Retour obligatoire
Fichier `RETOUR_POUR_CHATGPT.md` : audit avec chemins code ; tables, API, captures/états ; liste détaillée des changements ; schéma des écritures validé ou points à faire valider ; résultats de tests (preuve d'exécution) ; écarts par rapport à l'exemple ; décisions nécessaires de la direction. Générer `RETOUR_CLAUDE_CODE_ERP_TRANSPORT.zip` du projet anonymisé si l'utilisateur le demande. Exclure `.env`, clés privées, tokens, archives de sauvegarde contenant de vraies données personnelles, dumps clients/employés, mots de passe, fichiers propriétaires non autorisés. Ne pas modifier les environnements de production sans procédure de recette et autorisation.
