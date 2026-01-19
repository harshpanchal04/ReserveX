import pandas as pd

def process_vacancies(raw_vacancies, station_map, start_code, end_code, berth_preferences=None, ac_only=False):
    """
    Filters and enriches vacancy data based on user's journey and preferences.
    berth_preferences: List of allowed berth codes (e.g., ['LB', 'SL']). If None/Empty, allow all.
    ac_only: If True, only allow coaches that are NOT Sleeper (S) or General/2S (D).
    """
    processed = []
    
    # Get distances for user journey
    try:
        start_dist = station_map[start_code]
        end_dist = station_map[end_code]
    except KeyError:
        return [] # Invalid stations

    # Ensure direction is valid
    if start_dist >= end_dist:
        return []

    for vac in raw_vacancies:
        try:
            # 1. Berth Type Filter
            if berth_preferences and vac.get("Type") not in berth_preferences:
                continue

            # 2. AC Only Filter
            # AC Coaches usually start with B (3A), A (2A/1A), H (1A), M (3E), C (CC), E (Exec)
            # Non-AC are S (Sleeper), D (2S/General), GS (General)
            if ac_only:
                coach = vac.get("Coach", "").upper()
                if coach.startswith("S") or coach.startswith("D") or coach.startswith("G"):
                    # Edge case: S1, S2... are Sleeper. 
                    # But sometimes special trains have different codes. 
                    # For standard IRCTC, S=Sleeper.
                    continue

            vac_start_dist = station_map.get(vac["From"])
            vac_end_dist = station_map.get(vac["To"])
            
            if vac_start_dist is None or vac_end_dist is None:
                continue

            # Check overlap with user journey
            overlap_start = max(start_dist, vac_start_dist)
            overlap_end = min(end_dist, vac_end_dist)
            
            if overlap_start < overlap_end:
                # Calculate coverage within the user's requested journey
                coverage_dist = overlap_end - overlap_start
                total_journey_dist = end_dist - start_dist
                coverage_pct = (coverage_dist / total_journey_dist) * 100
                
                processed.append({
                    "Coach": vac["Coach"],
                    "Berth": vac["Berth"],
                    "Type": vac["Type"],
                    "From": vac["From"],
                    "To": vac["To"],
                    "Distance": vac_end_dist - vac_start_dist, # Total length of this seat's vacancy
                    "Coverage_Km": coverage_dist,
                    "Coverage_Pct": round(coverage_pct, 1),
                    "Start_Dist": vac_start_dist,
                    "End_Dist": vac_end_dist
                })
        except Exception as e:
            # Log the error but continue processing other vacancies
            import logging
            logging.error(f"Error processing vacancy: {e}")
            continue
            
    return processed

def find_all_seat_chains(vacancies, station_map, start_code, end_code, limit=5):
    """
    Finds multiple valid seat chains to cover the journey.
    Returns a list of chains (each chain is a list of vacancy dicts).
    """
    try:
        start_dist = station_map[start_code]
        end_dist = station_map[end_code]
    except KeyError:
        return []

    # Filter relevant vacancies
    relevant = [v for v in vacancies if v['End_Dist'] > start_dist and v['Start_Dist'] < end_dist]
    
    # Identify potential starting seats (must cover the start station)
    # A seat covers start if Start_Dist <= user_start and End_Dist > user_start
    starting_seats = [v for v in relevant if v['Start_Dist'] <= start_dist and v['End_Dist'] > start_dist]
    
    # Sort starting seats by how far they go (greedy preference)
    starting_seats.sort(key=lambda x: x['End_Dist'], reverse=True)
    
    valid_chains = []
    seen_chains = set() # To avoid duplicates
    
    for first_seat in starting_seats:
        chain = [first_seat]
        current_seat = first_seat
        
        while current_seat['End_Dist'] < end_dist:
            # Find next seat that overlaps/connects and extends further
            # Overlap requirement: Next Start <= Current End
            # Extension requirement: Next End > Current End
            candidates = [
                v for v in relevant 
                if v['Start_Dist'] <= current_seat['End_Dist'] 
                and v['End_Dist'] > current_seat['End_Dist']
            ]
            
            if not candidates:
                break # Dead end
            
            # Greedy: Pick the one that extends the furthest
            best_next = max(candidates, key=lambda x: x['End_Dist'])
            chain.append(best_next)
            current_seat = best_next
            
        # Check if chain successfully reached the destination
        if current_seat['End_Dist'] >= end_dist:
            # Create a signature tuple to check for duplicates
            chain_sig = tuple((s['Coach'], s['Berth']) for s in chain)
            if chain_sig not in seen_chains:
                valid_chains.append(chain)
                seen_chains.add(chain_sig)
        
        if len(valid_chains) >= limit:
            break
            
    return valid_chains
