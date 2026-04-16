import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
import yfinance as yf
import plotly.express as px
from datetime import date, datetime

# ====================== DATABASE ======================
conn = sqlite3.connect('tracker.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS investments (date TEXT, ticker TEXT, shares REAL, price REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS fitness (date TEXT, activity TEXT, duration REAL, calories REAL, notes TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS sleep (date TEXT, hours REAL, quality INTEGER, notes TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS diet (date TEXT, meal_type TEXT, meal TEXT, calories REAL, protein REAL, carbs REAL, fat REAL, notes TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS todos (id INTEGER PRIMARY KEY, task TEXT, due_date TEXT, priority TEXT, completed INTEGER DEFAULT 0)''')
c.execute('''CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY, name TEXT, description TEXT, status TEXT, due_date TEXT, progress INTEGER DEFAULT 0)''')
conn.commit()

# ====================== APP CONFIG ======================
st.set_page_config(page_title="My Life Tracker", layout="wide", page_icon="🏋️", initial_sidebar_state="expanded")

st.title("🏋️‍♂️💰 My All-in-One Life Tracker")
st.markdown("Track **Fitness • Sleep • Diet • Investments • Tasks • Projects**")

# Use radio for permanent visible navigation
page = st.sidebar.radio("Navigation", 
    ["📊 Dashboard", "🏋️ Fitness", "😴 Sleep", "🍽️ Diet & grocery list", "💰 Investments", 
     "✅ To-Do List", "📋 Projects"], label_visibility="collapsed")

# ====================== DASHBOARD - CENTERED TITLE + HORIZONTAL OVERVIEW ======================
if page == "📊 Dashboard":
    # Centered Main Title
    st.markdown("""
        <h1 style='text-align: center; margin-bottom: 10px;'>
            🏋️‍♂️💰 My All-in-One Life Tracker
        </h1>
    """, unsafe_allow_html=True)
    
    st.markdown("<p style='text-align: center; color: #888; margin-bottom: 30px;'>Track Fitness • Sleep • Diet • Investments • Tasks • Projects</p>", 
                unsafe_allow_html=True)

    # Load data
    inv_df = pd.read_sql("SELECT * FROM investments", conn)
    fit_df = pd.read_sql("SELECT * FROM fitness", conn)
    sleep_df = pd.read_sql("SELECT * FROM sleep", conn)
    diet_df = pd.read_sql("SELECT * FROM diet", conn)
    todo_df = pd.read_sql("SELECT * FROM todos WHERE completed = 0", conn)
    proj_df = pd.read_sql("SELECT * FROM projects WHERE status != 'Completed'", conn)

    # Main content area with two columns: Overview (left) + Weekly Plan (right)
    col_overview, col_weekly = st.columns([2, 1])

    with col_overview:
        # Horizontal Overview Metrics - Bordered Section
        with st.container(border=True):
            st.subheader("📊 Overview")
            metric_row1 = st.columns(4)
            with metric_row1[0]:
                if not inv_df.empty:
                    portfolio = inv_df.groupby('ticker')['shares'].sum().reset_index()
                    portfolio['current_price'] = portfolio['ticker'].apply(
                        lambda x: yf.Ticker(x).history(period="1d")['Close'].iloc[-1] 
                        if not yf.Ticker(x).history(period="1d").empty else 0)
                    total_value = (portfolio['shares'] * portfolio['current_price']).sum()
                    st.metric("💰 Portfolio Value", f"${total_value:,.2f}")
                else:
                    st.metric("💰 Portfolio Value", "$0.00")

            with metric_row1[1]:
                st.metric("🏋️ Workouts", len(fit_df))

            with metric_row1[2]:
                avg_sleep = sleep_df['hours'].mean() if not sleep_df.empty else 0
                st.metric("😴 Avg Sleep", f"{avg_sleep:.1f} hrs")

            with metric_row1[3]:
                st.metric("✅ Pending Tasks", len(todo_df))

            # Second row of metrics
            if not diet_df.empty:
                today_cal = diet_df[diet_df['date'] == str(date.today())]['calories'].sum()
                st.metric("🍽️ Calories Today", f"{today_cal:.0f}")

    with col_weekly:
        # Weekly Planning Calendar - Bordered on the right
        with st.container(border=True):
            st.subheader("📅 Weekly Plan")
            today = date.today()
            st.caption(f"Week of {today.strftime('%B %d, %Y')}")

            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            start_of_week = today - pd.Timedelta(days=today.weekday())

            for i, day_name in enumerate(days):
                day_date = start_of_week + pd.Timedelta(days=i)
                with st.expander(f"{day_name} ({day_date.strftime('%b %d')})", 
                               expanded=(day_date == today)):
                    goal = st.text_input(f"Main Goal - {day_name}", key=f"goal_{i}")
                    workout = st.checkbox(f"🏋️ Workout planned", key=f"workout_{i}")
                    notes = st.text_area("Notes", height=60, key=f"notes_{i}")
                    
                    if st.button(f"Save {day_name}", key=f"save_{i}"):
                        st.success(f"Saved plan for {day_name}!")

            st.caption("Tip: Expand each day to plan your week.")

    st.divider()

    # Bottom row - Pending Tasks and Active Projects
    col_tasks, col_projects = st.columns(2)

    with col_tasks:
        with st.container(border=True):
            st.subheader("📌 Pending To-Do Tasks")
            if not todo_df.empty:
                for _, task in todo_df.head(8).iterrows():
                    st.write(f"• {task['task']} ({task['priority']}) — Due: {task['due_date']}")
            else:
                st.info("No pending tasks today.")

    with col_projects:
        with st.container(border=True):
            st.subheader("📋 Active Projects")
            if not proj_df.empty:
                for _, p in proj_df.head(5).iterrows():
                    st.progress(p['progress']/100, text=f"{p['name']} — {p['progress']}%")
            else:
                st.info("No active projects.")

    st.info("Use the sidebar to log new data.")
    
