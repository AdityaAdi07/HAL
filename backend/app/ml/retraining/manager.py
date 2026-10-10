class ModelManager:
    def __init__(self):
        self.models = {
            "CHAMPION": "v1.0",
            "CHALLENGER": None,
            "PREVIOUS": None
        }
        self.status = "HEALTHY"
        
    def evaluate_challenger(self, challenger_metrics: dict, champion_metrics: dict, overload_metrics: dict):
        """
        Evaluate if Challenger beats Champion. 
        Rule: "A challenger that wins overall but regresses on OVERLOAD segment or bottleneck dept must not auto-promote."
        """
        win_overall = challenger_metrics["mae"] < champion_metrics["mae"]
        regress_overload = overload_metrics["challenger_mae"] > overload_metrics["champion_mae"]
        
        if win_overall and not regress_overload:
            return "PROMOTE"
        elif win_overall and regress_overload:
            return "REJECT_DUE_TO_OVERLOAD_REGRESSION"
        else:
            return "REJECT_OVERALL"
            
    def promote_challenger(self, challenger_id: str):
        self.models["PREVIOUS"] = self.models["CHAMPION"]
        self.models["CHAMPION"] = challenger_id
        self.models["CHALLENGER"] = None
        self.status = "PROMOTED"
        
    def rollback(self):
        if self.models["PREVIOUS"]:
            self.models["CHAMPION"] = self.models["PREVIOUS"]
            self.models["PREVIOUS"] = None
            self.status = "ROLLED_BACK"
            return True
        return False
