# from .enums import *
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    TypeVar,
    Union,
    Type,
    get_origin,
    get_args,
)
from dataclasses import dataclass
from pydantic import BaseModel, ConfigDict, Field, create_model
import json
from enum import Enum
from pydantic import field_validator


def get_type_json_name(var_type):
    if var_type is str:
        return {"type": "string"}
    elif var_type is int:
        return {"type": "int"}
    elif var_type is float:
        return {"type": "float"}
    elif var_type is bool:
        return {"type": "bool"}
    elif get_origin(var_type) is list:
        inner_type = get_args(var_type)[0]
        return {"type": "list", "value": get_type_json_name(inner_type)}
    # if is enum
    elif issubclass(var_type, Enum):
        return {"type": "enum", "values": [e.value for e in var_type]}
    elif issubclass(var_type, BaseModel):
        fields = []
        for field_name, field_info in var_type.model_fields.items():
            fields.append({
                "name": field_name,
                "value": get_type_json_name(field_info.annotation)
            })
        return {"type": "object", "values": fields}

class PartialDate:
    """
    A partial date is a date that is not fully specified. For example, "2023-10" is a partial date.
    """

    year: int 
    month: Optional[int] = None
    day: Optional[int] = None

    def __init__(
        self, year: int, month: Optional[int] = None, day: Optional[int] = None
    ):
        self.year = year
        self.month = month
        self.day = day

    @classmethod
    def parse(cls, date_str: str) -> Optional["PartialDate"]:
        """
        Parse a date string in the format YYYY-MM-DD or YYYY-MM or YYYY.
        """
        parts = date_str.split("-")

        if len(parts) < 1 or len(parts) > 3:
            return None
    
        if not all(part.isdigit() for part in parts):
            return None

        year = int(parts[0])
        if year < 1900 or year > 2999:
            return None

        month = int(parts[1]) if len(parts) > 1 else None
        if month is not None and (month < 1 or month > 12):
            return None

        day = int(parts[2]) if len(parts) > 2 else None
        if day is not None and (day < 1 or day > 31):
            return None

        return cls(year, month, day)

    def __str__(self):
        if self.month is not None and self.day is not None:
            return f"{self.year}-{self.month:02d}-{self.day:02d}"
        elif self.month is not None:
            return f"{self.year}-{self.month:02d}"
        else:
            return str(self.year)

    def __repr__(self):
        if self.month is not None and self.day is not None:
            return f"PartialDate(year={self.year}, month={self.month}, day={self.day})"
        elif self.month is not None:
            return f"PartialDate(year={self.year}, month={self.month})"
        else:
            return f"PartialDate(year={self.year}, month={self.month}, day={self.day})"

    def __eq__(self, other):
        if isinstance(other, PartialDate):
            return (
                self.year == other.year
                and self.month == other.month
                and self.day == other.day
            )
        return False

    def __hash__(self):
        return hash((self.year, self.month, self.day))

    def __lt__(self, other):
        if isinstance(other, PartialDate):
            if self.year != other.year:
                return self.year < other.year
            if not self.month and not other.month:
                return False
            if self.month is None:
                return True
            if other.month is None:
                return False
            if self.month != other.month:
                return self.month < other.month
            if not self.day and not other.day:
                return False
            if self.day is None:
                return True
            if other.day is None:
                return False
            if self.day != other.day:
                return self.day < other.day
        return False

    def __le__(self, other):
        if isinstance(other, PartialDate):
            if self.year != other.year:
                return self.year < other.year
            if not self.month and not other.month:
                return False
            if self.month is None:
                return True
            if other.month is None:
                return False
            if self.month != other.month:
                return self.month < other.month
            if not self.day and not other.day:
                return False
            if self.day is None:
                return True
            if other.day is None:
                return False
            if self.day != other.day:
                return self.day < other.day
        return False

    def __gt__(self, other):
        if isinstance(other, PartialDate):
            if self.year != other.year:
                return self.year > other.year
            if not self.month and not other.month:
                return False
            if self.month is None:
                return True
            if other.month is None:
                return False
            if self.month != other.month:
                return self.month > other.month
            if not self.day and not other.day:
                return False
            if self.day is None:
                return True
            if other.day is None:
                return False
            if self.day != other.day:
                return self.day > other.day
        return False

    def __ge__(self, other):
        if isinstance(other, PartialDate):
            if self.year != other.year:
                return self.year > other.year
            if not self.month and not other.month:
                return False
            if self.month is None:
                return True
            if other.month is None:
                return False
            if self.month != other.month:
                return self.month > other.month
            if not self.day and not other.day:
                return False
            if self.day is None:
                return True
            if other.day is None:
                return False
            if self.day != other.day:
                return self.day > other.day
        return False

    def __ne__(self, other):
        if isinstance(other, PartialDate):
            return (
                self.year != other.year
                or self.month != other.month
                or self.day != other.day
            )
        return True


class MedicalFact[T](BaseModel):
    citation: str
    value: T
    note_id: int

    @classmethod
    def with_enum(cls, enum_cls: Type[Enum]):
        class _EnumFact(cls):
            value: enum_cls  # override field type

            @field_validator("value", mode="before")
            @classmethod
            def validate_enum(cls, v):
                if v not in enum_cls._value2member_map_:
                    raise ValueError(f"Invalid value '{v}' for {enum_cls.__name__}")
                return enum_cls(v)

        return _EnumFact

    @classmethod
    def with_type(cls, value_type: Type[T]):
        class _TypedFact(cls):
            value: value_type

        return _TypedFact

T = TypeVar("T", bound=Union[str, int, float, bool, Enum, List[Any]])
V = TypeVar("V", bound=Union[str, int, float, bool, Enum, List[Any]])

