import streamlit as st
import re
import string
import zxcvbn
import time
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

# Set page configuration
st.set_page_config(
    page_title="Password Strength Meter",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stTextInput > div > div > input {
        font-size: 20px;
        padding: 12px;
        border-radius: 8px;
    }
    .password-feedback {
        margin-top: 20px;
        padding: 15px;
        border-radius: 8px;
    }
    .password-meter {
        height: 10px;
        border-radius: 5px;
        margin: 15px 0;
    }
    .header-container {
        display: flex;
        align-items: center;
        margin-bottom: 30px;
    }
    .header-text {
        margin-left: 15px;
    }
    .password-indicator {
        padding: 10px 15px;
        border-radius: 5px;
        font-weight: bold;
        display: inline-block;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Define functions for password analysis
def analyze_password(password):
    """Analyze password strength using multiple criteria"""
    if not password:
        return {
            "score": 0,
            "strength": "Empty",
            "feedback": {"warning": "Password is empty", "suggestions": ["Enter a password"]},
            "time_to_crack": "Instant",
            "entropy": 0,
            "length": 0,
            "has_lowercase": False,
            "has_uppercase": False,
            "has_digits": False,
            "has_special": False,
            "has_common_patterns": False,
            "is_common_password": False
        }
    
    # Use zxcvbn for comprehensive analysis
    result = zxcvbn.zxcvbn(password)
    
    # Additional checks
    has_lowercase = bool(re.search(r'[a-z]', password))
    has_uppercase = bool(re.search(r'[A-Z]', password))
    has_digits = bool(re.search(r'[0-9]', password))
    has_special = bool(re.search(f'[{re.escape(string.punctuation)}]', password))
    
    # Check if password contains common patterns
    common_patterns = [
        r'12345', r'qwerty', r'password', r'admin', r'welcome',
        r'abc123', r'123abc', r'111111', r'555555', r'football',
        r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$'  # Common policy pattern
    ]
    has_common_patterns = any(re.search(pattern, password, re.IGNORECASE) for pattern in common_patterns)
    
    # Common passwords check (simplified - in production use a real database)
    common_passwords = ['password', 'admin', '12345', 'welcome', 'abc123', 'qwerty', 'iloveyou']
    is_common_password = password.lower() in common_passwords
    
    # Map score to strength description
    strength_mapping = {
        0: "Very Weak",
        1: "Weak",
        2: "Medium",
        3: "Strong",
        4: "Very Strong"
    }
    
    return {
        "score": result['score'],
        "strength": strength_mapping[result['score']],
        "feedback": result['feedback'],
        "time_to_crack": result['crack_times_display']['offline_slow_hashing_1e4_per_second'],
        "entropy": result['guesses_log10'],
        "length": len(password),
        "has_lowercase": has_lowercase,
        "has_uppercase": has_uppercase,
        "has_digits": has_digits,
        "has_special": has_special,
        "has_common_patterns": has_common_patterns,
        "is_common_password": is_common_password
    }

def get_strength_color(score):
    """Return color based on password strength score"""
    colors = {
        0: "#FF4136",  # Red
        1: "#FF851B",  # Orange
        2: "#FFDC00",  # Yellow
        3: "#2ECC40",  # Green
        4: "#0074D9"   # Blue
    }
    return colors.get(score, "#AAAAAA")  # Grey as default

def create_bar_chart(analysis):
    """Create a horizontal bar chart showing password elements"""
    factors = [
        {"name": "Length", "value": min(analysis["length"] / 12, 1) * 100 if analysis["length"] > 0 else 0},
        {"name": "Lowercase", "value": 100 if analysis["has_lowercase"] else 0},
        {"name": "Uppercase", "value": 100 if analysis["has_uppercase"] else 0},
        {"name": "Digits", "value": 100 if analysis["has_digits"] else 0},
        {"name": "Special Chars", "value": 100 if analysis["has_special"] else 0},
        {"name": "No Common Patterns", "value": 0 if analysis["has_common_patterns"] else 100},
        {"name": "Uniqueness", "value": 0 if analysis["is_common_password"] else 100}
    ]
    
    df = pd.DataFrame(factors)
    
    plt.figure(figsize=(10, 5))
    chart = sns.barplot(x="value", y="name", data=df, palette="viridis")
    plt.xlim(0, 100)
    plt.xlabel("Score")
    plt.title("Password Strength Factors")
    
    # Convert plot to base64 for embedding
    buffer = BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight")
    buffer.seek(0)
    chart_data = base64.b64encode(buffer.read()).decode()
    plt.close()
    
    return chart_data

def generate_password_suggestions():
    """Generate helpful suggestions for creating strong passwords"""
    return [
        "Use at least 12 characters - longer is generally better",
        "Mix uppercase and lowercase letters, numbers, and special characters",
        "Avoid using personal information like your name, birthdate, or common words",
        "Consider using a passphrase - multiple random words combined with numbers and symbols",
        "Don't reuse passwords across different accounts",
        "Use a password manager to generate and store complex passwords",
        "Avoid common password patterns and predictable character substitutions"
    ]

def main():
    """Main application function"""
    # Header with logo
    st.markdown(
        """
        <div class="header-container">
            <div style="font-size: 42px;">🔒</div>
            <div class="header-text">
                <h1>Password Strength Meter</h1>
                <p>Evaluate and improve your password security</p>
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Create two columns
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Password input with toggle for visibility
        st.subheader("Enter Your Password")
        show_password = st.checkbox("Show password", value=False)
        password_input_type = "text" if show_password else "password"
        
        password = st.text_input(
            "Type or paste your password here",
            type=password_input_type,
            key="password_input",
            help="Your password is analyzed locally and not stored or transmitted",
            placeholder="Enter password to analyze..."
        )
        
        if password:
            # Add a small loading effect
            with st.spinner("Analyzing password..."):
                time.sleep(0.5)  # Small delay for UX
                analysis = analyze_password(password)
            
            score = analysis["score"]
            strength = analysis["strength"]
            color = get_strength_color(score)
            
            # Display strength meter
            st.markdown(f"""
            <h3>Password Strength: 
                <span class="password-indicator" style="background-color: {color}; color: {'white' if score < 3 else 'black'}">
                    {strength}
                </span>
            </h3>
            <div class="password-meter" style="background: linear-gradient(to right, {color} {(score + 1) * 20}%, #f0f2f6 {(score + 1) * 20}%);"></div>
            """, unsafe_allow_html=True)
            
            # Display time to crack
            st.markdown(f"""
            <div style="margin: 20px 0;">
                <h4>Estimated time to crack: <span style="color: {color}; font-weight: bold;">{analysis["time_to_crack"]}</span></h4>
            </div>
            """, unsafe_allow_html=True)
            
            # Display detailed breakdown
            with st.expander("See detailed analysis", expanded=True):
                st.markdown("### Password Properties")
                
                # Create two columns for the properties
                prop_col1, prop_col2 = st.columns(2)
                
                with prop_col1:
                    st.markdown(f"- **Length:** {analysis['length']} characters")
                    st.markdown(f"- **Contains lowercase:** {'✅' if analysis['has_lowercase'] else '❌'}")
                    st.markdown(f"- **Contains uppercase:** {'✅' if analysis['has_uppercase'] else '❌'}")
                    st.markdown(f"- **Contains digits:** {'✅' if analysis['has_digits'] else '❌'}")
                
                with prop_col2:
                    st.markdown(f"- **Contains special characters:** {'✅' if analysis['has_special'] else '❌'}")
                    st.markdown(f"- **Has common patterns:** {'❌' if analysis['has_common_patterns'] else '✅'}")
                    st.markdown(f"- **Is a common password:** {'❌' if analysis['is_common_password'] else '✅'}")
                    st.markdown(f"- **Entropy score:** {analysis['entropy']:.2f}")
                
                # Display feedback from zxcvbn
                if analysis["feedback"]["warning"]:
                    st.markdown(f"### Warning\n{analysis['feedback']['warning']}", unsafe_allow_html=True)
                
                if analysis["feedback"]["suggestions"]:
                    st.markdown("### Specific Suggestions")
                    for suggestion in analysis["feedback"]["suggestions"]:
                        st.markdown(f"- {suggestion}")
                
                # Display chart
                chart_data = create_bar_chart(analysis)
                st.markdown(f"""
                ### Strength Factors
                <img src="data:image/png;base64,{chart_data}" width="100%">
                """, unsafe_allow_html=True)
                
        else:
            # Instructions when no password is entered
            st.info("Enter a password above to see its strength analysis")
    
    with col2:
        # Tips and best practices
        st.markdown("""
        ## Password Best Practices
        
        Creating strong, secure passwords is essential for protecting your accounts and personal information.
        """)
        
        with st.expander("Tips for Strong Passwords", expanded=True):
            suggestions = generate_password_suggestions()
            for i, suggestion in enumerate(suggestions, 1):
                st.markdown(f"{i}. {suggestion}")
        
        # Common password mistakes
        with st.expander("Common Password Mistakes to Avoid"):
            st.markdown("""
            - Using the same password for multiple accounts
            - Using easily guessable information (birthdays, names)
            - Simple word + number combinations (password123)
            - Using sequential keyboard patterns (qwerty, 12345)
            - Making minor changes to an existing password
            - Using words spelled backward or with obvious substitutions
            - Sharing passwords with others
            """)
        
        # About section
        with st.expander("About This Tool"):
            st.markdown("""
            This Password Strength Meter evaluates your password's security using multiple advanced algorithms and criteria:
            
            - **Length and complexity** - longer passwords with varied characters are stronger
            - **Pattern recognition** - identifies common patterns that make passwords predictable
            - **Dictionary attacks** - checks against commonly used passwords
            - **Entropy calculation** - measures randomness and unpredictability
            
            All analysis is performed locally in your browser. Your password is never stored or transmitted.
            """)
    
    # Footer
    st.markdown("""
    <div style="margin-top: 50px; text-align: center; color: #666; font-size: 14px;">
        <p>Password Strength Meter v1.0.0 | Developed with ❤️ for security</p>
        <p>This tool is meant for educational purposes. Always use additional security measures like 2FA.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()