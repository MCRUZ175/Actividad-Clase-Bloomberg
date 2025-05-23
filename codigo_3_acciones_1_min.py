# -*- coding: utf-8 -*-
"""Codigo 3 acciones 1 min

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1h6WYCG2NwBE2LCLSVEJLMNE-E1XWubBR
"""

# Commented out IPython magic to ensure Python compatibility.
# Import required libraries
import pandas as pd
import numpy as np
from google.colab import files
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.vector_ar.vecm import coint_johansen
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import matplotlib.pyplot as plt

# Ensure plotting works in Colab
# %matplotlib inline

# Upload Excel files
print("Please upload AMZN 1MIN-1DIA Excel file")
amzn_upload = files.upload()
amzn_filename = list(amzn_upload.keys())[0]
amzn_df = pd.read_excel(amzn_filename)

print("Please upload MSFT 1MIN-1DIA Excel file")
msft_upload = files.upload()
msft_filename = list(msft_upload.keys())[0]
msft_df = pd.read_excel(msft_filename)

print("Please upload GOOGLE 1MIN-1DIA Excel file")
google_upload = files.upload()
google_filename = list(google_upload.keys())[0]
google_df = pd.read_excel(google_filename)

# Print available columns
print("\nAMZN DataFrame columns:", list(amzn_df.columns))
print("MSFT DataFrame columns:", list(msft_df.columns))
print("GOOGLE DataFrame columns:", list(google_df.columns))

# Ask user for the correct column name
close_column = input("Please enter the column name containing closing prices: ")

# Function to clean and validate price data
def clean_price_series(series, name):
    print(f"\nSample of {name} data (first 5 rows):")
    print(series.head())

    # Convert to numeric, coerce errors to NaN
    cleaned_series = pd.to_numeric(series, errors='coerce')

    # Check for non-numeric values
    if cleaned_series.isna().any():
        print(f"Warning: Non-numeric values found in {name} data")
        print(f"Rows with non-numeric values:\n{series[cleaned_series.isna()]}")

    # Drop NaN values
    cleaned_series = cleaned_series.dropna()

    if len(cleaned_series) == 0:
        raise ValueError(f"No valid numeric data in {name} column '{close_column}'")

    print(f"Number of valid data points for {name}: {len(cleaned_series)}")
    if len(cleaned_series) < 100:
        print(f"Warning: Small sample size ({len(cleaned_series)} points). Expected ~390 for 1-min data over 1 day. Check for missing or invalid data.")
    return cleaned_series

# Extract and clean closing prices
try:
    amzn_close = clean_price_series(amzn_df[close_column], "AMZN")
    msft_close = clean_price_series(msft_df[close_column], "MSFT")
    google_close = clean_price_series(google_df[close_column], "GOOGLE")
except KeyError:
    print(f"Error: Column '{close_column}' not found in one or more DataFrames")
    print("Please check the column names and try again")
    raise

# Ensure all series have the same length
min_length = min(len(amzn_close), len(msft_close), len(google_close))
amzn_close = amzn_close[:min_length]
msft_close = msft_close[:min_length]
google_close = google_close[:min_length]

# Function for unit root tests with interpretation
def unit_root_tests(series, name):
    print(f"\nUnit Root Tests for {name}:")

    # ADF Test
    adf_result = adfuller(series)
    print("ADF Test:")
    print(f'ADF Statistic: {adf_result[0]:.4f}')
    print(f'p-value: {adf_result[1]:.4f}')
    print(f'Critical Values: {adf_result[4]}')
    print("Interpretation:")
    if adf_result[1] < 0.05:
        print(f"  - p-value < 0.05: Reject null hypothesis - {name} is stationary")
    else:
        print(f"  - p-value >= 0.05: Fail to reject null - {name} may be non-stationary")

    # KPSS Test
    kpss_result = kpss(series, regression='c', nlags="auto")
    print("\nKPSS Test:")
    print(f'KPSS Statistic: {kpss_result[0]:.4f}')
    print(f'p-value: {kpss_result[1]:.4f}')
    print(f'Critical Values: {kpss_result[3]}')
    print("Interpretation:")
    if kpss_result[1] < 0.05:
        print(f"  - p-value < 0.05: Reject null hypothesis - {name} is non-stationary")
    else:
        print(f"  - p-value >= 0.05: Fail to reject null - {name} may be stationary")

