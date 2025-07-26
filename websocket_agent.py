import asyncio
import json
import logging
import os
import websockets
from typing import Optional, Callable, Dict, Any
from dotenv import load_dotenv
from datetime_utils import get_conversation_metadata, format_current_context

load_dotenv()

class WebSocketConversationalAgent:
    """
    Agent conversationnel utilisant WebSocket API ElevenLabs
    """
    
    def __init__(
        self,
        agent_id: str,
        api_key: Optional[str] = None,
        on_message: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        self.agent_id = agent_id
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.websocket = None
        self.is_connected = False
        self.on_message = on_message or self._default_message_handler
        
        # Configuration du logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # URL WebSocket ElevenLabs
        self.ws_url = f"wss://api.elevenlabs.io/v1/convai/conversation?agent_id={self.agent_id}"
    
    def _default_message_handler(self, message: Dict[str, Any]) -> None:
        """Gestionnaire de messages par défaut"""
        message_type = message.get("type", "unknown")
        
        if message_type == "user_transcript":
            transcript = message.get("transcript", "")
            print(f"Utilisateur: {transcript}")
            
        elif message_type == "agent_response":
            response = message.get("response", "")
            print(f"Agent: {response}")
            
        elif message_type == "audio_response":
            self.logger.info("Réponse audio reçue")
            
        elif message_type == "conversation_initiation_metadata":
            self.logger.info("Métadonnées de conversation reçues")
            
        else:
            self.logger.info(f"Message reçu: {message_type}")
    
    async def connect(self) -> None:
        """Établit la connexion WebSocket"""
        try:
            # Ajout de l'authentification dans l'URL si nécessaire
            ws_url = self.ws_url
            if self.api_key:
                ws_url += f"&api_key={self.api_key}"
            
            self.logger.info(f"Connexion à {ws_url}")
            self.websocket = await websockets.connect(ws_url)
            self.is_connected = True
            self.logger.info("Connexion WebSocket établie")
            
        except Exception as e:
            self.logger.error(f"Erreur de connexion: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Ferme la connexion WebSocket"""
        if self.websocket and self.is_connected:
            await self.websocket.close()
            self.is_connected = False
            self.logger.info("Connexion WebSocket fermée")
    
    async def send_message(self, message: Dict[str, Any]) -> None:
        """Envoie un message via WebSocket"""
        if not self.is_connected or not self.websocket:
            self.logger.error("WebSocket non connecté")
            return
        
        try:
            await self.websocket.send(json.dumps(message))
            self.logger.debug(f"Message envoyé: {message.get('type', 'unknown')}")
        except Exception as e:
            self.logger.error(f"Erreur lors de l'envoi: {e}")
    
    async def send_conversation_initiation(self, user_data: Optional[Dict[str, Any]] = None) -> None:
        """Initie une conversation avec contexte temporel Paris"""
        # Récupération du contexte temporel actuel
        temporal_context = get_conversation_metadata()
        
        # Fusion avec les données utilisateur
        conversation_data = user_data or {}
        conversation_data.update({
            "temporal_context": temporal_context,
            "system_prompt_addition": format_current_context()
        })
        
        message = {
            "type": "conversation_initiation_client_data",
            "conversation_initiation_client_data": conversation_data
        }
        
        self.logger.info(f"Envoi du contexte temporel: {temporal_context['current_date']} {temporal_context['current_time']}")
        await self.send_message(message)
    
    async def send_user_message(self, text: str, include_temporal_context: bool = False) -> None:
        """Envoie un message texte utilisateur"""
        message_content = text
        
        # Ajouter contexte temporel si demandé
        if include_temporal_context:
            temporal_info = get_conversation_metadata()
            message_content = f"{format_current_context()}\n\nMESSAGE UTILISATEUR: {text}"
        
        message = {
            "type": "user_message",
            "message": message_content
        }
        await self.send_message(message)
    
    async def send_user_message_with_context(self, text: str) -> None:
        """Envoie un message utilisateur avec contexte temporel automatique"""
        await self.send_user_message(text, include_temporal_context=True)
    
    async def send_audio_chunk(self, audio_data: bytes) -> None:
        """Envoie un chunk audio utilisateur"""
        message = {
            "type": "user_audio_chunk",
            "chunk": audio_data.hex()  # Convertir en hex pour JSON
        }
        await self.send_message(message)
    
    async def listen(self) -> None:
        """Écoute les messages entrants"""
        if not self.websocket or not self.is_connected:
            self.logger.error("WebSocket non connecté")
            return
        
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(data)
                except json.JSONDecodeError as e:
                    self.logger.error(f"Erreur de décodage JSON: {e}")
                except Exception as e:
                    self.logger.error(f"Erreur lors du traitement du message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            self.logger.info("Connexion fermée")
            self.is_connected = False
        except Exception as e:
            self.logger.error(f"Erreur lors de l'écoute: {e}")
    
    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """Traite un message reçu"""
        try:
            self.on_message(message)
        except Exception as e:
            self.logger.error(f"Erreur dans le gestionnaire de messages: {e}")
    
    async def start_conversation(self) -> None:
        """Démarre une conversation complète"""
        await self.connect()
        await self.send_conversation_initiation()
        
        # Démarrer l'écoute en arrière-plan
        listen_task = asyncio.create_task(self.listen())
        
        try:
            await listen_task
        except KeyboardInterrupt:
            self.logger.info("Interruption clavier")
        finally:
            listen_task.cancel()
            await self.disconnect()

async def main():
    """Fonction principale pour tester l'agent WebSocket"""
    agent_id = os.getenv("AGENT_ID")
    
    if not agent_id:
        print("Erreur: AGENT_ID non défini dans les variables d'environnement")
        return
    
    def custom_message_handler(message):
        message_type = message.get("type", "unknown")
        print(f"[{message_type}] {message}")
    
    agent = WebSocketConversationalAgent(
        agent_id=agent_id,
        on_message=custom_message_handler
    )
    
    try:
        print("Démarrage de l'agent WebSocket...")
        await agent.start_conversation()
    except KeyboardInterrupt:
        print("\nArrêt demandé")
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    asyncio.run(main())