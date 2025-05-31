import asyncio
from openai_service import OpenAIService

async def test_openai_service():
    # Initialize the service
    service = OpenAIService()
    
    # Test article JSON
    test_article = {
        "title": "Avances en Inteligencia Artificial Transforman la Industria Tecnológica",
        "content": """
        La inteligencia artificial está revolucionando la forma en que las empresas operan y compiten en el mercado global. 
        Recientes desarrollos en aprendizaje automático han llevado a avances significativos en procesamiento de lenguaje natural, 
        visión por computadora y robótica. Empresas como OpenAI, Google y Microsoft están a la vanguardia de estas innovaciones, 
        desarrollando sistemas de IA cada vez más sofisticados que pueden entender y generar lenguaje humano, reconocer imágenes 
        y tomar decisiones complejas.

        Según expertos del sector, estos avances están impulsando una nueva ola de transformación digital, con aplicaciones 
        que van desde asistentes virtuales hasta sistemas de diagnóstico médico. Sin embargo, también plantean importantes 
        cuestiones éticas y de privacidad que requieren atención inmediata.
        """,
        "author": "María González",
        "published_at": "2024-03-20T10:30:00Z",
        "source": "TechNews"
    }
    
    try:
        # Test embeddings
        print("Testing embeddings...")
        # Combine all article fields into a single string without keys
        article_text = f"{test_article['title']} {test_article['author']} {test_article['published_at']} {test_article['source']} {test_article['content']}"
        embeddings = await service.get_embeddings([article_text])
        print(f"Generated embedding with {len(embeddings[0])} dimensions")
        
        # Test text analysis
        print("\nTesting text analysis...")
        analysis = await service.analyze_text(test_article)
        print("Analysis results:", analysis)
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_openai_service()) 