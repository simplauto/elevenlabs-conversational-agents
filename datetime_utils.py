from datetime import datetime, timedelta
import pytz
from typing import Dict, Any

def get_paris_datetime() -> datetime:
    """Retourne la date et heure actuelle à Paris"""
    paris_tz = pytz.timezone('Europe/Paris')
    return datetime.now(paris_tz)

def format_current_context() -> str:
    """Formate le contexte temporel complet pour l'agent"""
    now = get_paris_datetime()
    
    # Calcul des dates de référence
    yesterday = now - timedelta(days=1)
    day_before_yesterday = now - timedelta(days=2)
    tomorrow = now + timedelta(days=1)
    day_after_tomorrow = now + timedelta(days=2)
    
    # Calcul du prochain lundi (semaine prochaine)
    days_until_next_monday = (7 - now.weekday()) % 7
    if days_until_next_monday == 0:  # Si c'est lundi, prendre le lundi suivant
        days_until_next_monday = 7
    next_monday = now + timedelta(days=days_until_next_monday)
    
    # Dans 2 semaines = lundi suivant le prochain lundi
    monday_in_2_weeks = next_monday + timedelta(weeks=1)
    
    # Mois prochain (du 1er au dernier jour)
    if now.month == 12:
        next_month_start = now.replace(year=now.year + 1, month=1, day=1)
        next_month_end = now.replace(year=now.year + 1, month=1, day=31)
    else:
        next_month_start = now.replace(month=now.month + 1, day=1)
        # Dernier jour du mois prochain
        if now.month + 1 == 12:
            next_month_end = now.replace(year=now.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            next_month_end = now.replace(month=now.month + 2, day=1) - timedelta(days=1)
    
    context = f"""
CONTEXTE TEMPOREL ACTUEL (Heure de Paris, France) :

📅 MAINTENANT : {now.strftime('%A %d %B %Y à %H:%M')} (UTC+{now.strftime('%z')[1:3]}:{now.strftime('%z')[3:5]})

📋 DATES DE RÉFÉRENCE :
• Avant-hier : {day_before_yesterday.strftime('%A %d %B %Y')}
• Hier : {yesterday.strftime('%A %d %B %Y')}
• Aujourd'hui : {now.strftime('%A %d %B %Y')}
• Ce matin : {now.strftime('%A %d %B %Y')} matin (08h00-12h00)
• Cet après-midi : {now.strftime('%A %d %B %Y')} après-midi (13h00-18h00)
• Demain : {tomorrow.strftime('%A %d %B %Y')}
• Après-demain : {day_after_tomorrow.strftime('%A %d %B %Y')}
• La semaine prochaine : du {next_monday.strftime('%A %d %B %Y')} au {(next_monday + timedelta(days=6)).strftime('%A %d %B %Y')}
• Dans 2 semaines : du {monday_in_2_weeks.strftime('%A %d %B %Y')} au {(monday_in_2_weeks + timedelta(days=6)).strftime('%A %d %B %Y')}
• Le mois prochain : du {next_month_start.strftime('%d %B %Y')} au {next_month_end.strftime('%d %B %Y')}

⏰ POUR LES CRÉNEAUX HORAIRES :
• Matin : 08h00-12h00
• Après-midi : 13h00-18h00  
• Soirée : 18h00-21h00

🗓️ FORMATS À UTILISER POUR L'API :
• Date ISO : {now.strftime('%Y-%m-%d')}
• DateTime ISO : {now.isoformat()}
• Timestamp Unix : {int(now.timestamp())}

IMPORTANT : Utilisez ces informations pour interpréter correctement les demandes temporelles des utilisateurs et interroger l'API de réservation avec les bonnes dates.
"""
    
    return context

def get_conversation_metadata() -> Dict[str, Any]:
    """Retourne les métadonnées de conversation avec contexte temporel"""
    now = get_paris_datetime()
    
    return {
        "timestamp": now.isoformat(),
        "timezone": "Europe/Paris",
        "locale": "fr-FR",
        "current_date": now.strftime('%Y-%m-%d'),
        "current_time": now.strftime('%H:%M:%S'),
        "day_of_week": now.strftime('%A'),
        "context": format_current_context()
    }

def calculate_relative_date(reference: str) -> str:
    """Calcule une date relative à partir d'une référence textuelle"""
    now = get_paris_datetime()
    
    # Calcul du prochain lundi
    days_until_next_monday = (7 - now.weekday()) % 7
    if days_until_next_monday == 0:  # Si c'est lundi, prendre le lundi suivant
        days_until_next_monday = 7
    next_monday = now + timedelta(days=days_until_next_monday)
    
    relative_dates = {
        "avant-hier": now - timedelta(days=2),
        "hier": now - timedelta(days=1),
        "aujourd'hui": now,
        "ce matin": now,  # même jour, créneau matin
        "cet après-midi": now,  # même jour, créneau après-midi
        "demain": now + timedelta(days=1),
        "après-demain": now + timedelta(days=2),
        "la semaine prochaine": next_monday,
        "semaine prochaine": next_monday,
    }
    
    if reference.lower() in relative_dates:
        return relative_dates[reference.lower()].strftime('%Y-%m-%d')
    
    # Gestion des semaines avec nombres
    if "semaine" in reference.lower():
        import re
        match = re.search(r'(\d+)', reference)
        if match:
            weeks = int(match.group(1))
            # "Dans X semaines" = lundi de la Xème semaine à partir du prochain lundi
            target_date = next_monday + timedelta(weeks=weeks-1)
            return target_date.strftime('%Y-%m-%d')
        else:
            # "la semaine prochaine" déjà géré au-dessus
            return next_monday.strftime('%Y-%m-%d')
    
    # Gestion des mois
    if "mois" in reference.lower():
        if "prochain" in reference.lower():
            months = 1
        else:
            import re
            match = re.search(r'(\d+)', reference)
            months = int(match.group(1)) if match else 1
        
        target_month = now.month + months
        target_year = now.year
        while target_month > 12:
            target_month -= 12
            target_year += 1
            
        target_date = now.replace(month=target_month, year=target_year)
        return target_date.strftime('%Y-%m-%d')
    
    return now.strftime('%Y-%m-%d')

def get_week_range(monday_date: datetime) -> tuple:
    """Retourne le lundi et dimanche d'une semaine donnée"""
    sunday = monday_date + timedelta(days=6)
    return monday_date, sunday

def get_month_range(year: int, month: int) -> tuple:
    """Retourne le premier et dernier jour d'un mois"""
    first_day = datetime(year, month, 1)
    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)
    
    # Applique le timezone Paris
    paris_tz = pytz.timezone('Europe/Paris')
    first_day = paris_tz.localize(first_day)
    last_day = paris_tz.localize(last_day)
    
    return first_day, last_day