# ====================== FITNESS ======================
elif page == "🏋️ Fitness":
    st.header("🏋️ Fitness Tracker")

    with st.form("log_fitness"):
        col1, col2 = st.columns(2)
        with col1:
            f_date = st.date_input("Date", value=date.today())
            activity = st.selectbox("Activity", 
                ["Weight Training", "Running", "Cycling", "Swimming", "Walking", "HIIT", "Yoga", "Basketball", "Other"])
        with col2:
            if activity == "Other":
                activity = st.text_input("Custom Activity")
            duration = st.slider("Duration (minutes)", 5, 180, 45)
            calories = st.number_input("Calories Burned", 0, 2000, 400)
        notes = st.text_input("Notes (optional)")
        
        if st.form_submit_button("✅ Log Workout"):
            c.execute("INSERT INTO fitness VALUES (?, ?, ?, ?, ?)", 
                     (str(f_date), activity, duration, calories, notes))
            conn.commit()
            st.success("✅ Workout logged!")
            st.rerun()

    df = pd.read_sql("SELECT * FROM fitness ORDER BY date DESC", conn)
    if not df.empty:
        st.subheader("Workout History")
        st.dataframe(df, width='stretch')

# ====================== SLEEP ======================
elif page == "😴 Sleep":
    st.header("😴 Sleep Tracker")

    with st.form("log_sleep"):
        col1, col2 = st.columns(2)
        with col1:
            s_date = st.date_input("Date", value=date.today())
            hours = st.slider("Hours Slept", 0.0, 12.0, 7.5, 0.5)
        with col2:
            quality = st.slider("Sleep Quality (1-10)", 1, 10, 7)
        notes = st.text_input("Notes (optional)")
        
        if st.form_submit_button("✅ Log Sleep"):
            c.execute("INSERT INTO sleep VALUES (?, ?, ?, ?)", 
                     (str(s_date), hours, quality, notes))
            conn.commit()
            st.success("✅ Sleep logged!")
            st.rerun()

    df = pd.read_sql("SELECT * FROM sleep ORDER BY date DESC", conn)
    if not df.empty:
        st.subheader("Sleep History")
        st.dataframe(df, width='stretch')