@dataclass
class ChunkValue[T]:
    date: PartialDate
    value: T

    @classmethod
    def get_most_frequent(cls, chunks: List["ChunkValue[V]"]) -> Optional[V]:
        """,
        Returns the most frequently occurring value in a list of ChunkValue objects.
        If there is a tie, it returns the first one encountered.
        """
        if not chunks:
            return None

        frequency = {}
        for chunk in chunks:
            if chunk.value not in frequency:
                frequency[chunk.value] = 0
            frequency[chunk.value] += 1

        most_frequent = max(frequency, key=frequency.get) # type: ignore
        return most_frequent
    
    @classmethod
    def list_unique(cls, chunks: List["ChunkValue[List[V]]"]) -> List[V]:
        """
        Returns a list of unique elements from a list of ChunkValue objects, 
        where each ChunkValue contains a list of elements.
        """
        
        return list(set(
            element for chunk in chunks for element in chunk.value
        ))

    @classmethod
    def get_most_recent(cls, chunks: List["ChunkValue[V]"]) -> Optional[V]:
        """
        Returns the value of the most recent ChunkValue object based on the date.
        """
        if not chunks:
            return None

        most_recent_chunk = max(chunks, key=lambda chunk: chunk.date)
        return most_recent_chunk.value
    
    @classmethod
    def get_least_recent(cls, chunks: List["ChunkValue[V]"]) -> Optional[V]:
        """
        Returns the value of the least recent ChunkValue object based on the date.
        """
        if not chunks:
            return None

        least_recent_chunk = min(chunks, key=lambda chunk: chunk.date)
        return least_recent_chunk.value


@dataclass
class LMVariable[T]:
    name: str
    """ Human-readable name shown in the UI."""
    description: str
    """ Human-readable description, also shown in the UI."""
    type: Type[T]
    """ Type that will be passed to the extraction class. Is wrapped withing MedicalFact when passed to the extraction class."""
    is_active: Optional[Callable[[Dict[str, Any]], bool]] = None
    """ Optional function to determine if the variable should be active. Takes in a dict which maps variable ids to their resolved values."""
    prompt: Optional[str] = None
    """ Optional prompt passed to the LLM for this variable."""
    resolver: Optional[Callable[[List[ChunkValue[T]]], Optional[T]]] = None
    """
    As the extraction is done on a per-chunk basis, we also get multiple values for the same variable, one per chunk.
    In order to get a final value of the variable for each patient, the resolver is called to merge the extracted values into one.
    """
    redcap_id: Optional[str] = None
    to_redcap: Optional[Callable[[T], Union[str, int, float]]] = None
    is_date: Optional[bool] = False

    def to_json(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "type": get_type_json_name(self.type),
            "redcap_id": self.redcap_id,
        }


class SmokingStatus(str, Enum):
    former_smoker = "former_smoker"
    current_smoker = "current_smoker"
    never_smoker = "never_smoker"


class NeoplasiaFindings(str, Enum):
    lgd = "low_grade_dysplasia"
    hgd = "high_grade_dysplasia"
    ind_dysplasia = "indefinite_grade_dysplasia"
    # crc = "colorectal_cancer"


class FamilyMember(str, Enum):
    father = "father"
    mother = "mother"
    siblings = "siblings"
    children = "children"
    second_degree_relative = "second_degree_relative"


class IBDType(str, Enum):
    crohns_disease = "cd"
    ulcerative_colitis = "uc"
    unclassified = "ibd_u"


class RelationshipToPatient(str, Enum):
    first_degree_relative = "first_degree_relative"
    second_degree_relative = "second_degree_relative"
    other = "other"


# c_types_cancer
# Are there types of cancer indicated in the notes? (Colorectal, Breast,Ovarian,Uterine,Lung, Gastric, Prostate,Brain,Thyroid, Liver,Cholangiocarcinoma,Other)
class CancerTypes(str, Enum):
    other = "other"
    colorectal = "colorectal"
    breast = "breast"
    ovarian = "ovarian"
    uterine = "uterine"
    lung = "lung"
    gastric = "gastric"
    prostate = "prostate"
    brain = "brain"
    thyroid = "thyroid"
    liver = "liver"
    cholangiocarcinoma = "cholangiocarcinoma"


class RelativeCancerInfo(BaseModel):
    model_config = ConfigDict(use_enum_values=True, frozen=True)  # serialize enums as their values

    relationship: RelationshipToPatient
    type: CancerTypes

    def __str__(self):
        return self.model_dump_json()

    def __json__(self):
        return json.dumps(self.model_dump_json())

    def __hash__(self):
        return hash((self.relationship, self.type))


class CancerTherapyType(str, Enum):
    chemotherapy = "chemotherapy"
    surgery = "surgery"
    radiation = "radiation"
    other = "other"


# stage_ca_crc
# What is the stage of the patient's colorectal cancer? (1=stage I, 2=stage IIa, 3=stage IIb, 4=stage IIIa, 5=stage IIIb, 6=stage IIIc, 7=stage IV, 99=Unknown)
class StageCRC(str, Enum):
    stage_I = "stage_I"
    stage_IIa = "stage_IIa"
    stage_IIb = "stage_IIb"
    stage_IIIa = "stage_IIIa"
    stage_IIIb = "stage_IIIb"
    stage_IIIc = "stage_IIIc"
    stage_IV = "stage_IV"


## new


# What is the Montreal classification of extent of UC(not crohns) at enrollment?
# (1=E1, Ulcerative proctitis; 2=E2, Left-sided colitis; 3=E3, Extensive UC; 99=Unknown)
class MontrealExtentUC(str, Enum):
    E1 = "E1 Ulcerative proctitis "
    E2 = "E2 Left-sided colitis"
    E3 = "E3 Extensive UC"


