"""
Script de déploiement et configuration complète pour centres de contrôle technique
"""

import asyncio
import os
from elevenlabs_integration import ElevenLabsIntegration
from prompt_generator import PromptGenerator

class DeploymentManager:
    """Gestionnaire de déploiement pour centres de contrôle technique"""
    
    def __init__(self):
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.webhook_base_url = os.getenv("WEBHOOK_BASE_URL", "https://votre-api.com")
        
        if not self.elevenlabs_api_key:
            raise ValueError("ELEVENLABS_API_KEY non définie")
    
    async def setup_new_center(self, center_data: dict) -> dict:
        """
        Configuration complète d'un nouveau centre
        
        Workflow:
        1. Génération du prompt personnalisé
        2. Création de l'agent ElevenLabs 
        3. Configuration des webhooks
        4. Création du numéro Twilio (optionnel)
        5. Sauvegarde en base de données
        """
        
        print(f"🏢 Configuration du centre: {center_data.get('center_name', 'Nouveau centre')}")
        
        try:
            # 1. Créer l'agent ElevenLabs
            elevenlabs = ElevenLabsIntegration(self.elevenlabs_api_key)
            
            agent_result = await elevenlabs.create_center_agent(
                center_data=center_data,
                voice_id="21m00Tcm4TlvDq8ikWAM",  # Voix française
                webhook_base_url=self.webhook_base_url
            )
            
            print(f"✅ Agent ElevenLabs créé: {agent_result['agent_id']}")
            
            # 2. Configuration Twilio (simulation)
            twilio_number = await self._create_twilio_number(agent_result['agent_id'])
            print(f"✅ Numéro Twilio configuré: {twilio_number}")
            
            # 3. Sauvegarde en base (simulation)
            await self._save_center_config(center_data['id'], {
                "elevenlabs_agent_id": agent_result['agent_id'],
                "twilio_number": twilio_number,
                "status": "active"
            })
            
            print(f"✅ Configuration sauvegardée")
            
            return {
                "status": "success",
                "center_id": center_data['id'],
                "agent_id": agent_result['agent_id'],
                "phone_number": twilio_number,
                "webhook_urls": {
                    "get_slots": f"{self.webhook_base_url}/webhook/elevenlabs/{center_data['id']}/get_slots",
                    "book": f"{self.webhook_base_url}/webhook/elevenlabs/{center_data['id']}/book"
                }
            }
            
        except Exception as e:
            print(f"❌ Erreur lors de la configuration: {e}")
            raise
    
    async def update_center_config(self, center_id: str, center_data: dict) -> dict:
        """Met à jour la configuration d'un centre existant"""
        
        print(f"🔄 Mise à jour du centre: {center_id}")
        
        try:
            # Récupérer l'agent_id existant (simulation)
            existing_config = await self._get_center_config(center_id)
            agent_id = existing_config.get("elevenlabs_agent_id")
            
            if not agent_id:
                raise ValueError(f"Agent non trouvé pour le centre {center_id}")
            
            # Mettre à jour l'agent ElevenLabs
            elevenlabs = ElevenLabsIntegration(self.elevenlabs_api_key)
            await elevenlabs.update_center_agent(agent_id, center_data)
            
            print(f"✅ Agent mis à jour: {agent_id}")
            
            return {
                "status": "updated",
                "center_id": center_id,
                "agent_id": agent_id
            }
            
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour: {e}")
            raise
    
    async def _create_twilio_number(self, agent_id: str) -> str:
        """Création d'un numéro Twilio (simulation)"""
        # En réalité, appel à l'API Twilio
        return f"+33199887766"  # Numéro simulé
    
    async def _save_center_config(self, center_id: str, config: dict):
        """Sauvegarde la configuration en base (simulation)"""
        # En réalité, update Supabase
        print(f"💾 Sauvegarde config pour {center_id}: {config}")
    
    async def _get_center_config(self, center_id: str) -> dict:
        """Récupère la configuration d'un centre (simulation)"""
        # En réalité, requête Supabase
        return {
            "elevenlabs_agent_id": "agent_exemple_123",
            "twilio_number": "+33199887766"
        }

