from typing import List
import regex as re


# Nous définissons une classe pour les règles additionnelles que nous nommons Rule.
# La définition d'une classe permet de transmettre des propriétés aux objets qui héritent de cette classe.
# Nous l'utilisons pour ne pas avoir à utiliser l'indexation dans la boucle.


class ManualRule:
    """ Rule that needs to be respected by each line

    :param regle: List of 5 elements : Rule Type, Category First value, Category Second Value, First Value, Controlled
    Value

    Maybe conditional value/category // controlled value/category

    ToDo: REFACTOR/DELETE ?
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
