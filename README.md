# Agent Conversationnel - Centres de Contrôle Technique

API backend pour agents conversationnels ElevenLabs spécialisés dans la prise de rendez-vous pour centres de contrôle technique automobile.

## 🚀 Déploiement sur Railway

### 1. Variables d'environnement

Configurez ces variables dans Railway :

```
ELEVENLABS_API_KEY=your_elevenlabs_api_key
AGENT_ID=your_agent_id
```

### 2. Déploiement

1. Fork ce repo
2. Connectez-le à Railway
3. Railway détectera automatiquement les fichiers de config
4. L'API sera déployée sur `https://votre-app.railway.app`

### 3. Configuration de l'agent

Après déploiement, lancez :

```bash
python update_agent_railway.py
```

Et entrez votre URL Railway pour configurer les webhooks.

## 📋 Endpoints

- `POST /webhook/elevenlabs/{center_id}/get_slots` - Récupère les créneaux disponibles
- `POST /webhook/elevenlabs/{center_id}/book` - Réserve un créneau
- `GET /test/generate-slots/{center_id}` - Test de génération de créneaux

## 🎯 Fonctionnalités

✅ **Calcul exact des dates** - Plus d'erreurs "mardi 1er août"  
✅ **Contextualisation temporelle** - Comprend "la semaine prochaine"  
✅ **Gestion multi-centres** - Un centre = un ID  
✅ **Formatage français** - Dates en français correct  

## 🛠️ Structure

- `backend_api.py` - API FastAPI principale
- `elevenlabs_integration.py` - Intégration ElevenLabs
- `prompt_generator.py` - Génération de prompts personnalisés
- `datetime_utils.py` - Utilitaires de gestion temporelle
- `update_agent_railway.py` - Configuration des webhooks

## 📞 Test

Une fois déployé, testez avec ces phrases :

- "Je voudrais prendre rendez-vous"
- "C'est possible demain ?"
- "J'ai vu moins cher en ligne"

L'agent devrait maintenant donner les jours de la semaine corrects !

## Configuration locale (développement)

## Utilisation

### Agent SDK Python (Recommandé)

```python
from conversational_agent import ConversationalAgent

agent = ConversationalAgent(agent_id="your_agent_id")
agent.start_conversation()
```

### Agent WebSocket (Avancé)

```python
import asyncio
from websocket_agent import WebSocketConversationalAgent

async def main():
    agent = WebSocketConversationalAgent(agent_id="your_agent_id")
    
    # Connexion avec contexte temporel automatique
    await agent.connect()
    await agent.send_conversation_initiation()  # Envoie date/heure Paris
    
    # Message avec contexte temporel
    await agent.send_user_message_with_context(
        "Je voudrais réserver demain matin"
    )
    
    await agent.disconnect()

asyncio.run(main())
```

### Exécution directe

```bash
# Agent SDK
python conversational_agent.py

# Agent WebSocket
python websocket_agent.py

# Test du contexte temporel
python test_temporal_context.py
```

## Usage pour Centres de Contrôle Technique

Cet agent est spécialement conçu pour les centres de contrôle technique automobile avec :

### 🎯 Fonctionnalités principales :
1. **Prise de rendez-vous automatisée** avec tools `get_slots` et `book`
2. **Réponses personnalisées** selon les données du centre
3. **Contexte temporel intelligent** (Paris, France)
4. **Gestion complète des informations client**

### 📝 Génération de prompt personnalisé :

```python
from prompt_generator import PromptGenerator

# Données de votre centre (depuis Supabase)
center_data = {
    "average_control_duration": 50,
    "opening_hours": {...},
    "pricing_grid": {...},
    "allow_early_drop_off": True,
    "payment_methods": ["Espèces", "CB", "Chèque"],
    "phone_number": "01 XX XX XX XX"
}

# Génération du prompt
generator = PromptGenerator()
prompt = generator.generate_center_prompt(center_data)

# Le prompt est prêt pour ElevenLabs
```

### 🕐 Contexte Temporel Automatique

L'agent comprend automatiquement :
- **"Ce matin"** → Aujourd'hui 8h-12h
- **"La semaine prochaine"** → Du lundi au dimanche suivant
- **"Dans 2 semaines"** → Du lundi au dimanche de la 2ème semaine
- **"Le mois prochain"** → Du 1er au dernier jour du mois

### 📋 Variables Supabase intégrées :
- `average_control_duration` - Durée des contrôles
- `opening_hours` - Horaires par jour de la semaine
- `pricing_grid` - Tarifs par type de véhicule/carburant
- `allow_early_drop_off` - Dépôt anticipé
- `allow_previous_day_drop_off` - Dépôt la veille
- `allow_late_pickup` - Récupération tardive
- `allow_next_day_pickup` - Récupération lendemain
- `client_can_wait` - Attente sur place
- `payment_methods` - Moyens de paiement
- `calendar_url` - URL agenda en ligne
- `phone_number` - Numéro de transfert

### 🔧 Test complet :

```bash
# Test du générateur de prompt
python test_prompt_generation.py

# Test de l'agent avec contexte temporel
python test_temporal_context.py
```

## APIs Supportées

- **SDK Python** : Interface simplifiée avec gestion audio automatique
- **WebSocket** : Contrôle complet des échanges en temps réel
- **Voix** : 5000+ voix disponibles en 31 langues
- **Modèles** : Support GPT, Claude, Gemini

## Documentation

- [ElevenLabs Conversational AI](https://elevenlabs.io/docs/conversational-ai/overview)
- [API WebSocket](https://elevenlabs.io/docs/conversational-ai/api-reference/conversational-ai/websocket)
- [SDK Python](https://elevenlabs.io/docs/conversational-ai/libraries/python)