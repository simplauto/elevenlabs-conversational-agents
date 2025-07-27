# Configuration manuelle des tools ElevenLabs

## 🔧 Créer les tools dans l'interface ElevenLabs

### 1. Aller dans votre agent
- Ouvrez https://elevenlabs.io/app/conversational-ai
- Sélectionnez votre agent `agent_6901k10dw8qpemyshh1vchsvf3tk`

### 2. Ajouter le tool "get_slots"

**Cliquez "Add Tool" puis "Webhook" :**

**Name:** `get_slots`

**Description:** `Récupère les créneaux disponibles pour le centre de contrôle technique. Utilise ce tool quand un client demande un rendez-vous.`

**Method:** `POST`

**URL:** `https://elevenlabs-conversational-agents-production.up.railway.app/webhook/elevenlabs/center_test_001/get_slots`

**Parameters:**
```json
{
  "vehicle_type": {
    "type": "string",
    "description": "Type de véhicule du client: voiture_particuliere, utilitaire, moto, camping_car. Utiliser voiture_particuliere par défaut.",
    "default": "voiture_particuliere"
  }
}
```

**IMPORTANT:**
- ❌ **NE PAS ajouter start_date** - Évite les erreurs de calcul de dates par le LLM
- ✅ **L'API récupère automatiquement TOUS les créneaux** disponibles  
- ✅ **Dates calculées côté serveur** pour éviter "mardi 1er août" au lieu de "vendredi 1er août"

### 3. Ajouter le tool "book"

**Cliquez "Add Tool" puis "Webhook" :**

**Name:** `book`

**Description:** `Réserve un créneau pour un client après avoir collecté toutes ses informations.`

**Method:** `POST`

**URL:** `https://elevenlabs-conversational-agents-production.up.railway.app/webhook/elevenlabs/center_test_001/book`

**Parameters:**
```json
{
  "slot_id": {
    "type": "string",
    "description": "ID du créneau à réserver (reçu de get_slots)",
    "required": true
  },
  "client_info": {
    "type": "object",
    "description": "Informations du client",
    "properties": {
      "first_name": {"type": "string", "description": "Prénom"},
      "last_name": {"type": "string", "description": "Nom de famille"},
      "phone": {"type": "string", "description": "Numéro de téléphone"},
      "email": {"type": "string", "description": "Email (optionnel)"},
      "vehicle_brand": {"type": "string", "description": "Marque du véhicule"},
      "vehicle_model": {"type": "string", "description": "Modèle du véhicule"},
      "license_plate": {"type": "string", "description": "Plaque d'immatriculation"}
    },
    "required": ["first_name", "last_name", "phone", "vehicle_brand", "license_plate"]
  }
}
```

### 4. Tester l'API

**Avant de tester l'agent, vérifiez que l'API fonctionne :**

Ouvrez dans votre navigateur :
`https://elevenlabs-conversational-agents-production.up.railway.app/test/generate-slots/center_test_001`

Vous devriez voir des créneaux JSON.

### 5. Test de l'agent

**Une fois les tools ajoutés, testez :**
- "Je voudrais prendre rendez-vous"
- L'agent devrait appeler get_slots et vous dire les vraies dates

## 🎯 Résultat attendu

L'agent dira : "Nos prochains créneaux disponibles sont : le jeudi 31 juillet 2025 à 08:00..." au lieu de "mardi 31 juillet".