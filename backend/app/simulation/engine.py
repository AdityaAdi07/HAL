import simpy
import random
import datetime

class SimEngine:
    def __init__(self, seed: int = 42):
        self.env = simpy.Environment()
        self.seed = seed
        random.seed(seed)
        self.events_generated = []
        self.current_time = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
        
    def log_event(self, unit_id: str, event_type: str, offset_hours: float):
        ts = self.current_time + datetime.timedelta(hours=offset_hours)
        self.events_generated.append({
            "component_unit_id": unit_id,
            "event_type": event_type,
            "ts": ts,
            "data_source": "SYNTHETIC"
        })
        
    def simulate_unit(self, unit_id: str, expected_h: float):
        # READY -> START -> COMPLETE
        self.log_event(unit_id, "READY", self.env.now)
        yield self.env.timeout(0.5) # Wait for worker/workstation
        
        self.log_event(unit_id, "START", self.env.now)
        
        # Add noise
        noise = random.uniform(-0.1, 0.1) * expected_h
        duration = expected_h + noise
        yield self.env.timeout(duration)
        
        self.log_event(unit_id, "COMPLETE", self.env.now)
        
    def run(self, units: list, duration_limit: int):
        for unit in units:
            self.env.process(self.simulate_unit(unit["id"], unit["expected_h"]))
        self.env.run(until=duration_limit)
        return self.events_generated
