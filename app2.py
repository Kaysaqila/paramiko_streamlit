import streamlit as st
import pandas as pd
import plotly.express as px
import paramiko
from server_monitor import get_server_stats

# Fungsi untuk memuat file CSS
# def load_css(file_name):
#     with open(file_name, "r") as f:
#         css = f"<style>{f.read()}</style>"
#         st.markdown(css, unsafe_allow_html=True)

# Konfigurasi halaman (harus paling atas)
st.set_page_config(page_title="SSH Server Monitoring", layout="wide")

# Load CSS
# load_css("styles.css")

st.markdown(
    """
    <style>
    /* Container utama dashboard */
    .main {
        background-color: ##7d45ba;
        padding: 30px;
        border-radius: 10px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
    }

    /* Header */
    h1 {
        color: #333;
        text-align: center;
        font-size: 28px;
        font-weight: bold;
    }

    /* Metric Box */
    div[data-testid="stMetric"] {
        background: linear-gradient(to right, #007bff, #6610f2) !important;
        color: white !important;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        font-weight: bold;
    }

    /* Tombol */
    .stButton>button {
        background-color: #007bff !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: bold;
        padding: 10px 20px !important;
        font-size: 16px !important;
        transition: 0.3s;
    }

    .stButton>button:hover {
        background-color: #0056b3 !important;
        box-shadow: 0px 4px 10px rgba(0, 123, 255, 0.4);
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #e9ecef;
        padding: 20px;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# Fungsi untuk login SSH
def check_ssh_login(server_ip, username, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(server_ip, username=username, password=password, timeout=5)
        client.close()
        return True, "Login SSH Berhasil!"
    except Exception as e:
        return False, f"Login SSH Gagal: {str(e)}"

# Fungsi untuk menjalankan perintah SSH
def run_ssh_command(server_ip, username, password, command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(server_ip, username=username, password=password, timeout=5)
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        client.close()
        return output if output else error
    except Exception as e:
        return f"Error: {str(e)}"

# Menyimpan sesi login di Streamlit
if "ssh_logged_in" not in st.session_state:
    st.session_state.ssh_logged_in = False
if "server_ip" not in st.session_state:
    st.session_state.server_ip = ""

# Halaman Login SSH
if not st.session_state.ssh_logged_in:
    st.title("🔐 Login to SSH Server")

    # Pakai st.columns() untuk membuat form lebih sempit
    col1, col2, col3 = st.columns([1, 2, 1])  # Tengah lebih besar

    with col2:  # Taruh form di tengah
        with st.container():
            # st.markdown(
            #     """
            #     <h3 style="text-align:center;"></h3>
            #     """, 
            #     unsafe_allow_html=True)

            server_ip = st.text_input("Server IP", st.session_state.server_ip)
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            if st.button("Login SSH"):
                success, message = check_ssh_login(server_ip, username, password)
                if success:
                    st.session_state.ssh_logged_in = True
                    st.session_state.server_ip = server_ip
                    st.session_state.ssh_username = username
                    st.session_state.ssh_password = password
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)


else:
    # Halaman Dashboard setelah login
    st.title("📡 SSH Server Monitoring")
    st.sidebar.success(f"✅ Connected to {st.session_state.server_ip}")

    # Tombol Logout
    if st.sidebar.button("Logout"):
        st.session_state.ssh_logged_in = False

    # Bagian Monitoring Server
    st.header("📊 Server Monitoring Dashboard")
    host = st.session_state.server_ip
    username = st.session_state.ssh_username
    password = st.session_state.ssh_password

    if st.button("Monitor Server"):
        with st.spinner("Fetching server data..."):
            stats = get_server_stats(host, username, password)

        if "Error" in stats:
            st.error(f"Error: {stats['Error']}")
        else:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("CPU Usage (%)", stats["CPU Usage"])
            col2.metric("Memory Usage (%)", stats["Memory Usage"])
            col3.metric("Disk Usage", stats["Disk Usage"])
            col4.metric("Uptime", stats["Uptime"])

            # Membuat DataFrame untuk visualisasi
            data = {
                "Resource": ["CPU Usage", "Memory Usage", "Disk Usage"],
                "Usage (%)": [float(stats["CPU Usage"]), float(stats["Memory Usage"].strip('%')), 
                              float(stats["Disk Usage"].strip('%'))]
            }
            df = pd.DataFrame(data)

            fig = px.bar(df, x="Resource", y="Usage (%)", text="Usage (%)", color="Resource",
                         title="Server Resource Usage", labels={"Usage (%)": "Percentage"})
            fig.update_traces(textposition="outside")

            st.plotly_chart(fig, use_container_width=True)

    # Bagian Jalankan Perintah SSH
    st.header("🖥️ Jalankan Perintah di Server")
    command = st.text_input("Masukkan perintah SSH:")
    if st.button("Jalankan Perintah"):
        output = run_ssh_command(host, username, password, command)
        st.text_area("Output:", output, height=200)