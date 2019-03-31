CLI pour contrôler la qualité des annotations faites par l'outil PyrrhaCI.

Un CLI (Command Line Interface) permet d'exécuter un script sans interface graphique.
Il s'agit d'un script de contrôle qualité qui vérifie ligne par ligne si les lemmes ainsi que leurs POS (catégorie grammaticale) et leurs MORPH (nature morphologique) sont autorisés car présents dans les fichiers correspondants.

Le script parse 3 fichiers cités dans une fichier de configuration "config.yml" : 
- fichier lemma.txt
-   --> sous forme de liste
-   --> liste tous les lemmes autorisés dans l'outil
- fichier POS.txt
-   --> liste sur une seule ligne toutes les catégories grammaticales sous formes d'abbréviations
-   --> chaque chaîne de caractère est séparée par une virgule
- fichier morph.tsv
-   --> liste toutes les catégories grammaticales  : genre, cas , nombre et conjugaison
-   --> sous forme de 2 colonnes, la seconde ayant l'intérêt d'être intelligible pour le cerveau humain.
-   --> seule la première colonne 'label' est parsé et verifié par le script.
De manière optionelle, le fichier config.yml contient également des règles 'ignore', qui prévalent les autres règles et normes, également parsées par le code. Chaque règle est composée de 3 colonnes : index_de_catégorie_erreur, l'index_de_token et un message intelligible qui explique la clef. Chaque colonne est séparée par :. 
De même, un fichier additional_rules peut être fourni. Le fichier additional_rules.tsv est composé de 6 colonnes et contient des règles autorisant ou interdisant la combinaison des POS et MORPH.

Le fichier input_example.tsv est composé de 4 colonnes : le token, le lemme, la POS et la morph. Chaque ligne précise donc les lemmes, POS et morph pour le token.

Le script vérifie d'une part si les annotations sont autorisées par chacun de ces fichiers puis si les annotations sont autorisées ensemble (règles indiquées dans le fichier additional_rules) et si les règles doivent être ignorées (fichier ignore).

Ce script CLI a été réalisé en mars 2019 dans le cadre d'un devoir de M2 Technologies numériques appliquées à l'histoire de l'Ecole nationale des Chartes, par deux étudiantes Marie-Caroline Schmied et Emilie Blotière sous le regard avisé de leur professeur Thibault Clérice.

Pour faire fonctionner le CLI


