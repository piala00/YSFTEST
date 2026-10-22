# Réponses et limites

Date de recherche : 22 octobre 2026.

## D-autorisations — Liste exacte des autorisations V12

**NON_ETABLI**. Les expressions proposées dans la demande ne sont pas certifiées comme liste V12 par les sources recueillies. Ne pas choisir arbitrairement entre Tout interdire et Interdire la lecture et l’écriture.

Sources : S01,S03,S04 ; S01 tables de protection ; S03/S04 Autorisations d’accès.

À établir : Capturer la liste déroulante V12 complète, selon type de fonction et profil.

## D-visible — Commande interdite masquée ou grisée

**NON_ETABLI**. Le découpage fonctionnel décrit l’offre, pas le comportement d’un menu interdit pour un profil donné.

Sources : S03,S04 ; Autorisations d’accès.

À établir : Comparer compte administrateur et profil limité, mode d’interface et offre identiques.

## E-lieu — Emplacement et libellé de Fichier lié

**SANS_BUILD**. Les matrices des deux applications donnent Fichiers liés dans Fichier > Paramètres société > Identification. Le pluriel est celui de la matrice. Le chemin À propos de votre société n’est pas confirmé ici comme libellé V12. Les colonnes locales le donnent Standard ; les cinq colonnes hébergées Non disponible.

Sources : S03,S04 ; S03 PDF 1 L19 ; S04 PDF 1.

À établir : Relever le chemin exact dans les deux interfaces V12 et l’offre cible ; ne pas généraliser le chemin local au cloud.

## E-donnees — Données partagées et écritures transférées

**PARTIEL**. Le référentiel comptable et les tiers sont liés aux objets commerciaux ; les factures, règlements et engagements sont comptabilisés par un traitement. L’existence du lien ne signifie pas qu’une facture est déjà comptabilisée. Les familles/articles fournissent des affectations comptes/taxes ; cette configuration ne rend pas tous les fichiers de chaque produit identiques.

Sources : S01,S02,S06,S20 ; S01 F_COMPTET/F_COMPTETG ; S02 applications ; S06 lancement.

À établir : Inventaire exhaustif des objets partagés, données propres à chaque logiciel et sens de propagation par champ V12.

## E-invite — Sens d’invité et utilisateur

**PARTIEL**. Une procédure Sage pour GC multiposte liée à une Comptabilité monoposte affecte le profil comptable au groupe invité et autorise Gestion commerciale côté GC. Elle documente un scénario d’accès. Elle ne définit pas invité comme lecture seule et ne garantit pas une absence de consommation de licence V12.

Sources : S05 ; Description et résolution.

À établir : Matrice V12 des capacités invité/utilisateur et règles contractuelles de licence selon offre et simultanéité.

## E-profils — Droits communs ou séparés

**FAIT_TECHNIQUE_V12.20**. Le manuel V12.20 répertorie F_PROTECTIONCPTA/F_EPROTECTIONCPTA et F_PROTECTIONCIAL/F_EPROTECTIONCIAL. Il existe donc des structures de protection propres aux applications. Cela ne prouve pas à lui seul où chaque profil est stocké ni tous les mécanismes de propagation.

Sources : S01 ; PDF 6 et 11.

À établir : Décodage complet des profils et éventuelles synchronisations ; aucune modification SQL directe autorisée.

## E-identifiants — Identifiants des fichiers liés

**PARTIEL**. Le Driver Sage ODBC documente les mêmes utilisateur/mot de passe pour les fichiers liés. Les Objets Métiers documentent aussi une connexion avec deux objets et CptaApplication si les identifiants diffèrent. Les contraintes dépendent donc du canal ; identifiants communs ne signifie pas droits de menus uniques.

Sources : S17,S18 ; Résolution §4 / exemples OM.

À établir : Relever le canal effectivement utilisé et les droits effectifs dans chacun des logiciels.

## F-fenetre — Options de mise à jour comptable

**SANS_BUILD**. L’aide officielle décrit la sélection des dates, souches, factures et catégories, le journal modifiable, les factures/règlements/engagements et la comptabilisation ou l’export. L’option associant factures et règlements est décrite. Les factures doivent être validées.

Sources : S06 ; Prérequis / lancement.

À établir : Relevé V12 exact des libellés, valeurs initiales, regroupement, date d’écriture retenue et message en période fermée.

## F-validation — Modifier une facture validée avant comptabilisation

**FAIT_TECHNIQUE_V12.20**. Le chapitre de sécurisation couvre les documents de vente DO_Domaine=0, DO_Type 6 à 7, DO_Valide=1 et leurs données sécurisées. Le fait d’attendre la mise à jour comptable n’autorise pas à considérer ces données comme librement modifiables. Ne pas étendre cette conclusion à tous les champs annexes ni à tous les achats.

Sources : S01 ; PDF 440 / imprimée 439.

À établir : Champs annexes éventuellement modifiables dans l’UI, achats, et messages exacts par droit.

## F-droit — Droit de comptabiliser distinct des factures

**PARTIEL**. La matrice répertorie Mise à jour comptable et les documents de facture comme fonctions différentes. Cela n’établit pas la dépendance précise entre autorisations V12 ni l’autonomie effective du droit.

Sources : S04 ; Menu Traitement.

À établir : Tester profil facture seule, comptabilisation seule, aucun droit et administrateur ; relever dépendances et messages.

## E-parametres — Impact des tiers et paramètres sur le lien

**PARTIEL**. Les catégories et taxes influencent les affectations comptables des nouveaux documents ; une modification de taxe/catégorie n’est pas rétroactive sur les pièces antérieures selon l’aide. La reprise du payeur et du compte principal dépend du contexte de création. Le nom affiché de société ne prouve pas l’identité de la base liée.

Sources : S01,S18,S20,S21 ; Tiers et connexions ; paramétrage taxes ; note facture sans TVA.

À établir : Propagation champ par champ de la raison sociale, coordonnées, NIU, devise, périodes, tiers et droits ; ne pas supposer un rafraîchissement de toutes les pièces historiques.
