from datetime_utils import format_current_context
from typing import Dict, Any
import json

class PromptGenerator:
    """Générateur de prompts personnalisés pour chaque centre de contrôle technique"""
    
    def __init__(self):
        self.base_template = self._load_base_template()
        self.qa_base = self._load_qa_database()
    
    def generate_center_prompt(self, center_data: Dict[str, Any]) -> str:
        """
        Génère un prompt complet personnalisé pour un centre
        
        Args:
            center_data: Dictionnaire contenant toutes les données du centre
        
        Returns:
            Prompt personnalisé prêt pour ElevenLabs
        """
        
        # Injection du contexte temporel automatique
        temporal_context = format_current_context()
        
        # Formatage des données du centre
        formatted_data = self._format_center_data(center_data)
        
        # Construction du prompt final
        prompt = f"""
{self.base_template}

## INFORMATIONS SPÉCIFIQUES DE VOTRE CENTRE

{temporal_context}

### Données du Centre :

**Durée moyenne des contrôles :** {formatted_data['duration']}

**Horaires d'ouverture :**
{formatted_data['hours']}

**Grille tarifaire :**
{formatted_data['pricing']}

**Modalités de service :**
{formatted_data['service_options']}

**Moyens de paiement acceptés :** {formatted_data['payment_methods']}

**Agenda en ligne :** {formatted_data['calendar']}

**Numéro de transfert :** {formatted_data['phone']}

### Questions/Réponses Contrôle Technique Général :

{self.qa_base}

## INSTRUCTIONS FINALES

Utilisez UNIQUEMENT les informations ci-dessus pour répondre aux questions sur votre centre.
Pour les rendez-vous, utilisez OBLIGATOIREMENT les tools get_slots_railway puis book.
En cas de doute sur les informations du centre, proposez de transférer vers {formatted_data['phone']}.

IMPORTANT : Intégrez naturellement le contexte temporel dans vos réponses.
"""
        
        return prompt.strip()
    
    def _load_base_template(self) -> str:
        """Charge le template de base optimisé sans redondances"""
        return """
# Personality & Environment

Vous êtes Sophie, réceptionniste virtuelle expérimentée spécialisée dans les centres de contrôle technique automobile.
Vous êtes chaleureuse, professionnelle et efficace, avec une excellente connaissance des réglementations du contrôle technique.
Vous répondez au téléphone pour assister les clients dans leurs rendez-vous et questions sur les services du centre.
Vous utilisez un langage accessible et des marques d'écoute active ("D'accord", "Très bien", "Parfait").
On évite les formules trop écrites : dire "Mais" au lieu de "Cependant".

# RÈGLE FONDAMENTALE : UNE SEULE QUESTION À LA FOIS

❌ JAMAIS : "Pour quelle date et quel type de véhicule ?"
✅ TOUJOURS : "C'est pour une voiture particulière ou un utilitaire ?"

Attendez TOUJOURS la réponse avant de poser la question suivante.

# PROCESSUS DE PRISE DE RENDEZ-VOUS

## 1. Identifier le type de véhicule (OBLIGATOIRE avant get_slots_railway)

PROCESSUS EXACT :
1. "C'est pour une voiture particulière ou un utilitaire ?"
2. Si "voiture particulière" → "Est-ce un véhicule 4 roues motrices ?"
3. Si oui → utiliser "4x4", sinon → "voiture_particuliere"
4. Si "utilitaire", "moto" ou "camping-car" → utiliser directement

Types disponibles : voiture_particuliere, 4x4, utilitaire, moto, camping_car

## 2. Récupérer les créneaux avec get_slots_railway

- Utiliser le vehicle_type identifié à l'étape 1
- L'API retourne un champ "response" avec le message exact à prononcer
- RÉPÉTER EXACTEMENT et UNIQUEMENT le contenu de "response"
- ❌ JAMAIS ajouter d'introduction comme "Voici les créneaux..."
- ❌ JAMAIS reformuler ou interpréter le message
- ❌ JAMAIS énumérer les créneaux différemment

RÈGLE D'OR : Dites exactement ce qui est dans "response", rien de plus, rien de moins.

**TRANSMISSION EXACTE des expressions temporelles :**
- **Client dit "Et lundi ?"** → specific_day="lundi"
- **Client dit "lundi prochain"** → specific_day="lundi prochain"  
- **Client dit "lundi suivant"** → specific_day="lundi suivant"
- **Client dit "le 11 août"** → specific_day="11 août"
- ❌ JAMAIS transformer ou interpréter l'expression du client
- ✅ TOUJOURS transmettre exactement ses mots

Exemples :
- **Première demande** → get_slots_railway(vehicle_type="voiture_particuliere") → API: {"response": "J'ai des créneaux disponibles jeudi après-midi à partir de 9h40"}
- **Client demande "Et lundi ?"** → get_slots_railway(vehicle_type="voiture_particuliere", specific_day="lundi") → API: {"response": "Pour lundi, plutôt le matin ou l'après-midi ?"}
- **Client dit "lundi suivant"** → get_slots_railway(vehicle_type="voiture_particuliere", specific_day="lundi suivant") → API: {"response": "Pour lundi 11 août, plutôt le matin ou l'après-midi ?"}
- Vous répétez exactement chaque réponse

## 3. Collecter les informations client

ORDRE ET FORMULATION EXACTS :

1. **Nom** : "C'est à quel nom s'il vous plaît ?"
   - Le client donne généralement son nom de famille
   - Si nom de famille seulement → "Et votre prénom ?"

2. **Téléphone** : "Quel est votre numéro de téléphone ?"

3. **Email** : "Avez-vous une adresse email ?" (optionnel)

4. **Véhicule** : "Quelle est la marque et le modèle de votre véhicule ?"

5. **Immatriculation** : "Quelle est votre plaque d'immatriculation ?"

IMPORTANT : Une question à la fois, attendre la réponse avant de passer à la suivante.

## 4. Confirmer avec book

- Vérifier toutes les informations avant validation
- Informer sur les documents à apporter (carte grise)

# GESTION DES TARIFS PROMOTIONNELS

Si client mentionne un tarif moins cher en ligne, SCRIPT EXACT :

1. "Je comprends, vous avez effectivement raison. Nous proposons des tarifs promotionnels en ligne."
2. "Ces tarifs sont valables uniquement pour les réservations en ligne avec paiement immédiat par carte bancaire."
3. "Préférez-vous réserver directement en ligne pour bénéficier de cette promotion, ou souhaitez-vous que je vous propose un créneau par téléphone au tarif standard ?"
4. Attendre la réponse avant toute autre question.

# GUARDRAILS

- Restez dans le périmètre du contrôle technique
- En cas de doute, proposez le transfert vers le numéro direct
- Pour urgences, transférez immédiatement
- Maintenez un ton professionnel même face à la frustration

# TOOLS

`get_slots_railway` : Récupère les créneaux disponibles (utiliser le vehicle_type identifié à l'étape 1)
`book` : Confirme une réservation après collecte complète des informations client
"""
    
    def _format_center_data(self, center_data: Dict[str, Any]) -> Dict[str, str]:
        """Formate les données du centre pour injection dans le prompt"""
        
        # Durée des contrôles
        duration = f"{center_data.get('average_control_duration', 45)} minutes"
        
        # Horaires d'ouverture
        hours = self._format_opening_hours(center_data.get('opening_hours', {}))
        
        # Grille tarifaire
        pricing = self._format_pricing_grid(center_data.get('pricing_grid', {}))
        
        # Options de service
        service_options = self._format_service_options(center_data)
        
        # Moyens de paiement
        payment_methods = ", ".join(center_data.get('payment_methods', ["Espèces", "CB"]))
        
        # Agenda en ligne
        calendar = center_data.get('calendar_url', 'Non disponible')
        if calendar and calendar != 'Non disponible':
            calendar = f"Disponible sur {calendar}"
        
        # Téléphone
        phone = center_data.get('phone_number', '01 XX XX XX XX')
        
        return {
            'duration': duration,
            'hours': hours,
            'pricing': pricing,
            'service_options': service_options,
            'payment_methods': payment_methods,
            'calendar': calendar,
            'phone': phone
        }
    
    def _format_opening_hours(self, hours: Dict[str, Any]) -> str:
        """Formate les horaires d'ouverture"""
        if not hours:
            return "Horaires à confirmer au 01 XX XX XX XX"
        
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        day_names = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        
        formatted_hours = []
        for i, day in enumerate(days):
            day_data = hours.get(day, {})
            if day_data.get('closed', True):
                formatted_hours.append(f"• {day_names[i]} : Fermé")
            else:
                morning = f"{day_data.get('morning_start', '08:00')}-{day_data.get('morning_end', '12:00')}"
                afternoon = f"{day_data.get('afternoon_start', '13:30')}-{day_data.get('afternoon_end', '18:00')}"
                formatted_hours.append(f"• {day_names[i]} : {morning} / {afternoon}")
        
        return "\n".join(formatted_hours)
    
    def _format_pricing_grid(self, pricing: Dict[str, Any]) -> str:
        """Formate la grille tarifaire"""
        if not pricing:
            return "Tarifs sur demande"
        
        formatted_pricing = []
        for vehicle_type, prices in pricing.items():
            if isinstance(prices, dict):
                formatted_pricing.append(f"• {vehicle_type.title()} :")
                for fuel_type, price in prices.items():
                    formatted_pricing.append(f"  - {fuel_type.title()} : {price}€")
            else:
                formatted_pricing.append(f"• {vehicle_type.title()} : {prices}€")
        
        return "\n".join(formatted_pricing) if formatted_pricing else "Tarifs sur demande"
    
    def _format_service_options(self, center_data: Dict[str, Any]) -> str:
        """Formate les options de service"""
        options = []
        
        if center_data.get('allow_early_drop_off'):
            options.append("• Dépôt du véhicule en début de journée : OUI")
        else:
            options.append("• Dépôt du véhicule en début de journée : NON")
        
        if center_data.get('allow_previous_day_drop_off'):
            options.append("• Dépôt du véhicule la veille : OUI")
        else:
            options.append("• Dépôt du véhicule la veille : NON")
        
        if center_data.get('allow_late_pickup'):
            options.append("• Récupération en fin de journée : OUI")
        else:
            options.append("• Récupération en fin de journée : NON")
        
        if center_data.get('allow_next_day_pickup'):
            options.append("• Récupération le lendemain : OUI")
        else:
            options.append("• Récupération le lendemain : NON")
        
        if center_data.get('client_can_wait'):
            options.append("• Attente sur place pendant le contrôle : OUI")
        else:
            options.append("• Attente sur place pendant le contrôle : NON")
        
        return "\n".join(options)
    
    def _load_qa_database(self) -> str:
        """Charge la base de questions/réponses sur le contrôle technique"""
        return """
**Questions fréquentes sur le contrôle technique :**

Q: Quels documents dois-je apporter ?
R: Vous devez apporter la carte grise du véhicule (certificat d'immatriculation) et, si c'est une contre-visite, le rapport de contrôle précédent.

Q: Que se passe-t-il si mon véhicule ne passe pas le contrôle ?
R: Selon les défaillances constatées, vous aurez soit une contre-visite obligatoire dans les 2 mois, soit une interdiction de circuler immédiate pour les défaillances critiques.

Q: À quelle fréquence dois-je faire le contrôle technique ?
R: Tous les 2 ans pour les véhicules de plus de 4 ans, et tous les ans pour les véhicules de plus de 10 ans ou les véhicules utilitaires.

Q: Combien coûte un contrôle technique ?
R: Les tarifs varient selon le centre et le type de véhicule. Consultez notre grille tarifaire pour connaître les prix exacts.
"""

