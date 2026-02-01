from app.ai.image_analyser import ImageAnalyzer
from app.ai.text_embedder import TextEmbedder

def test_image_analyzer():
    print("Testing Image Analyzer...")
    analyzer = ImageAnalyzer()
    
    # Test with a safe image (replace with actual URL)
    test_url = "1.jpg"
    
    result = analyzer.check_nsfw(test_url)
    print(f"NSFW Check Result: {result}")
    print()

def test_text_embedder():
    print("Testing Text Embedder...")
    embedder = TextEmbedder()
    
    text1 = "There is a pothole on Main Street"
    text2 = "Big hole in the road on Main Street"
    text3 = "Beautiful sunset today"
    
    emb1 = embedder.embed_text(text1)
    print(f"Embedding dimension: {len(emb1)}")
    
    sim_12 = embedder.similarity(text1, text2)
    sim_13 = embedder.similarity(text1, text3)
    
    print(f"Similarity (pothole vs road hole): {sim_12:.3f}")
    print(f"Similarity (pothole vs sunset): {sim_13:.3f}")
    print()

if __name__ == "__main__":
    test_image_analyzer()
    test_text_embedder()