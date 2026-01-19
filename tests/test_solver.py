
import sys
import os
import pytest

# Add parent directory to path to import solver
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from solver import process_vacancies, find_all_seat_chains

# Mock Data
MOCK_STATION_MAP = {
    "NDLS": 0,
    "CNB": 400,
    "PRYJ": 600,
    "DDU": 800,
    "PNBE": 1000
}

def test_process_vacancies_basic():
    """Test standard vacancy processing"""
    raw_vacancies = [
        {"Coach": "B1", "Berth": 20, "Type": "UB", "From": "NDLS", "To": "DDU"}
    ]
    
    # User journey: NDLS -> PNBE (0 -> 1000)
    # Vacancy: NDLS -> DDU (0 -> 800) -> Coverage: 800km / 1000km = 80%
    
    result = process_vacancies(raw_vacancies, MOCK_STATION_MAP, "NDLS", "PNBE")
    
    assert len(result) == 1
    assert result[0]["Coach"] == "B1"
    assert result[0]["Coverage_Pct"] == 80.0
    assert result[0]["Distance"] == 800

def test_process_vacancies_filter_ac():
    """Test AC only filter"""
    raw_vacancies = [
        {"Coach": "S1", "Berth": 10, "Type": "SL", "From": "NDLS", "To": "PNBE"}, # Sleeper
        {"Coach": "B1", "Berth": 20, "Type": "UB", "From": "NDLS", "To": "PNBE"}  # AC
    ]
    
    result = process_vacancies(raw_vacancies, MOCK_STATION_MAP, "NDLS", "PNBE", ac_only=True)
    
    assert len(result) == 1
    assert result[0]["Coach"] == "B1"

def test_process_vacancies_no_overlap():
    """Test vacancy clearly outside journey"""
    raw_vacancies = [
        {"Coach": "B1", "Berth": 20, "Type": "UB", "From": "DDU", "To": "PNBE"} # starts late
    ]
    
    # User journey: NDLS -> DDU
    # Vacancy: DDU -> PNBE (No overlap in range [0, 800])
    
    result = process_vacancies(raw_vacancies, MOCK_STATION_MAP, "NDLS", "CNB")
    assert len(result) == 0

def test_find_all_seat_chains_success():
    """Test successful chain finding"""
    # Chain: B1 (NDLS->CNB) + B2 (CNB->PNBE)
    vacancies = [
        {"Coach": "B1", "Berth": 1, "Type": "LB", "From": "NDLS", "To": "CNB", "Start_Dist": 0, "End_Dist": 400},
        {"Coach": "B2", "Berth": 2, "Type": "LB", "From": "CNB", "To": "PNBE", "Start_Dist": 400, "End_Dist": 1000}
    ]
    
    chains = find_all_seat_chains(vacancies, MOCK_STATION_MAP, "NDLS", "PNBE")
    
    assert len(chains) >= 1
    assert len(chains[0]) == 2
    assert chains[0][0]["Coach"] == "B1"
    assert chains[0][1]["Coach"] == "B2"

def test_find_all_seat_chains_broken():
    """Test broken chain (gap in middle)"""
    # Chain: B1 (NDLS->CNB) ... gap ... B2 (DDU->PNBE)
    vacancies = [
        {"Coach": "B1", "Berth": 1, "Type": "LB", "From": "NDLS", "To": "CNB", "Start_Dist": 0, "End_Dist": 400},
        {"Coach": "B2", "Berth": 2, "Type": "LB", "From": "DDU", "To": "PNBE", "Start_Dist": 800, "End_Dist": 1000}
    ]
    
    chains = find_all_seat_chains(vacancies, MOCK_STATION_MAP, "NDLS", "PNBE")
    assert len(chains) == 0
