import streamlit as st
import pandas as pd
import datetime
import os
import json
import matplotlib.pyplot as plt

DATA_FILE = "workout_data.csv"
USER_FILE = "users.json"

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE, parse_dates=["date"])
    return pd.DataFrame(columns=["user", "date", "exercise", "weight", "reps", "sets"])

def save_data(new_entries):
    df = load_data()
    df = pd.concat([df, pd.DataFrame(new_entries)], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)

def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f)

def get_workout_plan(day):
    return {
        "Push": [
            "Incline Bench Press",
            "DB OHP",
            "Lat Raise",
            "Incline Cabel Chest Fly",
            "Cable Triceps Pushdown",
            "DB Triceps OH"
        ],
        "Pull": [
            "Lat Pulldown",
            "Cable Row",
            "Chest Assisted Row"
            "Rear delt fly",
            "Curl",
            "Hammer Curl"
        ],
        "Legs": [
            "Heel Raised Squat",
            "Leg Press",
            "Leg Ext.",
            "Leg Curl"
            "Stnading Calf Raises"
        ],
        "Upper": [
            "Bench Press",
            "OHP",
            "Shrugs"
            "Lat Raise"
        ],
        "Lower": [
            "Front Squat",
            "Bulgarian Split Squat",
            "Standing Calf Raise",
            "Bent Leg Calf Raises",
            "Leg Ext"
        ]
    }.get(day, [])

# inside workout_page()
def workout_page(user, day):
    st.header(f"Workout - {day}")
    today = datetime.date.today()
    workout = get_workout_plan(day)
    entries = []

    for exercise in workout:
        st.subheader(exercise)

        key_prefix = exercise.replace(" ", "_")
        if f"sets_{key_prefix}" not in st.session_state:
            st.session_state[f"sets_{key_prefix}"] = [
                {"weight": 0.0, "reps": 0, "sets": 1}
            ]

        sets = st.session_state[f"sets_{key_prefix}"]
        set_container = st.container()
        for i, s in enumerate(sets):
            cols = set_container.columns(3)
            s["weight"] = cols[0].number_input(
                f"Weight (kg) Set {i+1}", min_value=0.0, step=0.5, key=f"{key_prefix}_w_{i}"
            )
            s["reps"] = cols[1].number_input(
                f"Reps Set {i+1}", min_value=0, step=1, key=f"{key_prefix}_r_{i}"
            )
            s["sets"] = cols[2].number_input(
                f"Sets Set {i+1}", min_value=1, step=1, key=f"{key_prefix}_s_{i}"
            )

        if st.button(f"Add Another Set for {exercise}", key=f"add_{key_prefix}"):
            sets.append({"weight": 0.0, "reps": 0, "sets": 1})

        # Append entries for each set
        for s in sets:
            if s["weight"] > 0 and s["reps"] > 0:
                entries.append({
                    "user": user,
                    "date": today,
                    "exercise": exercise,
                    "weight": s["weight"],
                    "reps": s["reps"],
                    "sets": s["sets"]
                })

    if st.button("Finish Workout"):
        if entries:
            save_data(entries)
            st.success("Workout saved!")
            # Reset sets state
            for exercise in workout:
                st.session_state.pop(f"sets_{exercise.replace(' ', '_')}", None)
        else:
            st.warning("Please enter workout data before saving.")

# inside summary_page()
def summary_page(user):
    st.header("Workout Summary")
    df = load_data()
    df = df[df["user"] == user]
    if df.empty:
        st.info("No data yet.")
        return

    df["date"] = pd.to_datetime(df["date"], errors='coerce')
    df = df.dropna(subset=["date"])

    exercise = st.selectbox("Select Exercise", sorted(df["exercise"].unique()))
    ex_df = df[df["exercise"] == exercise].sort_values("date")

    ex_df["week"] = ex_df["date"].dt.to_period("W").apply(lambda r: r.start_time)
    ex_df["volume"] = ex_df["weight"] * ex_df["reps"] * ex_df["sets"]
    weekly_volume = ex_df.groupby("week")["volume"].sum().reset_index()

    fig1, ax1 = plt.subplots()
    ax1.plot(weekly_volume["week"], weekly_volume["volume"], marker='o', color='orange')
    ax1.set_title(f"Weekly Volume - {exercise}")
    ax1.set_ylabel("Volume (kg)")
    ax1.set_xlabel("Week")
    st.pyplot(fig1)

    ex_df["1RM"] = ex_df.apply(lambda row: row["weight"] * (1 + row["reps"] / 30), axis=1)
    fig2, ax2 = plt.subplots()
    ax2.plot(ex_df["date"], ex_df["1RM"], marker='o')
    ax2.set_title(f"1RM Over Time - {exercise}")
    ax2.set_ylabel("Estimated 1RM (kg)")
    ax2.set_xlabel("Date")
    st.pyplot(fig2)

    st.write("Max Weight:", ex_df["weight"].max())
    st.write("Total Volume (Weight x Reps x Sets):", ex_df["volume"].sum())


def login():
    st.sidebar.header("Login")
    users = load_users()

    login_tab, register_tab = st.sidebar.tabs(["Login", "Register"])

    with login_tab:
        user = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Log in"):
            if user in users and users[user] == password:
                st.session_state.user = user
            else:
                st.error("Invalid username or password")

    with register_tab:
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password", type="password")
        if st.button("Create Account"):
            if new_user in users:
                st.warning("Username already exists")
            elif not new_user or not new_pass:
                st.warning("Username and password required")
            else:
                users[new_user] = new_pass
                save_users(users)
                st.success("Account created. Please log in.")

def main():
    st.title("🏋️ Weightlifting Tracker")

    if "user" not in st.session_state:
        login()
        return

    user = st.session_state.user
    st.sidebar.success(f"Logged in as {user}")

    selection = st.selectbox("Select View", ["Push", "Pull", "Legs", "Upper", "Lower", "Summary"])

    if selection == "Summary":
        summary_page(user)
    else:
        workout_page(user, selection)

if __name__ == "__main__":
    main()