def calculate_relative_date_range(reference: str) -> str:
    """Calcule une plage de dates relative (pour semaines et mois)"""
    now = get_paris_datetime()
    
    # Calcul du prochain lundi
    days_until_next_monday = (7 - now.weekday()) % 7
    if days_until_next_monday == 0:  # Si c'est lundi, prendre le lundi suivant
        days_until_next_monday = 7
    next_monday = now + timedelta(days=days_until_next_monday)
    
    reference_lower = reference.lower()
    
    # Gestion des semaines
    if "semaine" in reference_lower:
        if "prochaine" in reference_lower:
            monday, sunday = get_week_range(next_monday)
            return f"{monday.strftime('%Y-%m-%d')} au {sunday.strftime('%Y-%m-%d')}"
        
        # "Dans X semaines"
        import re
        match = re.search(r'(\d+)', reference)
        if match:
            weeks = int(match.group(1))
            target_monday = next_monday + timedelta(weeks=weeks-1)
            monday, sunday = get_week_range(target_monday)
            return f"{monday.strftime('%Y-%m-%d')} au {sunday.strftime('%Y-%m-%d')}"
    
    # Gestion des mois
    if "mois" in reference_lower:
        if "prochain" in reference_lower:
            if now.month == 12:
                target_year, target_month = now.year + 1, 1
            else:
                target_year, target_month = now.year, now.month + 1
        else:
            import re
            match = re.search(r'(\d+)', reference)
            months = int(match.group(1)) if match else 1
            
            target_month = now.month + months
            target_year = now.year
            while target_month > 12:
                target_month -= 12
                target_year += 1
        
        first_day, last_day = get_month_range(target_year, target_month)
        return f"{first_day.strftime('%Y-%m-%d')} au {last_day.strftime('%Y-%m-%d')}"
    
    # Pour les autres références, retourner une date simple
    return calculate_relative_date(reference)