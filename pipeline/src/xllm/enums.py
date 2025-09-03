from enum import Enum


# enum definitions
class BaseEnumWithId(str, Enum):
    def __new__(cls, value, id_):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.id = id_
        return obj

    @property
    def identifier(self):
        return self.id


class TwoNoBooleanEnum(BaseEnumWithId):
    TRUE = ("true", 1)
    FALSE = ("false", 2)
    UNKNOWN = ("Unknown", 99)


class ZeroNoBooleanEnum(BaseEnumWithId):
    TRUE = ("true", 1)
    FALSE = ("false", 0)
    UNKNOWN = ("Unknown", 99)


class SmokingHistoryEnum(BaseEnumWithId):
    NEVER_SMOKER = ("never smoker", 1)
    CURRENT_SMOKER = ("current smoker", 2)
    FORMER_SMOKER = ("former smoker", 3)
    UNKNOWN = ("Unknown", 99)


class FamilyRelationshipEnum(BaseEnumWithId):
    """
    Relationship to the patient
    """

    FATHER = ("father", 1)
    MOTHER = ("mother", 2)
    SIBLINGS = ("siblings", 3)
    CHILDREN = ("children", 4)
    SECOND_DEGREE_RELATIVE = ("second degree relative", 5)


class CancerTypeEnum(BaseEnumWithId):
    BREAST = ("breast", 1)
    OVARIAN = ("ovarian", 2)
    UTERINE = ("uterine", 3)
    LUNG = ("lung", 4)
    GASTRIC = ("gastric", 5)
    PROSTATE = ("prostate", 6)
    BRAIN = ("brain", 7)
    THYROID = ("thyroid", 8)
    LIVER = ("liver", 9)
    CHOLANGIOCARCINOMA = ("cholangiocarcinoma", 10)
    OTHER = ("other", 11)


# 1=Crohn's Disease, 2=Ulcerative Colitis, 3=Unclassified)
class IBDTypeEnum(BaseEnumWithId):
    CD = ("Crohn's Disease", 1)
    UC = ("Ulcerative Colitis", 2)
    IBDU = ("Unclassified", 3)
    UNKNOWN = ("Unknown", 99)


# age group (1=A1 (< 16y), 2=A2 (17-40y), 3=A3 (>40y)
class AgeGroupEnum(BaseEnumWithId):
    A1 = ("< 16y", 1)
    A2 = ("17-40y", 2)
    A3 = (">40y", 3)
    UNKNOWN = ("Unknown", 99)


# What is the most recently reported disease location of the patient? (1=L1 (ileal), 2=L2 (colonic), 3=L3 (ileocolonic), 4=L4 (isolated upper disease), 5=L1+L4, 6=L2+L4, 7=L3+L4, 99=Unknown)
class DiseaseLocationEnum(BaseEnumWithId):
    L1 = ("ileal", 1)
    L2 = ("colonic", 2)
    L3 = ("ileocolonic", 3)
    L4 = ("isolated upper disease", 4)
    L1_L4 = ("ileal + isolated upper disease", 5)
    L2_L4 = ("colonic + isolated upper disease", 6)
    L3_L4 = ("ileocolonic + isolated upper disease", 7)
    UNKNOWN = ("Unknown", 99)


# behaviour state (1=B1 non-stricturing, non-penetrating, 2=B2 stricturing, 3=B3 penetrating, 99=Unknown
class BehaviourStateEnum(BaseEnumWithId):
    B1 = ("non-stricturing, non-penetrating", 1)
    B2 = ("stricturing", 2)
    B3 = ("penetrating", 3)

    UNKNOWN = ("Unknown", 99)
