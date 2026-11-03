import time
import random
from concurrent.futures import ThreadPoolExecutor, TimeoutError

class AICategorizationService:
    """
    Simulates remote AI categorization service (AIR-01, AIR-02, NFR-03).
    Implements preemptive 2.0-second timeout enforcement.
    """
    CATEGORIES = ['Respiratory', 'Digestive', 'Musculoskeletal', 'General/Other']

    def __init__(self, delay: float = 0.5, failure_rate: float = 0.10):
        self.delay = delay
        self.failure_rate = failure_rate

    def _execute_prediction(self, note_text: str) -> dict:
        # Simulate network or compute delay
        time.sleep(self.delay)

        # Simulate service drop/unavailability
        if random.random() < self.failure_rate:
            return {"status": "UNAVAILABLE", "suggested_category": None, "confidence": 0.0}

        text_lower = note_text.lower()
        if any(w in text_lower for w in ["cough", "lung", "breath", "wheezing", "asthma", "chest"]):
            pred, conf = "Respiratory", 0.88
        elif any(w in text_lower for w in ["stomach", "nausea", "vomit", "abdomen", "acid", "cramp"]):
            pred, conf = "Digestive", 0.82
        elif any(w in text_lower for w in ["knee", "bone", "joint", "back pain", "fracture", "sprain"]):
            pred, conf = "Musculoskeletal", 0.85
        else:
            pred, conf = "General/Other", 0.55

        # Check confidence against the 0.60 threshold
        if conf < 0.60:
            return {"status": "LOW_CONFIDENCE", "suggested_category": pred, "confidence": conf}

        return {"status": "SUCCESS", "suggested_category": pred, "confidence": conf}

    def categorize_note(self, note_text: str) -> dict:
        """Enforces a strict 2.0-second preemptive cutoff using ThreadPoolExecutor."""
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._execute_prediction, note_text)
            try:
                return future.result(timeout=2.0)
            except TimeoutError:
                return {"status": "TIMEOUT", "suggested_category": None, "confidence": 0.0}