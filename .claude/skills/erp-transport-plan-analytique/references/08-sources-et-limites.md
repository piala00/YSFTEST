# 08 — Références documentaires officielles et périmètre

## Sources vérifiées (consultées le 25 octobre 2026)

1. **OHADA — Acte uniforme relatif au droit comptable et à l'information financière (AUDCIF)**, publié sur le site de l'organisation : https://www.ohada.org/acte-uniforme-relatif-au-droit-comptable-et-a-linformation-financiere-audcif/4/  . Ce texte et son annexe SYSCOHADA constituent une base du référentiel général de comptabilité ; l'analytique ici proposée est un modèle de gestion propre au transport, **pas** un plan réglementaire de dix axes imposé par l'OHADA.
2. **Sage X3 V12 — Dimensions (GESCCE)** : https://online-help.sagex3.com/erp/12/en-us/Content/FCT/GESCCE.htm . Cette notice mentionne des axes/dimensions pour analyser service, secteur ou véhicule. Elle indique une capacité de dimensionnement spécifique à Sage X3 qui **ne limite pas** les modèles de notre ERP.
3. **Sage X3 V12 — Expenses (GESLOF)** : https://online-help.sagex3.com/erp/12/en-us/Content/FCT/GESLOF.htm . Référence sur les imputations et clés de répartition analytiques.
4. **Claude Code — Skills** : https://code.claude.com/docs/en/skills . Un Skill comprend `SKILL.md` sous `.claude/skills/<nom>/`, ses ressources annexes et s'invoque par `/nom` ; la syntaxe sera à re-vérifier si Claude Code évolue.

## Limites essentielles

- Les dix plans proposés sont **des choix de conception**, non des obligations légales ou des objets copiés à l'identique de Sage X3.
- Dans Sage X3, la documentation parle de *dimension types*, *dimensions* et répartitions selon son vocabulaire. Ne pas déduire que toutes ces dénominations correspondent directement à la structure SQL de l'ERP.
- Sans le dépôt applicatif, impossible d'affirmer que des tables, APIs, écrans ou migrations sont déjà implémentés. Ce package ne les installe pas à lui seul.
- Aucune règle de tarification réelle Classique/VIP, commission partenaire, répartition officielle des charges, règle fiscale ou de paie n'est fournie par ce Skill : il faut la configurer avec les décisions métier et textes applicables.
- Se conformer à la séparation des sociétés/établissements, au contrôle d'accès et aux règles locales de confidentialité des données.
