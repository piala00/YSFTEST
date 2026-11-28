# 14 — Cadre réglementaire et sources de référence (à vérifier lors de l'implémentation)

**Important :** ce dossier constitue un cahier technique et métier, pas un avis juridique ni un logiciel certifié conforme. Les règles sont versionnées et leur applicabilité dépend du pays, de l'entreprise, de l'activité, du contrat et de la période. Toute mise en production exige contrôle par un expert-comptable, fiscaliste et conseiller juridique compétents localement.

## Sources institutionnelles confirmées

1. OHADA — **Acte uniforme relatif au droit comptable et à l'information financière (AUDCIF)**, adopté le 26 janvier 2017 ; SYSCOHADA révisé et dispositif de comptes consolidés/combinés. Entrée en vigueur le 1er janvier 2018 pour les comptes personnels des entités ; 1er janvier 2019 pour comptes consolidés/combinés. Site officiel : https://www.ohada.org/acte-uniforme-relatif-au-droit-comptable-et-a-linformation-financiere-audcif/4/
2. OHADA — **Acte uniforme relatif aux contrats de transport de marchandises par route**, adopté le 22 mars 2003, entré en vigueur le 1er janvier 2004, champ d'application et exclusions à examiner : https://www.ohada.org/en/contracts-of-carriage-of-goods-by-road/
3. Claude Code — **Skills**, structure `SKILL.md` avec frontmatter YAML et références complémentaires dans le répertoire du skill : https://code.claude.com/docs/en/skills

## Points à documenter par pays AVANT de coder des constantes

- Cameroun et pays de déploiement : réglementation du transport interurbain de passagers, émission et conservation des billets, documents de bord, assurances, sécurité routière, taxes propres au transport, transit inter-États, transport de colis particuliers et interdictions.
- RH et paie : Code du travail national, SMIG, rémunérations minimum, heures supplémentaires, congés, prélèvements sociaux (CNPS et autres), plafonds, contributions employeur, fiscalité salariale et déclarations.
- Comptabilité/fiscalité : plan SYSCOHADA et adaptations sectorielles, TVA/impôt par pays, méthode de constatation du chiffre d'affaires, nature du contrat d'exploitation partenaires, amortissements, dispositions sur plusieurs devises (XAF dans la CEMAC et autres).
- Données personnelles : obligations nationales applicables et règles de communication des données voyageurs, employés, partenaires.
- Paiements : Mobile Money, espèces, virements, vérification des transactions, sécurité et conservation des reçus. Ne jamais considérer une simple intention de paiement comme un règlement final.

## Démarche de validation

Pour chaque règle financière, fiscale, RH ou juridique : enregistrer `country`, `legal_entity`, `rule_name`, `source_title`, `source_url`, `effective_start`, `effective_end`, `approved_by`, `approved_at`, `rule_version` et scénario de test correspondant. Si le texte légal est inaccessible ou ambigu, marquer la règle « validation requise » et ne pas prétendre qu'elle est officielle. Conserver les documents contractuels et décisions d'approbation.

## Sources techniques indicatives

- PostgreSQL — transactions et isolation : https://www.postgresql.org/docs/current/transaction-iso.html
- Microsoft — modèle Transactional Outbox : https://learn.microsoft.com/en-us/azure/architecture/databases/guide/transactional-outbox-cosmos
- OWASP — risques API / contrôles d'autorisation : https://owasp.org/API-Security/editions/2023/en/0x11-t10/

Les liens de sources servent à orienter Claude vers des documents à jour : ils ne se substituent pas à l'examen du texte intégral à la date d'implémentation.
