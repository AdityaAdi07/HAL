import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import numpy as np

class WorkloadForecaster:
    def __init__(self, seasonal_periods=7):
        self.seasonal_periods = seasonal_periods
        self.model = None
        self.method_note = ""
        
    def fit(self, series: pd.Series):
        """Fit Holt-Winters to daily workload series."""
        # Short history check (< 2 seasonal cycles)
        if len(series) < 2 * self.seasonal_periods:
            self.method_note = "trend-only (insufficient history for seasonality)"
            self.model = ExponentialSmoothing(
                series, 
                trend='add', 
                seasonal=None
            ).fit()
        else:
            self.method_note = "additive trend, weekly seasonality"
            self.model = ExponentialSmoothing(
                series, 
                trend='add', 
                seasonal='add', 
                seasonal_periods=self.seasonal_periods
            ).fit()
            
    def forecast(self, horizon_days: int) -> pd.DataFrame:
        """Returns forecast with expected, P75, P90 derived from residual quantiles."""
        if self.model is None:
            raise ValueError("Model not fitted")
            
        fcst = self.model.forecast(horizon_days)
        
        # Calculate residuals on training data
        residuals = self.model.resid
        std_resid = np.std(residuals) if len(residuals) > 0 else 0
        
        # Simple interval estimation
        df = pd.DataFrame({
            "expected": fcst,
            "p75": fcst + 0.674 * std_resid, # Approx 75th percentile for normal
            "p90": fcst + 1.282 * std_resid  # Approx 90th percentile for normal
        })
        
        df["method_note"] = self.method_note
        return df
