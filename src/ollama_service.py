# src/ollama_service.py
import httpx
from typing import Optional
from src.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from src.master_prompt import MASTER_PROMPT

BASE_TIMEOUT = 120.0


class OllamaService:
    """Servicio para interactuar con Ollama"""
    
    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.model = OLLAMA_MODEL
        self.client = httpx.AsyncClient(timeout=BASE_TIMEOUT)
    

    async def chat(self, message: str, context: Optional[str] = None) -> str:
        """
        Enviar un mensaje al modelo de Ollama y obtener una respuesta
        
        Args:
            message: Mensaje del usuario
            context: Contexto adicional (por ejemplo, información sobre citas existentes)
        
        Returns:
            Respuesta del modelo
        """
        # Construir el prompt con contexto del sistema
        system_prompt = MASTER_PROMPT
        
        if context:
            system_prompt += f"\n\nContexto adicional: {context}"
        
        prompt = f"{system_prompt}\n\nUsuario: {message}\n\nAsistente:"
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "Lo siento, no pude procesar tu solicitud.")
        except httpx.HTTPError as e:
            return f"Error al conectar con el servicio de Ollama: {str(e)}"
        except Exception as e:
            return f"Error inesperado: {str(e)}"
    
    async def close(self):
        """Cerrar el cliente HTTP"""
        await self.client.aclose()


# Instancia global del servicio
ollama_service = OllamaService()

