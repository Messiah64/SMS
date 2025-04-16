import streamlit as st
import pandas as pd
import base64
from io import BytesIO
from supabase import create_client
import uuid
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="SCDF Turnout Deployment",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Retrieve Supabase credentials from Streamlit secrets
SUPABASE_URL = st.secrets["supabase"]["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["supabase"]["SUPABASE_KEY"]

def init_supabase():
    """Initialize Supabase client"""
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Failed to connect to Supabase: {e}")
        return None

# Simple function to load all current positions
def load_positions():
    """Load all positions from the database"""
    supabase = init_supabase()
    if not supabase:
        return {}
    
    try:
        response = supabase.table('assignments').select('*').execute()
        
        positions = {}
        for item in response.data:
            vehicle = item['vehicle_code']
            position = item['position_code']
            name = item['personnel_name']
            
            if vehicle not in positions:
                positions[vehicle] = {}
            
            positions[vehicle][position] = name
        
        return positions
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return {}

# Simple function to save a single position
def update_position(vehicle, position, name):
    """Update a single position in the database"""
    supabase = init_supabase()
    if not supabase:
        return False
    
    try:
        # Check if position exists
        response = supabase.table('assignments')\
            .select('id')\
            .eq('vehicle_code', vehicle)\
            .eq('position_code', position)\
            .execute()
        
        if response.data:
            # Position exists, update or delete
            if name:
                # Update existing position
                supabase.table('assignments')\
                    .update({'personnel_name': name})\
                    .eq('vehicle_code', vehicle)\
                    .eq('position_code', position)\
                    .execute()
            else:
                # Delete position if name is empty
                supabase.table('assignments')\
                    .delete()\
                    .eq('vehicle_code', vehicle)\
                    .eq('position_code', position)\
                    .execute()
        elif name:
            # Position doesn't exist and we have a name, create it
            supabase.table('assignments')\
                .insert({
                    'id': str(uuid.uuid4()),
                    'vehicle_code': vehicle,
                    'position_code': position,
                    'personnel_name': name
                })\
                .execute()
        
        return True
    except Exception as e:
        st.error(f"Error updating position: {e}")
        return False

# Initialize session state variables
if 'page' not in st.session_state:
    st.session_state.page = 'home'  # Default to home page

if 'positions' not in st.session_state:
    # Load positions from database on first load
    st.session_state.positions = load_positions()

if 'is_changed' not in st.session_state:
    st.session_state.is_changed = False

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 36px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 20px;
    }
    .sub-header {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .column-header {
        font-size: 20px;
        font-weight: bold;
        text-align: center;
        padding: 10px;
        background-color: #f0f2f6;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .role-label {
        font-weight: bold;
        margin-bottom: 0px;
    }
    .stButton button {
        width: 100%;
    }
    .footer-buttons {
        padding-top: 20px;
    }
    .position-row {
        display: flex;
        margin-bottom: 5px;
    }
    .position-label {
        font-weight: bold;
        width: 100px;
    }
    .personnel-name {
        flex-grow: 1;
    }
    .nav-button {
        margin-right: 10px;
    }
    .notification {
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    .success {
        background-color: #d4edda;
        color: #155724;
    }
    .warning {
        background-color: #fff3cd;
        color: #856404;
    }
    .error {
        background-color: #f8d7da;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

# Sample names
sample_names = [
    "", "LTA SHABIR", "WO2 AMIN", "SGT MUZAMIL", "SGT SULTAN", "CPL PUTRA", 
    "LCP BU XIANG XUAN", "LCP QUINN", "SGT RAIHAN", "LCP HAROUN", "SGT FAUZI", 
    "SGT ADLY", "LCP NATHAN", "ORNS 1", "ORNS 2", "WO2 AZHAR", "SGT3 ZHUBRAN", 
    "SSG AHMAD", "WO2 ZULHAINI", "LCP KHAMBHATI", "LCP CHINMAY"
]

# Role descriptions (full names)
role_descriptions = {
    'RC': 'ROTA COMMANDER',
    'DRC': 'DEPUTY ROTA COMMANDER',
    'PO': 'SECTION COMMANDER',
    'SC': 'SECTION COMMANDER',
    'FF1': 'FIREFIGHTER',
    'FF2': 'FIREFIGHTER',
    'FF3': 'FIREFIGHTER',
    'FF4': 'FIREFIGHTER',
    'PRM': 'PARAMEDIC',
    'EMTD': 'DRIVER',
    'EMT1': 'EMT',
    'EMT2': 'EMT'
}

# Function to generate CSV
def generate_csv(data):
    df = pd.DataFrame(data)
    buffer = BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    return buffer

# Function to get position value with fallback
def get_position_value(vehicle, position):
    """Get value for a position with fallback to empty string"""
    if vehicle in st.session_state.positions and position in st.session_state.positions[vehicle]:
        return st.session_state.positions[vehicle][position]
    return ""

# Function to track selection changes
def on_select_change(vehicle, position):
    """Callback for when a selection changes"""
    # Get the new value from session state
    key = f"{vehicle}_{position}"
    new_value = st.session_state[key]
    
    # Update our positions dictionary
    if vehicle not in st.session_state.positions:
        st.session_state.positions[vehicle] = {}
    
    # Only mark as changed if value is actually different
    old_value = st.session_state.positions[vehicle].get(position, "")
    if new_value != old_value:
        st.session_state.is_changed = True
        st.session_state.positions[vehicle][position] = new_value

# Function to clear form
def clear_form():
    for vehicle in ['PL181', 'LF181E', 'CPL181E', 'A181D', 'A182D']:
        if vehicle not in st.session_state.positions:
            st.session_state.positions[vehicle] = {}
            
        for position in get_positions_for_vehicle(vehicle):
            # Clear in our positions dictionary
            if position in st.session_state.positions[vehicle]:
                st.session_state.positions[vehicle][position] = ""
            
            # Clear in widget state
            key = f"{vehicle}_{position}"
            if key in st.session_state:
                st.session_state[key] = ""
    
    st.session_state.is_changed = True

# Helper function to get positions for a vehicle
def get_positions_for_vehicle(vehicle):
    """Return list of positions for a vehicle"""
    if vehicle == 'PL181':
        return ['RC', 'DRC', 'PO', 'SC', 'FF1', 'FF2', 'FF3']
    elif vehicle == 'LF181E':
        return ['PO', 'SC', 'FF1', 'FF2']
    elif vehicle == 'CPL181E':
        return ['PO', 'SC', 'FF1', 'FF2', 'FF3', 'FF4']
    elif vehicle in ['A181D', 'A182D']:
        return ['PRM', 'EMTD', 'EMT1', 'EMT2']
    return []

# Navigation buttons
def navigation():
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button("📊 Summary View", key="nav_summary"):
            # Check if we need to save changes before navigating
            if st.session_state.is_changed:
                # Reload positions before showing summary
                st.session_state.positions = load_positions()
                st.session_state.is_changed = False
            
            st.session_state.page = 'home'
            st.rerun()
    with col3:
        if st.button("✏️ Edit Deployment", key="nav_edit"):
            # Reload positions when going to edit page
            st.session_state.positions = load_positions()
            st.session_state.is_changed = False
            st.session_state.page = 'edit'
            st.rerun()

# Helper function to order positions consistently
def order_position(position):
    order = {
        'RC': 0, 
        'DRC': 1, 
        'PO': 2, 
        'SC': 3, 
        'FF1': 4, 
        'FF2': 5, 
        'FF3': 6, 
        'FF4': 7,
        'PRM': 0,
        'EMTD': 1,
        'EMT1': 2,
        'EMT2': 3
    }
    return order.get(position, 99)

# Home page with summary view
def home_page():
    st.markdown('<div class="main-header">SCDF TURNOUT DEPLOYMENT</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Summary View</div>', unsafe_allow_html=True)
    
    # Navigation
    navigation()
    
    if not st.session_state.positions:
        st.markdown(
            '<div class="notification error">No deployment data found. Create a new deployment using the Edit button.</div>',
            unsafe_allow_html=True
        )
        return
    
    # Display positions in a clean format
    cols = st.columns(5)
    
    vehicle_columns = {
        'PL181': cols[0],
        'LF181E': cols[1],
        'CPL181E': cols[2],
        'A181D': cols[3],
        'A182D': cols[4]
    }
    
    for vehicle_code, column in vehicle_columns.items():
        with column:
            st.markdown(f'<div class="column-header">{vehicle_code}</div>', unsafe_allow_html=True)
            
            if vehicle_code in st.session_state.positions and st.session_state.positions[vehicle_code]:
                # Get all positions for this vehicle
                positions = get_positions_for_vehicle(vehicle_code)
                
                # Display all positions with values
                for position in positions:
                    name = get_position_value(vehicle_code, position)
                    if name:  # Only show filled positions
                        st.markdown(
                            f'<div class="position-row">'
                            f'<div class="position-label">{position}</div>'
                            f'<div class="personnel-name">{name}</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
            else:
                st.markdown("No assignments")

# Edit page with deployment form
def edit_page():
    st.markdown('<div class="main-header">TURNOUT DEPLOYMENT</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Edit View</div>', unsafe_allow_html=True)
    
    # Navigation
    navigation()
    
    # Status bar for changes
    if st.session_state.is_changed:
        st.warning("You have unsaved changes.")
    
    # Create columns for each vehicle type
    cols = st.columns(5)

    # PL181
    with cols[0]:
        st.markdown('<div class="column-header">PL181</div>', unsafe_allow_html=True)
        
        # RC
        st.markdown('<div class="role-label">RC</div>', unsafe_allow_html=True)
        rc_name = st.selectbox(
            "ROTA COMMANDER Rota ?",
            options=sample_names,
            key="PL181_RC",
            index=sample_names.index(get_position_value('PL181', 'RC')) if get_position_value('PL181', 'RC') in sample_names else 0,
            on_change=on_select_change,
            args=('PL181', 'RC'),
            label_visibility="collapsed"
        )
        
        # DRC
        st.markdown('<div class="role-label">DRC</div>', unsafe_allow_html=True)
        drc_name = st.selectbox(
            "DEPUTY ROTA COMMANDER Rota ?",
            options=sample_names,
            key="PL181_DRC",
            index=sample_names.index(get_position_value('PL181', 'DRC')) if get_position_value('PL181', 'DRC') in sample_names else 0,
            on_change=on_select_change,
            args=('PL181', 'DRC'),
            label_visibility="collapsed"
        )
        
        # PO
        st.markdown('<div class="role-label">PO</div>', unsafe_allow_html=True)
        po_name = st.selectbox(
            "SECTION COMMANDER Rota ?",
            options=sample_names,
            key="PL181_PO",
            index=sample_names.index(get_position_value('PL181', 'PO')) if get_position_value('PL181', 'PO') in sample_names else 0,
            on_change=on_select_change,
            args=('PL181', 'PO'),
            label_visibility="collapsed"
        )
        
        # SC
        st.markdown('<div class="role-label">SC</div>', unsafe_allow_html=True)
        sc_name = st.selectbox(
            "SECTION COMMANDER Rota ?",
            options=sample_names,
            key="PL181_SC",
            index=sample_names.index(get_position_value('PL181', 'SC')) if get_position_value('PL181', 'SC') in sample_names else 0,
            on_change=on_select_change,
            args=('PL181', 'SC'),
            label_visibility="collapsed"
        )
        
        # FF1
        st.markdown('<div class="role-label">FF</div>', unsafe_allow_html=True)
        ff1_name = st.selectbox(
            "FIREFIGHTER Rota ?",
            options=sample_names,
            key="PL181_FF1",
            index=sample_names.index(get_position_value('PL181', 'FF1')) if get_position_value('PL181', 'FF1') in sample_names else 0,
            on_change=on_select_change,
            args=('PL181', 'FF1'),
            label_visibility="collapsed"
        )
        
        # FF2
        st.markdown('<div class="role-label">FF</div>', unsafe_allow_html=True)
        ff2_name = st.selectbox(
            "FIREFIGHTER Rota ?",
            options=sample_names,
            key="PL181_FF2",
            index=sample_names.index(get_position_value('PL181', 'FF2')) if get_position_value('PL181', 'FF2') in sample_names else 0,
            on_change=on_select_change,
            args=('PL181', 'FF2'),
            label_visibility="collapsed"
        )
        
        # FF3
        st.markdown('<div class="role-label">FF</div>', unsafe_allow_html=True)
        ff3_name = st.selectbox(
            "FIREFIGHTER Rota ?",
            options=sample_names,
            key="PL181_FF3",
            index=sample_names.index(get_position_value('PL181', 'FF3')) if get_position_value('PL181', 'FF3') in sample_names else 0,
            on_change=on_select_change,
            args=('PL181', 'FF3'),
            label_visibility="collapsed"
        )

    # LF181E
    with cols[1]:
        st.markdown('<div class="column-header">LF181E</div>', unsafe_allow_html=True)
        
        # PO
        st.markdown('<div class="role-label">PO</div>', unsafe_allow_html=True)
        po_name = st.selectbox(
            "SECTION COMMANDER Rota ?",
            options=sample_names,
            key="LF181E_PO",
            index=sample_names.index(get_position_value('LF181E', 'PO')) if get_position_value('LF181E', 'PO') in sample_names else 0,
            on_change=on_select_change,
            args=('LF181E', 'PO'),
            label_visibility="collapsed"
        )
        
        # SC
        st.markdown('<div class="role-label">SC</div>', unsafe_allow_html=True)
        sc_name = st.selectbox(
            "SECTION COMMANDER Rota ?",
            options=sample_names,
            key="LF181E_SC",
            index=sample_names.index(get_position_value('LF181E', 'SC')) if get_position_value('LF181E', 'SC') in sample_names else 0,
            on_change=on_select_change,
            args=('LF181E', 'SC'),
            label_visibility="collapsed"
        )
        
        # FF1
        st.markdown('<div class="role-label">FF</div>', unsafe_allow_html=True)
        ff1_name = st.selectbox(
            "FIREFIGHTER Rota ?",
            options=sample_names,
            key="LF181E_FF1",
            index=sample_names.index(get_position_value('LF181E', 'FF1')) if get_position_value('LF181E', 'FF1') in sample_names else 0,
            on_change=on_select_change,
            args=('LF181E', 'FF1'),
            label_visibility="collapsed"
        )
        
        # FF2
        st.markdown('<div class="role-label">FF</div>', unsafe_allow_html=True)
        ff2_name = st.selectbox(
            "FIREFIGHTER Rota ?",
            options=sample_names,
            key="LF181E_FF2",
            index=sample_names.index(get_position_value('LF181E', 'FF2')) if get_position_value('LF181E', 'FF2') in sample_names else 0,
            on_change=on_select_change,
            args=('LF181E', 'FF2'),
            label_visibility="collapsed"
        )

    # CPL181E
    with cols[2]:
        st.markdown('<div class="column-header">CPL181E</div>', unsafe_allow_html=True)
        
        # PO
        st.markdown('<div class="role-label">PO</div>', unsafe_allow_html=True)
        po_name = st.selectbox(
            "SECTION COMMANDER Rota ?",
            options=sample_names,
            key="CPL181E_PO",
            index=sample_names.index(get_position_value('CPL181E', 'PO')) if get_position_value('CPL181E', 'PO') in sample_names else 0,
            on_change=on_select_change,
            args=('CPL181E', 'PO'),
            label_visibility="collapsed"
        )
        
        # SC
        st.markdown('<div class="role-label">SC</div>', unsafe_allow_html=True)
        sc_name = st.selectbox(
            "SECTION COMMANDER Rota ?",
            options=sample_names,
            key="CPL181E_SC",
            index=sample_names.index(get_position_value('CPL181E', 'SC')) if get_position_value('CPL181E', 'SC') in sample_names else 0,
            on_change=on_select_change,
            args=('CPL181E', 'SC'),
            label_visibility="collapsed"
        )
        
        # FF1
        st.markdown('<div class="role-label">FF</div>', unsafe_allow_html=True)
        ff1_name = st.selectbox(
            "FIREFIGHTER Rota ?",
            options=sample_names,
            key="CPL181E_FF1",
            index=sample_names.index(get_position_value('CPL181E', 'FF1')) if get_position_value('CPL181E', 'FF1') in sample_names else 0,
            on_change=on_select_change,
            args=('CPL181E', 'FF1'),
            label_visibility="collapsed"
        )
        
        # FF2
        st.markdown('<div class="role-label">FF</div>', unsafe_allow_html=True)
        ff2_name = st.selectbox(
            "FIREFIGHTER Rota ?",
            options=sample_names,
            key="CPL181E_FF2",
            index=sample_names.index(get_position_value('CPL181E', 'FF2')) if get_position_value('CPL181E', 'FF2') in sample_names else 0,
            on_change=on_select_change,
            args=('CPL181E', 'FF2'),
            label_visibility="collapsed"
        )
        
        # FF3
        st.markdown('<div class="role-label">FF</div>', unsafe_allow_html=True)
        ff3_name = st.selectbox(
            "FIREFIGHTER Rota ?",
            options=sample_names,
            key="CPL181E_FF3",
            index=sample_names.index(get_position_value('CPL181E', 'FF3')) if get_position_value('CPL181E', 'FF3') in sample_names else 0,
            on_change=on_select_change,
            args=('CPL181E', 'FF3'),
            label_visibility="collapsed"
        )
        
        # FF4
        st.markdown('<div class="role-label">FF</div>', unsafe_allow_html=True)
        ff4_name = st.selectbox(
            "FIREFIGHTER Rota ?",
            options=sample_names,
            key="CPL181E_FF4",
            index=sample_names.index(get_position_value('CPL181E', 'FF4')) if get_position_value('CPL181E', 'FF4') in sample_names else 0,
            on_change=on_select_change,
            args=('CPL181E', 'FF4'),
            label_visibility="collapsed"
        )

    # A181D
    with cols[3]:
        st.markdown('<div class="column-header">A181D</div>', unsafe_allow_html=True)
        
        # PRM
        st.markdown('<div class="role-label">PRM</div>', unsafe_allow_html=True)
        prm_name = st.selectbox(
            "PARAMEDIC",
            options=sample_names,
            key="A181D_PRM",
            index=sample_names.index(get_position_value('A181D', 'PRM')) if get_position_value('A181D', 'PRM') in sample_names else 0,
            on_change=on_select_change,
            args=('A181D', 'PRM'),
            label_visibility="collapsed"
        )
        
        # EMTD
        st.markdown('<div class="role-label">EMT (DRIVER)</div>', unsafe_allow_html=True)
        emtd_name = st.selectbox(
            "DRIVER",
            options=sample_names,
            key="A181D_EMTD",
            index=sample_names.index(get_position_value('A181D', 'EMTD')) if get_position_value('A181D', 'EMTD') in sample_names else 0,
            on_change=on_select_change,
            args=('A181D', 'EMTD'),
            label_visibility="collapsed"
        )
        
        # EMT1
        st.markdown('<div class="role-label">EMT</div>', unsafe_allow_html=True)
        emt1_name = st.selectbox(
            "EMT",
            options=sample_names,
            key="A181D_EMT1",
            index=sample_names.index(get_position_value('A181D', 'EMT1')) if get_position_value('A181D', 'EMT1') in sample_names else 0,
            on_change=on_select_change,
            args=('A181D', 'EMT1'),
            label_visibility="collapsed"
        )
        
        # EMT2
        st.markdown('<div class="role-label">EMT</div>', unsafe_allow_html=True)
        emt2_name = st.selectbox(
            "EMT",
            options=sample_names,
            key="A181D_EMT2",
            index=sample_names.index(get_position_value('A181D', 'EMT2')) if get_position_value('A181D', 'EMT2') in sample_names else 0,
            on_change=on_select_change,
            args=('A181D', 'EMT2'),
            label_visibility="collapsed"
        )

    # A182D
    with cols[4]:
        st.markdown('<div class="column-header">A182D</div>', unsafe_allow_html=True)
        
        # PRM
        st.markdown('<div class="role-label">PRM</div>', unsafe_allow_html=True)
        prm_name = st.selectbox(
            "PARAMEDIC",
            options=sample_names,
            key="A182D_PRM",
            index=sample_names.index(get_position_value('A182D', 'PRM')) if get_position_value('A182D', 'PRM') in sample_names else 0,
            on_change=on_select_change,
            args=('A182D', 'PRM'),
            label_visibility="collapsed"
        )
        
        # EMTD
        st.markdown('<div class="role-label">EMT (DRIVER)</div>', unsafe_allow_html=True)
        emtd_name = st.selectbox(
            "DRIVER",
            options=sample_names,
            key="A182D_EMTD",
            index=sample_names.index(get_position_value('A182D', 'EMTD')) if get_position_value('A182D', 'EMTD') in sample_names else 0,
            on_change=on_select_change,
            args=('A182D', 'EMTD'),
            label_visibility="collapsed"
        )
        
        # EMT1
        st.markdown('<div class="role-label">EMT</div>', unsafe_allow_html=True)
        emt1_name = st.selectbox(
            "EMT",
            options=sample_names,
            key="A182D_EMT1",
            index=sample_names.index(get_position_value('A182D', 'EMT1')) if get_position_value('A182D', 'EMT1') in sample_names else 0,
            on_change=on_select_change,
            args=('A182D', 'EMT1'),
            label_visibility="collapsed"
        )
        
        # EMT2
        st.markdown('<div class="role-label">EMT</div>', unsafe_allow_html=True)
        emt2_name = st.selectbox(
            "EMT",
            options=sample_names,
            key="A182D_EMT2",
            index=sample_names.index(get_position_value('A182D', 'EMT2')) if get_position_value('A182D', 'EMT2') in sample_names else 0,
            on_change=on_select_change,
            args=('A182D', 'EMT2'),
            label_visibility="collapsed"
        )

    # Footer with action buttons
    st.markdown('<div class="footer-buttons"></div>', unsafe_allow_html=True)
    cols_btn = st.columns(3)

    # Save button
    with cols_btn[0]:
        if st.button("Save Deployment"):
            success = True
            # Save each changed position individually
            for vehicle in st.session_state.positions:
                for position, name in st.session_state.positions[vehicle].items():
                    if update_position(vehicle, position, name) == False:
                        success = False
            
            if success:
                st.success("Deployment updated successfully!")
                st.session_state.is_changed = False
                # Switch to home page after saving
                st.session_state.page = 'home'
                st.rerun()

    # Reset button
    with cols_btn[1]:
        if st.button("Reset All", on_click=clear_form):
            pass  # The on_click handler does the work

    # Export button
    with cols_btn[2]:
        if st.button("Export CSV"):
            # Convert the positions data to a format suitable for CSV
            csv_data = []
            for vehicle in st.session_state.positions:
                for position, name in st.session_state.positions[vehicle].items():
                    if name:  # Only include filled positions
                        csv_data.append({
                            'Vehicle': vehicle,
                            'Position': position,
                            'Role_Description': role_descriptions.get(position, ''),
                            'Name': name
                        })
            
            if csv_data:
                csv_buffer = generate_csv(csv_data)
                st.success("CSV generated successfully!")
                st.download_button(
                    label="Download CSV",
                    data=csv_buffer,
                    file_name="turnout_deployment.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No deployment data to export!")

# Main app logic - Load current deployment data on startup
def main():
    if st.session_state.page == 'home':
        home_page()
    elif st.session_state.page == 'edit':
        edit_page()

if __name__ == "__main__":
    main()