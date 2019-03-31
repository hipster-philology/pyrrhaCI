# CLI de contrôle pour l'outil Pyrrha.

Un CLI permet d'exécuter un script sans interface graphique.
Il s'agit d'un script de contrôle qualité qui vérifie les annotations de l'outil [Pyrrha](https://github.com/hipster-philology/pyrrha) ligne par ligne. Si les lemmes ainsi que les POS (catégorie grammaticale) et les MORPH (nature morphologique) sont autorisés, car présents dans les fichiers correspondants, le CLI renvoie un message pour signaler qu'il n'y a pas d'erreur. S'il y en a, le CLI renvoie un commentaire et le numéro de la ligne où se trouve l'erreur.

## Les fichiers à fournir au CLI

Ce CLI fonctionne avec deux fichiers d'entrée, un fichier de configuration au format .yml et un fichier à contrôler au format .tsv. Ce fichier doit être composé de 4 colonnes : le token, le lemme, la POS et la morph.

## Les fichiers obligatoires

Le fichier config.yml doit nécessairement contenir le chemin de trois fichiers: 

*fichier lemma.txt
  *sous forme de liste
  *liste tous les lemmes autorisés dans l'outil
*fichier POS.txt
  *liste sur une seule ligne toutes les catégories grammaticales sous formes d'abbréviations
  *chaque chaîne de caractère est séparée par une virgule
*fichier morph.tsv
  *liste toutes les catégories grammaticales  : genre, cas , nombre et conjugaison
  *sous forme de 2 colonnes, la seconde ayant l'intérêt d'être intelligible pour l'être humain.
  *seule la première colonne 'label' est parsée et verifiée par le script.

## Les fichiers optionnels

Le fichier config.yml peut aussi contenir:

- Des règles 'ignore', qui prévalent sur les autres règles et normes. Chaque règle est composée de 3 colonnes : index_de_catégorie_erreur, index_de_token et un message intelligible qui explique l'exception. Ces trois parties doivent être séparées par des :. 
- Un fichier de règle additionel. C'est un .tsv, qui est composé de 6 colonnes et contient des règles autorisant ou interdisant la combinaison des POS et MORPH.

## Forme du fichier de configuration

Le fichier config.yml doit avoir cette forme:
allowed_lemma: "fichier.txt"
allowed_pos: "fichier.txt"
allowed_morph: "fichier.tsv"
additional_rules: "fichier.tsv"
ignore:
-"AllowedLemma:8:Estre5 est particulier au projet"

Le script vérifie d'une part si les annotations sont autorisées par chacun des fichiers obligatoires puis si les annotations sont autorisées ensemble (règles indiquées dans le fichier additional_rules) et si les règles doivent être ignorées (règle ignore).

Ce script CLI a été réalisé en mars 2019 dans le cadre d'un devoir de M2 Technologies numériques appliquées à l'histoire de l'Ecole nationale des Chartes, par deux étudiantes Marie-Caroline Schmied et Emilie Blotière sous le regard avisé de leur professeur Thibault Clérice.


## Pour installer le CLI:

*Installer Python 3
*Cloner ce repository
*Installer et activer un environnement virtuel
*Installer le CLI en faisant python setup.py install dans votre terminal
*Lancer le CLI en faisant pyrrha_ci  "config.yml" "fichier à contrôler" dans votre terminal


