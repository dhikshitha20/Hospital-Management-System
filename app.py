import streamlit as st
import pandas as pd
import sqlite3
from database import init_db, get_connection
from fpdf import FPDF
import datetime
import tempfile
import os

# Page config
st.set_page_config(page_title="Hospital Management System", page_icon="🏥", layout="wide")

# Init DB
init_db()

# CSS
st.markdown("""
<style>
    .stApp { background-color: #FDF6F0 !important; }
    [data-testid="stAppViewContainer"] { background-color: #FDF6F0 !important; }
    [data-testid="stHeader"] { background-color: #FDF6F0 !important; }
    html, body, p, span, div, label { color: #1A1A1A !important; }
    h1, h2, h3 { color: #1A1A1A !important; font-family: 'Georgia', serif !important; }
    .stButton > button {
        background-color: #1A1A1A !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: none !important;
    }
    .stButton > button:hover { background-color: #333333 !important; }
    .stTextInput input, .stSelectbox select, .stNumberInput input {
        background-color: #FFFFFF !important;
        color: #1A1A1A !important;
        border: 1.5px solid #E8C9B0 !important;
        border-radius: 8px !important;
    }
    .stat-card {
        background: #FFF8F4;
        border-radius: 14px;
        padding: 20px;
        border: 1px solid #E8C9B0;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    [data-testid="stSidebar"] { background-color: #FFF0E8 !important; }
</style>
""", unsafe_allow_html=True)

# Helper functions
def get_patients():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM patients", conn)
    conn.close()
    return df

def get_doctors():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM doctors", conn)
    conn.close()
    return df

def get_appointments():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT a.id, p.name as patient, d.name as doctor,
               a.date, a.time, a.status, a.notes
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN doctors d ON a.doctor_id = d.id
    """, conn)
    conn.close()
    return df

def get_records():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT r.id, p.name as patient, d.name as doctor,
               r.diagnosis, r.prescription, r.date
        FROM medical_records r
        JOIN patients p ON r.patient_id = p.id
        JOIN doctors d ON r.doctor_id = d.id
    """, conn)
    conn.close()
    return df

# Sidebar
st.sidebar.markdown("<h2 style='color:#1A1A1A'>🏥 HMS</h2>", unsafe_allow_html=True)
page = st.sidebar.radio("Navigate", ["Dashboard", "Patients", "Doctors", "Appointments", "Medical Records"])

# Dashboard
if page == "Dashboard":
    st.markdown("<h1 style='text-align:center'>🏥 Hospital Management System</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#555'>Manage patients, doctors, appointments and records</p>", unsafe_allow_html=True)
    st.markdown("---")

    patients = get_patients()
    doctors = get_doctors()
    conn = get_connection()
    appt_count = pd.read_sql("SELECT COUNT(*) as c FROM appointments", conn).iloc[0]['c']
    records_count = pd.read_sql("SELECT COUNT(*) as c FROM medical_records", conn).iloc[0]['c']
    conn.close()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<div class='stat-card'><h2>{len(patients)}</h2><p>Total Patients</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='stat-card'><h2>{len(doctors)}</h2><p>Total Doctors</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='stat-card'><h2>{appt_count}</h2><p>Appointments</p></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='stat-card'><h2>{records_count}</h2><p>Medical Records</p></div>", unsafe_allow_html=True)

    if len(patients) > 0:
        st.markdown("### Recent Patients")
        st.dataframe(patients.tail(5), use_container_width=True)

# Patients
elif page == "Patients":
    st.markdown("## 👤 Patient Management")
    tab1, tab2 = st.tabs(["View Patients", "Add Patient"])

    with tab1:
        search = st.text_input("Search by name")
        patients = get_patients()
        if search:
            patients = patients[patients['name'].str.contains(search, case=False)]
        st.dataframe(patients, use_container_width=True)

        if len(patients) > 0:
            def generate_patient_pdf():
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Helvetica", "B", 16)
                pdf.cell(0, 12, "Patient Report", ln=True, align="C")
                pdf.set_font("Helvetica", "", 11)
                pdf.cell(0, 8, f"Generated: {datetime.datetime.now().strftime('%d %B %Y')}", ln=True, align="C")
                pdf.ln(6)
                pdf.set_font("Helvetica", "B", 11)
                for col in ['id', 'name', 'age', 'gender', 'phone', 'blood_group']:
                    pdf.cell(30, 8, str(col).upper(), border=1)
                pdf.ln()
                pdf.set_font("Helvetica", "", 10)
                for _, row in patients.iterrows():
                    for col in ['id', 'name', 'age', 'gender', 'phone', 'blood_group']:
                        pdf.cell(30, 8, str(row.get(col, '')), border=1)
                    pdf.ln()
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
                    pdf.output(f.name)
                    return f.name
            pdf_path = generate_patient_pdf()
            with open(pdf_path, "rb") as f:
                st.download_button("📄 Download Patient Report", data=f,
                    file_name="patients_report.pdf", mime="application/pdf")
            os.unlink(pdf_path)

    with tab2:
        st.markdown("### Add New Patient")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name")
            age = st.number_input("Age", min_value=0, max_value=150, value=25)
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            phone = st.text_input("Phone Number")
        with col2:
            address = st.text_area("Address", height=100)
            blood_group = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])

        if st.button("Add Patient"):
            if name:
                conn = get_connection()
                conn.execute("INSERT INTO patients (name, age, gender, phone, address, blood_group) VALUES (?,?,?,?,?,?)",
                    (name, age, gender, phone, address, blood_group))
                conn.commit()
                conn.close()
                st.success(f"Patient {name} added successfully!")
            else:
                st.error("Please enter patient name!")