# Function to plot correlogram (ACF and PACF)
def plot_correlogram(series, name, lags=20):
    print(f"\nCorrelogram for {name}:")
    # Dynamically set lags to avoid exceeding 50% of sample size
    max_lags = min(lags, len(series) // 2 - 1)
    if max_lags < 1:
        print(f"Error: Sample size ({len(series)}) too small to compute correlogram.")
        return

    fig = plt.figure(figsize=(12, 8))

    # ACF Plot
    ax1 = fig.add_subplot(2, 1, 1)
    plot_acf(series, lags=max_lags, ax=ax1)
    ax1.set_title(f'Autocorrelation Function (ACF) - {name}')

    # PACF Plot
    ax2 = fig.add_subplot(2, 1, 2)
    plot_pacf(series, lags=max_lags, ax=ax2)
    ax2.set_title(f'Partial Autocorrelation Function (PACF) - {name}')

    plt.tight_layout()
    plt.show()

    print("Interpretation:")
    print(f"  - ACF: Shows the correlation of the series with its own lagged values.")
    print(f"    Significant spikes indicate potential MA terms for ARIMA.")
    print(f"  - PACF: Shows the partial correlation after removing earlier lag effects.")
    print(f"    Significant spikes indicate potential AR terms for ARIMA.")

# Perform unit root tests and correlograms
unit_root_tests(amzn_close, "AMZN")
plot_correlogram(amzn_close, "AMZN")
unit_root_tests(msft_close, "MSFT")
plot_correlogram(msft_close, "MSFT")
unit_root_tests(google_close, "GOOGLE")
plot_correlogram(google_close, "GOOGLE")

# Cointegration test with interpretation
def cointegration_test(df):
    try:
        result = coint_johansen(df, det_order=0, k_ar_diff=1)
        print("\nJohansen Cointegration Test:")
        print(f"Trace statistic: {result.lr1}")
        print(f"Critical values (90%, 95%, 99%): {result.cvt}")
        print("Interpretation:")
        for i in range(len(result.lr1)):
            if result.lr1[i] > result.cvt[i, 1]:
                print(f"  - r = {i}: Cointegration exists at 95% confidence level")
                print(f"    Trace statistic ({result.lr1[i]:.2f}) > 95% critical value ({result.cvt[i, 1]:.2f})")
            else:
                print(f"  - r = {i}: No cointegration at 95% confidence level")
                print(f"    Trace statistic ({result.lr1[i]:.2f}) <= 95% critical value ({result.cvt[i, 1]:.2f})")
        if result.lr1[0] > result.cvt[0, 1]:
            print("Conclusion: AMZN, MSFT, and GOOGLE are cointegrated - they share a long-run equilibrium relationship")
        else:
            print("Conclusion: No evidence of cointegration between AMZN, MSFT, and GOOGLE")
    except np.linalg.LinAlgError:
        print("Cointegration test failed due to singular matrix. Data may be too short or highly correlated.")

# Prepare data for cointegration
coint_df = pd.DataFrame({
    'AMZN': amzn_close,
    'MSFT': msft_close,
    'GOOGLE': google_close
}).dropna()
cointegration_test(coint_df)

# Function to find best ARIMA model with interpretation
def find_best_arima(series, name, max_p=3, max_d=2, max_q=3):
    best_aic = float('inf')
    best_order = None

    for p in range(max_p + 1):
        for d in range(max_d + 1):
            for q in range(max_q + 1):
                try:
                    model = ARIMA(series, order=(p, d, q))
                    results = model.fit()
                    if results.aic < best_aic:
                        best_aic = results.aic
                        best_order = (p, d, q)
                except:
                    continue

    print(f"\nBest ARIMA model for {name}:")
    print(f"Order: {best_order}")
    print(f"AIC: {best_aic:.2f}")
    print("Interpretation:")
    print(f"  - p={best_order[0]}: {best_order[0]} autoregressive term(s)")
    print(f"  - d={best_order[1]}: {best_order[1]} difference(s) needed for stationarity")
    print(f"  - q={best_order[2]}: {best_order[2]} moving average term(s)")
    return best_order

# Find and fit best ARIMA models
amzn_order = find_best_arima(amzn_close, "AMZN")
msft_order = find_best_arima(msft_close, "MSFT")
google_order = find_best_arima(google_close, "GOOGLE")

# Fit final ARIMA models
amzn_model = ARIMA(amzn_close, order=amzn_order).fit()
msft_model = ARIMA(msft_close, order=msft_order).fit()
google_model = ARIMA(google_close, order=google_order).fit()

# Forecast next 30 minutes (30 periods for 1-min data)
forecast_steps = 30
amzn_forecast = amzn_model.forecast(steps=forecast_steps)
msft_forecast = msft_model.forecast(steps=forecast_steps)
google_forecast = google_model.forecast(steps=forecast_steps)

# Create forecast index
last_index = len(amzn_close) - 1
forecast_index = range(last_index + 1, last_index + 1 + forecast_steps)

# Plot original series with forecasts
plt.figure(figsize=(12,6))
plt.plot(amzn_close, label='AMZN Historical')
plt.plot(forecast_index, amzn_forecast, label='AMZN Forecast', color='red')
plt.plot(msft_close, label='MSFT Historical')
plt.plot(forecast_index, msft_forecast, label='MSFT Forecast', color='green')
plt.plot(google_close, label='GOOGLE Historical')
plt.plot(forecast_index, google_forecast, label='GOOGLE Forecast', color='purple')
plt.title('AMZN, MSFT, and GOOGLE Closing Prices with Forecasts (1-min, 1-day)')
plt.legend()
plt.show()

# Detailed forecast plot with confidence intervals and interpretation
def plot_forecast(model, series, name, steps=30):
    forecast_obj = model.get_forecast(steps=steps)
    forecast = forecast_obj.predicted_mean
    conf_int = forecast_obj.conf_int()

    forecast_index = range(len(series), len(series) + steps)

    plt.figure(figsize=(12,6))
    plt.plot(series, label=f'{name} Historical')
    plt.plot(forecast_index, forecast, label='Forecast', color='red')
    plt.fill_between(forecast_index,
                    conf_int.iloc[:, 0],
                    conf_int.iloc[:, 1],
                    color='pink',
                    alpha=0.3,
                    label='95% Confidence Interval')
    plt.title(f'{name} Price Forecast (1-min, 1-day)')
    plt.legend()
    plt.show()

    # Forecast interpretation
    last_value = series.iloc[-1]
    mean_forecast = forecast.mean()
    print(f"\nForecast Interpretation for {name}:")
    print(f"Last observed value: {last_value:.2f}")
    print(f"Average forecast value: {mean_forecast:.2f}")
    print(f"Forecast change: {mean_forecast - last_value:.2f}")
    if mean_forecast > last_value:
        print("Trend: Upward forecast trend")
    elif mean_forecast < last_value:
        print("Trend: Downward forecast trend")
    else:
        print("Trend: Flat forecast trend")
    print(f"95% CI range at period {steps}: [{conf_int.iloc[-1, 0]:.2f}, {conf_int.iloc[-1, 1]:.2f}]")

# Generate detailed forecast plots and interpretations
plot_forecast(amzn_model, amzn_close, "AMZN")
plot_forecast(msft_model, msft_close, "MSFT")
plot_forecast(google_model, google_close, "GOOGLE")

# Print forecast values
print("\nAMZN Forecast Values (next 5 periods, 5 minutes):")
print(amzn_forecast[:5])
print("\nMSFT Forecast Values (next 5 periods, 5 minutes):")
print(msft_forecast[:5])
print("\nGOOGLE Forecast Values (next 5 periods, 5 minutes):")
print(google_forecast[:5])