import re
import time
from typing import List, Dict, Any, Tuple, Optional

from app.rag.structure.types import StructuredChunk, ElementType
from app.rag.structure.element_detector import ElementDetector

class EnrichmentConfig:
    def __init__(
        self,
        analyzeSemantics: bool = True,
        extractKeywords: bool = True,
        detectEntities: bool = True,
        computeReadability: bool = True
    ):
        self.analyzeSemantics = analyzeSemantics
        self.extractKeywords = extractKeywords
        self.detectEntities = detectEntities
        self.computeReadability = computeReadability

    def to_dict(self) -> dict:
        return self.__dict__

class MetadataEnricher:
    def __init__(self, config: dict = None):
        cfg = config or {}
        self.config = EnrichmentConfig(
            analyzeSemantics=cfg.get("analyzeSemantics", True),
            extractKeywords=cfg.get("extractKeywords", True),
            detectEntities=cfg.get("detectEntities", True),
            computeReadability=cfg.get("computeReadability", True)
        )

    async def enrich_chunks(self, chunks: List[StructuredChunk]) -> List[StructuredChunk]:
        enriched = []
        for chunk in chunks:
            enriched.append(await self.enrich_chunk(chunk))
        return enriched

    async def enrich_chunk(self, chunk: StructuredChunk) -> StructuredChunk:
        enriched_metadata = {**chunk.metadata}

        if self.config.extractKeywords:
            keywords, key_phrases = self.extract_keywords_and_phrases(chunk.content)
            enriched_metadata["keywords"] = keywords
            enriched_metadata["keyPhrases"] = key_phrases

        if self.config.detectEntities:
            enriched_metadata["entities"] = self.detect_entities(chunk.content)

        if self.config.computeReadability:
            readability = self.compute_readability(chunk.content)
            enriched_metadata.update(readability)

        if self.config.analyzeSemantics:
            semantics = self.analyze_semantics(chunk.content, chunk.type)
            enriched_metadata.update(semantics)

        enriched_metadata["searchBoost"] = self.compute_search_boost(chunk, enriched_metadata)

        return StructuredChunk(
            id=chunk.id,
            content=chunk.content,
            type=chunk.type,
            metadata=enriched_metadata,
            embedding=chunk.embedding
        )

    def extract_keywords_and_phrases(self, content: str) -> Tuple[List[str], List[str]]:
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'this',
            'that', 'these', 'those', 'it', 'its', 'they', 'them', 'their',
        }

        clean_text = re.sub(r"[^\w\s]", " ", content.lower())
        words = [w for w in clean_text.split() if len(w) > 2 and w not in stop_words]

        freqs = {}
        for w in words:
            freqs[w] = freqs.get(w, 0) + 1

        sorted_kws = sorted(freqs.items(), key=lambda item: item[1], reverse=True)
        keywords = [item[0] for item in sorted_kws[:10]]

        key_phrases = self.extract_phrases(content)
        return keywords, key_phrases

    def extract_phrases(self, content: str) -> List[str]:
        phrases = []
        patterns = [
            r"(?:the\s+)?([\w]+\s+[\w]+(?:\s+[\w]+)?)\s+(?:is|are|was|were)\b",
            r"(?:how\s+to\s+)([\w]+(?:\s+[\w]+)*)",
            r"([\w]+\s+[\w]+)\s+(?:method|function|process|system|algorithm)"
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for m in matches:
                if isinstance(m, tuple):
                    m = m[0]
                phrase = m.strip().lower()
                if phrase and len(phrase) > 3 and phrase not in phrases:
                    phrases.append(phrase)

        return phrases[:5]

    def detect_entities(self, content: str) -> dict:
        entities = {}

        numbers = re.findall(r"\b\d+(?:[.,]\d+)*(?:\s*(?:%|percent|dollars?|USD|EUR))?", content)
        if numbers:
            entities["numbers"] = list(dict.fromkeys(numbers))[:10]

        potential_names = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", content)
        non_names = {
            'The', 'This', 'That', 'These', 'Those', 'What', 'Where', 'When', 'Why', 'How',
            'Section', 'Chapter', 'Table', 'Figure', 'Page', 'Row', 'Column', 'Sample',
            'Key', 'Points', 'List', 'Document', 'Data', 'Information', 'Unstructured',
            'Columns', 'Remarks', 'Name', 'Department', 'Working', 'Preparing', 'Managing', 'Handling'
        }
        names = [n for n in potential_names if n not in non_names and len(n) >= 2]
        if names:
            entities["names"] = list(dict.fromkeys(names))[:20]

        depts = re.findall(r"\b(Engineering|Design|HR|Finance|Marketing|Sales|IT|Legal|Operations|R&D|Research|Development|Support|Customer\s+Service)\b", content, re.IGNORECASE)
        if depts:
            entities["departments"] = list(dict.fromkeys([d.strip() for d in depts]))

        date_patterns = [
            r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4}\b",
            r"\b\d{4}[/-]\d{2}[/-]\d{2}\b"
        ]
        dates = []
        for pat in date_patterns:
            dates.extend(re.findall(pat, content, re.IGNORECASE))
        if dates:
            entities["dates"] = list(dict.fromkeys(dates))

        percentages = re.findall(r"\b\d+(?:\.\d+)?%", content)
        if percentages:
            entities["percentages"] = list(dict.fromkeys(percentages))

        currencies = re.findall(r"[$€£¥]\s*\d+(?:[.,]\d+)*|\b\d+(?:[.,]\d+)*\s*(?:USD|EUR|GBP)", content, re.IGNORECASE)
        if currencies:
            entities["currencies"] = list(dict.fromkeys(currencies))

        emails = re.findall(r"\b[\w.-]+@[\w.-]+\.\w{2,}\b", content)
        if emails:
            entities["emails"] = list(dict.fromkeys(emails))

        urls = re.findall(r"https?://[^\s]+", content)
        if urls:
            entities["urls"] = list(dict.fromkeys(urls))

        return entities

    def compute_readability(self, content: str) -> dict:
        words = [w for w in content.split() if len(w) > 0]
        sentences = [s for s in re.split(r"[.!?]+", content) if s.strip()]

        word_count = len(words)
        sentence_count = len(sentences)
        avg_words = word_count / sentence_count if sentence_count > 0 else word_count

        unique_words = {w.lower() for w in words}
        info_density = len(unique_words) / word_count if word_count > 0 else 0

        return {
            "wordCount": word_count,
            "sentenceCount": sentence_count,
            "avgWordsPerSentence": round(avg_words, 1),
            "informationDensity": round(info_density, 2)
        }

    def analyze_semantics(self, content: str, element_type: ElementType) -> dict:
        lower = content.lower()

        has_definitions = bool(re.search(r"(?:is defined as|refers to|means|is the|:=)", lower))
        has_examples = bool(re.search(r"(?:for example|e\.g\.|such as|like|instance|consider)", lower))
        has_instructions = bool(re.search(r"(?:step \d|first|then|next|finally|how to|guide|tutorial)", lower))

        el_val = element_type.value if isinstance(element_type, ElementType) else element_type
        
        category = "conceptual"
        if el_val == ElementType.TABLE.value:
            category = "reference"
        elif has_instructions:
            category = "procedural"
        elif has_definitions or bool(re.search(r"(?:what is|definition|concept)", lower)):
            category = "conceptual"
        elif ElementDetector.contains_numeric_data(content):
            category = "factual"

        topic_hints = self.extract_topic_hints(content)

        return {
            "hasDefinitions": has_definitions,
            "hasExamples": has_examples,
            "hasInstructions": has_instructions,
            "contentCategory": category,
            "topicHints": topic_hints
        }

    def extract_topic_hints(self, content: str) -> List[str]:
        hints = []
        topic_patterns = [
            r"(?:topic|subject|about|regarding|concerning)\s*:?\s*([\w\s]+)",
            r"(?:chapter|section|module)\s+\d*:?\s*([\w\s]+)"
        ]

        for pattern in topic_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for m in matches:
                topic = m.group(1).strip()
                if topic and 2 < len(topic) < 50:
                    hints.append(topic.lower())

        return list(dict.fromkeys(hints))[:3]

    def compute_search_boost(self, chunk: StructuredChunk, metadata: dict) -> float:
        boost = 1.0
        el_val = chunk.type.value if isinstance(chunk.type, ElementType) else chunk.type

        if el_val == ElementType.TABLE.value:
            boost *= 1.3
        elif el_val == ElementType.HEADER.value:
            boost *= 1.2
        elif el_val == ElementType.LIST.value:
            boost *= 1.1
        elif el_val == ElementType.CODE_BLOCK.value:
            boost *= 1.15

        if metadata.get("hasDefinitions"):
            boost *= 1.15
        if metadata.get("hasExamples"):
            boost *= 1.1
        if metadata.get("entities", {}).get("numbers"):
            boost *= 1.05

        density = metadata.get("informationDensity")
        if density and density > 0.5:
            boost *= 1.05

        word_cnt = metadata.get("wordCount")
        if word_cnt and word_cnt < 20:
            boost *= 0.9

        return round(boost, 2)
