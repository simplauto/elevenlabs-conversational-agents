from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
from datetime import datetime, timedelta
import asyncio

app = FastAPI(title="API Backend Centre Contrôle Technique")
security = HTTPBearer()

# Models Pydantic
class SlotRequest(BaseModel):
    start_date: str
    end_date: Optional[str] = None
    vehicle_type: str = "voiture_particuliere"
    preferred_time: str = "any"

class ClientInfo(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: Optional[str] = None
    vehicle_brand: str
    vehicle_model: str
    license_plate: str

class BookingRequest(BaseModel):
    slot_id: str
    client_info: ClientInfo

class AvailableSlot(BaseModel):
    slot_id: str
    datetime: str
    duration_minutes: int
    price: float
    available: bool = True

# Simulateur de base de données (à remplacer par Supabase)
class MockDatabase:
    """Simulateur de base de données pour l'exemple"""
    
    def __init__(self):
        self.centers = {}
        self.bookings = {}
        self.slots = {}
    
    async def get_center_data(self, center_id: str) -> Dict[str, Any]:
        """Récupère les données d'un centre"""
        # Simulation - en réalité, requête Supabase
        return {
            "id": center_id,
            "center_name": "Centre de Contrôle Technique",
            "opening_hours": {
                "monday": {"morning_start": "08:00", "morning_end": "12:00", "afternoon_start": "13:30", "afternoon_end": "18:30", "closed": False},
                # ... autres jours
            },
            "pricing_grid": {
                "voiture_particuliere": {"essence": 78, "diesel": 85},
                "utilitaire": {"essence": 95, "diesel": 105}
            },
            "average_control_duration": 50
        }
    
    async def get_available_slots(
        self, 
        center_id: str, 
        start_date: str, 
        end_date: str,
        vehicle_type: str,
        preferred_time: str
    ) -> List[AvailableSlot]:
        """Récupère les créneaux réels depuis l'API Simplauto"""
        
        import httpx
        
        # Mapping des types de véhicules
        vehicle_type_mapping = {
            "voiture_particuliere": {"vehicle_type": 6, "vehicle_engine": 1},  # Voiture Essence par défaut
            "utilitaire": {"vehicle_type": 2, "vehicle_engine": 2},  # Utilitaire Diesel
            "moto": {"vehicle_type": 9, "vehicle_engine": 1},  # Moto Essence
            "camping_car": {"vehicle_type": 4, "vehicle_engine": 2}  # Camping-car Diesel
        }
        
        # Récupérer les paramètres pour l'API Simplauto
        vehicle_params = vehicle_type_mapping.get(vehicle_type, {"vehicle_type": 6, "vehicle_engine": 1})
        
        # URL et headers pour l'API Simplauto
        simplauto_url = "https://www.simplauto.com/private-api/slots/"
        headers = {
            "accept": "application/json",
            "Authorization": "Bearer 940c066c0c2d6e1f0d302a5b44f77f8af7b236b8"
        }
        
        params = {
            "center_id": center_id,
            "is_available": True,
            "vehicle_engine": vehicle_params["vehicle_engine"],
            "vehicle_type": vehicle_params["vehicle_type"]
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(simplauto_url, headers=headers, params=params, timeout=10)
                response.raise_for_status()
                real_slots_data = response.json()
            
            # Convertir vers notre format
            slots = []
            for slot_data in real_slots_data:
                if slot_data.get("is_available", True):
                    # Convertir starts_at vers datetime
                    starts_at = slot_data.get("starts_at")
                    if starts_at:
                        slots.append(AvailableSlot(
                            slot_id=slot_data.get("id", "unknown"),
                            datetime=starts_at,
                            duration_minutes=50,  # Valeur par défaut
                            price=slot_data.get("price"),
                            available=slot_data.get("is_available", True)
                        ))
            
            # Filtrer par preferred_time si nécessaire
            if preferred_time != "any":
                filtered_slots = []
                for slot in slots:
                    slot_dt = datetime.fromisoformat(slot.datetime.replace('+02:00', ''))
                    hour = slot_dt.hour
                    
                    if preferred_time == "morning" and 8 <= hour <= 12:
                        filtered_slots.append(slot)
                    elif preferred_time == "afternoon" and 13 <= hour <= 18:
                        filtered_slots.append(slot)
                
                slots = filtered_slots
            
            return slots[:10]  # Limiter à 10 créneaux
            
        except Exception as e:
            print(f"Erreur appel API Simplauto: {e}")
            # Fallback: retourner des créneaux vides
            return []
    
    async def create_booking(
        self, 
        center_id: str, 
        slot_id: str, 
        client_info: ClientInfo
    ) -> Dict[str, Any]:
        """Crée une réservation"""
        
        booking_id = f"booking_{len(self.bookings) + 1}"
        booking = {
            "id": booking_id,
            "center_id": center_id,
            "slot_id": slot_id,
            "client_info": client_info.dict(),
            "status": "confirmed",
            "created_at": datetime.now().isoformat()
        }
        
        self.bookings[booking_id] = booking
        return booking

# Instance de la base de données simulée
db = MockDatabase()

# Endpoints webhook pour ElevenLabs
@app.post("/webhook/elevenlabs/{center_id}/get_slots")
async def get_slots_webhook(center_id: str, request: SlotRequest):
    """
    Webhook appelé par ElevenLabs pour récupérer les créneaux disponibles
    """
    try:
        # Calcul de la date de fin si non fournie
        end_date = request.end_date
        if not end_date:
            start = datetime.fromisoformat(request.start_date)
            end_date = (start + timedelta(days=14)).strftime("%Y-%m-%d")
        
        # Récupération des créneaux
        slots = await db.get_available_slots(
            center_id=center_id,
            start_date=request.start_date,
            end_date=end_date,
            vehicle_type=request.vehicle_type,
            preferred_time=request.preferred_time
        )
        
        # Format de réponse pour ElevenLabs
        if not slots:
            return {
                "message": "Aucun créneau disponible pour cette période",
                "slots": [],
                "suggestion": "Essayez une autre période ou appelez directement le centre"
            }
        
        # Formatage des créneaux avec jour français et labels relatifs
        from datetime_utils import get_paris_datetime
        
        formatted_slots = []
        day_names = {
            0: "lundi", 1: "mardi", 2: "mercredi", 3: "jeudi", 
            4: "vendredi", 5: "samedi", 6: "dimanche"
        }
        month_names = {
            1: "janvier", 2: "février", 3: "mars", 4: "avril", 5: "mai", 6: "juin",
            7: "juillet", 8: "août", 9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre"
        }
        
        # Date actuelle à Paris
        now_paris = get_paris_datetime()
        today = now_paris.date()
        
        def get_relative_label(slot_date):
            """Calcule le label relatif pour une date"""
            delta = (slot_date - today).days
            slot_weekday = slot_date.weekday()
            today_weekday = today.weekday()
            
            # Cas spéciaux : aujourd'hui, demain, après-demain
            if delta == 0:
                return "aujourd'hui"
            elif delta == 1:
                return "demain"
            elif delta == 2:
                return "après-demain"
            
            # Pour les jours de cette semaine (avant dimanche)
            # Si on est samedi (5) et le créneau est dimanche (6), c'est "demain"
            # Déjà géré par delta == 1
            
            # Semaine prochaine : du lundi prochain au dimanche prochain
            # Calculer le lundi de la semaine prochaine
            if today_weekday == 6:  # Si on est dimanche
                days_until_next_monday = 1
            else:  # Sinon, jours jusqu'au lundi suivant
                days_until_next_monday = 7 - today_weekday
            
            next_monday = today + timedelta(days=days_until_next_monday)
            next_sunday = next_monday + timedelta(days=6)
            
            
            if next_monday <= slot_date <= next_sunday:
                return f"{day_names[slot_weekday]} prochain"
            
            # Si c'est dans la semaine courante mais après après-demain
            if delta <= 7 and delta > 2:
                # Vérifier si c'est cette semaine ou la suivante
                this_week_end = today + timedelta(days=(6 - today_weekday))  # Dimanche de cette semaine
                if slot_date <= this_week_end:
                    return f"ce {day_names[slot_weekday]}"  # "ce jeudi", "ce vendredi"
                else:
                    return f"{day_names[slot_weekday]} prochain"
            
            return None
        
        for slot in slots:
            # Nettoyer le datetime pour parser correctement
            slot_datetime_str = slot.datetime
            if '+02:00' in slot_datetime_str:
                slot_datetime_str = slot_datetime_str.replace('+02:00', '')
            
            slot_dt = datetime.fromisoformat(slot_datetime_str)
            slot_date = slot_dt.date()
            
            day_name = day_names[slot_dt.weekday()]
            month_name = month_names[slot_dt.month]
            
            # Calculer le label relatif
            relative_label = get_relative_label(slot_date)
            
            # Format de base
            base_text = f"{day_name} {slot_dt.day} {month_name} {slot_dt.year} à {slot_dt.strftime('%H:%M')}"
            
            # Format avec label relatif si applicable
            if relative_label:
                if relative_label in ["aujourd'hui", "demain", "après-demain"]:
                    full_text = f"{relative_label} ({day_name} {slot_dt.day} {month_name}) à {slot_dt.strftime('%H:%M')}"
                else:  # "lundi prochain", etc.
                    full_text = f"{relative_label} ({slot_dt.day} {month_name}) à {slot_dt.strftime('%H:%M')}"
            else:
                full_text = base_text
            
            formatted_slots.append({
                "id": slot.slot_id,
                "full_text": full_text,
                "base_text": base_text,
                "relative_label": relative_label,
                "day_name": day_name,
                "date_only": f"{day_name} {slot_dt.day} {month_name}",
                "time_only": slot_dt.strftime("%H:%M"),
                "duration": f"{slot.duration_minutes} minutes",
                "price": f"{slot.price}€"
            })
        
        # Générer les jours manquants avec créneaux vides
        # Créer une structure complète des jours demandés
        start_dt = datetime.fromisoformat(request.start_date)
        end_dt = datetime.fromisoformat(end_date) if end_date else start_dt + timedelta(days=14)
        
        # Grouper les créneaux par date
        slots_by_date = {}
        for slot in formatted_slots:
            slot_datetime_str = slot["id"]  # Utilisons l'ID pour retrouver la date originale
            # Rechercher dans les créneaux originaux pour obtenir la date
            for original_slot in slots:
                if original_slot.slot_id == slot["id"]:
                    clean_datetime = original_slot.datetime.replace('+02:00', '') if '+02:00' in original_slot.datetime else original_slot.datetime
                    slot_date = datetime.fromisoformat(clean_datetime).date()
                    if slot_date not in slots_by_date:
                        slots_by_date[slot_date] = []
                    slots_by_date[slot_date].append(slot)
                    break
        
        # Générer la réponse structurée par jour
        daily_availability = []
        current_date = start_dt.date()
        
        while current_date <= end_dt.date() and len(daily_availability) < 7:  # Limiter à 7 jours
            day_name = day_names[current_date.weekday()]
            month_name = month_names[current_date.month]
            
            # Calculer le label relatif pour ce jour
            relative_label = get_relative_label(current_date)
            
            # Format du jour
            if relative_label:
                if relative_label in ["aujourd'hui", "demain", "après-demain"]:
                    day_display = f"{relative_label} ({day_name} {current_date.day} {month_name})"
                else:
                    day_display = f"{relative_label} ({current_date.day} {month_name})"
            else:
                day_display = f"{day_name} {current_date.day} {month_name}"
            
            # Créneaux pour ce jour
            day_slots = slots_by_date.get(current_date, [])
            
            daily_availability.append({
                "date": current_date.isoformat(),
                "day_display": day_display,
                "relative_label": relative_label,
                "day_name": day_name,
                "slots_count": len(day_slots),
                "slots": day_slots[:3],  # Max 3 créneaux par jour pour la lisibilité
                "is_available": len(day_slots) > 0
            })
            
            current_date += timedelta(days=1)
        
        # Générer le message pour l'agent - Proposer les 2 prochaines demi-journées disponibles
        if formatted_slots:
            # Créer une liste des demi-journées avec disponibilité
            half_days = []
            
            for day in daily_availability:
                if day["is_available"] and day["slots"]:
                    # Séparer les créneaux matin/après-midi pour ce jour
                    morning_slots = []
                    afternoon_slots = []
                    
                    for slot in day["slots"]:
                        hour = int(slot["time_only"].split(":")[0])
                        if hour < 13:  # Avant 13h = matin
                            morning_slots.append(slot)
                        else:  # 13h et après = après-midi
                            afternoon_slots.append(slot)
                    
                    # Ajouter les demi-journées disponibles
                    if morning_slots:
                        half_days.append({
                            "day_display": day["day_display"],
                            "relative_label": day["relative_label"],
                            "period": "matin",
                            "slots": morning_slots,
                            "period_display": f"{day['day_display']} matin"
                        })
                    
                    if afternoon_slots:
                        half_days.append({
                            "day_display": day["day_display"],
                            "relative_label": day["relative_label"],
                            "period": "après-midi",
                            "slots": afternoon_slots,
                            "period_display": f"{day['day_display']} après-midi"
                        })
            
            # Proposer les 2 prochaines demi-journées disponibles
            if len(half_days) >= 2:
                first_half = half_days[0]
                second_half = half_days[1]
                
                # Simplifier l'affichage selon les labels relatifs
                first_display = first_half["period_display"]
                second_display = second_half["period_display"]
                
                # Simplifier pour les expressions courantes
                if first_half["relative_label"] == "demain":
                    first_display = f"demain {first_half['period']}"
                elif first_half["relative_label"] == "aujourd'hui":
                    first_display = f"aujourd'hui {first_half['period']}"
                elif first_half["relative_label"] == "après-demain":
                    first_display = f"après-demain {first_half['period']}"
                
                if second_half["relative_label"] == "demain":
                    second_display = f"demain {second_half['period']}"
                elif second_half["relative_label"] == "aujourd'hui":
                    second_display = f"aujourd'hui {second_half['period']}"
                elif second_half["relative_label"] == "après-demain":
                    second_display = f"après-demain {second_half['period']}"
                
                response_message = f"Je peux vous proposer un créneau {first_display} ou {second_display} si vous le souhaitez."
                
            elif len(half_days) == 1:
                first_half = half_days[0]
                first_display = first_half["period_display"]
                
                if first_half["relative_label"] == "demain":
                    first_display = f"demain {first_half['period']}"
                elif first_half["relative_label"] == "aujourd'hui":
                    first_display = f"aujourd'hui {first_half['period']}"
                elif first_half["relative_label"] == "après-demain":
                    first_display = f"après-demain {first_half['period']}"
                
                response_message = f"Je peux vous proposer un créneau {first_display}."
            else:
                response_message = "Tous les créneaux sont complets pour la période demandée."
        else:
            response_message = "Aucun créneau disponible actuellement."
        
        return {
            "message": response_message,
            "daily_availability": daily_availability,
            "slots": formatted_slots[:5],  # Limiter à 5 pour l'agent  
            "total_available": len(slots),
            "instructions": "Utilisez exactement le texte du message ci-dessus. Si un jour est demandé spécifiquement, consultez daily_availability pour voir s'il est complet."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération créneaux: {str(e)}")

@app.post("/webhook/elevenlabs/{center_id}/book")
async def book_slot_webhook(center_id: str, request: BookingRequest):
    """
    Webhook appelé par ElevenLabs pour réserver un créneau
    """
    try:
        # Validation du créneau
        if not request.slot_id.startswith(f"slot_{center_id}"):
            raise HTTPException(status_code=400, detail="Créneau invalide pour ce centre")
        
        # Création de la réservation
        booking = await db.create_booking(
            center_id=center_id,
            slot_id=request.slot_id,
            client_info=request.client_info
        )
        
        # Extraction des informations du créneau
        slot_parts = request.slot_id.split("_")
        if len(slot_parts) >= 3:
            date_part = slot_parts[2]
            time_part = slot_parts[3]
            
            try:
                slot_dt = datetime.strptime(f"{date_part}_{time_part}", "%Y%m%d_%H%M")
                formatted_date = slot_dt.strftime("%A %d %B %Y à %H:%M")
            except:
                formatted_date = "Date à confirmer"
        else:
            formatted_date = "Date à confirmer"
        
        # TODO: Envoyer email/SMS de confirmation
        # TODO: Notifier le centre
        
        return {
            "message": f"Parfait ! Votre rendez-vous est confirmé pour {formatted_date}",
            "booking_id": booking["id"],
            "client_name": f"{request.client_info.first_name} {request.client_info.last_name}",
            "vehicle": f"{request.client_info.vehicle_brand} {request.client_info.vehicle_model}",
            "license_plate": request.client_info.license_plate,
            "confirmation": "Un email de confirmation vous sera envoyé",
            "reminder": "Pensez à apporter votre carte grise le jour du rendez-vous"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la réservation: {str(e)}")

# Endpoints de gestion pour le site Lovable
@app.post("/api/centers/{center_id}/agent")
async def create_center_agent(center_id: str):
    """
    Crée un agent ElevenLabs pour un nouveau centre
    Appelé après souscription sur le site Lovable
    """
    try:
        from elevenlabs_integration import ElevenLabsIntegration
        
        # 1. Récupérer les données du centre
        center_data = await db.get_center_data(center_id)
        center_data["id"] = center_id
        
        # 2. Créer l'agent ElevenLabs
        elevenlabs = ElevenLabsIntegration(
            api_key=os.getenv("ELEVENLABS_API_KEY")
        )
        
        result = await elevenlabs.create_center_agent(
            center_data=center_data,
            webhook_base_url=os.getenv("WEBHOOK_BASE_URL", "https://votre-api.com")
        )
        
        # 3. TODO: Sauvegarder l'agent_id en base
        # await supabase.update_center(center_id, {"elevenlabs_agent_id": result["agent_id"]})
        
        # 4. TODO: Créer le numéro Twilio
        # twilio_number = await create_twilio_number(result["agent_id"])
        
        return {
            "status": "success",
            "agent_id": result["agent_id"],
            "message": "Agent créé avec succès"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur création agent: {str(e)}")

@app.get("/api/centers/{center_id}/status")
async def get_center_status(center_id: str):
    """Récupère le statut d'un centre"""
    try:
        center_data = await db.get_center_data(center_id)
        return {
            "center_id": center_id,
            "name": center_data.get("center_name", ""),
            "status": "active",  # TODO: récupérer depuis la base
            "agent_id": "agent_xxx",  # TODO: récupérer depuis la base
            "phone_number": "+33XXXXXXXXX"  # TODO: récupérer depuis la base
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail="Centre non trouvé")

# Endpoint de test
@app.get("/test/generate-slots/{center_id}")
async def test_generate_slots(center_id: str):
    """Endpoint de test pour vérifier la génération de créneaux"""
    from datetime import datetime
    
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    slots = await db.get_available_slots(
        center_id=center_id,
        start_date=tomorrow,
        end_date=tomorrow,
        vehicle_type="voiture_particuliere",
        preferred_time="any"
    )
    
    return {"test_slots": [slot.dict() for slot in slots]}

# Endpoint de test avec un vrai center_id
@app.get("/test/real-slots")
async def test_real_slots():
    """Test avec un vrai center_id Simplauto"""
    slots = await db.get_available_slots(
        center_id="c07110e4-7ef8-49ee-9c2b-ab62a106c417",  # Vrai center_id
        start_date="2025-07-27",
        end_date="2025-08-10",
        vehicle_type="voiture_particuliere",
        preferred_time="any"
    )
    
    return {
        "message": "Test avec vrais créneaux Simplauto",
        "slots_count": len(slots),
        "test_slots": [slot.dict() for slot in slots[:5]]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)