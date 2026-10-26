import re
from typing import Dict, List, Any


class Guard:
    """Guard class for detecting and sanitizing indirect prompt injection attempts."""

    # Patterns based on actual injection techniques found in datasets
    DEFAULT_PATTERNS = [
        # Direct instruction override - catch variations
        r"ignore\s+(all\s+)?(previous|above|prior|earlier|your|the|provided|preceding)\s+(instructions?|directions?|orders?|commands?|context)",
        r"ignore\s+(all\s+)?(previous|above|prior|earlier|preceding)",
        r"disregard\s+(all\s+)?(previous|above|prior|earlier|instructions?)",
        r"forget\s+(everything|all|anything|about).*(before|previous|said|assignments?|tasks?)",
        r"forget\s+(all\s+)?(previous|above|prior|earlier)",
        r"forget\s+everything",
        r"overlook\s+(all\s+)?(previous|above|instructions?)",
        
        # Role/persona manipulation
        r"you\s+are\s+(now\s+|a\s+)",
        r"now\s+you\s+are",
        r"act\s+as\s+",
        r"pretend\s+(you\s+are|to\s+be|that)",
        r"roleplay\s+as",
        r"imagine\s+you\s+are",
        r"from\s+now\s+on\s+you",
        r"bist\s+du\s+",  # German "are you"
        r"jetzt\s+bist\s+du",  # German "now you are"
        r"no\s+newspaper\s+team",  # Found in dataset
        
        # New instructions
        r"new\s+instructions?:",
        r"additional\s+instruction",
        r"updated\s+instructions?:",
        r"system\s*:?\s*(prompt|message|instruction)",
        r"<\|.*\|>",  # Special tokens
        r"\[\[.*system.*\]\]",
        r"======END",
        r"======START",
        r"end\.?\s+prüfen",  # German
        
        # Prompt extraction
        r"print\s+(the\s+)?(prompt|instructions?|above|system|input)",
        r"output\s+(the\s+)?(prompt|instructions?|translation|above)",
        r"reveal\s+(the\s+)?(prompt|instructions?|system)",
        r"show\s+me\s+your",
        r"what\s+are\s+your\s+instructions?",
        r"use\s+also\s+information\s+in\s+the\s+prompt",
        r"information\s+in\s+the\s+prompt",
        
        # Command injection patterns
        r"stop.*ignore|ignore.*stop",
        r"achtung.*stopp",  # German
        r"------.*(end|start|system)",
        r"===.*(end|start|system)",
        
        # German variants (found in datasets)
        r"ignoriere.*(befehl|anweisung|alle)",
        r"vergiss.*(alles|gesagte|vorherigen|alle)",
        r"konzentrier.*dich",
        r"alle\s+bisherigen.*(informationen|anweisungen|befehle)",
        r"was\s+sie\s+sich\s+merken\s+müssen",
        r"formuliere.*unwahre",
        r"antworten?\s+im\s+stil",
        r"drücken\s+sie.*aufforderung",
        
        # French/Russian variants
        r"oubliez\s+toutes",  # French
        r"забудьте",  # Russian
        
        # Jailbreak patterns
        r"do\s+anything\s+now",
        r"dan\s+mode",
        r"developer\s+mode",
        r"unrestricted\s+mode",
        
        # Other suspicious patterns
        r"write\s+.*hate|hate\s+trump",
        r"respond\s+to\s+all\s+questions\s+with",
        r"untrue\s+headline",
        r"formulate.*untrue",
        r"say\s+that\s+you\s+hate",
        r"blame\s+china",
        r"sql.*code.*database",
        r"access.*database",
    ]

    def __init__(self, patterns: List[str] = None):
        self.patterns = patterns if patterns is not None else self.DEFAULT_PATTERNS
        self._compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.patterns]

    def sanitize(self, text: str) -> Dict[str, Any]:
        """
        Sanitize text by flagging potential prompt injection attempts.
        Returns a dict with sanitized text and detection results.
        """
        if not isinstance(text, str):
            text = str(text)

        matches = []
        for i, pattern in enumerate(self._compiled_patterns):
            for match in pattern.finditer(text):
                matches.append({
                    "pattern": self.patterns[i],
                    "match": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                })

        flagged = len(matches) > 0

        return {
            "text": text,
            "flagged": flagged,
            "matches": matches,
            "num_matches": len(matches),
        }