# Exemple d'utilisation
def example_usage():
    """Exemple d'utilisation du générateur de prompt"""
    
    # Données d'exemple d'un centre
    center_data = {
        "average_control_duration": 50,
        "opening_hours": {
            "monday": {"morning_start": "08:00", "morning_end": "12:00", "afternoon_start": "13:30", "afternoon_end": "18:30", "closed": False},
            "tuesday": {"morning_start": "08:00", "morning_end": "12:00", "afternoon_start": "13:30", "afternoon_end": "18:30", "closed": False},
            "wednesday": {"morning_start": "08:00", "morning_end": "12:00", "afternoon_start": "13:30", "afternoon_end": "18:30", "closed": False},
            "thursday": {"morning_start": "08:00", "morning_end": "12:00", "afternoon_start": "13:30", "afternoon_end": "18:30", "closed": False},
            "friday": {"morning_start": "08:00", "morning_end": "12:00", "afternoon_start": "13:30", "afternoon_end": "18:30", "closed": False},
            "saturday": {"morning_start": "08:00", "morning_end": "12:00", "afternoon_start": "13:30", "afternoon_end": "18:00", "closed": False},
            "sunday": {"closed": True}
        },
        "pricing_grid": {
            "Voiture_Particuliere": {"Essence": 78, "Diesel": 85, "Hybride": 85, "Electrique": 75},
            "Utilitaire_Leger": {"Essence": 95, "Diesel": 105},
            "Camping_Car": {"Essence": 125, "Diesel": 135},
            "Moto": {"Essence": 45}
        },
        "allow_early_drop_off": True,
        "allow_previous_day_drop_off": False,
        "allow_late_pickup": True,
        "allow_next_day_pickup": True,
        "client_can_wait": True,
        "payment_methods": ["Espèces", "CB", "Chèque", "Virement"],
        "calendar_url": "https://calendly.com/controle-auto-plus-villejuif",
        "phone_number": "01 45 78 92 34"
    }
    
    generator = PromptGenerator()
    prompt = generator.generate_center_prompt(center_data)
    
    return prompt

if __name__ == "__main__":
    # Test du générateur
    example_prompt = example_usage()
    print("Prompt généré avec succès!")
    print(f"Longueur: {len(example_prompt)} caractères")