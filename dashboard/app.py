import streamlit as st
import requests

st.set_page_config(page_title="Wine Quality AI Pro", page_icon="🍷")

if "token" not in st.session_state:
    st.session_state.token = None

def login_ui():
    st.sidebar.title("🔐 Authentication")
    choice = st.sidebar.radio("Action", ["Login", "Register"])
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    
    if st.sidebar.button(choice):
        if choice == "Register":
            res = requests.post("http://backend:8000/register", json={"username": username, "password": password})
            if res.status_code == 200: st.sidebar.success("✅ Registered! Now please Login.")
            else: st.sidebar.error("❌ Registration Failed")
        else:
            res = requests.post("http://backend:8000/token", data={"username": username, "password": password})
            if res.status_code == 200:
                st.session_state.token = res.json()["access_token"]
                st.rerun()
            else: st.sidebar.error("❌ Invalid credentials")

if not st.session_state.token:
    login_ui()
    st.title("🍷 Welcome to Wine Quality AI")
    st.info("Please Login or Register from the sidebar to continue.")
else:
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    user_res = requests.get("http://backend:8000/me", headers=headers)
    
    if user_res.status_code == 200:
        user_data = user_res.json()
        st.sidebar.success(f"👤 User: {user_data['username']}")
        
        # --- التعديل هنا لعرض الأرصدة الجديدة ---
        st.sidebar.metric("Total Balance", f"{user_data['total_credits']} pts") 
        st.sidebar.write(f"🎁 Free: {user_data['free_credits']} | 💰 Paid: {user_data['paid_credits']}")
        # ---------------------------------------

        st.sidebar.divider()
        st.sidebar.subheader("💳 Billing")
        recharge_amt = st.sidebar.number_input("Recharge Amount ($)", min_value=10, value=10)
        if st.sidebar.button("Buy Credits"):
            requests.post(f"http://backend:8000/billing/recharge?amount={recharge_amt}", headers=headers)
            st.rerun()

        if st.sidebar.button("Logout"):
            st.session_state.token = None
            st.rerun()

        st.markdown("""
            <div style="background-color: #FFF3CD; padding: 20px; border-radius: 10px; border: 2px solid #FFEEBA; margin-bottom: 25px; color: #856404;">
                <h4 style="margin: 0; color: #856404; font-weight: bold;">🎁 Exclusive One-Time Offer!</h4>
                <p style="margin: 10px 0 0 0; font-size: 1.1rem; color: #856404;">
                    Get <b>100 free credits</b> instantly! <br>
                    Copy the code <b style="background-color: #ff4b4b; color: white; padding: 2px 6px; border-radius: 4px;">WINE2026</b> 
                    and paste it into the <b>"Promo Code"</b> field in the sidebar, then click <b>Redeem</b>.
                </p>
                <p style="font-size: 0.85rem; color: #856404; margin-top: 10px; opacity: 0.9;">
                    <i>* This offer is available for one-time use only per account.</i>
                </p>
            </div>
        """, unsafe_allow_html=True)

        st.sidebar.divider()
        promo_code = st.sidebar.text_input("Promo Code")
        if st.sidebar.button("Redeem"):
            p_res = requests.post(f"http://backend:8000/promo?promo_code={promo_code}", headers=headers)
            if p_res.status_code == 200:
                st.sidebar.balloons()
                st.rerun()
            else: st.sidebar.error("Invalid Code")

        st.title("🍷 Wine Quality Analysis")
        col1, col2 = st.columns(2)
        with col1:
            fixed_acidity = st.number_input("Fixed Acidity", value=7.4)
            volatile_acidity = st.number_input("Volatile Acidity", value=0.7)
            citric_acid = st.number_input("Citric Acid", value=0.0)
            residual_sugar = st.number_input("Residual Sugar", value=1.9)
            chlorides = st.number_input("Chlorides", value=0.076)
        with col2:
            free_sulfur_dioxide = st.number_input("Free Sulfur Dioxide", value=11.0)
            total_sulfur_dioxide = st.number_input("Total Sulfur Dioxide", value=34.0)
            density = st.number_input("Density", value=0.9978)
            ph = st.number_input("pH", value=3.51)
            sulphates = st.number_input("Sulphates", value=0.56)
        alcohol = st.number_input("Alcohol Content", value=9.4)

        current_cost = 10 if user_data.get('predictions_count', 0) < 5 else 5
        if st.button(f"Predict Quality ({current_cost} Credits)"):
            payload = {
                "fixed_acidity": fixed_acidity, "volatile_acidity": volatile_acidity,
                "citric_acid": citric_acid, "residual_sugar": residual_sugar,
                "chlorides": chlorides, "free_sulfur_dioxide": free_sulfur_dioxide,
                "total_sulfur_dioxide": total_sulfur_dioxide, "density": density,
                "ph": ph, "sulphates": sulphates, "alcohol": alcohol
            }
            res = requests.post("http://backend:8000/predict", json=payload, headers=headers)
            if res.status_code == 200:
                st.success(f"Predicted Quality: {res.json()['quality']}")
            else: st.error("❌ Failed: Check your credits.")