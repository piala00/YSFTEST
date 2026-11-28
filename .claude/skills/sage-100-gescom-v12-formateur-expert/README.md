# Claude Skill — Sage 100 Gestion Commerciale V12 (Formateur expert)

## Objectif

Fournir à Claude une base structurée pour **enseigner, expliquer, contrôler et diagnostiquer** l'utilisation de Sage 100 Gestion Commerciale V12 Windows/SQL Server : menus, fiches, ventes, achats, stocks, tiers, règlements, statistiques, personnalisation, sécurité et fonctions avancées.

## Installer dans Claude

### Claude (interface web / desktop qui prend en charge les Skills)
1. Accéder à **Customize > Skills** (ou personnalisation / Skills selon l'interface).
2. Cliquer sur `+` puis **Create skill > Upload a skill**.
3. Sélectionner le fichier ZIP fourni, puis activer le Skill.
4. Tester : « Utilise le Skill Sage 100 Gescom V12 pour m'enseigner pas à pas le menu Structure > Articles. »

Documentation officielle : https://support.claude.com/en/articles/12512180-use-skills-in-claude

### Claude Code
Décompresser le ZIP dans `.claude/skills/` pour un projet ou dans `~/.claude/skills/` pour tous les projets. Le résultat doit contenir `.claude/skills/sage-100-gescom-v12-formateur-expert/SKILL.md`.

## Organisation

- `SKILL.md` : instructions principales et routage entre références.
- `references/` : menus et inventaire d'interface repris et enrichis du premier Skill.
- `formations/` : parcours complet fonctionnel par famille métier.
- `exercices/` : société fictive, opérations pratiques et évaluation.
- `modeles/` : fiches pour cataloguer finement chaque champ/bouton/commande ; matrice de couverture.
- `examples/` : prompts test et exemples d'usage.

## Fiabilité et limites

Sage publie la matrice V12.10 qui confirme de nombreuses fonctions, mais **pas un relevé de tous les champs et boutons** de toutes les configurations. Ce Skill doit être complété avec des captures du logiciel réel, le manuel correspondant à la sous-version et des tests dans un dossier fictif. Il ne modifie pas Sage ni ne constitue une certification Sage. Il ne remplace pas une licence ou une documentation éditeur.

## Sources

- Sage : https://fr-kb.sage.com/portal/app/portlets/results/viewsolution.jsp?solutionid=240126080738580
- Sage KB sujets Gescom : https://fr-kb.sage.com/portal/app/portlets/results/viewsolution.jsp?solutionid=211010150079480
- Sage manuels techniques : https://fr-kb.sage.com/portal/app/portlets/results/viewsolution.jsp?solutionid=230113110234020
- Sage documentation : https://www.sage.com/fr-fr/documentations-produits/
- Anthropic création Skills : https://support.claude.com/en/articles/12512198-how-to-create-custom-skills

Version de ce package : 1.0 — 21 octobre 2026.
