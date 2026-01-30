from typing import Dict, List
import re

class ModerationRules:
    
    BANNED_WORDS = [
        "spam", "fake", "scam", "clickbait",
        "http://bit.ly", "http://tinyurl.com"
    ]
    
    PROFANITY = [
        "fuck", "shit", "asshole", "bastard"
    ]
    
    @staticmethod
    def check_spam(text: str) -> Dict:
        text_lower = text.lower()
        
        spam_indicators = 0
        flags = []
        
        if len(text) < 20:
            spam_indicators += 0.3
            flags.append("TOO_SHORT")
        
        if text.isupper() and len(text) > 50:
            spam_indicators += 0.4
            flags.append("ALL_CAPS")
        
        repeated_chars = re.findall(r'(.)\1{4,}', text)
        if repeated_chars:
            spam_indicators += 0.3
            flags.append("REPEATED_CHARS")
        
        for word in ModerationRules.BANNED_WORDS:
            if word in text_lower:
                spam_indicators += 0.5
                flags.append(f"BANNED_WORD_{word.upper()}")
        
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, text)
        if len(urls) > 2:
            spam_indicators += 0.4
            flags.append("EXCESSIVE_URLS")
        
        score = min(spam_indicators, 1.0)
        
        return {
            "score": score,
            "flags": flags,
            "decision": "REJECT" if score > 0.7 else "PASS"
        }
    
    @staticmethod
    def check_profanity(text: str) -> Dict:
        text_lower = text.lower()
        
        profanity_count = 0
        found_words = []
        
        for word in ModerationRules.PROFANITY:
            if word in text_lower:
                profanity_count += 1
                found_words.append(word)
        
        score = min(profanity_count * 0.3, 1.0)
        
        return {
            "score": score,
            "flags": found_words,
            "decision": "ESCALATE" if score > 0.5 else "PASS"
        }
    
    @staticmethod
    def check_phone_numbers(text: str) -> Dict:
        phone_pattern = r'\b\d{10,}\b'
        phones = re.findall(phone_pattern, text)
        
        if phones:
            return {
                "score": 1.0,
                "flags": ["PHONE_NUMBER"],
                "decision": "REJECT"
            }
        
        return {
            "score": 0.0,
            "flags": [],
            "decision": "PASS"
        }
    
    @staticmethod
    def check_duplicate_content(text: str) -> Dict:
        unique_words = len(set(text.split()))
        total_words = len(text.split())
        
        if total_words == 0:
            return {"score": 1.0, "flags": ["EMPTY"], "decision": "REJECT"}
        
        uniqueness_ratio = unique_words / total_words
        
        if uniqueness_ratio < 0.3:
            return {
                "score": 0.8,
                "flags": ["LOW_UNIQUENESS"],
                "decision": "ESCALATE"
            }
        
        return {"score": 0.0, "flags": [], "decision": "PASS"}
    
    @classmethod
    def run_all_checks(cls, title: str, description: str) -> Dict:
        combined_text = f"{title} {description}"
        
        spam_result = cls.check_spam(combined_text)
        profanity_result = cls.check_profanity(combined_text)
        phone_result = cls.check_phone_numbers(combined_text)
        duplicate_result = cls.check_duplicate_content(combined_text)
        
        all_flags = []
        all_flags.extend(spam_result["flags"])
        all_flags.extend(profanity_result["flags"])
        all_flags.extend(phone_result["flags"])
        all_flags.extend(duplicate_result["flags"])
        
        max_score = max(
            spam_result["score"],
            profanity_result["score"],
            phone_result["score"],
            duplicate_result["score"]
        )
        
        if any(r["decision"] == "REJECT" for r in [spam_result, phone_result, duplicate_result]):
            final_decision = "REJECT"
        elif any(r["decision"] == "ESCALATE" for r in [spam_result, profanity_result, duplicate_result]):
            final_decision = "ESCALATE"
        else:
            final_decision = "APPROVE"
        
        return {
            "stage": "RULES",
            "score": max_score,
            "confidence": 1.0,
            "flags": all_flags,
            "decision": final_decision,
            "details": {
                "spam": spam_result,
                "profanity": profanity_result,
                "phone": phone_result,
                "duplicate": duplicate_result
            }
        }