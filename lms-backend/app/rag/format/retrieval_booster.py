from typing import List, Dict, Any, Optional, Tuple

from app.rag.format.types import OutputFormat, DetectionConfidence
from app.rag.format.intent_detector import FormatIntent
from app.rag.structure.types import ElementType

class BoostConfig:
    def __init__(
        self,
        highConfidenceMultiplier: float = 1.5,
        mediumConfidenceMultiplier: float = 1.25,
        lowConfidenceMultiplier: float = 1.0
    ):
        self.highConfidenceMultiplier = highConfidenceMultiplier
        self.mediumConfidenceMultiplier = mediumConfidenceMultiplier
        self.lowConfidenceMultiplier = lowConfidenceMultiplier

class RetrievalBoostResult:
    def __init__(self, element_type_boosts: Dict[ElementType, float], metadata_filters: dict, preferred_types: List[ElementType]):
        self.elementTypeBoosts = element_type_boosts
        self.metadataFilters = metadata_filters
        self.preferredTypes = preferred_types

class RetrievalBooster:
    def __init__(self, config: dict = None):
        cfg = config or {}
        self.config = BoostConfig(
            highConfidenceMultiplier=cfg.get("highConfidenceMultiplier", 1.5),
            mediumConfidenceMultiplier=cfg.get("mediumConfidenceMultiplier", 1.25),
            lowConfidenceMultiplier=cfg.get("lowConfidenceMultiplier", 1.0)
        )

    def calculate_boosts(self, intent: FormatIntent) -> RetrievalBoostResult:
        boosts = {}
        preferred = []
        meta_filters = {}

        multiplier = self.get_confidence_multiplier(intent.confidence)
        fmt_val = intent.format.value if isinstance(intent.format, OutputFormat) else intent.format

        if fmt_val == OutputFormat.TABLE.value:
            boosts[ElementType.TABLE] = 1.5 * multiplier
            boosts[ElementType.LIST] = 1.2 * multiplier
            preferred.extend([ElementType.TABLE, ElementType.LIST])
            meta_filters["hasNumericData"] = True
        elif fmt_val == OutputFormat.LIST.value:
            boosts[ElementType.LIST] = 1.5 * multiplier
            boosts[ElementType.TABLE] = 1.2 * multiplier
            preferred.extend([ElementType.LIST, ElementType.TABLE])
        elif fmt_val == OutputFormat.STEPS.value:
            boosts[ElementType.LIST] = 1.4 * multiplier
            boosts[ElementType.CODE_BLOCK] = 1.3 * multiplier
            boosts[ElementType.PARAGRAPH] = 1.1 * multiplier
            preferred.extend([ElementType.LIST, ElementType.CODE_BLOCK])
        elif fmt_val == OutputFormat.COMPARISON.value:
            boosts[ElementType.TABLE] = 1.5 * multiplier
            boosts[ElementType.LIST] = 1.3 * multiplier
            boosts[ElementType.PARAGRAPH] = 1.1 * multiplier
            preferred.extend([ElementType.TABLE, ElementType.LIST])
        elif fmt_val == OutputFormat.JSON.value:
            boosts[ElementType.TABLE] = 1.3 * multiplier
            boosts[ElementType.LIST] = 1.3 * multiplier
            boosts[ElementType.CODE_BLOCK] = 1.2 * multiplier
            preferred.extend([ElementType.TABLE, ElementType.LIST])
        elif fmt_val == OutputFormat.SUMMARY.value:
            boosts[ElementType.PARAGRAPH] = 1.3 * multiplier
            boosts[ElementType.HEADER] = 1.2 * multiplier
            preferred.extend([ElementType.PARAGRAPH, ElementType.HEADER])
        else:
            boosts[ElementType.PARAGRAPH] = 1.0

        return RetrievalBoostResult(
            element_type_boosts=boosts,
            metadata_filters=meta_filters,
            preferred_types=preferred
        )

    def get_confidence_multiplier(self, confidence: DetectionConfidence) -> float:
        c_val = confidence.value if isinstance(confidence, DetectionConfidence) else confidence
        if c_val == DetectionConfidence.HIGH.value:
            return self.config.highConfidenceMultiplier
        elif c_val == DetectionConfidence.MEDIUM.value:
            return self.config.mediumConfidenceMultiplier
        else:
            return self.config.lowConfidenceMultiplier

    def apply_boosts(self, results: List[dict], boost_result: RetrievalBoostResult) -> List[dict]:
        boosted = []
        for item in results:
            sim = item.get("similarity", 0.0)
            meta = item.get("metadata") or {}
            el_type_str = meta.get("elementType")
            
            el_type = None
            if el_type_str:
                for et in ElementType:
                    if et.value == el_type_str:
                        el_type = et
                        break

            if el_type and el_type in boost_result.elementTypeBoosts:
                boost = boost_result.elementTypeBoosts[el_type]
                sim *= boost

            if el_type and el_type in boost_result.preferredTypes:
                sim *= 1.1

            boosted.append({
                **item,
                "similarity": min(sim, 1.0),
                "metadata": {
                    **meta,
                    "formatBoosted": True,
                    "originalSimilarity": item.get("similarity", 0.0)
                }
            })
        return boosted

    def sort_by_boosted_similarity(self, results: List[dict]) -> List[dict]:
        return sorted(results, key=lambda x: x.get("similarity", 0.0), reverse=True)
