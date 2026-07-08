import re
from enum import Enum
from typing import List, Dict, Any, Optional

from app.rag.structure.types import ElementType

class QueryType(str, Enum):
    FACTUAL = 'factual'
    PROCEDURAL = 'procedural'
    CONCEPTUAL = 'conceptual'
    COMPARATIVE = 'comparative'
    LISTING = 'listing'
    NUMERICAL = 'numerical'
    DEFINITION = 'definition'
    ENTITY = 'entity'
    SUMMARY = 'summary'

DEFAULT_BOOST_FACTORS = {
    "tableBoost": 1.0,
    "listBoost": 1.0,
    "paragraphBoost": 1.0,
    "codeBoost": 1.0,
    "headerBoost": 1.0,
    "numericContentBoost": 1.0,
    "definitionBoost": 1.0,
    "exampleBoost": 1.0,
}

class QueryAnalysis:
    def __init__(
        self,
        originalQuery: str,
        queryType: QueryType,
        preferredElementTypes: List[ElementType],
        requiredMetadata: dict,
        boostFactors: dict
    ):
        self.originalQuery = originalQuery
        self.queryType = queryType
        self.preferredElementTypes = preferredElementTypes
        self.requiredMetadata = requiredMetadata
        self.boostFactors = boostFactors

    def to_dict(self) -> dict:
        return {
            "originalQuery": self.originalQuery,
            "queryType": self.queryType.value if isinstance(self.queryType, QueryType) else self.queryType,
            "preferredElementTypes": [t.value if isinstance(t, ElementType) else t for t in self.preferredElementTypes],
            "requiredMetadata": self.requiredMetadata,
            "boostFactors": self.boostFactors
        }

