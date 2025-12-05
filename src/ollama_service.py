# src/ollama_service.py
import httpx
from typing import Optional
from src.config import OLLAMA_BASE_URL, OLLAMA_MODEL


class OllamaService:
    """Servicio para interactuar con Ollama"""
    
    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.model = OLLAMA_MODEL
        self.client = httpx.AsyncClient(timeout=60.0)
    
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
        system_prompt = """Eres un asistente virtual para agendar citas. 
Tu tarea es ayudar a los usuarios a programar citas de manera amigable y profesional.
Cuando un usuario quiera agendar una cita, debes extraer:
- Nombre de la persona
- Fecha y hora deseada
- Descripción o motivo de la cita
- Información de contacto (email o teléfono) si está disponible

Responde de manera clara y concisa. Si necesitas más información, haz preguntas específicas."""
        
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