# montreal_ext_enrol_ibdu
# What is the extent of IBD-U at enrollment? (1=E1, proctitis; 2=E2, Left-sided colitis; 3=E3, Extensive colitis; 99=Unknown) -> transform into computed. Most recent
class MontrealExtentIBDU(str, Enum):
    E1 = "E1 Proctitis"
    E2 = "E2 Left-sided colitis"
    E3 = "E3 Extensive colitis"


# What is the extent of the patient's Crohn's Colitis? (1=Pancolonic involvement, 2=34-67% colonic involvement, 3=10-33% colonic involvement, 4=<10%, 5=Endoscopic remission, 88=Not applicable, 99=Unknown)
class CrohnsColitisExtent(str, Enum):
    pancolonic = "Pancolonic involvement"
    colonic_34_67 = "34-67% colonic involvement"
    colonic_10_33 = "10-33% colonic involvement"
    colonic_less_10 = "<10%"
    endoscopic_remission = "Endoscopic remission"
    not_applicable = "Not applicable"


# What is the patient's behaviour state? (1=B1 non-stricturing, non-penetrating, 2=B2 stricturing, 3=B3 penetrating, 99=Unknown) -> take from paper
class CrohnsBehaviour(str, Enum):
    B1 = "B1 Non-stricturing, non-penetrating"
    B2 = "B2 Stricturing"
    B3 = "B3 Penetrating"


# (1=L1 (ileal), 2=L2 (colonic), 3=L3 (ileocolonic), 4=L4 (isolated upper disease), 5=L1+L4, 6=L2+L4, 7=L3+L4, 99=Unknown), e.g. L3 if ‘gentleman with ileocolonic Crohn's disease’
class CrohnsDiseaseLocation(str, Enum):
    L1 = "L1 Ileal"
    L2 = "L2 Colonic"
    L3 = "L3 Ileocolonic"
    L4 = "L4 Isolated upper disease"

# r IBD-related surgery the patient has undergone (1=Small bowel resection/ileocolic resection, 2=Total proctocolectomy, 3=Subtotal colectomy, 4=Segmental (partial) colonic resection, 5=Diversion, 6=Ileostomy (non-diversion), 7=Fistula/Abscess related procedure)
class IBDRelatedSurgery(str, Enum):
    small_bowel_resection = "small bowel resection/ileocolic resection"
    total_proctocolectomy = "total proctocolectomy"
    subtotal_colectomy = "subtotal colectomy"
    segmental_colonic_resection = "segmental (partial) colonic resection"
    diversion = "diversion"
    ileostomy = "ileostomy (non-diversion)"
    fistula_abscess_related_procedure = "fistula/abscess related procedure"

class PSCExtent(str, Enum):
    extra_hepatic = "Extra-hepatic bile ducts"
    intra_hepatic = "Intra-hepatic bile ducts"
    both = "Both intra-and extra-hepatic"

# (1=Never, 2=Once, 3=Two or more, 99=Unknown)
class FrequencyEnum(str, Enum):
    never = "Never"
    once = "Once"
    two_or_more = "Two or more"


TT = TypeVar("TT")



def sortStringsAsDates(values: List[ChunkValue]):
  to_dates = [PartialDate.parse(v.value) for v in values if v.value]
  to_dates = [d for d in to_dates if d is not None]
  # if list is empty, return None
  if not to_dates:
    return None
  return str(min(to_dates))  


