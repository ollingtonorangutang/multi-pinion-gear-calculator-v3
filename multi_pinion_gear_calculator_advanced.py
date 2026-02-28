import streamlit as st
import pandas as pd
import math
import matplotlib.pyplot as plt

# ----------------------------
# Helper Functions
# ----------------------------

def center_distance(module, z_pin, z_internal, x_pin, x_internal, helix_angle):
    beta = math.radians(helix_angle)
    return module * (z_pin + z_internal) / (2 * math.cos(beta)) + module * (x_pin + x_internal)

def calculate_profile_shift(a, module, z_pin, z_internal, x_internal, helix_angle):
    beta = math.radians(helix_angle)
    return (a * math.cos(beta) - module * (z_pin + z_internal)/2)/module - x_internal

def contact_ratio(face_width, module, z_pin, z_internal, helix_angle, gear_type):
    beta = math.radians(helix_angle)
    ratio = (face_width * math.cos(beta)) / (math.pi * module) * math.sqrt((z_pin + z_internal)/(2 * z_pin * z_internal))
    if gear_type == "Herringbone":
        ratio *= 2
    return ratio

def efficiency(mu, helix_angle, gear_type):
    beta = math.radians(helix_angle)
    if gear_type == "Spur":
        return 1 - mu * 0.01
    eta = 1 - mu * math.tan(beta)
    if gear_type == "Herringbone":
        eta = 1 - 2 * mu * math.tan(beta)
    return max(min(eta,1),0)

def bending_stress(F_t, face_width, module, gear_type):
    sigma = F_t / (face_width * module)
    if gear_type == "Herringbone":
        sigma /= math.sqrt(2)
    return sigma

def contact_stress(F_t, face_width, module, gear_type):
    sigma = F_t / (face_width * module)
    if gear_type == "Herringbone":
        sigma /= math.sqrt(2)
    return sigma

def specific_sliding(z_pin, z_internal):
    return (z_internal - z_pin) / (z_internal + z_pin)

# ----------------------------
# Streamlit UI
# ----------------------------

st.title("Multi-Pinion Internal Gear Calculator")

gear_type = st.selectbox("Gear Type", ["Spur", "Helical", "Herringbone"])

module = st.number_input("Gear Module (mm)", value=2.0)
face_width = st.number_input("Face Width (mm)", value=20.0)
z_internal = st.number_input("Internal Gear Teeth", value=60)
x_internal = st.number_input("Internal Gear Profile Shift", value=0.0)
helix_angle = st.number_input("Helix Angle (deg)", value=15.0)
mu = st.number_input("Friction Coefficient", value=0.05)
power = st.number_input("Power Transmitted (W)", value=1000.0)
backlash_allowed = st.number_input("Tangential Backlash Allowed (mm)", value=0.1)

st.write("### Pinion Inputs (5 Pinions)")

z_pins = []
a_centers = []

cols = st.columns(5)
for i in range(5):
    with cols[i]:
        z = st.number_input(f"Pinion {i+1} Teeth", value=12 + i*2)
        a = st.number_input(f"Center Distance {i+1} (mm)", value=40 + i*2)
        z_pins.append(z)
        a_centers.append(a)

results = []
x_values = []

for i in range(5):

    helix = 0 if gear_type == "Spur" else helix_angle

    x_pin = calculate_profile_shift(
        a_centers[i], module, z_pins[i], z_internal, x_internal, helix
    )

    # Backlash adjustment
    if gear_type == "Herringbone":
        x_pin += (backlash_allowed / 2) / (module * math.pi)
    else:
        x_pin += backlash_allowed / (module * math.pi)

    x_values.append(x_pin)

    a_actual = center_distance(module, z_pins[i], z_internal, x_pin, x_internal, helix)

    ratio = z_internal / z_pins[i]

    cr = contact_ratio(face_width, module, z_pins[i], z_internal, helix, gear_type)

    eff = efficiency(mu, helix, gear_type)

    torque = power / (2 * math.pi * 1500 / 60)  # assume 1500 rpm input
    F_t = 2 * torque / (module * z_pins[i] / 1000)

    sigma_b = bending_stress(F_t, face_width, module, gear_type)
    sigma_c = contact_stress(F_t, face_width, module, gear_type)
    slide = specific_sliding(z_pins[i], z_internal)

    results.append({
        "Pinion": i+1,
        "Profile Shift (x)": round(x_pin, 4),
        "Centre Distance Error (mm)": round(a_actual - a_centers[i], 4),
        "Transmission Ratio": round(ratio, 3),
        "Contact Ratio": round(cr, 3),
        "Specific Sliding": round(slide, 3),
        "Efficiency (%)": round(eff * 100, 2),
        "Bending Stress (MPa)": round(sigma_b, 2),
        "Contact Stress (MPa)": round(sigma_c, 2)
    })

df = pd.DataFrame(results)

st.write("### Results")
st.dataframe(df)

st.write("### Profile Shift vs Pinion Number")
plt.figure()
plt.plot(range(1,6), x_values, marker='o')
plt.xlabel("Pinion Number")
plt.ylabel("Profile Shift (x)")
plt.grid(True)
st.pyplot(plt)