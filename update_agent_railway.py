#!/usr/bin/env python3
"""
Met à jour l'agent ElevenLabs avec l'URL Railway
"""

import asyncio
import os
from dotenv import load_dotenv
from elevenlabs_integration import ElevenLabsIntegration

load_dotenv()

async def update_agent_with_railway(railway_url):
    """Met à jour l'agent avec l'URL Railway"""
    
    print(f"🔄 Mise à jour agent avec URL Railway: {railway_url}")
    
    # Données simplifiées du centre
    center_data = {
        'id': 'center_test_001',
        'center_name': 'Contrôle Auto Plus - Villejuif',
        'average_control_duration': 50,
        'opening_hours': {
            'monday': {'morning_start': '08:00', 'morning_end': '12:00', 'afternoon_start': '13:30', 'afternoon_end': '18:30', 'closed': False},
            'tuesday': {'morning_start': '08:00', 'morning_end': '12:00', 'afternoon_start': '13:30', 'afternoon_end': '18:30', 'closed': False},
            'wednesday': {'morning_start': '08:00', 'morning_end': '12:00', 'afternoon_start': '13:30', 'afternoon_end': '18:30', 'closed': False},
            'thursday': {'morning_start': '08:00', 'morning_end': '12:00', 'afternoon_start': '13:30', 'afternoon_end': '18:30', 'closed': False},
            'friday': {'morning_start': '08:00', 'morning_end': '12:00', 'afternoon_start': '13:30', 'afternoon_end': '18:30', 'closed': False},
            'saturday': {'morning_start': '08:00', 'morning_end': '12:00', 'afternoon_start': '13:30', 'afternoon_end': '18:00', 'closed': False},
            'sunday': {'closed': True}
        },
        'pricing_grid': {
            'Voiture_Particuliere': {'Essence': 78, 'Diesel': 85, 'Hybride': 85, 'Electrique': 75},
            'Utilitaire_Leger': {'Essence': 95, 'Diesel': 105},
            'Camping_Car': {'Essence': 125, 'Diesel': 135},
            'Moto': {'Essence': 45}
        },
        'allow_early_drop_off': True,
        'allow_previous_day_drop_off': False,
        'allow_late_pickup': True,
        'allow_next_day_pickup': True,
        'client_can_wait': True,
        'payment_methods': ['Espèces', 'CB', 'Chèque', 'Virement'],
        'calendar_url': 'https://calendly.com/controle-auto-plus-villejuif',
        'phone_number': '01 45 78 92 34'
    }
    
    try:
        api_key = os.getenv("ELEVENLABS_API_KEY")
        agent_id = os.getenv("AGENT_ID")
        
        if not api_key or not agent_id:
            print("❌ Variables ELEVENLABS_API_KEY ou AGENT_ID manquantes dans .env")
            return False
        
        elevenlabs = ElevenLabsIntegration(api_key)
        
        # Générer le prompt mis à jour
        custom_prompt = elevenlabs.generator.generate_center_prompt(center_data)
        
        # Configurer les tools avec Railway URL
        tools = [
            {
                "name": "get_slots",
                "description": "Récupère les créneaux disponibles pour le centre",
                "webhook": {
                    "url": f"{railway_url}/webhook/elevenlabs/center_test_001/get_slots",
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
                            "description": "Type de véhicule",
                            "default": "voiture_particuliere"
                        },
                        "preferred_time": {
                            "type": "string",
                            "enum": ["morning", "afternoon", "any"],
                            "description": "Créneau préféré",
                            "default": "any"
                        }
                    },
                    "required": ["start_date", "vehicle_type"]
                }
            },
            {
                "name": "book",
                "description": "Réserve un créneau pour un client",
                "webhook": {
                    "url": f"{railway_url}/webhook/elevenlabs/center_test_001/book",
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
        
        # Configuration complète pour l'agent
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
                },
                "tools": tools
            }
        }
        
        # Mise à jour via API
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{elevenlabs.base_url}/v1/convai/agents/{agent_id}",
                headers=elevenlabs.headers,
                json=update_config
            )
            
            if response.status_code == 200:
                print(f"✅ Agent mis à jour avec succès!")
                print(f"🔗 Webhook get_slots: {railway_url}/webhook/elevenlabs/center_test_001/get_slots")
                print(f"🔗 Webhook book: {railway_url}/webhook/elevenlabs/center_test_001/book")
                print(f"\n🎯 L'agent peut maintenant:")
                print(f"   - Récupérer les créneaux avec dates EXACTES")
                print(f"   - Dire 'jeudi 31 juillet' au lieu de 'mardi 31 juillet'")
                print(f"   - Réserver des créneaux")
                print(f"\n💡 TESTEZ: 'Je voudrais prendre rendez-vous'")
                return True
            else:
                print(f"❌ Erreur mise à jour: {response.text}")
                return False
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    print("🚀 CONFIGURATION AGENT AVEC RAILWAY")
    print("=" * 50)
    
    railway_url = input("Entrez votre URL Railway (https://xxx.railway.app): ").strip()
    
    if not railway_url or not railway_url.startswith('https://'):
        print("❌ URL Railway requise (https://xxx.railway.app)")
        return
    
    # Supprimer le slash final si présent
    railway_url = railway_url.rstrip('/')
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success = loop.run_until_complete(update_agent_with_railway(railway_url))
    
    if success:
        print(f"\n🎉 CONFIGURATION RÉUSSIE!")
        print(f"🤖 Votre agent peut maintenant calculer les dates correctement!")
    else:
        print(f"❌ Échec de la configuration")

if __name__ == "__main__":
    main()