# -*- coding: utf-8 -*-

# nous importons les librairies nécessaires à l'exécution du code.
import yaml
import csv
import click


# Nous définissons une classe pour les règles additionnelles que nous nommons Rule.
# La définition d'une classe permet de transmettre des propriétés aux objets qui héritent de cette classe.
# Nous l'utilisons pour ne pas avoir à utiliser l'indexation dans la boucle.
class Rule:
    ruleType = ""  # allowed_only | forbidden
    catIn = ""  # POS
    catOut = ""  # MORPH
    valIn = ""
    valOut = ""

    # les 2 arguments de la méthode sont self (par convention) et regle qui correspond à chaque colonne du fichier.
    def __init__(self, regle):
        self.ruleType = regle[1]
        self.catIn = regle[2]
        self.catOut = regle[3]
        self.valIn = regle[4]
        self.valOut = regle[5]


# Nous définissons une classe pour les règles à ignorer indiquées dans le fichier config.yml.
class Ignore:
    index = ""
    token = ""
    commentaire = ""

    # le premier arguement de la définition d'une classe est toujours par convention self, ign correspond à chaque colonne du fichier.
    def __init__(self, ign):
        # le .split, permet de créer une liste à partir d'une chaine de caractère. Le séparateur est indiqué entre ''.
        ign = ign.split(':')
        self.index = ign[0]
    # Nous forçons le type du token, pour qu'il soit du même type que le nombre de lignes.
        self.token = int(ign[1])
        self.commentaire = ign[2]


# Nous créons une classe pour parser le fichier d'exemple:
class Annotation:
    lemme = ""
    pos = ""
    morph = ""

    # là aussi par convention, nous reprenons le paramètre self et y ajoutons annotation. La première colonne n'est pas
    # prise en compte, car on n'utilisera jamais les tokens.
    def __init__(self, annotation):
        self.lemme = annotation[1]
        self.pos = annotation[2]
        self.morph = annotation[3]

# L'utilisation de class améliore la lisibilité du code. Nous avons ainsi un namespace local qui décrit les attributs.


