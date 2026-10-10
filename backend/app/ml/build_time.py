import lightgbm as lgb
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple

class BuildTimePredictor:
    def __init__(self):
        self.models = {}
        self.alphas = [0.5, 0.75, 0.9]
        self.is_trained = False
        
    def _prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract features per Phase 7 requirements."""
        # Dummy feature extraction for the structure
        features = ["std_hours", "complexity", "crew_size", "skill_level", "rework_history"]
        # Ensure all columns exist, fill with 0 if not
        for f in features:
            if f not in df.columns:
                df[f] = 1.0 # Default value
        return df[features]
        
    def train(self, df_train: pd.DataFrame, df_val: pd.DataFrame):
        X_train = self._prepare_features(df_train)
        y_train = df_train["actual_hours"]
        
        X_val = self._prepare_features(df_val)
        y_val = df_val["actual_hours"]
        
        for alpha in self.alphas:
            model = lgb.LGBMRegressor(
                objective="quantile",
                alpha=alpha,
                n_estimators=100,
                learning_rate=0.1,
                random_state=42,
                verbosity=-1
            )
            model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                callbacks=[lgb.early_stopping(stopping_rounds=10)]
            )
            self.models[alpha] = model
            
        self.is_trained = True
        
    def baseline_predict(self, row: pd.Series) -> Tuple[float, float, float]:
        """Phase 5 baseline predictor"""
        std_h = row.get("std_hours", 1.0)
        complexity = row.get("complexity", 1.0)
        
        expected = std_h * complexity
        # Empirical quantiles from baseline
        p75 = expected * 1.15
        p90 = expected * 1.30
        return expected, p75, p90
        
    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self.is_trained:
            # Cold start fallback
            preds = df.apply(self.baseline_predict, axis=1, result_type='expand')
            preds.columns = ['p50', 'p75', 'p90']
            preds['fallback_used'] = True
            return preds
            
        X = self._prepare_features(df)
        
        preds = pd.DataFrame(index=df.index)
        for alpha in self.alphas:
            preds[f"p_{alpha}"] = self.models[alpha].predict(X)
            
        # Enforce monotonicity: P50 <= P75 <= P90
        preds['p50'] = preds['p_0.5']
        preds['p75'] = np.maximum(preds['p50'], preds['p_0.75'])
        preds['p90'] = np.maximum(preds['p75'], preds['p_0.9'])
        
        preds['fallback_used'] = False
        
        return preds[['p50', 'p75', 'p90', 'fallback_used']]

    def evaluate(self, df_test: pd.DataFrame) -> Dict[str, float]:
        """Calculate metrics on holdout set to check if beats baseline."""
        if not self.is_trained:
            return {"beats_baseline": False}
            
        preds = self.predict(df_test)
        y_true = df_test["actual_hours"]
        
        baseline_preds = df_test.apply(self.baseline_predict, axis=1, result_type='expand')
        
        ml_mae = np.mean(np.abs(preds['p50'] - y_true))
        baseline_mae = np.mean(np.abs(baseline_preds[0] - y_true))
        
        # P90 coverage
        ml_p90_coverage = np.mean(y_true <= preds['p90'])
        
        return {
            "ml_mae": float(ml_mae),
            "baseline_mae": float(baseline_mae),
            "beats_baseline": bool(ml_mae < baseline_mae),
            "p90_coverage": float(ml_p90_coverage)
        }
