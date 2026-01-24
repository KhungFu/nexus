# -*- coding: utf-8 -*-
import google.generativeai as genai
import os
from logger import nexus_logger
class GeminiAnalyst:
    def __init__(self):
        self.keys = [os.getenv(f"GEMINI_API_KEY_{i}") for i in range(1, 4) if os.getenv(f"GEMINI_API_KEY_{i}")]
    def get_analysis(self, prompt):
        try:
            if not self.keys: return "API KEY EKSIK"
            genai.configure(api_key=self.keys[0])
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            nexus_logger.log_error("GEMINI_AI", e)
            return "Analiz su an yapilamiyor."
