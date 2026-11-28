# Contrats à construire pour ton ERP — différencier structure et métier

Le dictionnaire SQL **ne constitue pas à lui seul un contrat métier**. La section décrit les futurs contrats à faire valider, sans attribuer à Sage des règles non confirmées.

| Objet ERP | Sources candidates | Clé métier attendue | Validations indispensables |
|---|---|---|---|
| Document de vente | F_DOCENTETE | Source + DO_Type + DO_Piece | Provenance, statut, validation, comptabilisation, exercice |
| Ligne de vente | F_DOCLIGNE | Source + DL_No ; lien DO_Type/DO_Piece | Lignes texte/sous-totaux, taxes, remises, unités |
| Référentiel article | F_ARTICLE | Source + AR_Ref | Gamme, conditionnement, historique de changement |
| Stock dépôt | F_ARTSTOCK, F_GAMSTOCK | Source + AR_Ref + DE_No + gammes éventuelles | Disponible vs réel, suivi par lots, transferts |
| Encaissement | F_CREGLEMENT, F_REGLECH, F_DOCREGL | Source + RG_No et DR_No | Imputé, non imputé, acomptes, annulations |
| Écriture comptable | F_ECRITUREC | Source + EC_No | Journal, période, sens, lettrage, clôture, compte |
| Correspondance facture/écriture | F_ECDOCDN | Source + type de pièce + numéro + lien écriture | Existence dans base réelle, intégrité des rapprochements |

**Interdictions métier** :
- Ne jamais calculer le CA comme la somme des `DL_MontantHT` de toutes les pièces : commandes et BL créeraient des doublons.
- Ne jamais assimiler `DO_Type=6` à une facture normale sans considérer `DO_Provenance`; considérer aussi le type 7.
- Ne jamais calculer la disponibilité d'un article uniquement à partir des quantités de `F_DOCLIGNE` sans un modèle de mouvement validé.
- Ne jamais rapprocher comptabilité et gestion commerciale seulement par un numéro de pièce dépourvu de contexte de base, type et exercice.
- Ne jamais effectuer `UPDATE`/`DELETE` dans Sage au motif d'une correction de synchronisation.

**Réconciliation minimale sur base démo** : nombre de pièces par domaine/type/provenance ; totaux factures par période ; détail des mouvements et dépôts ; règlements avec/après imputation ; balance des débits/crédits par journal/période ; contrôle des documents transformés et archives.
