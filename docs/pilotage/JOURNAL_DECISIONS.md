# Journal des décisions et clarifications

| ID | Date / origine | Décision ou tension | Traitement |
|---|---|---|---|
| DEC-001 | Conversation et #24, 31/10 | Pas de fusion, déploiement, suppression réelle ou écriture Sage sans autorisation distincte | Appliqué ; aucune action de production dans ces lots |
| DEC-002 | Conversation, réponse « pas besoin » à la demande de public | Continuer sans nouvelle demande de clé ; préserver l’identité existante | Correctifs/tests fictifs poursuivis ; vraie personnalisation bloquée, aucun succès PC réel revendiqué |
| DEC-003 | Conversation / C-011 | Société retient 15 %, assiette brute ou nette inconnue | Hypothèses de simulation identifiées ; aucune règle réelle décidée |
| DEC-004 | Conversation, puis #24 | Simulation dans le vrai logiciel et nouveau gestionnaire indépendant | Cadrer un complément ; conserver .erpsim et l’import intégré, ne pas supprimer l’existant |
| DEC-005 | AGENTS/#24 et audit architecture #22 | Dix plans visibles demandés, onze axes présents dans le code | Mapping à valider ; aucune suppression arbitraire |
| DEC-006 | #1 commentaire6536570880 | Hardware ID renforcé, key_id et rotation sans perdre les licences actuelles | Garder l’identifiant historique pour les P0 ; migration et TPM séparés avant basculement |
| DEC-007 | #1 commentaire6536570880 | Autorisation d’installation distincte de licence d’exploitation | .erpinst avec domaine séparé, key_id/matériel/édition/échéance dans #25 ; .erplic reste l’exploitation |
| DEC-008 | Conversation initiale / #1 clarification | Demande ancienne d’import de clé privée dans le client, puis privé exclusivement chez l’éditeur | Ne jamais distribuer le coffre ; seul public autorisé intégré au client |
| DEC-009 | Anciennes recommandations GitHub | Suggestion de fusion quand les contrôles sont verts | Contradictoire avec DEC-001 : non appliquée ; CI n’autorise aucune fusion |
| DEC-010 | Conversation du propriétaire le 31/10, relayée dans [#24](https://github.com/piala00/YSFTEST/issues/24#issuecomment-6543383987) | Organiser les tâches depuis GitHub et poursuivre les développements/tests/PR sans confirmation courante | Clarification de Q-003, aucun ID d'exigence en double. DEC-001 conserve ses limites ; contradictions et décisions non tranchées consignées, tâches indépendantes poursuivies. Pas de garantie d'exécution hors session. |
| DEC-011 | Transmission utilisateur U5/U6, prioritaire sur U4 et ancienne revue du 24/10 | Règlement avec zéro/une/plusieurs factures et attente de rattachement, fenêtres indépendantes | B-002/A-003 ; ne pas réintroduire la règle historique d'une facture unique obligatoire. Les propositions de la revue ancienne ne deviennent pas des décisions utilisateur. |

Aucune « validation propriétaire » mentionnée par un commentaire tiers ne remplace une autorisation de l’action irréversible elle-même. Conserver les décisions précédentes lors des futures modifications.

Sources directes : [activation6536186700](https://github.com/piala00/YSFTEST/issues/1#issuecomment-6536186700), [installation6536201349](https://github.com/piala00/YSFTEST/issues/1#issuecomment-6536201349), [architecture6536570880](https://github.com/piala00/YSFTEST/issues/1#issuecomment-6536570880), [plan24](https://github.com/piala00/YSFTEST/issues/24), [AGENTS.md](../../AGENTS.md).
