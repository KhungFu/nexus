# -*- coding: utf-8 -*-
from google import genai
import os

class GeminiAnalyst:
    def __init__(self):
        # Deine 3 Keys für die Rotation
        self.api_keys = [
            os.getenv("GEMINI_API_KEY_1"),
            os.getenv("GEMINI_API_KEY_2"),
            os.getenv("GEMINI_API_KEY_3")
        ]
        # Exakt das Modell, das du angefordert hast
        self.model_id = "gemini-3-flash-preview" 

    def get_analysis(self, prompt):
        """Analysiert den Markt mit Gemini 3 Flash Preview."""
        for i, key in enumerate(self.api_keys):
            if not key:
                continue
            try:
                # Initialisierung nach der neuen Dokumentation
                client = genai.Client(api_key=key)
                
                # Aufruf gemäß Gemini 3 Syntax
                response = client.models.generate_content(
                    model=self.model_id,
                    contents=prompt
                )
                
                if response and response.text:
                    return response.text
                
            except Exception as e:
                print(f"⚠️ Key {i+1} (Gemini 3) fehlgeschlagen: {e}")
                continue # Nächsten Key ausprobieren
        
        # Falls kein Key funktioniert -> Trigger für den CEO Not-Stopp
        return "Analiz su an yapilamiyor."

    def load_mentor_instruction(self):
        """Lädt deine Strategie aus der mentor_name.txt."""
        file_path = "mentor_name.txt"
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        return "Handle nach der mentor_name.txt Doktrin."
