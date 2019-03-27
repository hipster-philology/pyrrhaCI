CLI pour contrôler la qualité des annotations faites par l'outil PyrrhaCI.

Un CLI (Command Line Interface) permet d'exécuter un script sans interface graphique.
Il s'agit d'un script de contrôle qualité et de vérifier ligne par ligne si les lemmes ainsi que leurs POS (catégorie grammaticale) et leurs MORPH (nature morphologique) sont autorisés car présents dans les listes..

Le script parse 3 fichiers cités dans une fichier de configuration pyrrhaci.yml : 
- fichier lemma.txt
- fichier POS.txt
- fichier morph.tsv

Le script vérifie d'une part si les annotations sont autorisées pour chacun de ces fichiers puis si les annotations sont autorisées ensemble ( règles indiquées dans le fichier additional_rules) et si les règles doivent être ignorées ( fichier ignore)
Le code compare donc ces données avec le fichier input_example.tsv qui contient les POS et MORPH autorisées pour chaque lemme et token (annotation).

Ce script CLI a été réalisé en mars 2019 dans le cadre d'un devoir de M2 Technologies numériques appliquées à l'histoire de l'Ecole nationale des Chartes, par deux étudiantes Marie-Caroline Schmied et Emilie Blotière.
