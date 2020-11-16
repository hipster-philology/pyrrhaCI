# -*- coding: utf-8 -*-

# nous importons les librairies nécessaires à l'exécution du code.
import regex as re
import yaml
import click

from pyrrha_ci.rules.dynamic_rules import ManualRule
from pyrrha_ci.utils import MESSAGE_TYPE, parse_tsv, merge, _relative_path
from .rules.proto import Rule
from typing import List, Optional, TextIO, Dict, Tuple, Set, Any
from collections import namedtuple
from importlib import import_module

_Ret = namedtuple("Ret", ["errors", "failed", "checked", "ignored"])
Numb = re.compile("^\d+$")
Punc = re.compile("^\W+$")

semi_colon_split = re.compile(r"(?<!\\):")


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


class PyrrhaCI:
    """ A Test class that handles reading of data and is called by the main command

    :param config_file: Address of the file that loads the configuration
    """

    @classmethod
    def from_file_io(cls, config_file: TextIO) -> "PyrrhaCI":
        # Nous ouvrons et stockons le contenu du fichier YAML
        config = yaml.safe_load(config_file)

        expected_columns = ["token"]

        # Si le fichier de config n'est pas constitué d'un des trois fichiers de base le code s'arrête.
        if "allowed_lemma" not in config:
            cls.static_print("Ce CLI n'a pas trouvé de fichier pour les lemmes autorisés",
                             level=MESSAGE_TYPE.INFO)
        else:
            expected_columns.append("lemma")
        if "allowed_pos" not in config:
            cls.static_print("Ce CLI n'a pas trouvé de fichier pour les POS autorisées",
                             level=MESSAGE_TYPE.INFO)
        else:
            expected_columns.append("POS")
        if "allowed_morph" not in config:
            cls.static_print("Ce CLI n'a pas trouvé de fichier pour les tags de morphologies autorisés",
                             level=MESSAGE_TYPE.INFO)
        else:
            expected_columns.append("morph")

        ignore = {}
        if "ignore" in config:
            for chaine in config["ignore"]:
                ignored = Ignore(chaine)
                if ignored.type.isnumeric() and ignored.type not in ignored:
                    ignore[ignored.type] = {}
                ignore[ignored.type][ignored.token] = ignored.commentaire
        else:
            cls.static_print("Vous n'avez pas d'ignore enregistré", level=MESSAGE_TYPE.INFO)

        allowed_rules: List[ManualRule] = []
        if "additional_rules" in config:
            # Ouverture et lecture du fichier additional_rules avec le délimiteur de colonne tsv \t et encapsulateur '',
            # s'il existe.
            for _, regle in parse_tsv(_relative_path(config_file.name, config["additional_rules"])):
                # On vérifie que le fichier à bien 6 colonnes. S'il en a moins, on envoie un message d'erreur.
                if len(regle) < 6:
                    cls.static_print("Votre fichier additionnal_rules est mal formé", level=MESSAGE_TYPE.FAIL)
                # Sinon, on ajoute à la liste les éléments auquel on donne la classe Rule.
                else:
                    allowed_rules.append(ManualRule(regle))
        else:
            cls.static_print("Vous n'avez pas de règles additionnelles enregistrées", level=MESSAGE_TYPE.INFO)

        # Ouverture et lecture du fichier lemma.txt, stockage du texte dans la variable lemme.
        allowed_lemma = {}
        cross_check_lemma = False
        if config.get("allowed_lemma"):
            for _, data in parse_tsv(_relative_path(config_file.name, config["allowed_lemma"])):
                if data["lemma"] not in allowed_lemma:
                    allowed_lemma[data["lemma"]] = set()
                if "POS" in data and data["POS"]:
                    cross_check_lemma = True
                    allowed_lemma[data["lemma"]] |= set(data["POS"].split(","))

        # Ouverture et lecture du fichier morph.tsv avec délimiteur tsv : \t et encapsulateur ''.
        allowed_morph: Dict[str, List[str]] = {}
        cross_check_morph = False
        if config.get("allowed_morph"):
            for row_num, row in parse_tsv(_relative_path(config_file.name, config.get("allowed_morph"))):
                morph = row["morph"]
                _morph_pos = row.get("POS", "").split(",") if row.get("POS") else []
                if morph in allowed_morph:
                    allowed_morph[morph].extend(_morph_pos)
                else:
                    allowed_morph[morph] = _morph_pos
                if len(allowed_morph[morph]):
                    cross_check_morph = True

        # ouverture et lecture du fichier POS, stockage du texte dans la variable pos.
        allowed_pos = None
        if config.get("allowed_pos"):
            with open(_relative_path(config_file.name, config.get("allowed_pos"))) as open_file:
                allowed_pos = set(open_file.read().strip().split(","))

        return cls(
            expected_columns=expected_columns,
            allowed_lemma=allowed_lemma,
            allowed_morph=allowed_morph,
            allowed_pos=allowed_pos,
            ignore=ignore,
            allowed_rules=allowed_rules,
            mapping=config.get("mapping", {}),
            options=config.get("options", {}),
            ruleset=config.get("ruleset", None),
            cross_check_lemma=cross_check_lemma,
            cross_check_morph=cross_check_morph
        )

    def __init__(
            self,
            expected_columns,
            allowed_lemma: Optional[Dict[str, Set[str]]] = None,
            allowed_pos: Optional[List[str]] = None,
            allowed_morph: Optional[Dict[str, List[str]]] = None,
            allowed_rules: Optional[List[ManualRule]] = None,
            ignore: Optional[Dict[str, Dict[str, Ignore]]] = None,
            mapping: Optional[Dict[str, Dict[str, str]]] = None,
            options: Optional[Dict[str, Any]] = None,
            cross_check_lemma: bool = False,
            cross_check_morph: bool = False,
            ruleset: Optional[str] = None
    ):
        """

        :param expected_columns: Columns expected in the file
        :param allowed_lemma: Dictionary of allowed lemma, with allowed POS for each lemma [Optional second part]
        :param allowed_morph: Dictionary of allowed morph with allowed POS for each morph [Optional second part]
        :param allowed_pos: Set of allowed POS
        :param ignore: Information to ignore
        :param mapping: For each category (morph, lemma, pos), a dictionary key->value where key in the tested file
                        is replaced by value. Example: `{"POS": {"VERaux": "VER"}}` will replace VERaux by VER.
        :param options: Available options (allow_punc, allow_numb, ignore_on_POS)
        :param ruleset: List of rules to use
        """
        self.expected_columns: List[str] = expected_columns
        self.allowed_lemma: Dict[str, Set[str]] = allowed_lemma or {}
        self.allowed_morph: Dict[str, List[str]] = allowed_morph or {}
        self.allowed_pos: Set[str] = allowed_pos or set()
        self.allowed_rules: List[ManualRule] = allowed_rules or []

        self.cross_check_lemma: bool = cross_check_lemma
        self.cross_check_morph: bool = cross_check_morph

        self.ignored: Dict[str, Dict[str, Ignore]] = {category: {} for category in self.expected_columns}
        merge(ignore or {}, self.ignored)

        self.mapping: Dict[str, Dict[str, str]] = {"morph": {}, "pos": {}, "lemma": {}}
        merge(mapping or {}, self.mapping)

        self.options = {
            "lemma":
                {
                    "allow_punc": False,
                    "allow_numb": False,
                    "ignore_on_POS": []
                }
        }
        self.ruleset: Optional[str] = ruleset
        self.rules: List[Rule] = []
        try:
            if ruleset:
                self.rules = import_module("pyrrha_ci.rules.{}.import".format(ruleset)).Rules
        except ImportError:
            print("The ruleset you tried to import ({}) seems to not exist.".format(ruleset))
            raise
        merge(options or {}, self.options)

    @staticmethod
    def static_print(message: str, line_number: Optional[int] = None, level: Optional[MESSAGE_TYPE] = None) -> None:
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

    def print(self, message: str, line_number: Optional[int] = None, level: Optional[MESSAGE_TYPE] = None) -> None:
        """ Print the given message with its line number and optional formating given the level

        :param message: Message to show
        :param line_number: Line Number to show
        :param level: Level of the message
        """
        self.static_print(message, line_number=line_number, level=level)

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
        if len(self.allowed_lemma[lem]) and pos not in self.allowed_lemma[lem]:
            self.print(
                "La POS `{}` n'est pas autorisée avec le lemme `{}` (Token `{}`). Autorisées: `{}`".format(
                    pos, lem, form, ",".join(self.allowed_lemma[lem])
                ),
                line_number=line_no, level=MESSAGE_TYPE.FAIL
            )
            return 1
        return 0

    def _test_cross_pos_morph(self, pos, morph, form, line_no=0) -> int:
        if len(self.allowed_morph[morph]) and pos not in self.allowed_morph[morph]:
            self.print(
                "La morph `{}` n'est pas  autorisée avec la POS `{}` (Token `{}`)".format(
                    morph, pos, form
                ),
                line_number=line_no, level=MESSAGE_TYPE.FAIL
            )
            return 1
        return 0

    def _get_values(self, row) -> Tuple[
        Optional[str], Optional[str], Optional[str], Optional[str], Dict[str, Optional[str]]
    ]:
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
        return form, lem, pos, morph, {"token": form, "lemma": lem, "POS": pos, "morph": morph}

    def test(self, control_file: TextIO, from_=0, to_=0):
        """ Test the file against the loaded rules

        :param control_file: File to test
        :param from_: Line to start with
        :param to_: Line to end with
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
        iterator = list([(row_num, self._get_values(row)) for row_num, row in parse_tsv(control_file)])
        max_row = len(iterator)

        for row_num, (form, lem, pos, morph, line_as_dict) in iterator:
            if from_ is not None and row_num < from_:
                continue
            elif to_ is not None and row_num > to_:
                continue

            previous = [row[-1] for _, row in iterator[max(0, row_num-5):row_num]]
            nextious = [row[-1] for _, row in iterator[row_num+1:min(max_row, row_num+5)]]

            cur_line_friendly = row_num + 1
            line_count += 1

            # Pour les lignes qui ne sont pas dans le ignore, le parsage continue et
            #   le système vérifie que les annotations soient bien dans les fichiers correspondants.
            if cur_line_friendly not in ligne_traite:
                lem_status = self._test_lemma(lem=lem, pos=pos, morph=morph, line_no=cur_line_friendly)
                errors += lem_status.errors

                pos_status = self._test_pos(lem=lem, pos=pos, morph=morph, line_no=cur_line_friendly)
                errors += pos_status.errors

                if self.cross_check_lemma and\
                        lem_status.checked and pos_status.checked and not lem_status.ignored and not pos_status.ignored\
                        and not lem_status.failed and not pos_status.failed:
                    errors += self._test_cross_lemma_pos(lem, pos, form=form, line_no=cur_line_friendly)

                morph_status = self._test_morph(lem=lem, pos=pos, morph=morph, line_no=cur_line_friendly)
                errors += morph_status.errors

                if self.cross_check_morph and\
                        morph_status.checked and pos_status.checked and not morph_status.ignored \
                        and not pos_status.ignored\
                        and not morph_status.failed and not pos_status.failed:
                    errors += self._test_cross_pos_morph(pos, morph, form=form, line_no=cur_line_friendly)

                # on parse ensuite les additional_rules.
                errors += self._test_additional_rules(line_as_dict)

                # Test avec le ruleset
                for rule in self.rules:
                    if rule.applies_to(line_as_dict):
                        if rule.check(line_as_dict, previous=previous, following=nextious):
                            self.static_print(rule.MESSAGE.format(**line_as_dict),
                                              line_number=cur_line_friendly, level=rule.TYPE)

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
    running = PyrrhaCI.from_file_io(control_file)
    return running.test(tested_file, from_=from_, to_=to_)


# cet idiome permet d'exécuter le script principal mais non importé. Dans notre cas, le script n'est pas importé,
# mais c'est une convention et le script principal s'appelle alors "main"
if __name__ == "__main__":
    test()