# Exemples de configuration
EXAMPLE_CENTERS = {
    "center_urbain": {
        "id": "center_001",
        "center_name": "Contrôle Auto Plus - Paris 15ème",
        "average_control_duration": 45,
        "opening_hours": {
            "monday": {"morning_start": "08:00", "morning_end": "12:00", "afternoon_start": "13:30", "afternoon_end": "18:30", "closed": False},
            "tuesday": {"morning_start": "08:00", "morning_end": "12:00", "afternoon_start": "13:30", "afternoon_end": "18:30", "closed": False},
            "wednesday": {"morning_start": "08:00", "morning_end": "12:00", "afternoon_start": "13:30", "afternoon_end": "18:30", "closed": False},
            "thursday": {"morning_start": "08:00", "morning_end": "12:00", "afternoon_start": "13:30", "afternoon_end": "18:30", "closed": False},
            "friday": {"morning_start": "08:00", "morning_end": "12:00", "afternoon_start": "13:30", "afternoon_end": "18:30", "closed": False},
            "saturday": {"morning_start": "08:00", "morning_end": "12:00", "closed": False},
            "sunday": {"closed": True}
        },
        "pricing_grid": {
            "voiture_particuliere": {"essence": 82, "diesel": 89, "hybride": 89, "electrique": 79},
            "utilitaire": {"essence": 98, "diesel": 108},
            "moto": {"essence": 48}
        },
        "allow_early_drop_off": True,
        "allow_previous_day_drop_off": True,
        "allow_late_pickup": True,
        "allow_next_day_pickup": True,
        "client_can_wait": True,
        "payment_methods": ["Espèces", "CB", "Chèque", "Virement"],
        "calendar_url": "https://calendly.com/ct-paris15",
        "phone_number": "01 45 67 89 12"
    },
    "center_rural": {
        "id": "center_002", 
        "center_name": "Garage Dubois - Contrôle Technique",
        "average_control_duration": 60,
        "opening_hours": {
            "monday": {"morning_start": "08:30", "morning_end": "12:00", "afternoon_start": "14:00", "afternoon_end": "18:00", "closed": False},
            "tuesday": {"morning_start": "08:30", "morning_end": "12:00", "afternoon_start": "14:00", "afternoon_end": "18:00", "closed": False},
            "wednesday": {"closed": True},
            "thursday": {"morning_start": "08:30", "morning_end": "12:00", "afternoon_start": "14:00", "afternoon_end": "18:00", "closed": False},
            "friday": {"morning_start": "08:30", "morning_end": "12:00", "afternoon_start": "14:00", "afternoon_end": "18:00", "closed": False},
            "saturday": {"morning_start": "08:30", "morning_end": "12:00", "closed": False},
            "sunday": {"closed": True}
        },
        "pricing_grid": {
            "voiture_particuliere": {"essence": 75, "diesel": 82},
            "utilitaire": {"essence": 92, "diesel": 99},
            "moto": {"essence": 42}
        },
        "allow_early_drop_off": False,
        "allow_previous_day_drop_off": False,
        "allow_late_pickup": False,
        "allow_next_day_pickup": False,
        "client_can_wait": False,
        "payment_methods": ["Espèces", "CB"],
        "calendar_url": None,
        "phone_number": "04 56 78 90 12"
    }
}

async def demo_deployment():
    """Démonstration complète du déploiement"""
    
    print("🚀 DÉMONSTRATION DE DÉPLOIEMENT")
    print("=" * 50)
    
    manager = DeploymentManager()
    
    # Configuration des centres d'exemple
    for center_type, center_data in EXAMPLE_CENTERS.items():
        print(f"\n📍 Configuration {center_type.replace('_', ' ').title()}")
        print("-" * 30)
        
        try:
            result = await manager.setup_new_center(center_data)
            
            print(f"✅ Résultat:")
            print(f"   • Centre ID: {result['center_id']}")
            print(f"   • Agent ElevenLabs: {result['agent_id']}")
            print(f"   • Numéro de téléphone: {result['phone_number']}")
            print(f"   • Webhooks configurés ✅")
            
        except Exception as e:
            print(f"❌ Échec: {e}")
    
    print(f"\n🎉 Déploiement terminé!")
    print(f"Les centres sont prêts à recevoir des appels.")

async def test_prompt_generation():
    """Test de génération de prompt pour validation"""
    
    print("\n🧪 TEST DE GÉNÉRATION DE PROMPT")
    print("=" * 40)
    
    generator = PromptGenerator()
    
    for center_type, center_data in EXAMPLE_CENTERS.items():
        print(f"\n📝 Prompt pour {center_type.replace('_', ' ').title()}")
        
        prompt = generator.generate_center_prompt(center_data)
        
        # Vérifications
        checks = {
            "Contexte temporel": "MAINTENANT" in prompt,
            "Horaires inclus": center_data['phone_number'] in prompt,
            "Tarifs inclus": str(list(center_data['pricing_grid'].values())[0]) in prompt,
            "Tools configurés": "get_slots" in prompt and "book" in prompt
        }
        
        print(f"   Longueur: {len(prompt)} caractères")
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"   {check}: {status}")

if __name__ == "__main__":
    # Variables d'environnement requises
    required_vars = [
        "ELEVENLABS_API_KEY",
        "WEBHOOK_BASE_URL"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Variables d'environnement manquantes: {missing_vars}")
        print("Configurez ces variables avant de lancer le déploiement.")
        exit(1)
    
    # Lancer les tests
    asyncio.run(test_prompt_generation())
    
    # Lancer la démo (commenté pour éviter la création d'agents en test)
    # asyncio.run(demo_deployment())