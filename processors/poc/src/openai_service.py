from typing import List, Dict
import openai
from config import OPENAI_API_KEY

class OpenAIService:
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
        self.embedding_model = "text-embedding-3-small"  # Latest OpenAI embedding model
        self.embedding_dimensions = 1536  # Dimensions for text-embedding-3-small

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for a list of texts using OpenAI's embedding model.
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            List of embedding vectors
        """
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=texts
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            print(f"Error getting embeddings: {str(e)}")
            raise

    async def analyze_text(self, article_json: Dict) -> Dict:
        """
        Analyze text using OpenAI's GPT model to extract various insights.
        
        Args:
            article_json: Dictionary containing the article data to analyze
            
        Returns:
            Dictionary containing analysis results including:
            - summary: A concise summary of 3-5 sentences
            - category: News category (e.g. politics, science, sports, finance)
            - hashtags: 5 relevant hashtags
            - journalistic_quality: Evaluation of writing quality
        """
        try:
            # Prepare the prompt for analysis
            prompt = f"""
              Eres un agente experto en análisis de noticias. Analiza el siguiente artículo y responde en formato JSON con los siguientes campos:

              1. summary: Un resumen conciso de 3 a 5 frases.
              2. category: Una categoría de noticias (por ejemplo: política, ciencia, deportes, finanzas).
              3. hashtags: 5 hashtags relevantes que empiecen con "#", cortos y basados en el tema.
              4. journalistic_quality: Una breve evaluación (máx. 3 frases) sobre la claridad, tono y estructura del artículo.

              Este es el artículo:
              {article_json}

              Responde únicamente con el JSON.
              """

            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "Eres un asistente útil y experto en análisis de medios. Proporciona un análisis detallado y estructurado en formato JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" }
            )

            # Parse the response
            analysis = response.choices[0].message.content
            return analysis

        except Exception as e:
            print(f"Error analyzing text: {str(e)}")
            raise