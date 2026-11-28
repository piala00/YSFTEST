# DSF Cameroun — R8

## Documents et modèles

La DGI décrit deux formats de droit commun : normal et SMT (D03), comprenant informations générales, états financiers avec notes et tableaux fiscaux. Les modèles banque/assurance existent séparément ; ils ne sont pas transposables à une société commerciale. Les organismes sans but lucratif relèvent d’un cadre distinct qui n’est pas traité par ce paquet.

Les fichiers D01 etD02 ont une date de 2021 et restent proposés sur la page publiqueD05 consultée. Leur structure est inventoriée dans STRUCTURE_DSF.csv : tous les onglets du classeur sont recensés. NOTES_ET_ANNEXES_DSF.csv conserve la grille des notes et annexes, notamment les CF du normal et les T du SMT. La publication de ces fichiers ne certifie ni leur absence d’erreur ni leur identité avec le fichier servi par le portail au contribuable en campagne 2026.

## Dépôt électronique

Le guide D04 présente la connexion depuis les e-services DGI, la création d’une DSF, la sélection de la période/fréquence/type, puis la saisie ou le chargement du fichier prévu par l’interface et la gestion des soldes d’impôts. Un ancien guide décrit le chargement d’Excel ; la procédure2026 doit être vérifiée sur le compte concerné, sans envoyer de déclaration pendant cette étude. Ne pas déclarer un fichier XML ou CSV propriétaire compatible sans schéma officiel. La création d’un PDF pour imprimer ne vaut pas transmission.

Le modèle technique à conserver est celui téléchargé au moment du dépôt, avec son nom, son empreinte et sa version. Le programme doit mapper les données vers ce modèle et produire un journal des contrôles. Ne pas renommer, déplacer ou supprimer des colonnes en supposant que le portail reconstruira leur signification.

## Échéances ordinaires relevées, hors prorogation particulière

CGI2026 art.18 : déclaration annuelle des résultats au 15mars pour la structure grandes entreprises,15avril pour centres moyens/spécialisés et15mai pour centres de fiscalité locale et particuliers. Pour les contribuables IGS visés, C44(3) prévoit la DSF au 15mai. La déclaration IGS visée àC41 a une échéance au 15avril : ne pas confondre ces deux déclarations. Les prorogations éventuelles d’une campagne doivent être recherchées séparément ; ce paquet n’en affirme aucune.

Le guide illustrant la sélection2026 ne prouve pas que toutes les déclarations déposées en2026 portent sur l’exercice2026. Stocker séparément exercice comptable, année fiscale déclarée et date de dépôt.

## États et calculs

L’AUDCIF signé O01 (article 26, page 22 imprimée) impose au normal bilan, résultat, flux et notes. Son article 28 prévoit pour le SMT bilan, résultat et notes avec prise en compte des variations significatives de stocks, créances et dettes. Le SMT n’est donc pas un simple solde de caisse.

ETATS_FINANCIERS_SYSCOHADA.csv décrit les références et libellés des modèles DGI et les traces de formules. Les références SMT_... sont des identifiants internes ajoutés pour distinguer les lignes ; elles ne sont pas des références officielles OHADA. Les comptes de rattachement non prouvés sont marqués NON_ETABLI. La copiePROJET ne sert pas à compléter silencieusement ces colonnes.

Les expressions du modèle 2021 doivent être auditées ; voir ANOMALIES_MODELES_DGI.csv. Un exemple significatif est l’omission de l’avance sur immobilisations AP dans la formule AZ. Les libellés et codes sont conservés tels qu’extraits, même lorsqu’ils contiennent une faute ; les corrections d’interface devront être documentées séparément.

## Contrôles proposés — recommandations pour le développement

Vérifier l’équilibre actif/passif, la concordance du résultat du bilan avec celui du compte de résultat, la variation de trésorerie et l’exclusion des mouvements sans flux. Contrôler les comptes à solde inhabituel et les comptes non mappés. Ne pas sommer une rubrique de regroupement et ses enfants dans le même total. Distinguer les notes OHADA des annexes fiscales camerounaises. Tant que les mappings et le modèle de campagne ne sont pas validés, conserver la fonction d’export en mode de préparation contrôlée.
