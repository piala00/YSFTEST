# Protocole de reprise en lecture seule

## 1. Identifier et figer le périmètre

Consigner produit, version/build, dossier, exercice et schéma. Travailler de préférence sur une copie restaurée autorisée ou un export cohérent pendant une fenêtre convenue. Ne pas changer les options d’isolation de production pour les besoins du modèle. Un compte limité à la lecture et à la visibilité nécessaire des métadonnées suffit au périmètre proposé ; aucun mot de passe n’est livré.

Définir : référentiels seuls, historique, soldes d’ouverture ou créances ouvertes. Éviter d’importer simultanément un historique déjà repris et ses reports à nouveau comme nouveaux mouvements. Enregistrer un identifiant de dossier source et un identifiant de lot dans l’ERP pour rendre les imports répétables sans doublons.

## 2. Relever les colonnes réelles

Exécuter `scripts/01_metadata_lecture_seule.sql` dans la base déjà sélectionnée. Il ne change pas la base et conserve les colonnes attendues absentes dans son résultat. Identifier les schémas concurrents avant de remplacer le schéma dans les autres modèles. Une table sans ligne de métadonnées peut être absente ou invisible au compte utilisé. Ne pas créer la colonne manquante dans Sage.

Archiver le résultat technique dans le dossier de migration privé : schéma, table, colonne, type déclaré/système, longueur en octets, précision, échelle, NULL, identité et calculé. Ajouter le build et la date de relevé. Contrôler séparément PK, index et liens physiques si nécessaires : les règles du manuel ne les certifient pas. Vérifier les paramètres P_UNITE et P_CATTARIF avant toute jointure sur cbIndice.

## 3. Profiler avant de filtrer

Adapter `scripts/02_profil_ecritures.sql` au schéma observé. Le premier résultat regroupe toutes les écritures par norme, centralisation, clôture et type de journal, y compris les journaux non retrouvés. Le second signale les comptes ou journaux orphelins. Aucun filtre de norme ou de simulation n’est appliqué dans ces profils.

Pour une vue nationale, proposer `EC_Norme IN (0,1)` ; pour IFRS, `(0,2)` : déductions des codes M01, à rapprocher des éditions Sage. Garder un rapport des codes inattendus et des NULL au lieu de les éliminer silencieusement. `JO_Type=4` désigne Situation ; son exclusion dépend du périmètre choisi. Aucun champ de simulation universel n’a été confirmé. Ne pas importer une règle trouvée pour Sage FRP 1000 ou Ciel.

Définir le traitement des lignes centrales après mesure. Vérifier période et jour avant de reconstituer la date comptable. Ne pas filtrer l’exercice d’après la seule date de saisie EC_Date. Garder séparément débits et crédits selon EC_Sens et contrôler le sens inconnu.

## 4. Exporter et contrôler

Choisir un export CSV technique UTF-8 avec séparateur et convention NULL explicites, dates ISO, nombres sans séparateurs de milliers et échappement correct des retours ligne. Conserver les références en texte et fixer la représentation décimale. Les CSV du présent skill sont des catalogues documentaires, pas des fichiers d’import Sage.

Produire un manifeste par lot : version de mapping, source anonymisée, périmètre, date de coupe, nombre de lignes par fichier, empreinte SHA-256 et totaux de contrôle. Préférer une extraction cohérente : ne pas additionner des fichiers pris à des dates incompatibles. Ne pas utiliser NOLOCK comme garantie de cohérence. Les lectures peuvent consommer des ressources : mesurer et découper sans casser la cohérence.

## 5. Importer dans l’ERP et rapprocher

Charger dans une zone intermédiaire propre à l’ERP. Vérifier unicité, relations, codes connus, arrondis, références trop longues et absence de doublons de lot. Conserver les tiers en sommeil utiles à l’historique et les écritures sans tiers. Garder les rejets détaillés ; aucun remplacement automatique d’un code inconnu par zéro.

Comparer à Sage : balance générale, total débit/crédit par journal et période, soldes par compte/tiers et nombre de lignes. Pour articles, comparer unités, tarifs et stock par dépôt ; le prix d’achat de fiche n’est pas une valorisation CMUP. Documenter les écarts et bloquer la bascule tant qu’ils restent inexpliqués.

## 6. Recette et retour arrière

Restaurer une sauvegarde de l’ERP de recette, rejouer le même lot deux fois et vérifier l’absence de doublons. Faire accepter les résultats métier avant bascule. Préserver la source Sage et le lot brut. Le retour arrière concerne l’import ERP ; aucun script du paquet n’écrit dans Sage.

Ce protocole est une proposition de conception. Les faits Sage viennent de M01, la lecture des types de MS01. Aucune exécution sur une base client n’a eu lieu.
