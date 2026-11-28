"""Clé(s) publique(s) de l'éditeur, GRAVÉES dans le code (ce module est compilé en natif : .pyd).

Pourquoi ici et pas dans un fichier texte : un fichier texte livré à côté du programme peut être remplacé par un
pirate (sa propre clé → fausses licences). Gravée dans un module compilé en code machine, la clé ne peut plus être
échangée sans recompiler le programme avec une chaîne C — la barre est beaucoup plus haute.

Le propriétaire envoie le contenu de cle-publique.txt (une ligne base64, créée par l'outil de licences) ; il est
collé ci-dessous, une chaîne par ligne. Tant que la liste est vide, le logiciel reste en période d'essai et accepte,
pour le développement seulement, une clé placée dans cle_publique.txt (fichier remplaçable, donc jamais seul en
production).

La clé PRIVÉE, elle, ne figure jamais dans le dépôt, l'exécutable ni l'installateur.
"""
CLES = [
    # "Base64DeLaClePubliqueDuProprietaire=",
]
