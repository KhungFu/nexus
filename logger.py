# -*- coding: utf-8 -*-
import json, datetime, os, traceback
class NexusLogger:
    def __init__(self, log_file="error_log.json"):
        self.log_file = log_file
    def log_error(self, module_name, error_message, extra_data=None):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_detail = traceback.format_exc()
        error_entry = {"timestamp": timestamp, "module": module_name, "error": str(error_message), "detail": error_detail, "context": extra_data if extra_data else "Boardroom"}
        logs = []
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r", encoding="utf-8") as f: logs = json.load(f)
            except: logs = []
        logs.append(error_entry)
        with open(self.log_file, "w", encoding="utf-8") as f: json.dump(logs, f, ensure_ascii=False, indent=4)
nexus_logger = NexusLogger()
