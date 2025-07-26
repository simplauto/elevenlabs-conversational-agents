#!/usr/bin/env python3
"""
Script pour mettre à jour dynamiquement l'agent ElevenLabs avec le prompt actualisé
"""

import asyncio
import os
from elevenlabs_integration import ElevenLabsIntegration
from prompt_generator import PromptGenerator
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

async def update_agent_prompt(agent_id: str):
    """
    Met à jour le prompt de l'agent ElevenLabs avec la date/heure actuelle
    """
    
    # Données du centre pour le test
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
    
    print(f"🔄 Mise à jour de l'agent {agent_id} avec contexte temporel actualisé...")
    
    try:
        # 1. Récupérer la clé API depuis .env
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            print("❌ ELEVENLABS_API_KEY non trouvée dans .env")
            return None
        
        # 2. Vérifier l'agent avant mise à jour
        elevenlabs = ElevenLabsIntegration(api_key)
        
        print("🔍 Récupération des infos actuelles de l'agent...")
        current_info = await elevenlabs.get_agent_info(agent_id)
        print(f"   Prompt actuel (100 premiers caractères): {current_info.get('prompt', 'Aucun prompt')[:100]}...")
        
        # 3. Mettre à jour l'agent
        result = await elevenlabs.update_center_agent(agent_id, center_data)
        
        print(f"✅ Agent mis à jour avec succès!")
        print(f"   Agent ID: {result['agent_id']}")
        print(f"   Status: {result['status']}")
        
        # 3. Afficher le contexte temporel actualisé
        from datetime_utils import format_current_context
        temporal_context = format_current_context()
        print(f"\n📅 Contexte temporel injecté:")
        lines = temporal_context.split('\n')
        for line in lines[:10]:  # Afficher les 10 premières lignes
            if line.strip():
                print(f"   {line}")
        
        print(f"\n🎯 Votre agent est maintenant prêt pour les tests d'appel vocal!")
        print(f"🔗 URL de test ElevenLabs : https://elevenlabs.io/app/conversational-ai")
        
        return result
        
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour: {e}")
        return None

async def main():
    """Point d'entrée principal"""
    
    print("🤖 MISE À JOUR DYNAMIQUE DE L'AGENT ELEVENLABS")
    print("=" * 60)
    
    # Récupérer l'agent ID depuis .env
    agent_id = os.getenv("AGENT_ID")
    
    if not agent_id:
        print("❌ AGENT_ID non trouvé dans .env")
        return
    
    print(f"🎯 Agent à mettre à jour: {agent_id}")
    
    # Mettre à jour l'agent
    result = await update_agent_prompt(agent_id)
    
    if result:
        print(f"\n🎉 SUCCÈS - L'agent est prêt pour vos tests!")
        print(f"💡 Testez maintenant les scénarios suivants:")
        print(f"   1. 'Bonjour, je voudrais prendre rendez-vous'")
        print(f"   2. 'J'ai vu moins cher en ligne'")
        print(f"   3. 'Je voudrais un rendez-vous la semaine prochaine'")
        print(f"   4. 'Quels sont vos tarifs ?'")

if __name__ == "__main__":
    # Lancer la mise à jour directement
    asyncio.run(main())