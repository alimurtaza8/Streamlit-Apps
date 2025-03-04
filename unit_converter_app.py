import streamlit as st
import pandas as pd
from typing import Dict, List, Tuple, Callable
import os

# Configuration and constants
CONVERSION_TYPES = {
    "Length": {
        "units": ["Meter", "Kilometer", "Centimeter", "Millimeter", "Mile", "Yard", "Foot", "Inch"],
        "conversions": {
            "Meter": {"Meter": 1, "Kilometer": 0.001, "Centimeter": 100, "Millimeter": 1000, "Mile": 0.000621371, "Yard": 1.09361, "Foot": 3.28084, "Inch": 39.3701},
            "Kilometer": {"Meter": 1000, "Kilometer": 1, "Centimeter": 100000, "Millimeter": 1000000, "Mile": 0.621371, "Yard": 1093.61, "Foot": 3280.84, "Inch": 39370.1},
            "Centimeter": {"Meter": 0.01, "Kilometer": 0.00001, "Centimeter": 1, "Millimeter": 10, "Mile": 0.00000621371, "Yard": 0.0109361, "Foot": 0.0328084, "Inch": 0.393701},
            "Millimeter": {"Meter": 0.001, "Kilometer": 0.000001, "Centimeter": 0.1, "Millimeter": 1, "Mile": 0.000000621371, "Yard": 0.00109361, "Foot": 0.00328084, "Inch": 0.0393701},
            "Mile": {"Meter": 1609.34, "Kilometer": 1.60934, "Centimeter": 160934, "Millimeter": 1609340, "Mile": 1, "Yard": 1760, "Foot": 5280, "Inch": 63360},
            "Yard": {"Meter": 0.9144, "Kilometer": 0.0009144, "Centimeter": 91.44, "Millimeter": 914.4, "Mile": 0.000568182, "Yard": 1, "Foot": 3, "Inch": 36},
            "Foot": {"Meter": 0.3048, "Kilometer": 0.0003048, "Centimeter": 30.48, "Millimeter": 304.8, "Mile": 0.000189394, "Yard": 0.333333, "Foot": 1, "Inch": 12},
            "Inch": {"Meter": 0.0254, "Kilometer": 0.0000254, "Centimeter": 2.54, "Millimeter": 25.4, "Mile": 0.0000157828, "Yard": 0.0277778, "Foot": 0.0833333, "Inch": 1}
        }
    },
    "Weight": {
        "units": ["Kilogram", "Gram", "Milligram", "Metric Ton", "Pound", "Ounce", "Stone"],
        "conversions": {
            "Kilogram": {"Kilogram": 1, "Gram": 1000, "Milligram": 1000000, "Metric Ton": 0.001, "Pound": 2.20462, "Ounce": 35.274, "Stone": 0.157473},
            "Gram": {"Kilogram": 0.001, "Gram": 1, "Milligram": 1000, "Metric Ton": 0.000001, "Pound": 0.00220462, "Ounce": 0.035274, "Stone": 0.000157473},
            "Milligram": {"Kilogram": 0.000001, "Gram": 0.001, "Milligram": 1, "Metric Ton": 0.000000001, "Pound": 0.00000220462, "Ounce": 0.000035274, "Stone": 0.000000157473},
            "Metric Ton": {"Kilogram": 1000, "Gram": 1000000, "Milligram": 1000000000, "Metric Ton": 1, "Pound": 2204.62, "Ounce": 35274, "Stone": 157.473},
            "Pound": {"Kilogram": 0.453592, "Gram": 453.592, "Milligram": 453592, "Metric Ton": 0.000453592, "Pound": 1, "Ounce": 16, "Stone": 0.0714286},
            "Ounce": {"Kilogram": 0.0283495, "Gram": 28.3495, "Milligram": 28349.5, "Metric Ton": 0.0000283495, "Pound": 0.0625, "Ounce": 1, "Stone": 0.00446429},
            "Stone": {"Kilogram": 6.35029, "Gram": 6350.29, "Milligram": 6350290, "Metric Ton": 0.00635029, "Pound": 14, "Ounce": 224, "Stone": 1}
        }
    },
    "Temperature": {
        "units": ["Celsius", "Fahrenheit", "Kelvin"],
        "conversions": {
            "Celsius": {"Celsius": lambda x: x, "Fahrenheit": lambda x: (x * 9/5) + 32, "Kelvin": lambda x: x + 273.15},
            "Fahrenheit": {"Celsius": lambda x: (x - 32) * 5/9, "Fahrenheit": lambda x: x, "Kelvin": lambda x: (x - 32) * 5/9 + 273.15},
            "Kelvin": {"Celsius": lambda x: x - 273.15, "Fahrenheit": lambda x: (x - 273.15) * 9/5 + 32, "Kelvin": lambda x: x}
        }
    },
    "Volume": {
        "units": ["Liter", "Milliliter", "Cubic Meter", "Gallon (US)", "Quart (US)", "Pint (US)", "Cup", "Fluid Ounce (US)"],
        "conversions": {
            "Liter": {"Liter": 1, "Milliliter": 1000, "Cubic Meter": 0.001, "Gallon (US)": 0.264172, "Quart (US)": 1.05669, "Pint (US)": 2.11338, "Cup": 4.22675, "Fluid Ounce (US)": 33.814},
            "Milliliter": {"Liter": 0.001, "Milliliter": 1, "Cubic Meter": 0.000001, "Gallon (US)": 0.000264172, "Quart (US)": 0.00105669, "Pint (US)": 0.00211338, "Cup": 0.00422675, "Fluid Ounce (US)": 0.033814},
            "Cubic Meter": {"Liter": 1000, "Milliliter": 1000000, "Cubic Meter": 1, "Gallon (US)": 264.172, "Quart (US)": 1056.69, "Pint (US)": 2113.38, "Cup": 4226.75, "Fluid Ounce (US)": 33814},
            "Gallon (US)": {"Liter": 3.78541, "Milliliter": 3785.41, "Cubic Meter": 0.00378541, "Gallon (US)": 1, "Quart (US)": 4, "Pint (US)": 8, "Cup": 16, "Fluid Ounce (US)": 128},
            "Quart (US)": {"Liter": 0.946353, "Milliliter": 946.353, "Cubic Meter": 0.000946353, "Gallon (US)": 0.25, "Quart (US)": 1, "Pint (US)": 2, "Cup": 4, "Fluid Ounce (US)": 32},
            "Pint (US)": {"Liter": 0.473176, "Milliliter": 473.176, "Cubic Meter": 0.000473176, "Gallon (US)": 0.125, "Quart (US)": 0.5, "Pint (US)": 1, "Cup": 2, "Fluid Ounce (US)": 16},
            "Cup": {"Liter": 0.236588, "Milliliter": 236.588, "Cubic Meter": 0.000236588, "Gallon (US)": 0.0625, "Quart (US)": 0.25, "Pint (US)": 0.5, "Cup": 1, "Fluid Ounce (US)": 8},
            "Fluid Ounce (US)": {"Liter": 0.0295735, "Milliliter": 29.5735, "Cubic Meter": 0.0000295735, "Gallon (US)": 0.0078125, "Quart (US)": 0.03125, "Pint (US)": 0.0625, "Cup": 0.125, "Fluid Ounce (US)": 1}
        }
    },
    "Time": {
        "units": ["Second", "Minute", "Hour", "Day", "Week", "Month", "Year"],
        "conversions": {
            "Second": {"Second": 1, "Minute": 1/60, "Hour": 1/3600, "Day": 1/86400, "Week": 1/604800, "Month": 1/2592000, "Year": 1/31536000},
            "Minute": {"Second": 60, "Minute": 1, "Hour": 1/60, "Day": 1/1440, "Week": 1/10080, "Month": 1/43200, "Year": 1/525600},
            "Hour": {"Second": 3600, "Minute": 60, "Hour": 1, "Day": 1/24, "Week": 1/168, "Month": 1/720, "Year": 1/8760},
            "Day": {"Second": 86400, "Minute": 1440, "Hour": 24, "Day": 1, "Week": 1/7, "Month": 1/30, "Year": 1/365},
            "Week": {"Second": 604800, "Minute": 10080, "Hour": 168, "Day": 7, "Week": 1, "Month": 0.23, "Year": 1/52},
            "Month": {"Second": 2592000, "Minute": 43200, "Hour": 720, "Day": 30, "Week": 4.35, "Month": 1, "Year": 1/12},
            "Year": {"Second": 31536000, "Minute": 525600, "Hour": 8760, "Day": 365, "Week": 52, "Month": 12, "Year": 1}
        }
    },
    "Area": {
        "units": ["Square Meter", "Square Kilometer", "Square Centimeter", "Square Millimeter", "Square Mile", "Square Yard", "Square Foot", "Square Inch", "Hectare", "Acre"],
        "conversions": {
            "Square Meter": {"Square Meter": 1, "Square Kilometer": 0.000001, "Square Centimeter": 10000, "Square Millimeter": 1000000, "Square Mile": 3.861e-7, "Square Yard": 1.19599, "Square Foot": 10.7639, "Square Inch": 1550, "Hectare": 0.0001, "Acre": 0.000247105},
            "Square Kilometer": {"Square Meter": 1000000, "Square Kilometer": 1, "Square Centimeter": 10000000000, "Square Millimeter": 1000000000000, "Square Mile": 0.386102, "Square Yard": 1195990, "Square Foot": 10763900, "Square Inch": 1.55e+9, "Hectare": 100, "Acre": 247.105},
            "Square Centimeter": {"Square Meter": 0.0001, "Square Kilometer": 1e-10, "Square Centimeter": 1, "Square Millimeter": 100, "Square Mile": 3.861e-11, "Square Yard": 0.000119599, "Square Foot": 0.00107639, "Square Inch": 0.155, "Hectare": 1e-8, "Acre": 2.47105e-8},
            "Square Millimeter": {"Square Meter": 0.000001, "Square Kilometer": 1e-12, "Square Centimeter": 0.01, "Square Millimeter": 1, "Square Mile": 3.861e-13, "Square Yard": 1.19599e-6, "Square Foot": 1.07639e-5, "Square Inch": 0.00155, "Hectare": 1e-10, "Acre": 2.47105e-10},
            "Square Mile": {"Square Meter": 2589990, "Square Kilometer": 2.58999, "Square Centimeter": 2.59e+10, "Square Millimeter": 2.59e+12, "Square Mile": 1, "Square Yard": 3097600, "Square Foot": 27878400, "Square Inch": 4.014e+9, "Hectare": 258.999, "Acre": 640},
            "Square Yard": {"Square Meter": 0.836127, "Square Kilometer": 8.36127e-7, "Square Centimeter": 8361.27, "Square Millimeter": 836127, "Square Mile": 3.22831e-7, "Square Yard": 1, "Square Foot": 9, "Square Inch": 1296, "Hectare": 8.36127e-5, "Acre": 0.000206612},
            "Square Foot": {"Square Meter": 0.092903, "Square Kilometer": 9.2903e-8, "Square Centimeter": 929.03, "Square Millimeter": 92903, "Square Mile": 3.587e-8, "Square Yard": 0.111111, "Square Foot": 1, "Square Inch": 144, "Hectare": 9.2903e-6, "Acre": 2.29568e-5},
            "Square Inch": {"Square Meter": 0.00064516, "Square Kilometer": 6.4516e-10, "Square Centimeter": 6.4516, "Square Millimeter": 645.16, "Square Mile": 2.491e-10, "Square Yard": 0.000771605, "Square Foot": 0.00694444, "Square Inch": 1, "Hectare": 6.4516e-8, "Acre": 1.59423e-7},
            "Hectare": {"Square Meter": 10000, "Square Kilometer": 0.01, "Square Centimeter": 100000000, "Square Millimeter": 10000000000, "Square Mile": 0.00386102, "Square Yard": 11959.9, "Square Foot": 107639, "Square Inch": 15500000, "Hectare": 1, "Acre": 2.47105},
            "Acre": {"Square Meter": 4046.86, "Square Kilometer": 0.00404686, "Square Centimeter": 40468600, "Square Millimeter": 4046860000, "Square Mile": 0.0015625, "Square Yard": 4840, "Square Foot": 43560, "Square Inch": 6272640, "Hectare": 0.404686, "Acre": 1}
        }
    },
    "Speed": {
        "units": ["Meter per Second", "Kilometer per Hour", "Mile per Hour", "Knot", "Foot per Second"],
        "conversions": {
            "Meter per Second": {"Meter per Second": 1, "Kilometer per Hour": 3.6, "Mile per Hour": 2.23694, "Knot": 1.94384, "Foot per Second": 3.28084},
            "Kilometer per Hour": {"Meter per Second": 0.277778, "Kilometer per Hour": 1, "Mile per Hour": 0.621371, "Knot": 0.539957, "Foot per Second": 0.911344},
            "Mile per Hour": {"Meter per Second": 0.44704, "Kilometer per Hour": 1.60934, "Mile per Hour": 1, "Knot": 0.868976, "Foot per Second": 1.46667},
            "Knot": {"Meter per Second": 0.514444, "Kilometer per Hour": 1.852, "Mile per Hour": 1.15078, "Knot": 1, "Foot per Second": 1.68781},
            "Foot per Second": {"Meter per Second": 0.3048, "Kilometer per Hour": 1.09728, "Mile per Hour": 0.681818, "Knot": 0.592484, "Foot per Second": 1}
        }
    },
    "Data": {
        "units": ["Bit", "Byte", "Kilobyte", "Megabyte", "Gigabyte", "Terabyte", "Petabyte"],
        "conversions": {
            "Bit": {"Bit": 1, "Byte": 0.125, "Kilobyte": 0.000125, "Megabyte": 1.25e-7, "Gigabyte": 1.25e-10, "Terabyte": 1.25e-13, "Petabyte": 1.25e-16},
            "Byte": {"Bit": 8, "Byte": 1, "Kilobyte": 0.001, "Megabyte": 1e-6, "Gigabyte": 1e-9, "Terabyte": 1e-12, "Petabyte": 1e-15},
            "Kilobyte": {"Bit": 8000, "Byte": 1000, "Kilobyte": 1, "Megabyte": 0.001, "Gigabyte": 1e-6, "Terabyte": 1e-9, "Petabyte": 1e-12},
            "Megabyte": {"Bit": 8000000, "Byte": 1000000, "Kilobyte": 1000, "Megabyte": 1, "Gigabyte": 0.001, "Terabyte": 1e-6, "Petabyte": 1e-9},
            "Gigabyte": {"Bit": 8000000000, "Byte": 1000000000, "Kilobyte": 1000000, "Megabyte": 1000, "Gigabyte": 1, "Terabyte": 0.001, "Petabyte": 1e-6},
            "Terabyte": {"Bit": 8000000000000, "Byte": 1000000000000, "Kilobyte": 1000000000, "Megabyte": 1000000, "Gigabyte": 1000, "Terabyte": 1, "Petabyte": 0.001},
            "Petabyte": {"Bit": 8000000000000000, "Byte": 1000000000000000, "Kilobyte": 1000000000000, "Megabyte": 1000000000, "Gigabyte": 1000000, "Terabyte": 1000, "Petabyte": 1}
        }
    }
}

