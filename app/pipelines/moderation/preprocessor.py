import re
from typing import Dict

class TextPreprocessor:
    
    @staticmethod
    def clean_text(text: str) -> str:
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        return text
    
    @staticmethod
    def extract_metadata(title: str, description: str) -> Dict:
        combined = f"{title} {description}"
        
        word_count = len(combined.split())
        char_count = len(combined)
        
        uppercase_ratio = sum(1 for c in combined if c.isupper()) / max(len(combined), 1)
        
        has_urls = bool(re.search(r'http[s]?://', combined))
        
        return {
            "word_count": word_count,
            "char_count": char_count,
            "uppercase_ratio": uppercase_ratio,
            "has_urls": has_urls
        }
    
    @classmethod
    def preprocess(cls, title: str, description: str) -> Dict:
        clean_title = cls.clean_text(title)
        clean_description = cls.clean_text(description)
        
        metadata = cls.extract_metadata(clean_title, clean_description)
        
        return {
            "stage": "PREPROCESSING",
            "clean_title": clean_title,
            "clean_description": clean_description,
            "metadata": metadata
        }