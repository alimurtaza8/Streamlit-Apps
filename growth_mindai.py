import streamlit as st
import google.generativeai as genai
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import stripe

# Set the Streamlit page configuration at the very top
st.set_page_config(page_title="GrowthMindset.AI", layout="wide")

# Initialize Firebase using your service account key file
firebase_credentials = st.secrets["firebase"]
if not firebase_admin._apps:
    # cred = credentials.Certificate(firebase_credentials)
    cred = credentials.Certificate(dict(firebase_credentials))
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Configure Gemini AI using your API key from st.secrets
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# Initialize Stripe with the secret key from st.secrets
stripe.api_key = st.secrets["STRIPE_API_KEY"]

def create_checkout_session(amount, currency, success_url, cancel_url):
    """
    Creates a Stripe Checkout session for a recurring subscription.
    Amount is in cents (e.g., 999 for $9.99).
    """
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": currency,
                "product_data": {
                    "name": "Premium Subscription",
                },
                "unit_amount": amount,
                "recurring": {"interval": "month"}
            },
            "quantity": 1,
        }],
        mode="subscription",
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session.url

# Check query parameters for Stripe payment success and update premium status
query_params = st.query_params
if query_params.get("payment") == ["success"] and query_params.get("email"):
    email = query_params["email"][0]
    user_ref = db.collection("users").document(email)
    user_data = user_ref.get().to_dict() or {"progress": {}, "premium": False}
    if not user_data.get("premium"):
        user_data["premium"] = True
        user_ref.set(user_data)
        st.session_state.user = user_data
        st.success("Your premium subscription has been activated!")

# AI Agent System
class GrowthCoach:
    def __init__(self):
        self.agents = {
            "planner": "You are expert at creating personalized growth challenges...",
            "analyst": "You specialize in tracking progress and identifying patterns...",
            "motivator": "You generate powerful motivational messages...",
            "mentor": "You simulate famous mentors like Tony Robbins..."
        }
    def generate_response(self, agent_type, prompt):
        response = model.generate_content(
            f"{self.agents[agent_type]}\n\n{prompt}"
        )
        return response.text

# Session State Management
if "user" not in st.session_state:
    st.session_state.user = {"progress": {}, "premium": False}

# Main App Interface
st.title("GrowthMindset.AI")
st.subheader("Your Personal AI Growth Coaching System")

# User Onboarding in Sidebar
with st.sidebar:
    st.header("Your Profile")
    user_email = st.text_input("Enter Email to Continue")
    if user_email:
        user_ref = db.collection("users").document(user_email)
        st.session_state.user = user_ref.get().to_dict() or {"progress": {}, "premium": False}
    else:
        st.write("Please enter your email to continue.")

# Define Main Feature Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Daily Challenge", "Progress Hub", "AI Coaching", "Premium"])

with tab1:
    coach = GrowthCoach()
    challenge_type = st.selectbox("Choose Challenge Focus", ["Career", "Health", "Relationships", "Skills"])
    if st.button("Generate Today's Challenge"):
        if user_email:
            prompt = f"Create {challenge_type} growth challenge for intermediate level user"
            challenge = coach.generate_response("planner", prompt)
            st.session_state.user["progress"][str(datetime.now())] = challenge
            db.collection("users").document(user_email).set(st.session_state.user)
            with st.chat_message("assistant"):
                st.markdown(f"## 🚀 Your Challenge\n{challenge}")
                st.button("I Completed This!", on_click=lambda: st.balloons())
        else:
            st.error("Please enter your email in the sidebar to generate a challenge.")

with tab2:
    st.header("Your Growth Journey")
    if st.session_state.user.get("progress"):
        for date, challenge in st.session_state.user["progress"].items():
            st.expander(f"{date}").write(challenge)
    else:
        st.write("No challenges completed yet!")

with tab3:
    st.header("24/7 AI Coaching")
    # If the user is premium, let them select from additional agents; otherwise, only show "analyst"
    if st.session_state.user.get("premium"):
        agent_choice = st.selectbox("Select a Coaching Agent", ["analyst", "motivator", "mentor"])
    else:
        agent_choice = "analyst"
    query = st.text_input("Ask your growth question:")
    if query:
        with st.spinner("Analyzing..."):
            response = coach.generate_response(agent_choice, f"User asked: {query}")
            st.write(response)
            if not st.session_state.user.get("premium"):
                st.warning("Unlock premium for detailed analysis and access to pro coaching agents!")

with tab4:
    st.header("Premium Features")
    # If user already has premium, show additional pro agent functionalities
    if st.session_state.user.get("premium"):
        st.success("Premium features unlocked!")
        st.markdown("### Pro Coaching Agents Available:")
        st.write("You now have access to advanced coaching agents like **Motivator** and **Mentor**. Enjoy tailored insights and specialized guidance!")
    else:
        st.image("https://b.stripecdn.com/docs-statics-srv/assets/fixed-price-collect-payment-details.57171d112df46d70abf40753d1ee7370.png")
        if st.button("Unlock Premium ($9.99/month)"):
            if user_email:
                # Create dynamic success URL with user's email; update the domain for your deployment.
                success_url = f"http://localhost:8501/?payment=success&email={user_email}"
                cancel_url = "http://localhost:8501/?payment=cancel"  # Update as needed
                payment_url = create_checkout_session(999, "usd", success_url, cancel_url)
                st.success("Redirecting to Stripe for payment...")
                st.markdown(f'<meta http-equiv="refresh" content="0;url={payment_url}" />', unsafe_allow_html=True)
            else:
                st.error("Please enter your email in the sidebar before unlocking premium.")

# Monetization Features in Sidebar
with st.sidebar:
    st.markdown("---")
    st.subheader("Monetization Addons")
    st.write("1. **Affiliate Products** (Books/Courses)")
    st.write("2. **Sponsored Challenges**")
    st.write("3. **Corporate Training Packages**")

# Community Features
st.markdown("---")
st.subheader("Community Challenges")
col1, col2 = st.columns(2)
with col1:
    st.write("**Most Popular Challenge**")
    st.write("30-Day Public Speaking Mastery")
with col2:
    st.write("**Leaderboard**")
    st.write("1. User123 - 450 pts")
