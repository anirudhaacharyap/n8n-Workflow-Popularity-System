import re

class Normalizer:
    @staticmethod
    def normalize_workflow_name(name: str) -> str:
        """
        Normalize workflow name for fuzzy matching and deduplication.
        Example: "Google Sheets -> Slack" -> "google sheets slack"
        """
        if not name:
            return ""
        
        # Lowercase
        normalized = name.lower()
        
        # Remove special characters except spaces using regex
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # Replace multiple spaces with single space
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized.strip()

    @staticmethod
    def get_fuzzy_match_score(str1: str, str2: str) -> int:
        """
        Simple Jaccard similarity or token overlap for now.
        For production, use Levenshtein or RapidFuzz.
        Returns 0-100 score.
        """
        set1 = set(str1.split())
        set2 = set(str2.split())
        
        if not set1 or not set2:
            return 0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return int((intersection / union) * 100)