LM_VARIABLES: Dict[str, LMVariable] = {
    "date_ibd_dx": LMVariable(
        name="IBD diagnosis date",
        description="What is the date of IBD diagnosis?",
        type=str,
        prompt="What is the date of the patient's IBD diagnosis? This could be either CD, UC or IBD-u.",
        resolver=lambda x: ChunkValue.get_most_frequent(x),
        redcap_id="date_ibd_dx",
        to_redcap=lambda x: x,
        is_date=True
    ),
    "appendectomy": LMVariable(
        name="Appendectomy",
        description="Has the patient had an appendectomy?",
        type=bool,
        prompt="Has the patient had an appendectomy?",
        resolver=lambda x: any(v.value for v in x),
        redcap_id="appendectomy",
        to_redcap=lambda x: 1 if x else 0,
    ),
    "smoking_history": LMVariable(
        name="Smoking History",
        description="What is the patient's smoking history?",
        type=SmokingStatus,
        resolver=lambda x: ChunkValue.get_most_recent(x),
        redcap_id="smoking_history",
        to_redcap=lambda x: 1
        if x == SmokingStatus.current_smoker
        else 2
        if x == SmokingStatus.former_smoker
        else 3
        if x == SmokingStatus.never_smoker
        else 99,
    ),
    "cd_fm_hx": LMVariable(
        name="Crohn's disease family history",
        description="Is there a family member with a history of CD?",
        type=FamilyMember,
        prompt="Do the notes explicitly mention a family member with Crohn's disease? Only consider blood relatives.",
        resolver=lambda x: ChunkValue.get_most_recent(x),
        redcap_id="cd_fm_hx",
        to_redcap=lambda x: 1
        if x == FamilyMember.father
        else 2
        if x == FamilyMember.mother
        else 3
        if x == FamilyMember.siblings
        else 4
        if x == FamilyMember.children
        else 5
        if x == FamilyMember.second_degree_relative
        else 99,
    ),
    "uc_ic_fm_hx": LMVariable(
        name="Ulcerative Colitis family history",
        description="Is there a family member with a history of UC?",
        type=FamilyMember,
        prompt="Do the notes mention a specific family member with Ulcerative colitis?",
        resolver=lambda x: ChunkValue.get_most_frequent(x),
        redcap_id="uc_ic_fm_hx",
        to_redcap=lambda x: 1
        if x == FamilyMember.father
        else 2
        if x == FamilyMember.mother
        else 3
        if x == FamilyMember.siblings
        else 4
        if x == FamilyMember.children
        else 5
        if x == FamilyMember.second_degree_relative
        else 99,
    ),
    "ibdu_fam_hx": LMVariable(
        name="IBD-U family history",
        description="Is there a family member with a history of IBD-U?",
        type=FamilyMember,
        prompt="Do the notes explicitly mention a family member with IBD-U?",
        resolver=lambda x: ChunkValue.get_most_frequent(x),
        redcap_id="ibdu_fam_hx",
        to_redcap=lambda x: 1
        if x == FamilyMember.father
        else 2
        if x == FamilyMember.mother
        else 3
        if x == FamilyMember.siblings
        else 4
        if x == FamilyMember.children
        else 5
        if x == FamilyMember.second_degree_relative
        else 99,
    ),
    "pers_cancer_hx": LMVariable(
        name="Types of cancer",
        description="Personal history of cancer",
        type=List[CancerTypes],
        prompt="Did the patient have cancer at some point? If so, what type? If the cancer is not in the list of known types or not specified, please reply with 'other'.",
        resolver=lambda x: ChunkValue.list_unique(x),
    ),
    "date_dx_crc": LMVariable(
        name="Colorectal Cancer Diagnosis Date",
        description="What was the date of diagnosis for colorectal cancer?",
        is_active=lambda resolved: resolved["pers_cancer_hx"] is not None and CancerTypes.colorectal in resolved["pers_cancer_hx"] ,
        type=str,
        prompt="What was the date of diagnosis for colorectal cancer?",
        resolver=lambda x: ChunkValue.get_most_frequent(x),
        redcap_id="date_dx_crc",
        to_redcap=lambda x: str(x) if x else "",
        is_date=True
    ),
    "type_therapy_crc": LMVariable(
        name="Colorectal Cancer Therapy Type",
        description="What type of therapy was used for colorectal cancer?",
        is_active=lambda resolved: resolved["pers_cancer_hx"] is not None and CancerTypes.colorectal in resolved["pers_cancer_hx"] ,
        type=CancerTherapyType,
        prompt="What type of therapy was used for colorectal cancer?",
        resolver=lambda x: ChunkValue.get_most_frequent(x),
        redcap_id="type_therapy_crc",
        to_redcap=lambda x: 1
        if x == CancerTherapyType.chemotherapy
        else 2
        if x == CancerTherapyType.surgery
        else 3
        if x == CancerTherapyType.radiation
        else 4
        if x == CancerTherapyType.other
        else 99,
    ),
    "in_remission": LMVariable(
        name="In Remission from Colorectal Cancer",
        description="Is the patient in remission from colorectal cancer?",
        is_active=lambda resolved: resolved["pers_cancer_hx"] is not None and CancerTypes.colorectal in resolved["pers_cancer_hx"] ,
        type=bool,
        prompt="Is the patient in remission from colorectal cancer?",
        resolver=lambda x: ChunkValue.get_most_recent(x),
        redcap_id="in_remission",
        to_redcap=lambda x: 1 if x else 0,
    ),
    "stage_ca_crc": LMVariable(
        name="Colorectal Cancer Stage",
        description="What is the stage of the patient's colorectal cancer?",
        is_active=lambda resolved: resolved["pers_cancer_hx"] is not None and CancerTypes.colorectal in resolved["pers_cancer_hx"] ,
        type=StageCRC,
        prompt="What is the stage of the patient's colorectal cancer?",
        resolver=lambda x: ChunkValue.get_most_recent(x),
        redcap_id="stage_ca_crc",
        to_redcap=lambda x: 1
        if x == StageCRC.stage_I
        else 2
        if x == StageCRC.stage_IIa
        else 3
        if x == StageCRC.stage_IIb
        else 4
        if x == StageCRC.stage_IIIa
        else 5
        if x == StageCRC.stage_IIIb
        else 6
        if x == StageCRC.stage_IIIc
        else 7
        if x == StageCRC.stage_IV
        else 99,
    ),
    "date_of_remission": LMVariable(
        name="Date of Remission from non-colorectal Cancer",
        description="What is the date of remission from non-colorectal cancer?",
        is_active=lambda resolved: resolved["pers_cancer_hx"] is not None and len(resolved["pers_cancer_hx"]) > 0 and CancerTypes.colorectal not in resolved["pers_cancer_hx"],
        type=str,
        prompt="What is the date of remission from non-colorectal cancer?",
        resolver=lambda x: ChunkValue.get_most_frequent(x),
        redcap_id="date_of_remission",
        to_redcap=lambda x: str(x) if x else "",
        is_date=True
    ),
    "type_therapy_ncrc": LMVariable(
        name="Colorectal Cancer Therapy Type",
        description="Type of therapy used for non-colorectal cancer",
        is_active=lambda resolved: resolved["pers_cancer_hx"] is not None and len(resolved["pers_cancer_hx"]) > 0 and CancerTypes.colorectal not in resolved["pers_cancer_hx"],
        type=CancerTherapyType,
        prompt="What type of therapy was used for non-colorectal cancer?",
        resolver=lambda x: ChunkValue.get_most_frequent(x),
        redcap_id="type_therapy_ncrc",
        to_redcap=lambda x: 1
        if x == CancerTherapyType.chemotherapy
        else 2
        if x == CancerTherapyType.surgery
        else 3
        if x == CancerTherapyType.radiation
        else 4
        if x == CancerTherapyType.other
        else 99,
    ),
    "in_remission_ncrc": LMVariable(
        name="In Remission from Non-Colorectal Cancer",
        description="Is the patient in remission from non-colorectal cancer?",
        is_active=lambda resolved: resolved["pers_cancer_hx"] is not None and len(resolved["pers_cancer_hx"]) > 0 and CancerTypes.colorectal not in resolved["pers_cancer_hx"],
        type=bool,
        prompt="Is the patient in remission from non-colorectal cancer?",
        resolver=lambda x: ChunkValue.get_most_recent(x),
        redcap_id="in_remission_ncrc",
        to_redcap=lambda x: 1 if x else 0,
    ),
    "fam_cancer_hx": LMVariable(
        name="Cancer Family History",
        description="Are there family members with a cancer diagnosis?",
        type=List[RelativeCancerInfo],
        prompt="List the family members and the kind of cancer if present in the notes. ",
        resolver=lambda x: ChunkValue.list_unique(x)
    ),
    "ibd_type": LMVariable(
        name="IBD type",
        description="What type of IBD has been diagnosed?",
        type=IBDType,
        prompt="What type of IBD has been diagnosed?", #Crohns Collitis is a type of CD.
        resolver=lambda x: ChunkValue.get_most_frequent(x),
        redcap_id="ibd_type",
        to_redcap=lambda x: 1
        if x == IBDType.crohns_disease
        else 2
        if x == IBDType.ulcerative_colitis
        else 3
        if x == IBDType.unclassified
        else 99,
    ),
    "montreal_ext_enrol_encnter": LMVariable(
        name="Montreal Classification: Extent of UC",
        description="What is the Montreal classification of extent of UC at enrollment?",
        is_active=lambda resolved: resolved["ibd_type"] == IBDType.ulcerative_colitis,
        type=MontrealExtentUC,
        prompt="What is the Montreal classification of extent of UC? E1=Involvement limited to the rectum (proximal extent of inflammation is distal to the rectosigmoid junction), E2=Involvement limited to a portion of the colorectum distal to the splenic flexure, E3=Involvement extends proximal to the splenic flexure",
        resolver=lambda x: ChunkValue.get_most_recent(x),
        redcap_id="montreal_ext_enrol_encnter",
        to_redcap=lambda x: 1
        if x == MontrealExtentUC.E1
        else 2
        if x == MontrealExtentUC.E2
        else 3
        if x == MontrealExtentUC.E3
        else 99,
    ),
    "montreal_ext_enrol_ibdu": LMVariable(
        name="Montreal Classification: Extent of IBD-U",
        description="What is the extent of IBD-U at enrollment?",
        is_active=lambda resolved: resolved["ibd_type"] == IBDType.unclassified,
        type=MontrealExtentIBDU,
        prompt="What is the extent of IBD-U?",
        resolver=lambda x: ChunkValue.get_least_recent(x),
        redcap_id="montreal_ext_enrol_ibdu",
        to_redcap=lambda x: 1
        if x == MontrealExtentIBDU.E1
        else 2
        if x == MontrealExtentIBDU.E2
        else 3
        if x == MontrealExtentIBDU.E3
        else 99,
    ),
    "crohn_colitis_baseline": LMVariable(
        name="Crohn's Colitis Extent",
        description="What is the extent of the patient's Crohn's Colitis?",
        is_active=lambda resolved: resolved["ibd_type"] == IBDType.crohns_disease,
        type=CrohnsColitisExtent,
        prompt="What is the extent of the patient's Crohn's Colitis?",
        resolver=lambda x: ChunkValue.get_most_recent(x),
        redcap_id="crohn_colitis_baseline",
        to_redcap=lambda x: 1
        if x == CrohnsColitisExtent.pancolonic
        else 2
        if x == CrohnsColitisExtent.colonic_34_67
        else 3
        if x == CrohnsColitisExtent.colonic_10_33
        else 4
        if x == CrohnsColitisExtent.colonic_less_10
        else 5
        if x == CrohnsColitisExtent.endoscopic_remission
        else 88
        if x == CrohnsColitisExtent.not_applicable
        else 99,
    ),
    "behaviour": LMVariable(
        name="Crohn's Disease Behaviour",
        description="What is the patient's behaviour state?",
        is_active=lambda resolved: resolved["ibd_type"] == IBDType.crohns_disease,
        type=CrohnsBehaviour,
        prompt="What is the patient's behaviour state?",
        resolver=lambda x: ChunkValue.get_most_recent(x),
        redcap_id="behaviour",
        to_redcap=lambda x: 1
        if x == CrohnsBehaviour.B1
        else 2
        if x == CrohnsBehaviour.B2
        else 3
        if x == CrohnsBehaviour.B3
        else 99,
    ),
    # "age_diagn": LMVariable(
    #     name="Age of CD Diagnosis",
    #     description="What was the patient's age at diagnosis of CD, UC or IBD-U?",
    #     type=int,
    #     prompt="What was the patient's age at diagnosis of CD, UC or IBD-U?",
    #     resolver=lambda x: ChunkValue.get_most_frequent(x),
    #     redcap_id="age_diagn",
    #     to_redcap=lambda x: 1 if x < 17 else 2 if x < 41 else 3 if x > 40 else 99,
    # ),
    # perianal_dis
    # Does the patient have perianal disease? (1=Yes, 0=No, 99=Unknown)
    "perianal_dis": LMVariable(
        name="Perianal Disease",
        description="Does the patient have perianal disease?",
        type=bool,
        prompt="Does the patient have perianal disease?",
        resolver=lambda x: any(v.value for v in x),
        redcap_id="perianal_dis",
        to_redcap=lambda x: 1 if x else 0,
    ),
    "disease_location": LMVariable(
        name="Disease Location",
        description="What is the most recently reported crohns disease location of the patient?",
        #  is active if crohns is found:
        is_active=lambda resolved: resolved["ibd_type"] == IBDType.crohns_disease,
        type=List[CrohnsDiseaseLocation],
        prompt="What is the most recently reported location of crohns in the patient?",
        resolver=lambda x: ChunkValue.get_most_recent(x),
        redcap_id="disease_location",
        to_redcap=lambda x: 
            7 if {CrohnsDiseaseLocation.L3, CrohnsDiseaseLocation.L4}.issubset(x)
            else 6 if {CrohnsDiseaseLocation.L2, CrohnsDiseaseLocation.L4}.issubset(x)
            else 5 if {CrohnsDiseaseLocation.L1, CrohnsDiseaseLocation.L4}.issubset(x)
            else 4 if CrohnsDiseaseLocation.L4 in x
            else 3 if CrohnsDiseaseLocation.L3 in x
            else 2 if CrohnsDiseaseLocation.L2 in x
            else 1 if CrohnsDiseaseLocation.L1 in x
            else 99,
    ),
    "date_hosp": LMVariable(
        name="Hospitalization Dates",
        description="Any dates at which the patient has been hospitalized.",
        type=List[str],
        prompt="List any dates at which the patient has been hospitalized. (format: YYYY-MM-DD)",
        resolver=lambda x: ChunkValue.list_unique(x),
        is_date=True
    ),
    "base_check_surg": LMVariable(
        name="IBD-related Surgery",
        description="Check any type of prior IBD-related surgery the patient has undergone.",
        type=List[IBDRelatedSurgery],
        prompt="List any type of prior IBD-related surgery the patient has undergone.",
        #  x is a list of list of IBDRelatedSurgery enums
        # get all unique values from all lists
        resolver=lambda x: ChunkValue.list_unique(x),
        redcap_id="base_check_surg",
        to_redcap=lambda x: str([
            1 if val == IBDRelatedSurgery.small_bowel_resection else
            2 if val == IBDRelatedSurgery.total_proctocolectomy else
            3 if val == IBDRelatedSurgery.subtotal_colectomy else
            4 if val == IBDRelatedSurgery.segmental_colonic_resection else
            5 if val == IBDRelatedSurgery.diversion else
            6 if val == IBDRelatedSurgery.ileostomy else
            7 if val == IBDRelatedSurgery.fistula_abscess_related_procedure else
            99 for val in x
        ]),
        is_date=True
    ),
    "prior_dyspl": LMVariable(
        name="Prior Colonic Dysplasia",
        description="Does the patient have a prior history of colonic dysplasia?",
        type=bool,
        prompt="Does the patient have a history of colonic dysplasia?",
        resolver=lambda x: any(v.value for v in x),
        redcap_id="prior_dyspl",
        to_redcap=lambda x: 1 if x else 0,
    ),
    "date_surg_dys_crc": LMVariable(
        name="Dysplasia or Cancer Surgery Date",
        description="When was the date of surgery for dysplasia or cancer?",
        is_active=lambda resolved: resolved["prior_dyspl"],
        type=str,
        prompt="When was the date of surgery for dysplasia or cancer? (format: YYYY-MM-DD)",
        resolver=lambda x: ChunkValue.get_most_frequent(x),
        redcap_id="date_surg_dys_crc",
        to_redcap=lambda x: str(x) if x else "",
        is_date=True
    ),
    "type_prior_dys": LMVariable(
        name="Dysplasia Type",
        description="What was the type of dysplasia?",
        is_active=lambda resolved: resolved["prior_dyspl"],
        type=NeoplasiaFindings,
        prompt="What is the type of dysplasia?",
        resolver=lambda x: ChunkValue.get_most_recent(x),
        redcap_id="type_prior_dys",
        to_redcap=lambda x: 1
        if x == NeoplasiaFindings.lgd
        else 2
        if x == NeoplasiaFindings.hgd
        else 3
        if x == NeoplasiaFindings.ind_dysplasia
        else 99,
    ),
    "sur_dys": LMVariable(
        name="Dysplasia Surgery History",
        description="Were any surgeries for dysplasia conducted at or prior to enrollment?",
        is_active=lambda resolved: resolved["prior_dyspl"],
        type=bool,
        prompt="Were any surgeries for dysplasia conducted at or prior to enrollment?",
        resolver=lambda x: any(v.value for v in x),
        redcap_id="sur_dys",
        to_redcap=lambda x: 1 if x else 0,
    ),
    "psc_hx": LMVariable(
        name="PSC History",
        description="Does the patient have a history of Primary Sclerosing Cholangitis (PSC) at the time of enrollment?",
        type=bool,
        prompt="Does the patient have a history of Primary Sclerosing Cholangitis (PSC)?",
        resolver=lambda x: any(v.value for v in x),
        redcap_id="psc_hx",
        to_redcap=lambda x: 1 if x else 0,
    ),
     "date_dgnsis_psc": LMVariable(
        name="PSC Diagnosis Date",
        description="What was the date of diagnosis for PSC?",
        is_active=lambda resolved: resolved["psc_hx"],
        type=str,
        prompt="What was the date of diagnosis for PSC? (format: YYYY-MM-DD)",
        # resolve to the most frequently reported value, NOT the one with the most recent date :
        resolver=lambda x: ChunkValue.get_most_frequent(x),
        redcap_id="date_dgnsis_psc",
        to_redcap=lambda x: str(x) if x else "",
        is_date=True
    ),
    "psc_dt_mt": LMVariable(
        name="Date of First Encounter for PSC",
        description="What was the date of the patient's first encounter at Sinai for PSC?",
        is_active=lambda resolved: resolved["psc_hx"],
        type=str,
        prompt="What was the date of the patient's first encounter for PSC? (format: YYYY-MM-DD)",
        resolver=lambda x: sortStringsAsDates(x) if x else None,
        redcap_id="psc_dt_mt",
        to_redcap=lambda x: str(x) if x else "",
        is_date=True
    ),
    "psc_extent": LMVariable(
        name="PSC Extent",
        description="What is the extent of the PSC?",
        is_active=lambda resolved: resolved["psc_hx"],
        type=PSCExtent,
        prompt="What is the extent of the PSC?",
        resolver=lambda x: ChunkValue.get_most_recent(x),
        redcap_id="psc_extent",
        to_redcap=lambda x: 1
        if x == PSCExtent.extra_hepatic
        else 2
        if x == PSCExtent.intra_hepatic
        else 3
        if x == PSCExtent.both
        else 99,
    ),
    "psc_hx_chlgitis2": LMVariable(
        name="PSC Cholangitis History",
        description="Has the patient ever had a history of cholangitis?",
        is_active=lambda resolved: resolved["psc_hx"],
        type=FrequencyEnum,
        prompt="Has the patient ever had a history of cholangitis? (1=Never, 2=Once, 3=Two or more, 99=Unknown)",
        resolver=lambda x: ChunkValue.get_most_recent(x),
        redcap_id="psc_hx_chlgitis2",
        to_redcap=lambda x: 1 if x == FrequencyEnum.never else
        2 if x == FrequencyEnum.once else
        3 if x == FrequencyEnum.two_or_more else
        99
    ),
    "psc_hx_bile": LMVariable(
        name="PSC Bile Duct Stricture History",
        description="Does the patient have a history of bile duct stricture?",
        is_active=lambda resolved: resolved["psc_hx"],
        type=bool,
        prompt="Does the patient have a history of bile duct stricture?",
        resolver=lambda x: any(v.value for v in x),
        redcap_id="psc_hx_bile",
        to_redcap=lambda x: 1 if x else 0,
    ),

    "psc_hx_var_bled": LMVariable(
        name="PSC Variceal Bleeding History",
        description="Has the patient had a history of variceal bleeding?",
        is_active=lambda resolved: resolved["psc_hx"],
        type=bool,
        prompt="Has the patient had a history of variceal bleeding?",
        resolver=lambda x: any(v.value for v in x),
        redcap_id="psc_hx_var_bled",
        to_redcap=lambda x: 1 if x else 0,
    ),


    "psc_hx_absc": LMVariable(
        name="PSC Ascites History",
        description="Does the patient have a history of ascites?",
        is_active=lambda resolved: resolved["psc_hx"],
        type=bool,
        prompt="Does the patient have a history of ascites?",
        resolver=lambda x: any(v.value for v in x),
        redcap_id="psc_hx_absc",
        to_redcap=lambda x: 1 if x else 0,
    ),

    "psc_hx_sbp2": LMVariable(
        name="PSC SBP History",
        description="Does the patient have a history of Spontaneous Bacterial Peritonitis (SBP)?",
        is_active=lambda resolved: resolved["psc_hx"],
        type=bool,
        prompt="Does the patient have a history of SBP?",
        resolver=lambda x: any(v.value for v in x),
        redcap_id="psc_hx_sbp2",
        to_redcap=lambda x: 1 if x else 0,
    ),
    "psc_hx_encl": LMVariable(
        name="PSC Encephalopathy History",
        description="Has there been any history of encephalopathy?",
        is_active=lambda resolved: resolved["psc_hx"],
        type=bool,
        prompt="Has there been any history of encephalopathy?",
        resolver=lambda x: any(v.value for v in x),
        redcap_id="psc_hx_encl",
        to_redcap=lambda x: 1 if x else 0,
    ),
    "psc_hx_hcc2": LMVariable(
        name="PSC HCC History",
        description="Does the patient have a history of hepatocellular carcinoma (HCC)?",
        is_active=lambda resolved: resolved["psc_hx"],
        type=bool,
        prompt="Does the patient have a history of HCC?",
        resolver=lambda x: any(v.value for v in x),
        redcap_id="psc_hx_hcc2",
        to_redcap=lambda x: 1 if x else 0,
    ),

    "psc_radiation": LMVariable(
        name="PSC Radiation/RFA Treatment",
        description="Has the patient received Radiation or Radiofrequency Ablation (RFA) treatment?",
        is_active=lambda resolved: resolved["psc_hx"],
        type=bool,
        prompt="Has the patient received Radiation or RFA treatment?",
        resolver=lambda x: any(v.value for v in x),
        redcap_id="psc_radiation",
        to_redcap=lambda x: 1 if x else 0,
    ),

    "psc_cholcanc": LMVariable(
        name="PSC Cholangiocarcinoma History",
        description="What is the patient's history of cholangiocarcinoma?",
        is_active=lambda resolved: resolved["psc_hx"],
        type=bool,
        prompt="What is the patient's history of cholangiocarcinoma?",
        resolver=lambda x: any(v.value for v in x),
        redcap_id="psc_cholcanc",
        to_redcap=lambda x: 1 if x else 0,
    ),

    "psc_cholcanc2": LMVariable(
        name="PSC Cholangiocarcinoma Diagnosis Date",
        description="What is the date of the cholangiocarcinoma diagnosis?",
        is_active=lambda resolved:  resolved["psc_hx"],
        type=str,
        prompt="What is the date of the cholangiocarcinoma diagnosis? (format: YYYY-MM-DD)",
        resolver=lambda x: ChunkValue.get_most_frequent(x),
        redcap_id="psc_cholcanc2",
        to_redcap=lambda x: str(x) if x else "",
        is_date=True
    ),

    "psc_hx_liv_trsn": LMVariable(
        name="PSC Liver Transplant History",
        description="What is the patient's history of liver transplant?",
        is_active=lambda resolved: resolved["psc_hx"],
        type=bool,
        prompt="What is the patient's history of liver transplant?",
        resolver=lambda x: any(v.value for v in x),
        redcap_id="psc_hx_liv_trsn",
        to_redcap=lambda x: 1 if x else 0,
    ),
    "psc_olt_dt": LMVariable(
        name="PSC OLT Date",
        description="What is the date of the patient's OLT?",
        is_active=lambda resolved: resolved["psc_hx"],
        type=str,
        prompt="What is the date of the patient's OLT? (format: YYYY-MM-DD)",
        resolver=lambda x: ChunkValue.get_most_frequent(x),
        redcap_id="psc_olt_dt",
        to_redcap=lambda x: str(x) if x else "",
        is_date=True
    ),

    "psc_hx_liv_surg": LMVariable(
        name="PSC Liver/Bile Duct Surgery History",
        description="Does the patient have a history of liver or bile duct surgery?",
        is_active=lambda resolved: resolved["psc_hx"],
        type=bool,
        prompt="Does the patient have a history of liver or bile duct surgery?",
        resolver=lambda x: any(v.value for v in x),
        redcap_id="psc_hx_liv_surg",
        to_redcap=lambda x: 1 if x else 0,
    ),

    "psc_olt_dt2_d28": LMVariable(
        name="PSC Liver/Bile Duct Surgery Date",
        description="What was the date of the patient's liver or bile duct surgery?",
        is_active=lambda resolved: resolved["psc_hx"],
        type=str,
        prompt="What was the date of the patient's liver or bile duct surgery? (format: YYYY-MM-DD)",
        resolver=lambda x: ChunkValue.get_most_frequent(x),
        redcap_id="psc_olt_dt2_d28",
        to_redcap=lambda x: str(x) if x else "",
        is_date=True
    ),
    "psc_dialysis2": LMVariable(
        name="PSC Dialysis Status",
        description="Is the patient currently on dialysis?",
        is_active=lambda resolved: resolved["psc_hx"],
        type=bool,
        prompt="Is the patient currently on dialysis?",
        resolver=lambda x: ChunkValue.get_most_frequent(x),
        redcap_id="psc_dialysis2",
        to_redcap=lambda x: 1 if x else 0,
    ),
}