@click.command()
# Notre CLI a besoin de deux fichiers pour fonctionner, un de règle, un à contrôler.
# Les fichiers sont ouverts par Click
@click.argument('input_file', default="config.yml", type=click.File('r'))
@click.argument('control_file', default="", type=click.File('r'))
# nous créons ci-dessous notre fonction appelée "test"avec 2 paramètres, le fichier de configuration et le fichier
# à contrôler.
def test(input_file, control_file):

    # Nous ouvrons et stockons le contenu du fichier YAML
    config = yaml.safe_load(input_file)
    # Si le fichier de config n'est pas constitué d'un des trois fichiers de base le code s'arrête.
    if "allowed_lemma" not in config:
        print("Ce CLI a besoin d'un fichier listant les lemmes autorisés pour fonctionner")
        return
    if "allowed_pos" not in config:
        print("Ce CLI a besoin d'un fichier listant les POS autorisés pour fonctionner")
        return
    if "allowed_morph" not in config:
        print("Ce CLI a besoin d'un fichier listant les MORPH autorisés pour fonctionner")
        return

    # Sinon, nous assignons à chaque fichier une variable qui nous permet de stocker les informations du fichier YAML
    allowed_lemma = config["allowed_lemma"]
    allowed_pos = config["allowed_pos"]
    allowed_morph = config["allowed_morph"]

    # S'il y a des règles ignores, nous les stockons dans la variable ignore_files
    # Sinon, nous passons en signalant à l'utilisateur qu'il n'a pas donné d'ignore.
    ignore_files = None
    if "ignore" in config:
        ignore_files = [Ignore(chaine) for chaine in config["ignore"]]
    else:
        print("Vous n'avez pas d'ignore enregistré")
        pass

    # S'il y a des règles additionnelles, nous les stockons dans la variable additional_rules
    # Sinon, nous passons en signalant à l'utilisateur qu'il n'a pas donné de règles additionnelles.
    additional_rules = None
    if "additional_rules" in config:
        additional_rules = config["additional_rules"]
    else:
        print("Vous n'avez pas de règles additionnelles enregistrées")
        pass

    # Ouverture et lecture du fichier additional_rules avec le délimiteur de colonne tsv \t et encapsulateur '',
    # s'il existe.
    if additional_rules is not None:
        with open(additional_rules, newline='') as a:
            rd = csv.reader(a, delimiter="\t", quotechar='"')
            # création d'une liste pour permettre l'indexation
            allowed_rules = []
            # nous sautons ici la première ligne qui contient l'en-tête au moment du parsage
            next(rd, None)
            for regle in rd:
                # On vérifie que le fichier à bien 6 colonnes. S'il en a moins, on envoie un message d'erreur.
                if len(regle) < 6:
                    print("Votre fichier additionnal_rules est mal formé")
                    return
                # Sinon, on ajoute à la liste les éléments auquel on donne la classe Rule.
                else:
                    allowed_rules.append(Rule(regle))

    # Ouverture et lecture du fichier lemma.txt, stockage du texte dans la variable lemme.
    with open(allowed_lemma) as liste_lemma:
        lemme = liste_lemma.read()

    # Ouverture et lecture du fichier morph.tsv avec délimiteur tsv : \t et encapsulateur ''.
    with open(allowed_morph) as a:
        rd = csv.reader(a, delimiter="\t", quotechar='"')
        # nous sautons ici la première ligne qui contient l'en-tête au moment du parsage
        next(rd, None)
        # nous lui demandons de lire chaque ligne du fichier et de stocker les données de la première colonne
        # dans une liste.
        morph = []
        for row in rd:
            # On vérifie que le fichier à bien 2 colonnes. S'il en a moins, on envoie un message d'erreur.
            if len(regle) < 2:
                print("Votre fichier Morph est mal formé")
                return
            # Sinon, on ajoute à la liste morph les éléments de la première colonne.
            else:
                morph.append(row[0])

    # ouverture et lecture du fichier POS, stockage du texte dans la variable pos.
    with open(allowed_pos) as liste_pos:
        pos = liste_pos.read()

    # On parse ensuite le fichier d'exemple
    rd = csv.reader(control_file, delimiter="\t", quotechar='"')
    # saute la première ligne
    next(rd, None)
    # on commence à compter les lignes à 1 et non à zéro pour que leur numéro matche celui du fichier à contrôler.
    line_count = 1
    # on crée une liste qui garde les lignes déjà traitées par les règles du ignore.
    ligne_traite = []
    # nous créons une boucle qui compare les annotations aux formes autorisées par les 3 fichiers de configuration,
    # les règles d'ignore et les additional_rules et qui vérifie si les lignes sont bien autorisées.
    for rowArray in rd:
        # On vérifie que le fichier à bien 4 colonnes. S'il en a moins, on envoie un message d'erreur.
        if len(regle) < 4:
            print("Votre fichier à contrôler est mal formé")
            return
        # Sinon, on ajoute à la liste les éléments auquel on donne la classe Annotation.
        else:
            row = Annotation(rowArray)
        line_count += 1
        # le script parse en premier les ignore. Pour chaque ignore du fichier de config, si une ligne se retrouve dans
        # le fichier, son numéro est stocké dans ligne_traite et il print le commentaire et le numéro de ligne.
        if ignore_files is not None:
            for ignore in ignore_files:
                if ignore.token == line_count:
                    # pour une meilleure lisibilité, nous indiquons le N° de la ligne
                    print(ignore.commentaire + " à la ligne " + str(line_count))
                    ligne_traite.append(ignore.token)
        # pour les lignes qui ne sont pas dans le ignore, le parsage continue et le système vérifie que les annotations
        # soient bien dans les fichiers correspondants.
        if line_count not in ligne_traite:
            if row.lemme in lemme:
                if row.pos in pos:
                    if row.morph in morph:
                        # nous définissons une variable à laquelle nous assignons la valeur True, pour utiliser les
                        # propriétés des boléens.
                        all_rules_ok = True
                        # S'il y a un fichier de règle additionnelles,
                        if additional_rules is not None:
                            # on parse ensuite les additional_rules.
                            for allowedRule in allowed_rules:
                                # On regarde si le pos du fichier à contrôler est dans les pos des additional_rules.
                                if row.pos in allowedRule.valIn:
                                    # On sépare les instructions selon le type de règle: allowed_only/forbbiden
                                    if allowedRule.ruleType == "allowed_only":
                                        # Pour les allowed_only, le morph du fichier de contrôle doit être le même que
                                        # celui des additional_rules. Si ce n'est pas le cas:
                                        if row.morph != allowedRule.valOut:
                                            # on change la valeur de la variable
                                            all_rules_ok = False
                                            # et on imprime un commentaire avec le N° de la ligne
                                            print("La Morph n'est pas celle attendue pour cette pos à la ligne " +
                                                  str(line_count))
                                            # le break nous permet d'arrêter notre boucle pour la ligne concernée.
                                            break
                                    else:
                                        # Si on a forbidden, le morph du fichier de contrôle ne doit pas être le même
                                        # que celui du fichier additional_rules. Si c'est le cas:
                                        if row.morph == allowedRule.valOut:
                                            # on change la valeur de la variable
                                            all_rules_ok = False
                                            # on print le commentaire avec le numéro de ligne
                                            print("Cette Morph ne peut pas être utilisée avec cette pos à la ligne " +
                                                  str(line_count))
                                            break
                            # Si les additional_rules n'ont pas modifié la valeur de all_rules_ok, l'annotation est
                            # correcte
                        if all_rules_ok:
                            print("tout est ok!")
                    else:
                        print("La morph n'est pas autorisé à la ligne " + str(line_count))
                else:
                    print("L'annotation n'est pas dans les pos autorisées à la ligne " + str(line_count))
            else:
                print("Le lemme n'est pas dans la liste des lemmes autorisés à la ligne " + str(line_count))


# cet idiome permet d'exécuter le script principal mais non importé. Dans notre cas, le script n'est pas importé,
# mais c'est une convention et le script principal s'appelle alors "main"
if __name__ == "__main__":
    test()