class QueryAnalyzer:
    PATTERNS = {
        QueryType.ENTITY: [
            r"\b(\w+)\s+works?\s+in\s+(which|what)\b",
            r"\bwho\s+works?\s+in\b",
            r"\bwhat\s+(department|team|role)\s+(does|is)\b",
            r"\bwhich\s+\w+\s+(is|does|has|works)\b",
            r"\bwhere\s+does\s+\w+\s+work\b",
            r"\b\w+['']s?\s+(department|role|team|job)\b",
        ],
        QueryType.NUMERICAL: [
            r"\bhow\s+(many|much)\b",
            r"\bnumber\s+of\b",
            r"\bcount\s+(of|the)?\b",
            r"\btotal\s+(number|count)?\s*(of)?\b",
            r"\bpercentage\b",
            r"\bstatistics?\b",
            r"\baverage\b",
            r"\brate\b",
            r"\bprice\b",
            r"\bcost\b",
            r"\bvalue\b",
        ],
        QueryType.PROCEDURAL: [
            r"\bhow\s+(do|can|to|should|would)\b",
            r"\bsteps?\s+to\b",
            r"\bguide\s+(to|for|on)\b",
            r"\btutorial\b",
            r"\bprocess\s+(of|for)\b",
            r"\bimplement\b",
            r"\bcreate\s+a?\b",
            r"\bset\s*up\b",
        ],
        QueryType.SUMMARY: [
            r"\bwhat\s+is\s+this\s+(document|file|pdf)\s+about\b",
            r"\bsummar(y|ize)\b",
            r"\bmain\s+(topic|subject|point|idea)\b",
            r"\boverview\b",
            r"\bwhat\s+does\s+this\s+(document|file)\b",
            r"\babout\s+this\s+(document|pdf)\b",
        ],
        QueryType.DEFINITION: [
            r"\bwhat\s+is\b",
            r"\bwhat\s+are\b",
            r"\bdefine\b",
            r"\bdefinition\s+of\b",
            r"\bmeaning\s+of\b",
            r"\bwhat\s+does\s+.+\s+mean\b",
        ],
        QueryType.LISTING: [
            r"\blist\s+(all|the)?\b",
            r"\bwhat\s+are\s+(all|the)\b",
            r"\benumerate\b",
            r"\bname\s+(all|the)\b",
            r"\btypes\s+of\b",
            r"\bkinds\s+of\b",
            r"\bcategories\s+of\b",
            r"\bmention(ed)?\b",
        ],
        QueryType.COMPARATIVE: [
            r"\bcompare\b",
            r"\bdifference\s+between\b",
            r"\bvs\.?\b",
            r"\bversus\b",
            r"\bbetter\s+than\b",
            r"\bsimilar\s+to\b",
            r"\bcontrast\b",
        ],
        QueryType.CONCEPTUAL: [
            r"\bexplain\b",
            r"\bdescribe\b",
            r"\bwhy\s+(does|is|do|are)\b",
            r"\bunderstand\b",
            r"\bconcept\s+of\b",
            r"\bpurpose\s+of\b",
        ],
        QueryType.FACTUAL: [
            r"\bwho\b",
            r"\bwhen\b",
            r"\bwhere\b",
            r"\bwhich\b",
        ],
    }

    CODE_KEYWORDS = [
        'code', 'function', 'class', 'method', 'api', 'syntax',
        'example', 'implementation', 'snippet', 'script', 'program',
    ]

    TABLE_KEYWORDS = [
        'table', 'data', 'statistics', 'numbers', 'comparison',
        'summary', 'overview', 'breakdown', 'results', 'metrics',
    ]

    LIST_KEYWORDS = [
        'list', 'steps', 'features', 'requirements', 'benefits',
        'advantages', 'options', 'types', 'kinds', 'categories',
    ]

    def analyze(self, query: str) -> QueryAnalysis:
        query_type = self.detect_query_type(query)
        preferred = self.determine_preferred_elements(query, query_type)
        metadata = self.determine_required_metadata(query, query_type)
        boosts = self.calculate_boost_factors(query, query_type)

        return QueryAnalysis(
            originalQuery=query,
            queryType=query_type,
            preferredElementTypes=preferred,
            requiredMetadata=metadata,
            boostFactors=boosts
        )

    def detect_query_type(self, query: str) -> QueryType:
        lower = query.lower()
        for q_type, patterns in self.PATTERNS.items():
            for pat in patterns:
                if re.search(pat, lower):
                    return q_type
        return QueryType.FACTUAL

    def determine_preferred_elements(self, query: str, query_type: QueryType) -> List[ElementType]:
        preferred = []
        lower = query.lower()

        if query_type == QueryType.ENTITY:
            preferred.extend([ElementType.TABLE, ElementType.PARAGRAPH, ElementType.LIST])
        elif query_type == QueryType.NUMERICAL:
            preferred.extend([ElementType.TABLE, ElementType.LIST, ElementType.PARAGRAPH])
        elif query_type == QueryType.SUMMARY:
            preferred.extend([ElementType.HEADER, ElementType.PARAGRAPH, ElementType.LIST])
        elif query_type == QueryType.LISTING:
            preferred.extend([ElementType.LIST, ElementType.TABLE, ElementType.PARAGRAPH])
        elif query_type == QueryType.PROCEDURAL:
            preferred.extend([ElementType.LIST, ElementType.CODE_BLOCK, ElementType.PARAGRAPH])
        elif query_type == QueryType.COMPARATIVE:
            preferred.extend([ElementType.TABLE, ElementType.LIST, ElementType.PARAGRAPH])
        elif query_type in [QueryType.DEFINITION, QueryType.CONCEPTUAL]:
            preferred.extend([ElementType.PARAGRAPH, ElementType.HEADER])
        else:
            preferred.append(ElementType.PARAGRAPH)

        has_code = any(k in lower for k in self.CODE_KEYWORDS)
        has_table = any(k in lower for k in self.TABLE_KEYWORDS)
        has_list = any(k in lower for k in self.LIST_KEYWORDS)

        if has_code and ElementType.CODE_BLOCK not in preferred:
            preferred.insert(0, ElementType.CODE_BLOCK)
        if has_table and ElementType.TABLE not in preferred:
            preferred.insert(0, ElementType.TABLE)
        if has_list and ElementType.LIST not in preferred:
            preferred.insert(0, ElementType.LIST)

        return preferred

    def determine_required_metadata(self, query: str, query_type: QueryType) -> dict:
        metadata = {}
        lower = query.lower()

        if query_type == QueryType.NUMERICAL:
            metadata["mustHaveNumbers"] = True

        if any(k in lower for k in self.CODE_KEYWORDS):
            metadata["mustHaveCode"] = True

        if re.search(r"\b(when|date|year|month|time)\b", lower):
            metadata["mustHaveDates"] = True

        return metadata

    def calculate_boost_factors(self, query: str, query_type: QueryType) -> dict:
        factors = {**DEFAULT_BOOST_FACTORS}
        lower = query.lower()

        if query_type == QueryType.ENTITY:
            factors["tableBoost"] = 1.8
            factors["listBoost"] = 1.3
            factors["paragraphBoost"] = 1.2
        elif query_type == QueryType.NUMERICAL:
            factors["tableBoost"] = 1.6
            factors["numericContentBoost"] = 1.5
            factors["listBoost"] = 1.3
        elif query_type == QueryType.SUMMARY:
            factors["headerBoost"] = 1.5
            factors["paragraphBoost"] = 1.4
            factors["listBoost"] = 1.2
        elif query_type == QueryType.LISTING:
            factors["listBoost"] = 1.5
            factors["tableBoost"] = 1.4
        elif query_type == QueryType.PROCEDURAL:
            factors["listBoost"] = 1.4
            factors["codeBoost"] = 1.3
            factors["exampleBoost"] = 1.3
        elif query_type == QueryType.DEFINITION:
            factors["definitionBoost"] = 1.5
            factors["paragraphBoost"] = 1.3
        elif query_type == QueryType.CONCEPTUAL:
            factors["paragraphBoost"] = 1.3
            factors["exampleBoost"] = 1.2
        elif query_type == QueryType.COMPARATIVE:
            factors["tableBoost"] = 1.4
            factors["listBoost"] = 1.3

        if any(k in lower for k in self.CODE_KEYWORDS):
            factors["codeBoost"] = max(factors.get("codeBoost", 1.0), 1.4)
        if re.search(r"\bexample\b", lower):
            factors["exampleBoost"] = max(factors.get("exampleBoost", 1.0), 1.4)

        return factors

    def apply_boosts(self, results: List[dict], analysis: QueryAnalysis) -> List[dict]:
        boosted = []
        for res in results:
            boost = 1.0
            meta = res.get("metadata") or {}
            factors = analysis.boostFactors

            el_type = meta.get("elementType")
            if el_type == ElementType.TABLE.value:
                boost *= factors.get("tableBoost", 1.0)
            elif el_type == ElementType.LIST.value:
                boost *= factors.get("listBoost", 1.0)
            elif el_type == ElementType.CODE_BLOCK.value:
                boost *= factors.get("codeBoost", 1.0)
            elif el_type == ElementType.HEADER.value:
                boost *= factors.get("headerBoost", 1.0)
            elif el_type == ElementType.PARAGRAPH.value:
                boost *= factors.get("paragraphBoost", 1.0)

            if meta.get("containsNumbers") or meta.get("hasNumericData"):
                boost *= factors.get("numericContentBoost", 1.0)
            if meta.get("hasDefinitions"):
                boost *= factors.get("definitionBoost", 1.0)
            if meta.get("hasExamples"):
                boost *= factors.get("exampleBoost", 1.0)

            if meta.get("searchBoost"):
                boost *= float(meta["searchBoost"])

            boosted.append({
                **res,
                "boostedScore": res.get("similarity", 0.0) * boost
            })
        return boosted