def create_medical_record_class(variables: Dict[str, LMVariable]) -> Type[BaseModel]:
    fields = {}

    for field_name, variable in variables.items():
        # Create the field type as Optional[MedicalFact[variable.type]]
        field_type = Optional[MedicalFact.with_type(variable.type)]

        # Create the Field with description from LMVariable
        field = Field(default=None, description=variable.prompt)

        fields[field_name] = (field_type, field)

    # Create the MedicalRecord class dynamically
    return create_model("MedicalRecord", **fields, __base__=BaseModel)


###########################
## 🧮 Computed Variables ##
###########################


def notNullExists(name, mrn_variables):
    """Check if any mrn_variable contains non-null value for given name"""
    return any(mrn_variable[name] is not None for mrn_variable in mrn_variables)


def anyEquals(name, value, mrn_variables):
    """Check if any mrn_variable contains specified value for given name"""
    return any(mrn_variable[name] == value for mrn_variable in mrn_variables)


def sumUniqueListItems(name, mrn_variables):
    """Sum unique items in a list for given name"""
    return sum(
        len(set(mrn_variable[name]))
        for mrn_variable in mrn_variables
        if isinstance(mrn_variable[name], list)
    )


@dataclass
class ComputedVariable:
    name: str
    description: str
    compute_func: Callable[[List[Dict]], Any]
    dependencies: List[str]

    def compute(self, mrn_variables: List[Dict]):
        # return {"name": self.name, "value": self.compute_func(mrn_variables)}
        return self.compute_func(mrn_variables)

    def validate_dependencies(self, mrn_variables: List[Any]) -> bool:
        for dep in self.dependencies:
            for cls in mrn_variables:
                if cls[dep]:
                    return True
        return False