# ====================== DIET TRACKER - Cleaner Layout ======================
elif page == "🍽️ Diet & grocery list":
    st.header("🍽️ Diet Tracker")

    # Use two clear sections with expanders (much cleaner on mobile + desktop)
    with st.expander("📝 Log Today's Meal", expanded=True):
        with st.form("log_diet"):
            col1, col2 = st.columns(2)
            with col1:
                d_date = st.date_input("Date", value=date.today())
                meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snack", "Other"])
                meal = st.text_input("What did you eat?")
            with col2:
                calories = st.number_input("Calories", 0, 2000, 600)
                protein = st.number_input("Protein (g)", 0.0, 200.0, 30.0)
                carbs = st.number_input("Carbs (g)", 0.0, 300.0, 60.0)
                fat = st.number_input("Fat (g)", 0.0, 150.0, 20.0)
            notes = st.text_input("Notes (optional)")
            
            if st.form_submit_button("✅ Log Meal"):
                c.execute("INSERT INTO diet VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                         (str(d_date), meal_type, meal, calories, protein, carbs, fat, notes))
                conn.commit()
                st.success("✅ Meal logged!")
                st.rerun()

    st.divider()   # Clean separator

    # Grocery Shopping List Section
    with st.expander("🛒 Grocery Shopping List", expanded=False):
        st.subheader("Add New Item")
        
        with st.form("add_grocery"):
            col1, col2, col3 = st.columns([3, 2, 2])
            with col1:
                item = st.text_input("Grocery Item")
            with col2:
                quantity = st.text_input("Quantity", "1")
            with col3:
                category = st.selectbox("Category", ["Fruits", "Vegetables", "Protein", "Dairy", 
                                                    "Grains", "Snacks", "Beverages", "Other"])
            
            if st.form_submit_button("➕ Add to List"):
                if item:
                    c.execute("""INSERT INTO grocery_list (item, quantity, category, bought) 
                                 VALUES (?, ?, ?, 0)""", (item.strip(), quantity, category))
                    conn.commit()
                    st.success(f"Added {item} to shopping list")
                    st.rerun()

        # Grocery list display
        c.execute('''CREATE TABLE IF NOT EXISTS grocery_list 
                     (id INTEGER PRIMARY KEY, item TEXT, quantity TEXT, category TEXT, bought INTEGER DEFAULT 0)''')
        conn.commit()

        grocery_df = pd.read_sql("SELECT * FROM grocery_list ORDER BY category, item", conn)

        if not grocery_df.empty:
            st.subheader("Current Shopping List")
            for category in grocery_df['category'].unique():
                cat_items = grocery_df[grocery_df['category'] == category]
                if not cat_items.empty:
                    st.write(f"**{category}**")
                    for _, row in cat_items.iterrows():
                        col1, col2, col3 = st.columns([0.65, 0.25, 0.1])
                        with col1:
                            checked = st.checkbox(f"{row['item']} ({row['quantity']})", 
                                                value=bool(row['bought']), 
                                                key=f"groc_{row['id']}")
                            if checked != bool(row['bought']):
                                c.execute("UPDATE grocery_list SET bought = ? WHERE id = ?", 
                                         (int(checked), row['id']))
                                conn.commit()
                                st.rerun()
                        with col2:
                            st.caption(row['category'])
                        with col3:
                            if st.button("🗑️", key=f"del_groc_{row['id']}"):
                                c.execute("DELETE FROM grocery_list WHERE id=?", (row['id'],))
                                conn.commit()
                                st.rerun()

            if st.button("🗑️ Clear All Bought Items"):
                c.execute("DELETE FROM grocery_list WHERE bought = 1")
                conn.commit()
                st.success("Cleared bought items!")
                st.rerun()
        else:
            st.info("Your grocery list is empty. Add items above.")

    # Diet History (always visible at bottom)
    df = pd.read_sql("SELECT * FROM diet ORDER BY date DESC", conn)
    if not df.empty:
        with st.expander("📜 Diet History", expanded=False):
            st.dataframe(df, width='stretch')
            
# ====================== INVESTMENTS - Improved with Cost Basis & P&L ======================
elif page == "💰 Investments":
    st.header("💰 Investments Tracker")

    # Add New Investment
    with st.form("add_investment"):
        col1, col2, col3 = st.columns(3)
        with col1:
            ticker = st.text_input("Stock Ticker", placeholder="AAPL").upper().strip()
        with col2:
            shares = st.number_input("Number of Shares", min_value=0.01, step=0.1, value=10.0)
        with col3:
            cost_per_share = st.number_input("Your Cost per Share ($)", min_value=0.01, step=0.01, value=50.0)
        
        if st.form_submit_button("➕ Add Investment"):
            if ticker and shares > 0 and cost_per_share > 0:
                try:
                    stock = yf.Ticker(ticker)
                    current_price = stock.history(period="1d")['Close'].iloc[-1]
                    
                    c.execute("INSERT INTO investments VALUES (?, ?, ?, ?)", 
                             (str(date.today()), ticker, shares, cost_per_share))
                    conn.commit()
                    st.success(f"✅ Added {shares} shares of {ticker} @ ${cost_per_share:.2f}")
                    st.rerun()
                except:
                    st.error(f"❌ Could not fetch data for {ticker}. Please check ticker symbol.")

    if st.button("🔄 Refresh Live Prices"):
        st.rerun()

    # Portfolio Display
    df = pd.read_sql("SELECT * FROM investments", conn)
    
    if not df.empty:
        st.subheader("Your Portfolio with Profit & Loss")

        portfolio = df.groupby('ticker').agg({
            'shares': 'sum',
            'price': 'mean'           # average cost basis
        }).reset_index()

        portfolio['current_price'] = portfolio['ticker'].apply(
            lambda x: round(yf.Ticker(x).history(period="1d")['Close'].iloc[-1], 4) 
            if not yf.Ticker(x).history(period="1d").empty else 0)

        portfolio['cost_basis'] = round(portfolio['shares'] * portfolio['price'], 2)
        portfolio['market_value'] = round(portfolio['shares'] * portfolio['current_price'], 2)
        portfolio['unrealized_pnl'] = round(portfolio['market_value'] - portfolio['cost_basis'], 2)
        portfolio['pnl_percent'] = round((portfolio['unrealized_pnl'] / portfolio['cost_basis']) * 100, 2) if portfolio['cost_basis'].sum() > 0 else 0

        # Display table
        st.dataframe(
            portfolio[['ticker', 'shares', 'price', 'current_price', 'cost_basis', 'market_value', 'unrealized_pnl', 'pnl_percent']],
            width='stretch',
            hide_index=True
        )

        # Summary Metrics
        total_cost = portfolio['cost_basis'].sum()
        total_value = portfolio['market_value'].sum()
        total_pnl = portfolio['unrealized_pnl'].sum()
        total_pnl_pct = round((total_pnl / total_cost) * 100, 2) if total_cost > 0 else 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Cost Basis", f"${total_cost:,.2f}")
        with col2:
            st.metric("Current Market Value", f"${total_value:,.2f}")
        with col3:
            st.metric("Total Unrealized P&L", f"${total_pnl:,.2f}", 
                     delta=f"{total_pnl_pct:.2f}%")

        # Portfolio Pie Chart
        fig = px.pie(portfolio, values='market_value', names='ticker', title="Portfolio Allocation")
        st.plotly_chart(fig, width='stretch')

        # Delete Section
        st.subheader("🗑️ Remove Holdings")
        if not portfolio.empty:
            ticker_to_delete = st.selectbox("Select Ticker to Delete", portfolio['ticker'].unique())
            if st.button("🗑️ Delete All Shares of this Ticker", type="primary"):
                c.execute("DELETE FROM investments WHERE ticker = ?", (ticker_to_delete,))
                conn.commit()
                st.success(f"Deleted all holdings of {ticker_to_delete}")
                st.rerun()

    else:
        st.info("No investments added yet. Use the form above to begin tracking.")
# ====================== TO-DO LIST ======================
elif page == "✅ To-Do List":
    st.header("✅ To-Do List")

    with st.form("add_todo"):
        task = st.text_input("New Task")
        due = st.date_input("Due Date", value=date.today())
        priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        if st.form_submit_button("➕ Add Task"):
            c.execute("INSERT INTO todos (task, due_date, priority, completed) VALUES (?, ?, ?, 0)",
                     (task, str(due), priority))
            conn.commit()
            st.success("✅ Task added!")
            st.rerun()

    df = pd.read_sql("SELECT * FROM todos ORDER BY completed, due_date", conn)
    if not df.empty:
        st.subheader("Your Tasks")
        for _, row in df.iterrows():
            col1, col2, col3, col4 = st.columns([0.6, 0.15, 0.15, 0.1])
            with col1:
                checked = st.checkbox(row['task'], value=bool(row['completed']), key=f"todo_{row['id']}")
                if checked != bool(row['completed']):
                    c.execute("UPDATE todos SET completed = ? WHERE id = ?", (int(checked), row['id']))
                    conn.commit()
                    st.rerun()
            with col2:
                st.caption(f"Due: {row['due_date']}")
            with col3:
                st.caption(row['priority'])
            with col4:
                if st.button("🗑️", key=f"del_todo_{row['id']}"):
                    c.execute("DELETE FROM todos WHERE id=?", (row['id'],))
                    conn.commit()
                    st.rerun()

        if st.button("🗑️ Clear Completed Tasks"):
            c.execute("DELETE FROM todos WHERE completed = 1")
            conn.commit()
            st.success("Cleared completed tasks!")
            st.rerun()
            
# ====================== PROJECTS ======================
elif page == "📋 Projects":
    st.header("📋 Projects & Goals")

    with st.form("add_project"):
        name = st.text_input("Project / Goal Name")
        desc = st.text_area("Description (optional)")
        due = st.date_input("Target Date", value=date.today())
        status = st.selectbox("Status", ["Not Started", "In Progress", "Review", "Completed"])
        progress = st.slider("Progress (%)", 0, 100, 0)
        
        if st.form_submit_button("➕ Add Project"):
            c.execute("""INSERT INTO projects (name, description, status, due_date, progress) 
                         VALUES (?, ?, ?, ?, ?)""", 
                     (name, desc, status, str(due), progress))
            conn.commit()
            st.success("✅ Project added!")
            st.rerun()

    df = pd.read_sql("SELECT * FROM projects ORDER BY due_date", conn)
    if not df.empty:
        st.subheader("Your Projects")
        for _, row in df.iterrows():
            col1, col2, col3 = st.columns([0.5, 0.3, 0.2])
            with col1:
                st.write(f"**{row['name']}**")
                if row['description']:
                    st.caption(row['description'])
            with col2:
                st.progress(row['progress'] / 100)
                st.caption(f"{row['progress']}% • Due: {row['due_date']}")
            with col3:
                new_status = st.selectbox("Status", 
                    ["Not Started", "In Progress", "Review", "Completed"], 
                    index=["Not Started", "In Progress", "Review", "Completed"].index(row['status']),
                    key=f"proj_{row['id']}")
                if new_status != row['status']:
                    c.execute("UPDATE projects SET status = ? WHERE id = ?", (new_status, row['id']))
                    conn.commit()
                    st.rerun()
                
                if st.button("🗑️ Delete", key=f"del_proj_{row['id']}"):
                    c.execute("DELETE FROM projects WHERE id=?", (row['id'],))
                    conn.commit()
                    st.rerun()

st.caption("💾 All data saved locally in tracker.db | Built with Python + Streamlit")
