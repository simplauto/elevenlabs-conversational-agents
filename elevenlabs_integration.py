import httpx
import asyncio
from typing import Dict, Any, Optional
from prompt_generator import PromptGenerator

class ElevenLabsIntegration:
    """Gestionnaire d'intégration avec ElevenLabs pour centres de contrôle technique"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.elevenlabs.io"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }
        self.generator = PromptGenerator()
    
    async def create_center_agent(
        self, 
        center_data: Dict[str, Any],
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",  # Voix par défaut
        webhook_base_url: str = None
    ) -> Dict[str, str]:
        """
        Crée un agent ElevenLabs spécifique pour un centre
        
        Args:
            center_data: Données du centre depuis Supabase
            voice_id: ID de la voix à utiliser
            webhook_base_url: URL de base pour les webhooks tools
            
        Returns:
            Dict avec agent_id et phone_number
        """
        
        # 1. Générer le prompt personnalisé
        custom_prompt = self.generator.generate_center_prompt(center_data)
        
        # 2. Configurer les tools avec webhooks
        tools = self._create_tools_config(center_data["id"], webhook_base_url)
        
        # 3. Créer l'agent via l'API ElevenLabs
        agent_config = {
            "name": f"Agent {center_data.get('center_name', 'Centre CT')}",
            "prompt": custom_prompt,
            "voice_id": voice_id,
            "language": "fr",
            "tools": tools,
            "conversation_config": {
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "suffix_padding_ms": 800
                }
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/convai/agents",
                headers=self.headers,
                json=agent_config
            )
            
            if response.status_code != 201:
                raise Exception(f"Erreur création agent: {response.text}")
            
            agent_data = response.json()
            
        return {
            "agent_id": agent_data["agent_id"],
            "agent_name": agent_data["name"],
            "status": "created"
        }
    
    async def update_center_agent(
        self, 
        agent_id: str,
        center_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Met à jour un agent existant avec les nouvelles données du centre
        """
        
        # Générer le nouveau prompt
        custom_prompt = self.generator.generate_center_prompt(center_data)
        
        update_config = {
            "name": f"Agent {center_data.get('center_name', 'Centre CT')}",
            "conversation_config": {
                "agent": {
                    "prompt": {
                        "prompt": custom_prompt,
                        "llm": "gpt-4o-mini",
                        "temperature": 0.3,
                        "max_tokens": -1
                    }
                }
            }
        }
        
        print(f"🔍 Prompt à envoyer (100 premiers caractères): {custom_prompt[:100]}...")
        print(f"🔍 Taille du prompt: {len(custom_prompt)} caractères")
        
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.base_url}/v1/convai/agents/{agent_id}",
                headers=self.headers,
                json=update_config
            )
            
            print(f"🔍 Response status: {response.status_code}")
            print(f"🔍 Response body: {response.text[:500]}...")
            
            if response.status_code != 200:
                raise Exception(f"Erreur mise à jour agent: {response.text}")
                
        return {"agent_id": agent_id, "status": "updated"}
    
    async def delete_center_agent(self, agent_id: str) -> Dict[str, str]:
        """Supprime un agent ElevenLabs"""
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/v1/convai/agents/{agent_id}",
                headers=self.headers
            )
            
            if response.status_code != 204:
                raise Exception(f"Erreur suppression agent: {response.text}")
                
        return {"agent_id": agent_id, "status": "deleted"}
    
    async def get_agent_info(self, agent_id: str) -> Dict[str, Any]:
        """Récupère les informations d'un agent"""
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v1/convai/agents/{agent_id}",
                headers=self.headers
            )
            
            if response.status_code != 200:
                raise Exception(f"Erreur récupération agent: {response.text}")
                
        return response.json()
    
    def _create_tools_config(
        self, 
        center_id: str, 
        webhook_base_url: str
    ) -> list:
        """Configure les tools avec webhooks pour le centre"""
        
        if not webhook_base_url:
            webhook_base_url = "https://votre-api.com"  # À remplacer
        
        return [
            {
                "name": "get_slots",
                "description": "Récupère les créneaux disponibles pour le centre",
                "webhook": {
                    "url": f"{webhook_base_url}/webhook/elevenlabs/{center_id}/get_slots",
                    "method": "POST"
                },
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "format": "date",
                            "description": "Date de début de recherche (YYYY-MM-DD)"
                        },
                        "end_date": {
                            "type": "string", 
                            "format": "date",
                            "description": "Date de fin de recherche (YYYY-MM-DD)"
                        },
                        "vehicle_type": {
                            "type": "string",
                            "enum": ["voiture_particuliere", "utilitaire", "moto", "camping_car"],
                            "description": "Type de véhicule"
                        },
                        "preferred_time": {
                            "type": "string",
                            "enum": ["morning", "afternoon", "any"],
                            "description": "Créneau préféré"
                        }
                    },
                    "required": ["start_date", "vehicle_type"]
                }
            },
            {
                "name": "book",
                "description": "Réserve un créneau pour un client",
                "webhook": {
                    "url": f"{webhook_base_url}/webhook/elevenlabs/{center_id}/book",
                    "method": "POST"
                },
                "parameters": {
                    "type": "object",
                    "properties": {
                        "slot_id": {
                            "type": "string",
                            "description": "ID du créneau à réserver"
                        },
                        "client_info": {
                            "type": "object",
                            "properties": {
                                "first_name": {"type": "string"},
                                "last_name": {"type": "string"},
                                "phone": {"type": "string"},
                                "email": {"type": "string"},
                                "vehicle_brand": {"type": "string"},
                                "vehicle_model": {"type": "string"},
                                "license_plate": {"type": "string"}
                            },
                            "required": ["first_name", "last_name", "phone", "vehicle_brand", "license_plate"]
                        }
                    },
                    "required": ["slot_id", "client_info"]
                }
            }
        ]

# Exemple d'utilisation
async def example_center_setup():
    """Exemple complet de configuration d'un centre"""
    
    # 1. Données du centre (récupérées depuis Supabase)
    center_data = {
        "id": "center_123",
        "center_name": "Contrôle Auto Plus - Villejuif",
        "average_control_duration": 50,
        "opening_hours": {
            "monday": {"morning_start": "08:00", "morning_end": "12:00", "afternoon_start": "13:30", "afternoon_end": "18:30", "closed": False},
            # ... autres jours
        },
        "pricing_grid": {
            "voiture_particuliere": {"essence": 78, "diesel": 85},
            # ... autres tarifs
        },
        "allow_early_drop_off": True,
        "phone_number": "01 45 78 92 34",
        # ... autres paramètres
    }
    
    # 2. Créer l'intégration ElevenLabs
    elevenlabs = ElevenLabsIntegration(
        api_key="sk_e1538037fba860d9bd3564e440e47207485444ef1a3803ce"
    )
    
    # 3. Créer l'agent pour ce centre
    result = await elevenlabs.create_center_agent(
        center_data=center_data,
        voice_id="21m00Tcm4TlvDq8ikWAM",  # Voix choisie
        webhook_base_url="https://votre-api-backend.com"
    )
    
    print(f"Agent créé: {result['agent_id']}")
    
    # 4. Sauvegarder l'agent_id en base de données
    # await supabase.update_center(center_data["id"], {"elevenlabs_agent_id": result["agent_id"]})
    
    return result

if __name__ == "__main__":
    # Test de création d'agent
    result = asyncio.run(example_center_setup())
    print("Configuration terminée:", result)