import re
from typing import List, Dict, Any, Optional

from app.rag.format.types import OutputFormat, DetectionConfidence

class FormatPattern:
    def __init__(self, format: OutputFormat, patterns: List[str], keywords: List[str], confidence: DetectionConfidence):
        self.format = format
        self.patterns = patterns
        self.keywords = keywords
        self.confidence = confidence

class FormatIntent:
    def __init__(
        self,
        format: OutputFormat,
        confidence: DetectionConfidence,
        signals: List[str],
        originalQuery: str,
        extractedSubject: str = None
    ):
        self.format = format
        self.confidence = confidence
        self.signals = signals
        self.originalQuery = originalQuery
        self.extractedSubject = extractedSubject or originalQuery

    def to_dict(self) -> dict:
        return {
            "format": self.format.value if isinstance(self.format, OutputFormat) else self.format,
            "confidence": self.confidence.value if isinstance(self.confidence, DetectionConfidence) else self.confidence,
            "signals": self.signals,
            "originalQuery": self.originalQuery,
            "extractedSubject": self.extractedSubject
        }

class FormatIntentDetector:
    EXPLICIT_PATTERNS = [
        FormatPattern(
            format=OutputFormat.TABLE,
            patterns=[
                r"\b(in\s+)?tabular\s+format\b",
                r"\b(as\s+)?a?\s*table\b",
                r"\bshow\s+(me\s+)?.*\s+in\s+table\b",
                r"\bformat\s+(as|in)\s+table\b",
                r"\btabulate\b",
            ],
            keywords=['tabular', 'table format', 'in a table'],
            confidence=DetectionConfidence.HIGH
        ),
        FormatPattern(
            format=OutputFormat.LIST,
            patterns=[
                r"\b(as\s+)?a?\s*list\b",
                r"\bbullet\s*points?\b",
                r"\bnumbered\s+list\b",
                r"\blist\s+(out|all|the)\b",
                r"\bformat\s+(as|in)\s+list\b",
            ],
            keywords=['bullet points', 'list format', 'bulleted'],
            confidence=DetectionConfidence.HIGH
        ),
        FormatPattern(
            format=OutputFormat.JSON,
            patterns=[
                r"\b(in\s+)?json\s+format\b",
                r"\bas\s+json\b",
                r"\breturn\s+json\b",
                r"\bjson\s+output\b",
                r"\bformat\s+(as|in)\s+json\b",
            ],
            keywords=['json', 'json format'],
            confidence=DetectionConfidence.HIGH
        ),
        FormatPattern(
            format=OutputFormat.SUMMARY,
            patterns=[
                r"\bsummarize\b",
                r"\bbrief\s+summary\b",
                r"\bshort\s+summary\b",
                r"\bgive\s+(me\s+)?a?\s*summary\b",
                r"\btl;?dr\b",
                r"\bin\s+brief\b",
            ],
            keywords=['summarize', 'summary', 'tldr', 'brief'],
            confidence=DetectionConfidence.HIGH
        ),
        FormatPattern(
            format=OutputFormat.STEPS,
            patterns=[
                r"\bstep[\s-]by[\s-]step\b",
                r"\b(show\s+)?(the\s+)?steps\s+(to|for)\b",
                r"\bhow\s+to\s+.+\s+step\s+by\s+step\b",
                r"\bprocedure\s+for\b",
                r"\bwalkthrough\b",
            ],
            keywords=['step by step', 'steps to', 'procedure', 'walkthrough'],
            confidence=DetectionConfidence.HIGH
        ),
        FormatPattern(
            format=OutputFormat.COMPARISON,
            patterns=[
                r"\bcompare\s+(and\s+contrast)?\b",
                r"\bcomparison\s+(of|between)\b",
                r"\bdifferences?\s+(between|of)\b",
                r"\bvs\.?\s+\b",
                r"\bversus\b",
                r"\bside[\s-]by[\s-]side\b",
            ],
            keywords=['compare', 'comparison', 'versus', 'differences'],
            confidence=DetectionConfidence.HIGH
        )
    ]

    IMPLICIT_PATTERNS = [
        FormatPattern(
            format=OutputFormat.TABLE,
            patterns=[
                r"\bwhat\s+are\s+the\s+(statistics|numbers|data)\b",
                r"\bshow\s+(me\s+)?(the\s+)?data\b",
                r"\bbreakdown\s+of\b",
                r"\bmetrics\s+for\b",
            ],
            keywords=['statistics', 'breakdown', 'metrics', 'data for'],
            confidence=DetectionConfidence.MEDIUM
        ),
        FormatPattern(
            format=OutputFormat.LIST,
            patterns=[
                r"\bwhat\s+are\s+(all\s+)?(the\s+)?\b",
                r"\bname\s+(all\s+)?(the\s+)?\b",
                r"\benumerate\b",
                r"\btypes\s+of\b",
                r"\bkinds\s+of\b",
                r"\bfeatures\s+of\b",
                r"\bbenefits\s+of\b",
            ],
            keywords=['types of', 'kinds of', 'features', 'benefits', 'enumerate'],
            confidence=DetectionConfidence.MEDIUM
        ),
        FormatPattern(
            format=OutputFormat.STEPS,
            patterns=[
                r"\bhow\s+(do|can|to|should)\s+i?\b",
                r"\bprocess\s+(of|for)\b",
                r"\bguide\s+(to|for|on)\b",
                r"\bhow\s+does\s+.*\s+work\b",
            ],
            keywords=['how do i', 'process for', 'guide to'],
            confidence=DetectionConfidence.MEDIUM
        ),
        FormatPattern(
            format=OutputFormat.SUMMARY,
            patterns=[
                r"\bexplain\s+(briefly|quickly)\b",
                r"\bquick\s+overview\b",
                r"\bmain\s+points?\b",
                r"\bkey\s+(points?|takeaways?)\b",
            ],
            keywords=['briefly', 'overview', 'main points', 'key takeaways'],
            confidence=DetectionConfidence.MEDIUM
        )
    ]

    def detect(self, query: str) -> FormatIntent:
        normalized = query.lower().strip()
        signals = []

        # High confidence patterns
        for p_def in self.EXPLICIT_PATTERNS:
            match = self.match_patterns(normalized, p_def)
            if match:
                signals.extend(match)
                return FormatIntent(
                    format=p_def.format,
                    confidence=DetectionConfidence.HIGH,
                    signals=signals,
                    originalQuery=query,
                    extractedSubject=self.extract_subject(query)
                )

        # Medium confidence patterns
        for p_def in self.IMPLICIT_PATTERNS:
            match = self.match_patterns(normalized, p_def)
            if match:
                signals.extend(match)
                return FormatIntent(
                    format=p_def.format,
                    confidence=DetectionConfidence.MEDIUM,
                    signals=signals,
                    originalQuery=query,
                    extractedSubject=self.extract_subject(query)
                )

        # Default
        return FormatIntent(
            format=OutputFormat.PARAGRAPH,
            confidence=DetectionConfidence.LOW,
            signals=['default'],
            originalQuery=query,
            extractedSubject=query
        )

    def match_patterns(self, query: str, p_def: FormatPattern) -> List[str]:
        signals = []
        for pat in p_def.patterns:
            m = re.search(pat, query, re.IGNORECASE)
            if m:
                signals.append(f"pattern: {m.group(0)}")

        for kw in p_def.keywords:
            if kw.lower() in query:
                signals.append(f"keyword: {kw}")

        return signals

    def extract_subject(self, query: str) -> str:
        subject = query
        format_phrases = [
            r"\b(in\s+)?tabular\s+format\b",
            r"\b(as\s+)?a?\s*table\b",
            r"\b(as\s+)?a?\s*list\b",
            r"\bbullet\s*points?\b",
            r"\b(in\s+)?json\s+format\b",
            r"\bstep[\s-]by[\s-]step\b",
            r"\bsummarize\b",
            r"\bcompare\s+(and\s+contrast)?\b",
            r"\bshow\s+me\b",
            r"\bgive\s+me\b",
            r"\bprovide\b"
        ]

        for pat in format_phrases:
            subject = re.sub(pat, "", subject, flags=re.IGNORECASE)

        subject = re.sub(r"\s+", " ", subject).strip()
        return subject or query

    def analyze_signals(self, query: str) -> Dict[str, List[str]]:
        analysis = {f.value: [] for f in OutputFormat}
        normalized = query.lower().strip()

        all_patterns = self.EXPLICIT_PATTERNS + self.IMPLICIT_PATTERNS
        for p_def in all_patterns:
            matches = self.match_patterns(normalized, p_def)
            if matches:
                analysis[p_def.format.value].extend(matches)
        return analysis
