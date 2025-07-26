# Guide d'Intégration - Agent Conversationnel Centre de Contrôle Technique

## 🎯 Vue d'ensemble

Ce système fournit un agent conversationnel téléphonique complet pour centres de contrôle technique, intégrable avec :
- **Site Lovable** (formulaire de souscription)
- **Supabase** (données des centres)
- **Twilio** (numéros de téléphone)
- **ElevenLabs** (agent conversationnel)

## 📋 Flux d'intégration

### 1. Souscription sur le site Lovable
```javascript
// Données collectées lors de l'inscription
const centerData = {
  center_name: "Contrôle Auto Plus",
  average_control_duration: 50,
  opening_hours: {...},
  pricing_grid: {...},
  allow_early_drop_off: true,
  allow_previous_day_drop_off: false,
  allow_late_pickup: true,
  allow_next_day_pickup: true,
  client_can_wait: true,
  payment_methods: ["Espèces", "CB", "Chèque"],
  calendar_url: "https://...",
  phone_number: "01 XX XX XX XX"
}
```

### 2. Génération automatique du prompt
```python
# Backend - Génération du prompt personnalisé
from prompt_generator import PromptGenerator

async def create_agent_for_center(center_id: str):
    # 1. Récupérer les données du centre depuis Supabase
    center_data = await supabase.get_center_data(center_id)
    
    # 2. Générer le prompt personnalisé
    generator = PromptGenerator()
    custom_prompt = generator.generate_center_prompt(center_data)
    
    # 3. Créer l'agent ElevenLabs
    agent_response = await elevenlabs.create_agent({
        "name": f"Agent {center_data['center_name']}",
        "prompt": custom_prompt,
        "voice_id": "selected_voice_id",
        "tools": [
            {
                "name": "get_slots",
                "description": "Récupère les créneaux disponibles",
                "parameters": {...}
            },
            {
                "name": "book",
                "description": "Réserve un créneau",
                "parameters": {...}
            }
        ]
    })
    
    # 4. Créer le numéro Twilio
    twilio_number = await twilio.create_phone_number()
    
    # 5. Configurer le webhook Twilio → ElevenLabs
    await twilio.configure_webhook(
        phone_number=twilio_number,
        webhook_url=f"https://api.elevenlabs.io/v1/convai/conversation?agent_id={agent_response.agent_id}"
    )
    
    # 6. Sauvegarder en base
    await supabase.update_center({
        "id": center_id,
        "twilio_number": twilio_number,
        "elevenlabs_agent_id": agent_response.agent_id,
        "status": "active"
    })
    
    return {
        "agent_id": agent_response.agent_id,
        "phone_number": twilio_number,
        "status": "ready"
    }
```

### 3. Configuration des tools ElevenLabs

#### Tool `get_slots`
```json
{
  "name": "get_slots",
  "description": "Récupère les créneaux disponibles pour le centre",
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
        "description": "Préférence horaire"
      }
    },
    "required": ["start_date", "vehicle_type"]
  }
}
```

#### Tool `book`
```json
{
  "name": "book",
  "description": "Réserve un créneau pour un client",
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
```

### 4. Endpoints API à développer

#### GET `/api/slots/{center_id}`
```python
@app.get("/api/slots/{center_id}")
async def get_available_slots(
    center_id: str,
    start_date: str,
    end_date: str = None,
    vehicle_type: str = "voiture_particuliere",
    preferred_time: str = "any"
):
    # Logique de récupération des créneaux
    # Intégration avec le système de planning du centre
    pass
```

#### POST `/api/booking/{center_id}`
```python
@app.post("/api/booking/{center_id}")
async def create_booking(
    center_id: str,
    booking_data: BookingRequest
):
    # Validation des données
    # Création du rendez-vous
    # Envoi de confirmation email/SMS
    # Notification au centre
    pass
```

## 🔧 Variables d'environnement requises

```bash
# ElevenLabs
ELEVENLABS_API_KEY=sk_...
ELEVENLABS_WEBHOOK_SECRET=...

# Twilio
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_WEBHOOK_SECRET=...

# Supabase
SUPABASE_URL=https://...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...

# Application
APP_SECRET_KEY=...
WEBHOOK_BASE_URL=https://votre-app.com
```

## 📊 Schema Supabase recommandé

```sql
-- Table des centres
CREATE TABLE centers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  center_name TEXT NOT NULL,
  average_control_duration INTEGER DEFAULT 45,
  opening_hours JSONB,
  pricing_grid JSONB,
  allow_early_drop_off BOOLEAN DEFAULT false,
  allow_previous_day_drop_off BOOLEAN DEFAULT false,
  allow_late_pickup BOOLEAN DEFAULT false,
  allow_next_day_pickup BOOLEAN DEFAULT false,
  client_can_wait BOOLEAN DEFAULT false,
  payment_methods JSONB,
  calendar_url TEXT,
  phone_number TEXT,
  twilio_number TEXT,
  elevenlabs_agent_id TEXT,
  status TEXT DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT NOW()
);

-- Table des rendez-vous
CREATE TABLE appointments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  center_id UUID REFERENCES centers(id),
  slot_datetime TIMESTAMP NOT NULL,
  client_first_name TEXT NOT NULL,
  client_last_name TEXT NOT NULL,
  client_phone TEXT NOT NULL,
  client_email TEXT,
  vehicle_brand TEXT NOT NULL,
  vehicle_model TEXT NOT NULL,
  license_plate TEXT NOT NULL,
  vehicle_type TEXT NOT NULL,
  status TEXT DEFAULT 'confirmed',
  created_at TIMESTAMP DEFAULT NOW()
);
```

## 🚀 Déploiement

### 1. Préparation
```bash
# Cloner le repository
git clone <repo>
cd conversational_agents

# Installer les dépendances
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Tests
```bash
# Tester le générateur de prompt
python test_prompt_generation.py

# Tester le contexte temporel
python test_temporal_context.py
```

### 3. Intégration
- Intégrer `prompt_generator.py` dans votre backend
- Configurer les webhooks Twilio → ElevenLabs
- Implémenter les endpoints de tools
- Tester avec un centre pilote

## 📞 Workflow d'appel

1. **Appel entrant** → Twilio reçoit l'appel
2. **Routage** → Twilio webhook vers ElevenLabs
3. **Agent IA** → Accueil et identification du besoin
4. **Prise de RDV** → Utilisation des tools `get_slots` et `book`
5. **Confirmation** → Email/SMS automatique
6. **Fallback** → Transfert vers le numéro du centre si nécessaire

## 🔍 Monitoring recommandé

- Taux de réussite des appels
- Durée moyenne des conversations
- Taux de prise de rendez-vous
- Satisfaction client (enquête post-appel)
- Erreurs tools et fallbacks

---

✅ **Le système est prêt pour la production !**