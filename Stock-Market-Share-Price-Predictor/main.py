import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
import datetime as dt

from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, LSTM

st.set_page_config(page_title="Stock Price Predictor", layout="centered")

st.title("📈 Stock Market Price Predictor")
st.markdown(
    """
Enter a valid stock ticker (e.g., `TATAMOTORS.NS`) to view predictions for Indian or global stocks.
"""
)

company = st.text_input("🔎 Enter Ticker Symbol:", "TATAMOTORS.NS")

if st.button("📊 Predict"):
    try:
        # Load historical data
        start = dt.datetime(2012, 1, 1)
        end = dt.datetime(2022, 1, 1)

        data = yf.download(company, start=start, end=end)
        if data.empty:
            st.error("⚠️ No data found. Please check the ticker symbol.")
            st.stop()

        # Preprocessing
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(data["Close"].values.reshape(-1, 1))

        prediction_days = 60
        x_train, y_train = [], []

        for x in range(prediction_days, len(scaled_data)):
            x_train.append(scaled_data[x - prediction_days : x, 0])
            y_train.append(scaled_data[x, 0])

        x_train, y_train = np.array(x_train), np.array(y_train)
        x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))

        # Model
        model = Sequential()
        model.add(
            LSTM(units=50, return_sequences=True, input_shape=(x_train.shape[1], 1))
        )
        model.add(Dropout(0.2))
        model.add(LSTM(units=50, return_sequences=True))
        model.add(Dropout(0.2))
        model.add(LSTM(units=50, return_sequences=True))
        model.add(Dropout(0.2))
        model.add(LSTM(units=50))
        model.add(Dropout(0.2))
        model.add(Dense(units=1))

        model.compile(optimizer="adam", loss="mean_squared_error")
        with st.spinner("⏳ Training model..."):
            model.fit(x_train, y_train, epochs=5, batch_size=32, verbose=0)

        # Load test data
        test_start = dt.datetime(2020, 1, 1)
        test_end = dt.datetime(2022, 1, 1)
        test_data = yf.download(company, start=test_start, end=test_end)
        actual_prices = test_data["Close"].values

        total_dataset = pd.concat((data["Close"], test_data["Close"]), axis=0)
        model_inputs = total_dataset[
            len(total_dataset) - len(test_data) - prediction_days :
        ].values
        model_inputs = model_inputs.reshape(-1, 1)
        model_inputs = scaler.transform(model_inputs)

        # Predict test set
        x_test = []
        for x in range(prediction_days, len(model_inputs)):
            x_test.append(model_inputs[x - prediction_days : x, 0])
        x_test = np.array(x_test)
        x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 1))

        predicted_prices = model.predict(x_test)
        predicted_prices = scaler.inverse_transform(predicted_prices)

        # Predict next day
        real_data = model_inputs[-prediction_days:]
        real_data = np.array([real_data])
        real_data = np.reshape(real_data, (real_data.shape[0], real_data.shape[1], 1))

        next_day_prediction = model.predict(real_data)
        next_day_prediction = scaler.inverse_transform(next_day_prediction)

        st.success(f"✅ Predicted price for next day: ₹{next_day_prediction[0][0]:.2f}")

        # Plot results
        fig, ax = plt.subplots()
        ax.plot(actual_prices, color="blue", label="Actual Price")
        ax.plot(predicted_prices, color="green", label="Predicted Price")
        ax.set_title(f"{company} Stock Price Prediction")
        ax.set_xlabel("Time")
        ax.set_ylabel("Price (INR)")
        ax.legend()
        st.pyplot(fig)

    except Exception as e:
        st.error(f"❌ Error: {e}")