# Doctors
elif page == "Doctors":
    st.markdown("## 👨‍⚕️ Doctor Management")
    tab1, tab2 = st.tabs(["View Doctors", "Add Doctor"])

    with tab1:
        doctors = get_doctors()
        st.dataframe(doctors, use_container_width=True)

    with tab2:
        st.markdown("### Add New Doctor")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Doctor Name")
            specialization = st.selectbox("Specialization", [
                "General Physician", "Cardiologist", "Neurologist",
                "Orthopedic", "Pediatrician", "Dermatologist",
                "ENT", "Gynecologist", "Psychiatrist", "Oncologist"
            ])
            phone = st.text_input("Phone")
        with col2:
            email = st.text_input("Email")
            available_days = st.multiselect("Available Days",
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])

        if st.button("Add Doctor"):
            if name:
                conn = get_connection()
                conn.execute("INSERT INTO doctors (name, specialization, phone, email, available_days) VALUES (?,?,?,?,?)",
                    (name, specialization, phone, email, ", ".join(available_days)))
                conn.commit()
                conn.close()
                st.success(f"Dr. {name} added successfully!")
            else:
                st.error("Please enter doctor name!")

# Appointments
elif page == "Appointments":
    st.markdown("## 📅 Appointment Management")
    tab1, tab2 = st.tabs(["View Appointments", "Book Appointment"])

    with tab1:
        try:
            appointments = get_appointments()
            st.dataframe(appointments, use_container_width=True)
        except:
            st.info("No appointments yet.")

    with tab2:
        st.markdown("### Book New Appointment")
        patients = get_patients()
        doctors = get_doctors()

        if len(patients) == 0 or len(doctors) == 0:
            st.warning("Please add patients and doctors first!")
        else:
            col1, col2 = st.columns(2)
            with col1:
                patient = st.selectbox("Select Patient", patients['name'].tolist())
                doctor = st.selectbox("Select Doctor", doctors['name'].tolist())
                date = st.date_input("Appointment Date")
            with col2:
                time = st.time_input("Appointment Time")
                status = st.selectbox("Status", ["Scheduled", "Completed", "Cancelled"])
                notes = st.text_area("Notes", height=100)

            if st.button("Book Appointment"):
                patient_id = patients[patients['name'] == patient].iloc[0]['id']
                doctor_id = doctors[doctors['name'] == doctor].iloc[0]['id']
                conn = get_connection()
                conn.execute("INSERT INTO appointments (patient_id, doctor_id, date, time, status, notes) VALUES (?,?,?,?,?,?)",
                    (patient_id, doctor_id, str(date), str(time), status, notes))
                conn.commit()
                conn.close()
                st.success("Appointment booked successfully!")

# Medical Records
elif page == "Medical Records":
    st.markdown("## 💊 Medical Records")
    tab1, tab2 = st.tabs(["View Records", "Add Record"])

    with tab1:
        try:
            records = get_records()
            st.dataframe(records, use_container_width=True)
        except:
            st.info("No records yet.")

    with tab2:
        st.markdown("### Add Medical Record")
        patients = get_patients()
        doctors = get_doctors()

        if len(patients) == 0 or len(doctors) == 0:
            st.warning("Please add patients and doctors first!")
        else:
            col1, col2 = st.columns(2)
            with col1:
                patient = st.selectbox("Select Patient", patients['name'].tolist())
                doctor = st.selectbox("Select Doctor", doctors['name'].tolist())
                date = st.date_input("Date")
            with col2:
                diagnosis = st.text_area("Diagnosis", height=100)
                prescription = st.text_area("Prescription", height=100)

            if st.button("Save Record"):
                patient_id = patients[patients['name'] == patient].iloc[0]['id']
                doctor_id = doctors[doctors['name'] == doctor].iloc[0]['id']
                conn = get_connection()
                conn.execute("INSERT INTO medical_records (patient_id, doctor_id, diagnosis, prescription, date) VALUES (?,?,?,?,?)",
                    (patient_id, doctor_id, diagnosis, prescription, str(date)))
                conn.commit()
                conn.close()
                st.success("Medical record saved successfully!")