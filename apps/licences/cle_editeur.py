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
    # Identité publique de l'éditeur (propriétaire du logiciel).
    # Empreinte SHA-256 de la clé brute : DA36A89B5B432DD7CA7D03CB811F8AE806F4250A9CAA49FAEC62354488F8AD0B
    # (à comparer avec le guide remis au client). La clé privée reste dans le coffre du propriétaire.
    "L7JRWfjuNAWtOk/yEI+MZnp/NlHR02IhdFUpFCTxVrQ=",
]
