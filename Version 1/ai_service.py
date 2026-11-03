import time
import random

class AICategorizationService:
    """
    Simulates remote AI categorization (AIR-01, AIR-02, NFR-03).
    Categories: Respiratory, Digestive, Musculoskeletal, General/Other
    """
    CATEGORIES = ['Respiratory', 'Digestive', 'Musculoskeletal', 'General/Other']

    def __init__(self, simulate_network_delay: float = 0.5, simulate_failure_rate: float = 0.15):
        self.delay = simulate_network_delay
        self.failure_rate = simulate_failure_rate

    def categorize_note(self, note_text: str) -> dict:
        """
        Sends text to AI endpoint. Returns prediction dict or fallback response.
        Enforces a 2-second timeout window.
        """
        start_time = time.time()
        
        # Simulate network or processing latency
        time.sleep(self.delay)
        
        # Timeout simulation (> 2.0s per AIR-02)
        if (time.time() - start_time) > 2.0:
            return {"status": "TIMEOUT", "suggested_category": None, "confidence": 0.0}

        # Failure/Unreachable service simulation
        if random.random() < self.failure_rate:
            return {"status": "UNAVAILABLE", "suggested_category": None, "confidence": 0.0}

        # Simulated NLP prediction heuristics
        text_lower = note_text.lower()
        if any(w in text_lower for w in ["cough", "lung", "breath", "wheezing", "asthma"]):
            pred = "Respiratory"
            conf = 0.88
        elif any(w in text_lower for w in ["stomach", "nausea", "vomit", "abdomen", "acid"]):
            pred = "Digestive"
            conf = 0.82
        elif any(w in text_lower for w in ["knee", "bone", "joint", "back pain", "fracture", "sprain"]):
            pred = "Musculoskeletal"
            conf = 0.85
        else:
            pred = "General/Other"
            conf = 0.55  # Below 0.60 threshold to test fallback trigger

        # Confidence threshold check (0.60 per requirements)
        if conf < 0.60:
            return {"status": "LOW_CONFIDENCE", "suggested_category": pred, "confidence": conf}

        return {"status": "SUCCESS", "suggested_category": pred, "confidence": conf}