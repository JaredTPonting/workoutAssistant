# file: app.py

import streamlit as st
import pandas as pd
import datetime
import os
import matplotlib.pyplot as plt

DATA_FILE = "workout_data.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE, parse_dates=["date"])
    return pd.DataFrame(columns=["date", "day", "exercise", "weight", "reps", "sets"])

def save_data(new_entries):
    df = load_data()
    df = pd.concat([df, pd.DataFrame(new_entries)], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)

def get_workout_plan(day):
    return {
        "Push": ["Bench Press", "Overhead Press", "Tricep Pushdown"],
        "Pull": ["Deadlift", "Pull-up", "Barbell Row"],
        "Legs": ["Squat", "Leg Press", "Calf Raise"],
        "Upper": ["Bench Press", "Pull-up", "Overhead Press"],
        "Lower": ["Deadlift", "Squat", "Calf Raise"]
    }.get(day, [])

def workout_page(day):
    st.header(f"Workout - {day}")
    today = datetime.date.today()
    workout = get_workout_plan(day)
    entries = []

    for exercise in workout:
        st.subheader(exercise)
        weight = st.number_input(f"Weight (kg) for {exercise}", min_value=0.0, step=0.5, key=f"{exercise}_w")
        reps = st.number_input(f"Reps for {exercise}", min_value=0, step=1, key=f"{exercise}_r")
        sets = st.number_input(f"Sets for {exercise}", min_value=0, step=1, key=f"{exercise}_s")
        if weight and reps and sets:
            entries.append({
                "date": today,
                "day": day,
                "exercise": exercise,
                "weight": weight,
                "reps": reps,
                "sets": sets
            })

    if st.button("Finish Workout"):
        if entries:
            save_data(entries)
            st.success("Workout saved!")
        else:
            st.warning("Please enter workout data before saving.")

def summary_page():
    st.header("Workout Summary")
    df = load_data()
    if df.empty:
        st.info("No data yet.")
        return

    exercise = st.selectbox("Select Exercise", df["exercise"].unique())
    ex_df = df[df["exercise"] == exercise].sort_values("date")
    ex_df["date"] = pd.to_datetime(ex_df["date"])

    # Weekly volume graph
    ex_df["week"] = ex_df["date"].dt.to_period("W").apply(lambda r: r.start_time)
    ex_df["volume"] = ex_df["weight"] * ex_df["reps"] * ex_df["sets"]
    weekly_volume = ex_df.groupby("week")["volume"].sum().reset_index()

    fig1, ax1 = plt.subplots()
    ax1.plot(weekly_volume["week"], weekly_volume["volume"], marker='o', color='orange')
    ax1.set_title(f"Weekly Volume - {exercise}")
    ax1.set_ylabel("Volume (kg)")
    ax1.set_xlabel("Week")
    st.pyplot(fig1)

    # Estimated 1RM using Epley formula: 1RM = w * (1 + reps / 30)
    ex_df["1RM"] = ex_df.apply(lambda row: row["weight"] * (1 + row["reps"] / 30), axis=1)

    fig2, ax2 = plt.subplots()
    ax2.plot(ex_df["date"], ex_df["1RM"], marker='o')
    ax2.set_title(f"1RM Over Time - {exercise}")
    ax2.set_ylabel("Estimated 1RM (kg)")
    ax2.set_xlabel("Date")
    st.pyplot(fig2)

    st.write("Max Weight:", ex_df["weight"].max())
    st.write("Total Volume (Weight x Reps x Sets):", ex_df["volume"].sum())


def main():
    st.title("🏋️ Weightlifting Tracker")
    selection = st.selectbox("Select View", ["Push", "Pull", "Legs", "Upper", "Lower", "Summary"])

    if selection == "Summary":
        summary_page()
    else:
        workout_page(selection)

if __name__ == "__main__":
    main()
