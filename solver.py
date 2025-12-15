import pandas as pd

def process_vacancies(raw_vacancies, station_map, start_code, end_code):
    """
    Filters and enriches vacancy data based on user's journey.
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
            vac_start_dist = station_map.get(vac["From"])
            vac_end_dist = station_map.get(vac["To"])
            
            if vac_start_dist is None or vac_end_dist is None:
                continue

            # Check overlap with user journey
            # We want segments that cover at least SOME part of the journey?
            # Or strictly inside? 
            # Let's say we want any segment that overlaps [start_dist, end_dist]
            
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
        except Exception:
            continue
            
    return processed

def find_seat_chain(processed_vacancies, station_map, start_code, end_code):
    """
    Finds a sequence of vacancies to cover the journey from start to end.
    Uses a Greedy approach: At each step, pick the vacancy that extends the furthest.
    This minimizes the number of swaps (segments).
    """
    try:
        start_dist = station_map[start_code]
        end_dist = station_map[end_code]
    except:
        return None

    current_dist = start_dist
    chain = []
    
    while current_dist < end_dist:
        # Find all options that start at or before current_dist and end after current_dist
        candidates = [
            v for v in processed_vacancies 
            if v['Start_Dist'] <= current_dist and v['End_Dist'] > current_dist
        ]
        
        if not candidates:
            return None # Gap in coverage
            
        # Greedy Choice: Pick the one that reaches the furthest distance
        best_option = max(candidates, key=lambda x: x['End_Dist'])
        
        # If the best option doesn't make progress, we are stuck (shouldn't happen with strict > check)
        if best_option['End_Dist'] <= current_dist:
             return None

        chain.append(best_option)
        current_dist = best_option['End_Dist']
        
    return chain
