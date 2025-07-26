import os
import logging
from typing import Optional, Callable
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
# Interface audio désactivée - utiliser websocket_agent.py pour les tests
# from elevenlabs.conversational_ai.conversation import Conversation
# from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface

load_dotenv()

class ConversationalAgent:
    """
    Agent conversationnel téléphonique utilisant ElevenLabs
    """
    
    def __init__(
        self,
        agent_id: str,
        api_key: Optional[str] = None,
        on_agent_response: Optional[Callable[[str], None]] = None,
        on_user_transcript: Optional[Callable[[str], None]] = None
    ):
        self.agent_id = agent_id
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.client = ElevenLabs(api_key=self.api_key)
        self.conversation = None
        self.is_running = False
        
        # Configuration des callbacks
        self.on_agent_response = on_agent_response or self._default_agent_response
        self.on_user_transcript = on_user_transcript or self._default_user_transcript
        
        # Configuration du logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _default_agent_response(self, response: str) -> None:
        """Callback par défaut pour les réponses de l'agent"""
        print(f"Agent: {response}")
    
    def _default_user_transcript(self, transcript: str) -> None:
        """Callback par défaut pour les transcriptions utilisateur"""
        print(f"Utilisateur: {transcript}")
    
    def start_conversation(self) -> None:
        """Démarre une nouvelle conversation"""
        try:
            self.logger.info(f"Démarrage de la conversation avec l'agent {self.agent_id}")
            
            self.conversation = Conversation(
                self.client,
                self.agent_id,
                requires_auth=bool(self.api_key),
                audio_interface=DefaultAudioInterface(),
                callback_agent_response=self.on_agent_response,
                callback_user_transcript=self.on_user_transcript
            )
            
            self.conversation.start_session()
            self.is_running = True
            self.logger.info("Conversation démarrée avec succès")
            
        except Exception as e:
            self.logger.error(f"Erreur lors du démarrage de la conversation: {e}")
            raise
    
    def stop_conversation(self) -> None:
        """Arrête la conversation en cours"""
        if self.conversation and self.is_running:
            try:
                self.conversation.end_session()
                self.is_running = False
                self.logger.info("Conversation arrêtée")
            except Exception as e:
                self.logger.error(f"Erreur lors de l'arrêt de la conversation: {e}")
        else:
            self.logger.warning("Aucune conversation active à arrêter")
    
    def send_message(self, message: str) -> None:
        """Envoie un message texte à l'agent"""
        if not self.conversation or not self.is_running:
            self.logger.error("Conversation non active")
            return
        
        try:
            # Note: Cette méthode peut nécessiter une adaptation selon l'API exacte
            self.logger.info(f"Envoi du message: {message}")
            # Implémentation spécifique à définir selon les besoins
        except Exception as e:
            self.logger.error(f"Erreur lors de l'envoi du message: {e}")
    
    def is_conversation_active(self) -> bool:
        """Vérifie si une conversation est active"""
        return self.is_running and self.conversation is not None

def main():
    """Fonction principale pour tester l'agent"""
    agent_id = os.getenv("AGENT_ID")
    
    if not agent_id:
        print("Erreur: AGENT_ID non défini dans les variables d'environnement")
        return
    
    # Création de l'agent
    agent = ConversationalAgent(agent_id)
    
    try:
        print("Démarrage de l'agent conversationnel...")
        agent.start_conversation()
        
        print("Agent prêt. Parlez dans votre microphone.")
        print("Appuyez sur Ctrl+C pour arrêter.")
        
        # Maintenir la conversation active
        while agent.is_conversation_active():
            try:
                import time
                time.sleep(1)
            except KeyboardInterrupt:
                break
                
    except KeyboardInterrupt:
        print("\nArrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"Erreur: {e}")
    finally:
        agent.stop_conversation()
        print("Agent arrêté")

if __name__ == "__main__":
    main()