import io
from json.encoder import ESCAPE_DCT
from re import S
from celery.result import ResultSet
import requests
from PIL import Image
import torch
from torch.compiler import reset
from torchvision import transforms
from nudenet import NudeDetector
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ImageAnalyzer:
    
    def __init__(self):
        # Initialize NSFW detector
        try:
            self.nsfw_detector = NudeDetector()
            logger.info("NudeNet detector initialized")
        except Exception as e:
            logger.error(f"Failed to initialize NudeNet: {e}")
            self.nsfw_detector = None
    
    def download_image(self, url: str) -> Optional[Image.Image]:
        #Download Image from URL
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return Image.open(io.BytesIO(response.content)).convert('RGB')
        
        except Exception as e:
            logger.error(f"Failed to Download {url}: {e}")
            return None
        
    
    def check_nsfw(self, image_url: str) -> Dict:
        """
        Check if the image contains NSFW.
        ReturnS {
            "isNsfw: bool,
            "confidence: float,
            detections: Lists
        }
        """

        if not self.nsfw_detector:
            return {
                "is_nsfw": False,
                "confidence": 0.0,
                "detections": [],
                "error": "Detector not initialised"
            }
        
        try:
            detections = self.nsfw_detector.detect(image_url)

            NSFW_CLASSES = [
                'BUTTOCKS_EXPOSED', 
                'FEMALE_BREAST_EXPOSED', 
                'FEMALE_GENITALIA_EXPOSED',
                'MALE_GENITALIA_EXPOSED',
                'ANUS_EXPOSED'
            ]

            max_nsfw_score = 0.0
            nsfw_found = []

            for detection in detections:
                if detection['class'] in NSFW_CLASSES:
                    score = detection['score']
                    if score > max_nsfw_score:
                        max_nsfw_score = score
                    nsfw_found.append({
                        "type": detection['class'],
                        "confidence": score
                    })

            is_nsfw = max_nsfw_score > 0.6 ## threshold

            return {
                "is_nsfw": is_nsfw,
                "confidence": max_nsfw_score,
                "detections": nsfw_found
            }
        
        except Exception as e:
            logger.error(f"NSFW check failed for {image_url}: {e}")
            return {
                "is_nsfw": False,
                "confidence": 0.0,
                "detections": [],
                "error": str(e)
            }
        
    def analyse_batch(self, image_urls: List[str]) -> Dict:
        """
        Analyses multiple images
        Return aggregate results
        """

        if not image_urls:
            return {
                "has_nsfw": False,
                "max_nsfw_score": 0.0,
                "flagged_images": []
            }
        
        results = []
        for url in image_urls:
            result = self.check_nsfw(url)
            results.append({
                "url": url,
                **result
            })

        flagged = [r for r in results if r.get("is_nsfw", False)]
        max_score = max([r.get("confidence", 0.0) for r in results])

        return {
            "has_nsfw": len(flagged) > 0,
            "max_nsfw_score": max_score,
            "flagged_images": flagged,
            "total_images": len(image_urls),
            "results": results
        }
