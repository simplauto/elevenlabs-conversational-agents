#!/usr/bin/env python3
"""
Met à jour l'agent ElevenLabs pour transmettre exactement les expressions temporelles
"""

import asyncio
import os
from dotenv import load_dotenv
from elevenlabs_integration import ElevenLabsIntegration

load_dotenv()

async def update_agent_with_exact_transmission():
    """Met à jour l'agent pour qu'il transmette exactement les expressions temporelles"""
    
    railway_url = "https://elevenlabs-conversational-agents-production.up.railway.app"
    print(f"🔄 Mise à jour agent avec transmission exacte des expressions")
    
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
        
        # Générer le prompt mis à jour avec les instructions de transmission exacte
        custom_prompt = elevenlabs.generator.generate_center_prompt(center_data)
        
        # Configuration pour mettre à jour le prompt
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
                print(f"📝 Instructions de transmission exacte ajoutées:")
                print(f"   - Client dit 'lundi suivant' → specific_day='lundi suivant' (pas 'lundi prochain')")
                print(f"   - Client dit '11 août' → specific_day='11 août'")
                print(f"   - ❌ JAMAIS transformer ou interpréter")
                print(f"   - ✅ TOUJOURS transmettre exactement")
                print(f"\n💡 L'API peut maintenant distinguer 'lundi prochain' vs 'lundi suivant'")
                return True
            else:
                print(f"❌ Erreur mise à jour: {response.text}")
                return False
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    print("🚀 TRANSMISSION EXACTE DES EXPRESSIONS")
    print("=" * 50)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success = loop.run_until_complete(update_agent_with_exact_transmission())
    
    if success:
        print(f"\n🎉 PROMPT MIS À JOUR!")
        print(f"📋 L'agent ne doit plus transformer les expressions temporelles!")
        print(f"🔧 Pensez à déployer aussi les changements API sur Railway")
    else:
        print(f"❌ Échec de la mise à jour")

if __name__ == "__main__":
    main()