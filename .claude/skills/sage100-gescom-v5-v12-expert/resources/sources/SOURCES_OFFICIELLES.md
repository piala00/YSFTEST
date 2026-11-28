# Références officielles et niveau de preuve

- **SAGE100-MANUELS** — Officiel Sage, manuels techniques : Objets métiers, programmes externes, SQL, migrations. [vérifié] https://fr-kb.sage.com/portal/app/portlets/results/viewsolution.jsp?solutionid=230113110234020
- **SAGE100-STRUCT-V12.20** — Officiel Sage, structure SQL V12.20, 447 pages, juillet 2026, tous les champs et jointures. [vérifié] https://fr-kb.sage.com/portal/app/portlets/results/viewdocument.jsp?solutionid=230113095648937
- **SAGE100-DEC-FONCT** — Officiel Sage, découpage fonctionnel détaillé Comptabilité et Gescom, V11 compatible V12. [vérifié] https://fr-kb.sage.com/portal/app/portlets/results/viewsolution.jsp?solutionid=240126081806063
- **SAGE100-DEC-V12.10** — Sage, découpage Sage 100 Gestion Commerciale V12.10, selon page consultée auparavant. [lien à contrôler] https://fr-kb.sage.com/portal/app/portlets/results/viewsolution.jsp?solutionid=240126080738580
- **BI-REPORTING** — Sage France, modules BI historique local et fonctions Excel. [vérifié] https://www.sage.com/fr-fr/produits/sage-bi-reporting/
- **X3-DOC** — Sage X3 V12, aide technique officielle. [vérifié] https://online-help.sagex3.com/erp/12/fr-fr/Content/Tech%20Help/TH_LP.htm
- **X3-SCREEN** — Sage X3 V12, dictionnaire des écrans/onglets/champs. [vérifié] https://online-help.sagex3.com/erp/12/fr-fr/Content/FCT/GESAMK.htm
- **X3-WINDOW** — Sage X3 V12, dictionnaire fenêtres, boutons et menus. [vérifié] https://online-help.sagex3.com/erp/12/fr-fr/Content/FCT/GESAWI.htm
- **X3-SCREEN-DB** — Sage X3, tables superviseur décrivant écrans et champs. [vérifié] https://online-help.sagex3.com/erp/12/fr-fr/Content/FCT/PRQ_AFC_GESAMK.htm
- **X3-WINDOW-DB** — Sage X3, tables superviseur fenêtres et boutons. [vérifié] https://online-help.sagex3.com/erp/12/fr-fr/Content/FCT/PRQ_AFC_GESAWI.htm
- **X3-DEV** — Sage, référence plateforme développeur X3. [vérifié] https://developer.sage.com/x3/docs/latest/guides/x3-development-platform/platform-reference
- **X3-API** — Sage, API X3 REST et SOAP. [vérifié] https://developer.sage.com/x3/docs/latest/guides/x3-development-platform/platform-reference/api-guide
- **X3-TEMPLATES** — Sage, modèles X3 objets, écrans, fenêtres. [vérifié] https://developer.sage.com/x3/docs/latest/guides/x3-development-platform/templates

## Sources : précisions d'usage

- Les docs Sage 100 V12 ne s'appliquent pas mécaniquement aux versions V5–V10 ; établir des différentiels de versions *observés*.
- Les bases Sage 100 Gestion Commerciale (`.GCM`) et Comptabilité (`.MAE`) doivent être identifiées par produit : des tables peuvent porter le même nom mais avoir des règles différentes.
- Les documents V12.20 sont des **structures de bases**, pas une cartographie exhaustive des contrôles UI.
- Ne jamais utiliser la documentation **Sage 100 USA** ou Sage 100 **Allemagne** comme si c'était Sage 100 France SQL Server.
- Sage BI Reporting historique n'est pas Sage Business Reporting SaaS.
- Sage X3 est un produit distinct de Sage 100 et n'utilise pas les mêmes tables ni API.
