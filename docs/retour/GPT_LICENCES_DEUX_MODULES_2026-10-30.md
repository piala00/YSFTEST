# GPT — outil propriétaire à deux modules et dossier unique — 30/10/2026

Nouvelle demande du propriétaire : séparer génération de clé d'installation et émission de licence, ne pas demander
de société pour un code, regrouper clé privée, clé publique et licence pour les retrouver. Préserver #11 à #20.

## Fonctionnement réalisé

- Deux onglets : Installation ; Licence. L'identité de signature se gère dans l'onglet Licence.
- Code 4×6 généré avec secrets, sans société, édition, clé, déverrouillage ou mot de passe, également en console.
  L'ancien parcours de clé d'installation signée, explicitement alimenté avec --cle/--client/--edition, reste lisible.
- Un dossier propriétaire choisi en haut : coffre.dat chiffré (PKCS8 DER), parametres.dat binaire, licences .erplic et
  registres. Le formulaire ne propose plus deux destinations distinctes pour les clés et les licences.
- Nouvelles paires binaires par défaut, y compris en console ; création PEM/public texte seulement via --ancien-format.
- Regroupement d'une identité existante : même paire, coffre réencodé/chiffré, public binaire, originaux conservés,
  refus d'écraser un autre éditeur. Les registres sont repris pour conserver la numérotation et les licences disponibles
  sont récupérées si leur signature correspond ; les fichiers externes absents restent référencés dans l'historique.
- Déverrouillage du coffre une fois par session ; changement de dossier ou bouton Verrouiller efface le cache mémoire.
- Export client sur liste fermée : licence, identité publique et notice ; aucun coffre, registre ni autre fichier du dossier.
  La notice utilise Administration > Licence et n'annonce plus qu'un fichier public remplaçable suffit à changer l'autorité.

## Protection et limites explicites

Le fichier public est binaire et reconnaissable par le logiciel. Il n'est pas secret ni chiffré « comme le privé » :
connaître la clé publique Ed25519 ne permet pas de déduire la clé privée. Un nom neutre/binaire évite la lecture de
confort, sans être une défense cryptographique contre un attaquant. Le coffre privé est réellement chiffré.

Le code court historique de 120 bits est une référence d'installation/essai. Dans le client actuel, vérifier sa forme
n'est PAS vérifier qu'il a été émis par le propriétaire. Cette PR ne lui attribue pas un faux rôle de verrou universel.
L'autorisation commerciale reste la licence signée, attachée au serveur, vérifiée par l'identité intégrée au binaire.
Un blocage d'installation fondé uniquement sur un code court autonome hors ligne ne peut pas être promis sans
mécanisme supplémentaire de confiance (catalogue signé, vérification distante ou autorisation signée plus longue).
La clé publique commerciale n'a toujours pas été fournie : aucun nouveau root privé n'est créé pour le propriétaire
et aucune identité de production n'est inventée dans le dépôt. Le client livré demeure en essai jusqu'à personnalisation.

## Validation

18 tests locaux de l'outil effectivement exécutés (sans Django) : formats, ancien/nouveau coffre, déverrouillage,
module installation sans clés ni société, CLI sans mot de passe, regroupement/identité, numérotation, refus de collision,
export client exact et refus d'identité altérée. La suite complète et les parcours GUI réels suivent en CI.

Le mode interface-essai utilise toujours un répertoire et une identité fictifs jetables : deux onglets construits,
code généré avant toute paire, coffre créé, demande fictive ouverte, licence produite dans le même dossier,
ZIP client vérifié, coffre verrouillé et second code généré. Exécution source sous écran virtuel et .exe Windows.
Aucune fusion, aucun déploiement, aucune production ni clé privée réelle touchée.
