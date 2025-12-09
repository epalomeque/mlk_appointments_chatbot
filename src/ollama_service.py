# src/ollama_service.py
import httpx
import logging
import json
from datetime import datetime
from typing import Optional, List, Tuple, Any, Dict
from src.config import (
    OLLAMA_BASE_TIMEOUT,
    OLLAMA_BASE_URL,
    OLLAMA_ENDPOINT_CHAT,
    OLLAMA_ENDPOINT_GENERATE,
    OLLAMA_MODEL,
    OLLAMA_MAX_ROUND_FOR_TOOL_CALL
)
from src.master_prompt import MASTER_PROMPT
from src.ollama_tools import TOOLS
from src import tools as local_tools


logger = logging.getLogger(__name__)


class OllamaService:
    """Servicio para interactuar con Ollama"""
    
    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.model = OLLAMA_MODEL
        self.client = httpx.AsyncClient(timeout=OLLAMA_BASE_TIMEOUT)
        self.tools = TOOLS
        self.api_generate = OLLAMA_ENDPOINT_GENERATE
        # Endpoint de chat de Ollama (requiere mensajes y soporta tools)
        self.api_chat = OLLAMA_ENDPOINT_CHAT
    

    async def chat(
        self,
        message: str,
        context: Optional[str] = None,
        history: Optional[List[Tuple[str, str]]] = None,
    ) -> str:
        """
        Enviar un mensaje al modelo de Ollama y obtener una respuesta
        
        Args:
            message: Mensaje del usuario
            context: Contexto adicional (por ejemplo, información sobre citas existentes)
            history: Historial de la conversacion, si existe en la BdD
        
        Returns:
            Respuesta del modelo
            :param history:
        """
        # Construir mensajes (formato chat) con contexto del sistema
        system_prompt = MASTER_PROMPT
        if context:
            system_prompt += f"\n\nContexto adicional: {context}"

        messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]

        # Incluir historial previo (si existe) en formato chat
        if history:
            for u, b in history:
                if u:
                    messages.append({"role": "user", "content": u})
                if b:
                    messages.append({"role": "assistant", "content": b})

        # Mensaje actual del usuario
        messages.append({"role": "user", "content": message})

        try:
            # Realizar una o más rondas para manejar tool calls si aparecen
            for _ in range(OLLAMA_MAX_ROUND_FOR_TOOL_CALL):  # límite de seguridad de iteraciones
                response = await self.client.post(
                    f"{self.base_url}{self.api_chat}",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False,
                        "tools": self.tools,
                    },
                )
                response.raise_for_status()
                data: Dict[str, Any] = response.json()
                logger.info(f'----- data -> {data}')

                # Formatos posibles: {"message": {...}} o directamente llaves arriba
                msg = data.get("message", data)
                tool_calls = msg.get("tool_calls") or data.get("tool_calls")
                assistant_content = msg.get("content") or data.get("response")
                logger.info(f'\n\n----- msg -> {msg}\n\n----- tool_calls -> {tool_calls}'
                            f'\n\n----- assistant_content {assistant_content}')

                if tool_calls:
                    # Despachar cada tool call y agregar su resultado
                    for tc in tool_calls:
                        fn = None
                        args: Dict[str, Any] = {}
                        tool_call_id = tc.get("id") or tc.get("tool_call_id")

                        # Estructura tipo OpenAI-like
                        if isinstance(tc, dict):
                            func_obj = tc.get("function") or {}
                            name = func_obj.get("name") or tc.get("name")
                            raw_args = func_obj.get("arguments") or tc.get("arguments")
                            if isinstance(raw_args, str):
                                try:
                                    args = json.loads(raw_args) if raw_args else {}
                                except Exception:
                                    # Si no parsea, intentar como dict literal
                                    try:
                                        args = json.loads(raw_args.replace("'", '"'))
                                    except Exception:
                                        args = {}
                            elif isinstance(raw_args, dict):
                                args = raw_args
                            else:
                                args = {}
                            fn = self._resolve_tool(name)

                        result_payload: Dict[str, Any] = {
                            "ok": False,
                            "result": None,
                            "error": None,
                        }

                        if fn:
                            try:
                                coerced_args = self._coerce_args_for_function(fn.__name__, args)
                                result = fn(**coerced_args)
                                # Serializar resultado a JSON-friendly
                                result_payload["ok"] = True
                                try:
                                    json.dumps(result)  # comprobación rápida
                                    result_payload["result"] = result
                                except TypeError:
                                    # Fallback de serialización simple
                                    if hasattr(result, "model_dump_json"):
                                        result_payload["result"] = json.loads(result.model_dump_json())
                                    else:
                                        result_payload["result"] = str(result)
                            except Exception as e:  # noqa: BLE001
                                logger.exception("Error ejecutando herramienta %s", fn.__name__)
                                result_payload["error"] = str(e)
                        else:
                            result_payload["error"] = "Tool no encontrada"

                        # Añadir mensaje de rol tool con el resultado
                        tool_msg: Dict[str, Any] = {
                            "role": "tool",
                            "content": json.dumps(result_payload, ensure_ascii=False),
                        }
                        if tool_call_id:
                            tool_msg["tool_call_id"] = tool_call_id
                        if fn:
                            tool_msg["name"] = fn.__name__
                        messages.append(tool_msg)

                    # Continuar el bucle para dar al modelo el contexto de tool results
                    continue

                # Si no hay tool calls, devolver el contenido del asistente
                if assistant_content:
                    return assistant_content

                # Fallback a respuesta tipo generate
                if "response" in data:
                    return data.get("response", "Lo siento, no pude procesar tu solicitud.")

                # Si no hay contenido, romper
                break

            # Si llegamos aquí, no se pudo obtener respuesta útil
            return "Lo siento, no pude procesar tu solicitud."
        except httpx.HTTPError as e:
            return f"Error al conectar con el servicio de Ollama: {str(e)}"
        except Exception as e:
            return f"Error inesperado: {str(e)}"


    async def close(self):
        """Cerrar el cliente HTTP"""
        await self.client.aclose()

    # -------------------------
    # Utilidades internas
    # -------------------------
    def _resolve_tool(self, name: Optional[str]):
        """Mapea el nombre de la herramienta a una función local en src.tools"""
        if not name:
            return None
        mapping = {
            "get_appointment_lists": local_tools.get_appointment_lists,
            "check_occupied_slots": local_tools.check_occupied_slots,
            "save_appointment": local_tools.save_appointment,
            "update_appointment": local_tools.update_appointment,
            "delete_appointment": local_tools.delete_appointment,
        }
        return mapping.get(name)

    def _coerce_args_for_function(self, fn_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Convierte strings ISO8601 a datetime y ajusta tipos según la función destino."""
        def parse_iso(dt_str: Optional[str]) -> Optional[datetime]:
            if not dt_str or not isinstance(dt_str, str):
                return None
            s = dt_str.strip()
            # Permitir sufijo 'Z'
            if s.endswith("Z"):
                s = s[:-1]
            try:
                return datetime.fromisoformat(s)
            except Exception:
                return None

        coerced = dict(args)
        if fn_name in ("get_appointment_lists",):
            coerced["start"] = parse_iso(args.get("start")) or args.get("start")
            coerced["end"] = parse_iso(args.get("end")) or args.get("end")
            # limit debe ser int
            if "limit" in coerced and isinstance(coerced["limit"], str):
                try:
                    coerced["limit"] = int(coerced["limit"])
                except ValueError:
                    pass
        elif fn_name in ("check_occupied_slots",):
            coerced["start"] = parse_iso(args.get("start")) or args.get("start")
            coerced["end"] = parse_iso(args.get("end")) or args.get("end")
        elif fn_name in ("save_appointment",):
            coerced["date"] = parse_iso(args.get("date")) or args.get("date")
        elif fn_name in ("update_appointment",):
            # id y date
            if "appointment_id" in coerced and isinstance(coerced["appointment_id"], str):
                try:
                    coerced["appointment_id"] = int(coerced["appointment_id"])
                except ValueError:
                    pass
            coerced["date"] = parse_iso(args.get("date")) or args.get("date")
        elif fn_name in ("delete_appointment",):
            if "appointment_id" in coerced and isinstance(coerced["appointment_id"], str):
                try:
                    coerced["appointment_id"] = int(coerced["appointment_id"])
                except ValueError:
                    pass
        return coerced


# Instancia global del servicio
ollama_service = OllamaService()

