# -*- coding: utf-8 -*-

# nous importons les librairies nécessaires à l'exécution du code.
import os
import csv
import regex as re
import yaml
import click
from enum import Enum
from typing import List, Optional, TextIO, Dict, Generator, Tuple, Set, Union
from collections import namedtuple

_Ret = namedtuple("Ret", ["errors", "failed", "checked", "ignored"])
Numb = re.compile("^\d+$")
Punc = re.compile("^\W+$")


class MESSAGE_TYPE(Enum):
    INFO = '\033[94m'
    OK = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    IGNORE = '\033[94m'


semi_colon_split = re.compile(r"(?<!\\):")


def parse_tsv(content: Union[str, TextIO]) -> Generator[Tuple[int, Dict[str, str]], None, None]:
    """ Parses a Pyrrha TSV

    :param content: Path to the file
    :yield: Yields the line number and the content
    """
    if isinstance(content, str):
        content = open(content)
    header = []
    for line_no, line in enumerate(content):
        if line_no == 0:
            header = line.strip().split("\t")
        else:
            yield line_no, dict(zip(header, line.strip().split("\t")))
    content.close()
    return None


def merge(source, destination):
    """Merges b into a

    Source: https://stackoverflow.com/questions/20656135/python-deep-merge-dictionary-data

    >>> a = { 'first' : { 'all_rows' : { 'pass' : 'dog', 'number' : '1' } } }
    >>> b = { 'first' : { 'all_rows' : { 'fail' : 'cat', 'number' : '5' } } }
    >>> merge(b, a) == { 'first' : { 'all_rows' : { 'pass' : 'dog', 'fail' : 'cat', 'number' : '5' } } }
    True
    """
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            merge(value, node)
        else:
            destination[key] = value

# Nous définissons une classe pour les règles additionnelles que nous nommons Rule.
# La définition d'une classe permet de transmettre des propriétés aux objets qui héritent de cette classe.
# Nous l'utilisons pour ne pas avoir à utiliser l'indexation dans la boucle.
class Rule:
    """ Rule that needs to be respected by each line

    :param regle: List of 5 elements : Rule Type, Category First value, Category Second Value, First Value, Controlled
    Value

    Maybe conditional value/category // controlled value/category
    """

    # les 2 arguments de la méthode sont self (par convention) et regle qui correspond à chaque colonne du fichier.
    def __init__(self, regle: List[str]):
        """ Setup the class """
        self.id = regle[0]
        self.ruleType = regle[1]
        self.catIn = regle[2]
        self.catOut = regle[3]
        self.valIn = re.compile(regle[4])
        self.valOut = re.compile(regle[5])


# Nous définissons une classe pour les règles à ignorer indiquées dans le fichier config.yml.
class Ignore:
    """ Errors to ignore

    :param ign: Information about things to ignore, separated by semi-colon (index of error, token focused, comment
    """

    def __init__(self, ign: str):
        """ Chaine représentant le type de token

        :param ign: Chaine de CSV
        """
        # le .split, permet de créer une liste à partir d'une chaine de caractère. Le séparateur est indiqué entre ''.
        ign = semi_colon_split.split(ign)
        self.type = ign[0]
        # Nous forçons le type du token, pour qu'il soit du même type que le nombre de lignes.
        self.token = ign[1]
        if self.token.isnumeric():
            self.token = int(self.token)
        self.commentaire = ign[2]

# L'utilisation de class améliore la lisibilité du code. Nous avons ainsi un namespace (?)
#   local qui décrit les attributs.


def _relative_path(first_file: str, second_file: str):
    """ Compute a relative path based on the path of the first
    file """
    return os.path.join(
        os.path.dirname(first_file),
        second_file
    )


