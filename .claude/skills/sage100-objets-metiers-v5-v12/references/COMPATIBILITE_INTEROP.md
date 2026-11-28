# Sage 100 Objets Métiers — matrice obligatoire V5–V12

| Dimension | À mesurer | Pourquoi |
|---|---|---|
| Version Sage | Version majeure, sous-version, build | Ruptures fonctionnelles et objets ajoutés |
| SDK installé | Version TypeLib et document associé | Signatures exactes des classes et méthodes |
| Architecture | x86/x64 du composant, hôte et Python | COM in-process : architecture doit correspondre |
| Contexte | Session Windows, service, DCOM selon doc | Droits et initialisation peuvent changer |
| Licence | Modules activés, options, droits utilisateur | Une méthode connue peut être interdite |
| Connexion | Authentification et base cible | Sécurité, isolation de sociétés |
| Erreurs | HRESULT, messages localisés | Différence entre tentative et écriture effective |
| Transactions | Commit/rollback réel selon API | Éviter documents partiels |
| Idempotence | Clé ERP/Sage et lookup | Éviter doubles factures |
| Synchronisation | Date/modification, clés et statut | Détection des changements et reprises |

**Interdiction** : produire un exemple de code de création COM avec classe/méthode non vérifiée par la documentation SDK de la version installée.

## Exemple de contrat d'adaptateur (conceptuel ; pseudo-interface, pas SDK)
`create_invoice(external_id, customer_code, lines, dates, tax_context) -> {source_document_id, status, warnings}`

Il appartient à l'adaptateur d'appeler les Objets Métiers exacts selon le build et de valider les effets de bord Sage. La réponse « résultat inconnu » ne doit jamais être rejouée automatiquement comme si aucune facture n'avait été créée.