computable_variables = [
    ComputedVariable(
        name="pt_survl_mts_out",
        description="Was the patient undergoing surveillance prior to enrollment either at Mt Sinai or outside? (1=Yes, 0=No, 99=Unknown)",
        compute_func=lambda mrn_variables: 1
        if notNullExists("pt_ibd_surv", mrn_variables)
        else 0,
        dependencies=["pt_ibd_surv"],
    ),
    # ComputedVariable(
    #     name="pers_crc",
    #     # Does the patient have Colorectal cancer?
    #     description="Does the patient have Colorectal cancer? (1=Yes, 0=No, 99=Unknown)",
    #     # check if any run.pers_cancer_hx has value CancerTypes.crc:
    #     # compute_func=lambda mrn_variables: any([ x. ])
    #     dependencies=["pers_cancer_hx"],
    # )
    # 🏗️ WIP
    # ComputedVariable(
    #     name="num_hosp",
    #     description="How many times has the patient been hospitalized?",
    #     compute_func=lambda mrn_variables: sumUniqueListItems(
    #         "dates_hosp", mrn_variables
    #     ),
    #     dependencies=["dates_hosp"],
    # ),
    # ComputedVariable(
    #     name="sur_dys_cancer",
    #     description="Were any surgeries for dysplasia and/or colorectal cancer conducted at or prior to enrollment? (1=Yes, 0=No, 99=Unknown)",
    #     compute_func=lambda mrn_variables: 1
    #     if notNullExists("date_surg_dys_crc", mrn_variables)
    #     else 0,
    #     dependencies=["date_surg_dys_crc"],
    # ),
]


def process_computed_vars(mrn_variables: List[Dict]):
    """
    Process computed variables from the extracted variables

    Args:
        mrn_variables (List[dict]): A list of dictionaries containing extracted variables for each MRN

    Returns:
        List[dict]: A list of dictionaries containing processed computed variables
    """

    results = {}
    for var in computable_variables:
        if var.validate_dependencies(mrn_variables):
            # results.append(var.compute(mrn_variables))
            results[var.name] = var.compute(mrn_variables)
        else:
            print(f"Dependencies not met for {var.name}. Skipping computation.")
    return results


def export_variable_definition():
    variables_json = {
        name: variable.to_json() for name, variable in LM_VARIABLES.items()
    }
    return json.dumps(variables_json, indent=2)