# Helper functions
def convert_value(value: float, from_unit: str, to_unit: str, conversion_type: Dict) -> float:
    """Convert a value from one unit to another."""
    if conversion_type == "Temperature":
        conversion_func = CONVERSION_TYPES[conversion_type]["conversions"][from_unit][to_unit]
        return conversion_func(value)
    else:
        from_to_base = CONVERSION_TYPES[conversion_type]["conversions"][from_unit][from_unit]
        base_to_target = CONVERSION_TYPES[conversion_type]["conversions"][from_unit][to_unit]
        return value * base_to_target / from_to_base

def format_result(value: float) -> str:
    """Format the result with appropriate precision."""
    if abs(value) >= 1000000:
        return f"{value:.6e}"
    elif abs(value) >= 1:
        return f"{value:.6f}".rstrip('0').rstrip('.') if '.' in f"{value:.6f}" else f"{value:.6f}"
    else:
        return f"{value:.10f}".rstrip('0').rstrip('.') if '.' in f"{value:.10f}" else f"{value:.10f}"

# App structure
class UnitConverterApp:
    def __init__(self):
        """Initialize the Streamlit app with settings and state."""
        self.setup_page_config()
        self.initialize_session_state()
        self.setup_sidebar()
        
    def setup_page_config(self):
        """Configure the Streamlit page."""
        st.set_page_config(
            page_title="Professional Unit Converter",
            page_icon="🔄",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
    def initialize_session_state(self):
        """Initialize session state variables."""
        if "conversion_history" not in st.session_state:
            st.session_state.conversion_history = []
        if "dark_mode" not in st.session_state:
            st.session_state.dark_mode = False
            
    def setup_sidebar(self):
        """Set up the sidebar with app information and settings."""
        with st.sidebar:
            st.title("Unit Converter")
            st.subheader("Settings")
            
            st.session_state.dark_mode = st.toggle("Dark Mode", st.session_state.dark_mode)
            if st.session_state.dark_mode:
                self.apply_dark_mode()
                
            st.divider()
            st.subheader("About")
            st.write("""
            This professional unit converter allows you to convert between various units across 
            different measurement categories. Use the dropdown menus to select your desired conversion type,
            source unit, and target unit.
            """)
            
            st.divider()
            if st.button("Clear History", use_container_width=True):
                st.session_state.conversion_history = []
                st.success("Conversion history cleared!")
    
    def apply_dark_mode(self):
        """Apply dark mode styling using custom CSS."""
        st.markdown("""
        <style>
        .stApp {
            background-color: #121212;
            color: #E0E0E0;
        }
        .stTextInput, .stNumberInput, .stSelectbox {
            background-color: #2D2D2D;
            color: white;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
        }
        div[data-testid="stMarkdownContainer"] {
            color: #E0E0E0;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def display_header(self):
        """Display the app header."""
        st.title("Professional Unit Converter")
        st.markdown("Convert between units of measurement with precision and ease.")
        st.divider()
    
    def display_converter_interface(self):
        """Display the main converter interface."""
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Conversion type selection
            conversion_type = st.selectbox(
                "Select Conversion Type",
                options=list(CONVERSION_TYPES.keys()),
                index=0
            )
            
            # Get units for the selected conversion type
            available_units = CONVERSION_TYPES[conversion_type]["units"]
            
            # Unit selection
            from_unit = st.selectbox(
                "From Unit",
                options=available_units,
                index=0,
                key="from_unit"
            )
            
            to_unit = st.selectbox(
                "To Unit",
                options=available_units,
                index=1 if len(available_units) > 1 else 0,
                key="to_unit"
            )
            
            # Input value
            input_value = st.number_input(
                f"Enter value ({from_unit})",
                value=1.0,
                format="%f",
                step=0.1
            )
            
            # Convert button
            convert_pressed = st.button("Convert", use_container_width=True, type="primary")
            
        with col2:
            # Results panel
            st.markdown("### Conversion Result")
            
            if convert_pressed:
                try:
                    # Perform conversion
                    result = convert_value(input_value, from_unit, to_unit, conversion_type)
                    formatted_result = format_result(result)
                    
                    # Display result
                    result_text = f"{input_value} {from_unit} = {formatted_result} {to_unit}"
                    st.markdown(f"<h2 style='text-align: center;'>{result_text}</h2>", unsafe_allow_html=True)
                    
                    # Formula explanation
                    st.markdown("#### Conversion Details")
                    if conversion_type == "Temperature":
                        if from_unit == "Celsius" and to_unit == "Fahrenheit":
                            formula = f"°F = (°C × 9/5) + 32 = ({input_value} × 9/5) + 32 = {formatted_result}"
                        elif from_unit == "Celsius" and to_unit == "Kelvin":
                            formula = f"K = °C + 273.15 = {input_value} + 273.15 = {formatted_result}"
                        elif from_unit == "Fahrenheit" and to_unit == "Celsius":
                            formula = f"°C = (°F - 32) × 5/9 = ({input_value} - 32) × 5/9 = {formatted_result}"
                        elif from_unit == "Fahrenheit" and to_unit == "Kelvin":
                            formula = f"K = (°F - 32) × 5/9 + 273.15 = ({input_value} - 32) × 5/9 + 273.15 = {formatted_result}"
                        elif from_unit == "Kelvin" and to_unit == "Celsius":
                            formula = f"°C = K - 273.15 = {input_value} - 273.15 = {formatted_result}"
                        elif from_unit == "Kelvin" and to_unit == "Fahrenheit":
                            formula = f"°F = (K - 273.15) × 9/5 + 32 = ({input_value} - 273.15) × 9/5 + 32 = {formatted_result}"
                        else:  # Same unit
                            formula = f"{from_unit} = {to_unit} (No conversion needed)"
                    else:
                        conversion_factor = CONVERSION_TYPES[conversion_type]["conversions"][from_unit][to_unit]
                        formula = f"{input_value} {from_unit} × {conversion_factor} = {formatted_result} {to_unit}"
                    
                    st.markdown(f"**Formula:** {formula}")
                    
                    # Add to history
                    conversion_record = {
                        "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "conversion_type": conversion_type,
                        "from_unit": from_unit,
                        "to_unit": to_unit,
                        "input_value": input_value,
                        "result": formatted_result
                    }
                    st.session_state.conversion_history.append(conversion_record)
                    
                except Exception as e:
                    st.error(f"Error performing conversion: {str(e)}")
            
            # Conversion explanation
            with st.expander("About this conversion"):
                if conversion_type == "Length":
                    st.write("""
                    Length conversion is used to convert between different units of distance measurement.
                    Common applications include construction, navigation, and manufacturing.
                    """)
                elif conversion_type == "Weight":
                    st.write("""
                    Weight conversion is used to convert between different units of mass.
                    Common applications include cooking, shipping, and scientific measurements.
                    """)
                elif conversion_type == "Temperature":
                    st.write("""
                    Temperature conversion involves different scales like Celsius, Fahrenheit, and Kelvin.
                    These conversions are important in weather forecasting, cooking, and scientific research.
                    """)
                elif conversion_type == "Volume":
                    st.write("""
                    Volume conversion is used to convert between different units of three-dimensional space.
                    Common applications include cooking, manufacturing, and liquid measurements.
                    """)
                elif conversion_type == "Time":
                    st.write("""
                    Time conversion is used to convert between different units of time measurement.
                    Important in scheduling, project management, and scientific calculations.
                    """)
                elif conversion_type == "Area":
                    st.write("""
                    Area conversion is used to convert between different units of two-dimensional space.
                    Common in real estate, land management, and construction.
                    """)
                elif conversion_type == "Speed":
                    st.write("""
                    Speed conversion is used to convert between different units of velocity.
                    Common in transportation, physics, and weather forecasting.
                    """)
                elif conversion_type == "Data":
                    st.write("""
                    Data conversion is used to convert between different units of digital information.
                    Essential in computing, telecommunications, and data storage.
                    """)
    
    def display_history(self):
        """Display the conversion history."""
        st.markdown("### Conversion History")
        
        if not st.session_state.conversion_history:
            st.info("No conversion history available. Make a conversion to see it here.")
            return
        
        # Create DataFrame from history
        history_df = pd.DataFrame(st.session_state.conversion_history)
        history_df = history_df.sort_values(by="timestamp", ascending=False).reset_index(drop=True)
        
        # Display as table
        st.dataframe(
            history_df,
            column_config={
                "timestamp": "Time",
                "conversion_type": "Type",
                "from_unit": "From",
                "to_unit": "To",
                "input_value": "Input Value",
                "result": "Result"
            },
            use_container_width=True,
            hide_index=True
        )
    
    def run(self):
        """Run the Streamlit app."""
        self.display_header()
        self.display_converter_interface()
        st.divider()
        self.display_history()

# Run the app
if __name__ == "__main__":
    app = UnitConverterApp()
    app.run()