class Test:
    """ A Test class that handles reading of data and is called by the main command

    :param config_file: Address of the file that loads the configuration
    """

    def __init__(self, config_file: TextIO):
        # Nous ouvrons et stockons le contenu du fichier YAML

        config = yaml.safe_load(config_file)

        # Les des colonnes attendues
        self.expected_columns: List[str] = ["token"]

        self.mapping: Dict[str, Dict[str, str]] = {
            "morph": config.get("mapping", {"morph": {}}).get("morph", {}),
            "pos": config.get("mapping", {"pos": {}}).get("pos", {}),
            "lemma": config.get("mapping", {"lemma": {}}).get("lemma", {})
        }

        self.options = {
            "lemma":
                {
                    "allow_punc": False,
                    "allow_numb": False,
                    "ignore_on_POS": []
                }
        }
        merge(config.get("options", {}), self.options)

        # Si le fichier de config n'est pas constitué d'un des trois fichiers de base le code s'arrête.
        if "allowed_lemma" not in config:
            self.print("Ce CLI n'a pas trouvé de fichier pour les lemmes autorisés",
                       level=MESSAGE_TYPE.INFO)
        else:
            self.expected_columns.append("lemma")
        if "allowed_pos" not in config:
            self.print("Ce CLI n'a pas trouvé de fichier pour les POS autorisées",
                       level=MESSAGE_TYPE.INFO)
        else:
            self.expected_columns.append("POS")
        if "allowed_morph" not in config:
            self.print("Ce CLI n'a pas trouvé de fichier pour les tags de morphologies autorisés",
                       level=MESSAGE_TYPE.INFO)
        else:
            self.expected_columns.append("morph")

        # S'il y a des règles ignores, nous les stockons dans la variable ignore_files
        # Sinon, nous passons en signalant à l'utilisateur qu'il n'a pas donné d'ignore.
        self.ignored = {category: {} for category in self.expected_columns}
        if "ignore" in config:
            for chaine in config["ignore"]:
                ignored = Ignore(chaine)
                if ignored.type.isnumeric() and ignored.type not in self.ignored:
                    self.ignored[ignored.type] = {}
                self.ignored[ignored.type][ignored.token] = ignored.commentaire
        else:
            self.print("Vous n'avez pas d'ignore enregistré", level=MESSAGE_TYPE.INFO)

        # S'il y a des règles additionnelles, nous les stockons dans la variable allowed_rules
        # Sinon, nous passons en signalant à l'utilisateur qu'il n'a pas donné de règles additionnelles.
        # création d'une liste pour permettre l'indexation
        self.allowed_rules = []
        if "additional_rules" in config:
            # Ouverture et lecture du fichier additional_rules avec le délimiteur de colonne tsv \t et encapsulateur '',
            # s'il existe.
            with open(_relative_path(config_file.name, config["additional_rules"])) as open_file:
                rd = csv.reader(open_file, delimiter="\t", quotechar='"')
                # nous sautons ici la première ligne qui contient l'en-tête au moment du parsage
                next(rd, None)
                for regle in rd:
                    # On vérifie que le fichier à bien 6 colonnes. S'il en a moins, on envoie un message d'erreur.
                    if len(regle) < 6:
                        self.print("Votre fichier additionnal_rules est mal formé", level=MESSAGE_TYPE.FAIL)
                    # Sinon, on ajoute à la liste les éléments auquel on donne la classe Rule.
                    else:
                        self.allowed_rules.append(Rule(regle))
        else:
            self.print("Vous n'avez pas de règles additionnelles enregistrées", level=MESSAGE_TYPE.INFO)

        # Ouverture et lecture du fichier lemma.txt, stockage du texte dans la variable lemme.
        self.allowed_lemma: Dict[str, Set[str]] = {}
        if config.get("allowed_lemma"):
            for _, data in parse_tsv(_relative_path(config_file.name, config["allowed_lemma"])):
                self.allowed_lemma[data["lemma"]] = set()
                if "POS" in data:
                    self.allowed_lemma[data["lemma"]] = set(data["POS"].split(","))

        # Ouverture et lecture du fichier morph.tsv avec délimiteur tsv : \t et encapsulateur ''.
        self.allowed_morph: Dict[str, List[str]] = {}
        if config.get("allowed_morph"):
            with open(_relative_path(config_file.name, config.get("allowed_morph"))) as open_file:
                rd = csv.reader(open_file, delimiter="\t")
                # nous lui demandons de lire chaque ligne du fichier et de stocker les données de la première colonne
                # dans une liste.
                header: List[str] = []
                for row_num, row in enumerate(rd):
                    if row_num == 0:
                        header = row
                    # Sinon, on ajoute à la liste morph les éléments de la première colonne.
                    else:
                        row = dict(zip(header, row))
                        morph = row["morph"]
                        if morph in self.allowed_morph:
                            self.allowed_morph[morph].extend(row.get("POS", "").split(","))
                        else:
                            self.allowed_morph[morph] = row.get("POS", "").split(",")

        # ouverture et lecture du fichier POS, stockage du texte dans la variable pos.
        self.allowed_pos = None
        if config.get("allowed_pos"):
            with open(_relative_path(config_file.name, config.get("allowed_pos"))) as open_file:
                self.allowed_pos = open_file.read()

    def print(self, message: str, line_number: Optional[int] = None, level: Optional[MESSAGE_TYPE] = None) -> None:
        """ Print the given message with its line number and optional formating given the level

        :param message: Message to show
        :param line_number: Line Number to show
        :param level: Level of the message
        """
        prefix = ""
        if line_number:
            prefix = '\033[4mL' + str(line_number) + '\033[0m:\t'
        if level:
            prefix += level.value
        print(prefix + message + '\033[0m')

    def _test_lemma(self, lem=None, morph=None, pos=None, line_no=0) -> _Ret:
        """

        :returns: Nb Error, Has Failed, Was Checked, Was Ignored
        """
        if not self.allowed_lemma:
            return _Ret(errors=0, failed=False, checked=False, ignored=False)
        elif lem in self.allowed_lemma:
            return _Ret(errors=0, failed=False, checked=True, ignored=False)
        else:
            # Si cette ligne est une ligne à ignorer pour les erreurs niveau lemme
            if self.ignored["lemma"].get(line_no):
                self.print(
                    "Erreur ignorée au niveau ligne ({})".format(self.ignored["lemma"][line_no]),
                    line_number=line_no, level=MESSAGE_TYPE.IGNORE
                )
                return _Ret(errors=0, failed=False, checked=True, ignored=True)
            # Si cette valeur de lemme est  autoriser en général
            elif self.ignored["lemma"].get(lem):
                self.print(
                    "Erreur ignorée au niveau lemme ({})".format(self.ignored["lemma"][lem]),
                    line_number=line_no, level=MESSAGE_TYPE.IGNORE
                )
                return _Ret(errors=0, failed=False, checked=True, ignored=True)
            # Sinon, c'est une erreur
            else:
                if self.options["lemma"]["allow_numb"] and Numb.match(lem):
                    return _Ret(errors=0, failed=False, checked=True, ignored=True)
                elif self.options["lemma"]["allow_punc"] and Punc.match(lem):
                    return _Ret(errors=0, failed=False, checked=True, ignored=True)
                elif pos and pos in self.options["lemma"]["ignore_on_POS"]:
                    return _Ret(errors=0, failed=False, checked=True, ignored=True)
                else:
                    self.print(
                        "Le lemme `{}` n'est pas dans la liste des valeurs autorisées".format(lem),
                        line_number=line_no, level=MESSAGE_TYPE.FAIL
                    )
                    return _Ret(errors=1, failed=True, checked=True, ignored=False)

    def _test_pos(self, lem, pos, morph, line_no=0) -> _Ret:
        # Vérifie les POS de la même manière
        if not self.allowed_pos:
            return _Ret(errors=0, failed=False, checked=False, ignored=False)
        elif pos in self.allowed_pos:
            return _Ret(errors=0, failed=False, checked=True, ignored=False)
        else:
            if self.ignored["POS"].get(line_no):
                self.print("Erreur ignorée au niveau POS ({})".format(self.ignored["POS"][line_no]),
                           line_number=line_no, level=MESSAGE_TYPE.IGNORE)
                return _Ret(errors=0, failed=False, checked=True, ignored=True)
            elif self.ignored["POS"].get(pos):
                self.print("Erreur ignorée au niveau POS ({})".format(self.ignored["POS"][pos]),
                           line_number=line_no, level=MESSAGE_TYPE.IGNORE)
                return _Ret(errors=0, failed=False, checked=True, ignored=True)
            else:
                self.print("La POS `{}` n'est pas dans la liste des valeurs autorisées".format(pos),
                           line_number=line_no, level=MESSAGE_TYPE.FAIL)
                return _Ret(errors=1, failed=True, checked=True, ignored=False)

    def _test_morph(self, lem, pos, morph, line_no=0) -> _Ret:
        if not self.allowed_morph:
            return _Ret(errors=0, failed=False, checked=False, ignored=False)
        elif morph in self.allowed_morph:
            return _Ret(errors=0, failed=False, checked=True, ignored=False)
        else:
            if self.ignored["morph"].get(line_no):
                self.print(
                    "Erreur ignorée au niveau morph ({})".format(self.ignored["morph"][line_no]),
                    line_number=line_no, level=MESSAGE_TYPE.IGNORE
                )
                return _Ret(errors=0, failed=False, checked=True, ignored=True)
            elif self.ignored["morph"].get(morph):
                self.print("Erreur ignorée au niveau morph ({})".format(self.ignored["morph"][morph]),
                           line_number=line_no, level=MESSAGE_TYPE.IGNORE)
                return _Ret(errors=0, failed=False, checked=True, ignored=True)
            else:
                self.print("La morph `{}` n'est pas dans la liste des morph autorisées".format(morph),
                           line_number=line_no, level=MESSAGE_TYPE.FAIL)
                return _Ret(errors=1, failed=True, checked=True, ignored=False)

    def _test_additional_rules(self, row, line_no=0) -> int:
        errors = 0
        for allowedRule in self.allowed_rules:
            if allowedRule.id in self.ignored and line_no in self.ignored[allowedRule.id]:
                self.print("Erreur ignorée au niveau de la règle supplémentaire {}".format(allowedRule.id),
                           line_number=line_no, level=MESSAGE_TYPE.IGNORE)
            else:
                # Si la catégorie de contrôle comporte la même valeur que catIn
                if row.get(allowedRule.catIn) and allowedRule.valIn.match(row.get(allowedRule.catIn)):
                    # On peut alors vérifier l'adéquation avec valOut
                    if allowedRule.ruleType == "allowed_only" and \
                            not allowedRule.valOut.match(row.get(allowedRule.catOut)):
                        # On marque une erreur supplémentaire
                        errors += 1
                        # et on imprime un commentaire avec le N° de la ligne
                        self.print(
                            "La valeur `{}` ne fait pas partie des valeurs autorisées en relation avec  la"
                            " valeur `{}` (Règle {})".format(
                                row.get(allowedRule.catOut),
                                row.get(allowedRule.catIn),
                                allowedRule.id
                            ),
                            line_number=line_no, level=MESSAGE_TYPE.FAIL
                        )
                    elif allowedRule.ruleType == "forbidden" and \
                            allowedRule.valOut.match(row.get(allowedRule.catOut)):
                        # On marque une erreur supplémentaire
                        errors += 1
                        # et on imprime un commentaire avec le N° de la ligne
                        self.print(
                            "La valeur `{}` est interdie en relation avec "
                            "la valeur `{}` (Règle {})".format(
                                row.get(allowedRule.catOut),
                                row.get(allowedRule.catIn),
                                allowedRule.id
                            ),
                            line_number=line_no, level=MESSAGE_TYPE.FAIL
                        )
                        # Si on a forbidden, le morph du fichier de contrôle ne doit pas être le même
                        # que celui du fichier additional_rules. Si c'est le cas:
        return errors

    def _test_cross_lemma_pos(self, lem, pos, form, line_no=0) -> int:
        if self.allowed_lemma[lem] and pos not in self.allowed_lemma[lem]:
            self.print(
                "La POS `{}` n'est pas autorisée avec le lemme `{}` (Token `{}`). Autorisées: `{}`".format(
                    pos, lem, form, ",".join(self.allowed_lemma[lem])
                ),
                line_number=line_no, level=MESSAGE_TYPE.FAIL
            )
            return 1
        return 0

    def _test_cross_pos_morph(self, pos, morph, form, line_no=0) -> int:
        if pos not in self.allowed_morph[morph]:
            self.print(
                "La morph `{}` n'est pas  autorisée avec la POS `{}` (Token `{}`)".format(
                    morph, pos, form
                ),
                line_number=line_no, level=MESSAGE_TYPE.FAIL
            )
            return 1
        return 0

    def _get_values(self, row) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        lem = row.get("lemma")
        if lem and lem in self.mapping["lemma"]:
            lem = self.mapping["morph"][lem]
        pos = row.get("POS")
        if pos and pos in self.mapping["pos"]:
            pos = self.mapping["pos"][pos]
        morph = row.get("morph")
        if morph and morph in self.mapping["morph"]:
            morph = self.mapping["morph"][morph]
        form = row.get("token", row.get("form"))
        return form, lem, pos, morph

    def test(self, control_file: TextIO, from_=0, to_=0):
        """ Test the file against the loaded rules

        :param control_file: File to test
        :return:
        """

        # Si on a une erreur, on l'ajoutera à ce décompte
        errors = 0

        # on commence à compter les lignes à 1 et non à zéro pour que leur numéro matche celui du fichier à contrôler.
        line_count = 1

        # on crée une liste qui garde les lignes déjà traitées par les règles du ignore.
        ligne_traite = []

        # nous créons une boucle qui compare les annotations aux formes autorisées par les 3 fichiers de configuration,
        # les règles d'ignore et les additional_rules et qui vérifie si les lignes sont bien autorisées.
        for row_num, row in parse_tsv(control_file):
            if from_ is not None and row_num < from_:
                continue
            elif to_ is not None and row_num > to_:
                continue

            # On vérifie que le fichier a au moins les colonnes attendues
            if len(row) < len(self.expected_columns):
                self.print("Votre fichier à contrôler est mal formé", level=MESSAGE_TYPE.FAIL)
                return

            cur_line_friendly = row_num + 1
            line_count += 1

            # Pour les lignes qui ne sont pas dans le ignore, le parsage continue et
            #   le système vérifie que les annotations soient bien dans les fichiers correspondants.
            if cur_line_friendly not in ligne_traite:
                form, lem, pos, morph = self._get_values(row)

                lem_status = self._test_lemma(lem=lem, pos=pos, morph=morph, line_no=cur_line_friendly)
                errors += lem_status.errors

                pos_status = self._test_pos(lem=lem, pos=pos, morph=morph, line_no=cur_line_friendly)
                errors += pos_status.errors

                if lem_status.checked and pos_status.checked and not lem_status.ignored and not pos_status.ignored\
                        and not lem_status.failed and not pos_status.failed:
                    errors += self._test_cross_lemma_pos(lem, pos, form=form, line_no=cur_line_friendly)

                morph_status = self._test_morph(lem=lem, pos=pos, morph=morph, line_no=cur_line_friendly)
                errors += morph_status.errors

                if morph_status.checked and pos_status.checked and not morph_status.ignored and not pos_status.ignored\
                        and not morph_status.failed and not pos_status.failed:
                    errors += self._test_cross_pos_morph(pos, morph, form=form, line_no=cur_line_friendly)

                # on parse ensuite les additional_rules.
                errors += self._test_additional_rules(row)

        if errors > 0:
            self.print("\n\n----------------\n\n")
            self.print("Status:\tFailed", level=MESSAGE_TYPE.FAIL)
            self.print("Errors:\t%s " % errors, level=MESSAGE_TYPE.FAIL)
            return False
        else:
            self.print("\n\n----------------\n\n")
            self.print("Status:\tPassed", level=MESSAGE_TYPE.OK)
            return True

@click.command()
# Notre CLI a besoin de deux fichiers pour fonctionner, un de règle, un à contrôler.
# Les fichiers sont ouverts par Click
@click.argument('control_file', default="config.yml", type=click.File('r'))
@click.argument('tested_file', default="", type=click.File('r'))
@click.option('--from', '-f', "from_", default=None, type=int)
@click.option('--to', '-t', 'to_', default=None, type=int)
# nous créons ci-dessous notre fonction appelée "test"avec 2 paramètres, le fichier de configuration et le fichier
# à contrôler.
def test(control_file, tested_file, from_=0, to_=0):
    """ Test CONTROL_FILE against configurations available in INPUT_FILE

    :param control_file: Address of the file that loads the configuration
    :param tested_file: File that needs to be tested
    :return: True if full success, False if one fails. None is returned when things go wrong
    """
    running = Test(control_file)
    return running.test(tested_file, from_=from_, to_=to_)


# cet idiome permet d'exécuter le script principal mais non importé. Dans notre cas, le script n'est pas importé,
# mais c'est une convention et le script principal s'appelle alors "main"
if __name__ == "__main__":
    test()
