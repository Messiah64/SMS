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
    initial_sidebar_state="collapsed",
    theme="light"
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

# Save deployment to Supabase - Updated to update instead of create new
def save_deployment_to_supabase():
    """Update the current deployment in Supabase"""
    supabase = init_supabase()
    if not supabase:
        return False
    
    try:
        current_time = datetime.now().isoformat()
        
        # Get current deployment ID
        response = supabase.table('current_deployment').select('id').execute()
        if not response.data:
            # Create a new deployment if none exists
            deployment_id = str(uuid.uuid4())
            supabase.table('current_deployment').insert({
                'id': deployment_id,
                'last_updated': current_time
            }).execute()
        else:
            deployment_id = response.data[0]['id']
            # Update last_updated timestamp
            supabase.table('current_deployment')\
                .update({'last_updated': current_time})\
                .eq('id', deployment_id)\
                .execute()
        
        # For each position in the current deployment form
        for vehicle, positions in st.session_state.deployment.items():
            for position, name in positions.items():
                if name:  # Only process filled positions
                    # Check if this position already exists
                    position_response = supabase.table('assignments')\
                        .select('id')\
                        .eq('vehicle_code', vehicle)\
                        .eq('position_code', position)\
                        .execute()
                    
                    if position_response.data:
                        # Update existing assignment
                        assignment_id = position_response.data[0]['id']
                        supabase.table('assignments')\
                            .update({
                                'personnel_name': name,
                                'updated_at': current_time
                            })\
                            .eq('id', assignment_id)\
                            .execute()
                    else:
                        # Create new assignment
                        supabase.table('assignments')\
                            .insert({
                                'id': str(uuid.uuid4()),
                                'vehicle_code': vehicle,
                                'position_code': position,
                                'personnel_name': name,
                                'created_at': current_time,
                                'updated_at': current_time
                            })\
                            .execute()
                else:
                    # If position is empty, delete any existing assignment
                    supabase.table('assignments')\
                        .delete()\
                        .eq('vehicle_code', vehicle)\
                        .eq('position_code', position)\
                        .execute()
        
        return True
    
    except Exception as e:
        st.error(f"Error saving to Supabase: {e}")
        return False

# Get current deployment from Supabase
def get_current_deployment_from_supabase():
    """Fetch the current deployment from Supabase"""
    supabase = init_supabase()
    if not supabase:
        return None, []
    
    try:
        # Get current deployment ID
        deployment_response = supabase.table('current_deployment').select('*').execute()
        
        if not deployment_response.data:
            return None, []
        
        current_deployment = deployment_response.data[0]
        
        # Get all assignments
        assignments_response = supabase.table('assignments').select('*').execute()
        
        return current_deployment, assignments_response.data
    
    except Exception as e:
        st.error(f"Error fetching from Supabase: {e}")
        return None, []

# Load deployment from Supabase to session state
def load_deployment_from_supabase():
    """Load current deployment from Supabase into session state"""
    supabase = init_supabase()
    if not supabase:
        return False
    
    try:
        # Reset current deployment in session state
        for vehicle in st.session_state.deployment:
            for position in st.session_state.deployment[vehicle]:
                st.session_state.deployment[vehicle][position] = ""
        
        # Get all assignments
        response = supabase.table('assignments').select('*').execute()
        
        if not response.data:
            return False
        
        # Update session state with assignments
        for assignment in response.data:
            vehicle = assignment['vehicle_code']
            position = assignment['position_code']
            name = assignment['personnel_name']
            
            if vehicle in st.session_state.deployment and position in st.session_state.deployment[vehicle]:
                st.session_state.deployment[vehicle][position] = name
                # Update widget state if exists
                widget_key = f"{vehicle}_{position}"
                if widget_key in st.session_state:
                    st.session_state[widget_key] = name
        
        return True
    
    except Exception as e:
        st.error(f"Error loading deployment from Supabase: {e}")
        return False

# Get personnel roster from Supabase
def get_personnel_roster():
    """Get list of all personnel from Supabase"""
    supabase = init_supabase()
    if not supabase:
        return []
    
    try:
        response = supabase.table('personnel').select('*').order('name').execute()
        
        # Format for selectbox - name only
        return [""] + [person['name'] for person in response.data]
    
    except Exception as e:
        st.error(f"Error fetching personnel from Supabase: {e}")
        return []

# Initialize session state variables
if 'page' not in st.session_state:
    st.session_state.page = 'home'  # Default to home page

if 'deployment' not in st.session_state:
    st.session_state.deployment = {
        'PL181': {
            'RC': '',
            'DRC': '',
            'PO': '',
            'SC': '',
            'FF1': '',
            'FF2': '',
            'FF3': ''
        },
        'LF181E': {
            'PO': '',
            'SC': '',
            'FF1': '',
            'FF2': ''
        },
        'CPL181E': {
            'PO': '',
            'SC': '',
            'FF1': '',
            'FF2': '',
            'FF3': '',
            'FF4': ''
        },
        'A181D': {
            'PRM': '',
            'EMTD': '',
            'EMT1': '',
            'EMT2': ''
        },
        'A182D': {
            'PRM': '',
            'EMTD': '',
            'EMT1': '',
            'EMT2': ''
        }
    }

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
    .card {
        padding: 15px;
        border-radius: 5px;
        background-color: #f9f9f9;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    .vehicle-header {
        background-color: #e6f3ff;
        padding: 10px;
        margin-bottom: 10px;
        border-radius: 5px;
        font-weight: bold;
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

# Try to get personnel from database, fall back to sample list if not available
try:
    sample_names = get_personnel_roster()
    if not sample_names or len(sample_names) <= 1:  # If only empty option or error
        # Sample data for demonstration
        sample_names = [
            "", "LTA SHABIR", "WO2 AMIN", "SGT MUZAMIL", "SGT SULTAN", "CPL PUTRA", 
            "LCP BU XIANG XUAN", "LCP QUINN", "SGT RAIHAN", "LCP HAROUN", "SGT FAUZI", 
            "SGT ADLY", "LCP NATHAN", "ORNS 1", "ORNS 2", "WO2 AZHAR", "SGT3 ZHUBRAN", 
            "SSG AHMAD", "WO2 ZULHAINI", "LCP KHAMBHATI", "LCP CHINMAY"
        ]
except:
    # Fallback sample data
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

# Function to clear form
def clear_form():
    for key in st.session_state:
        if key.startswith(('PL181_', 'LF181E_', 'CPL181E_', 'A181D_', 'A182D_')):
            st.session_state[key] = ""
    
    # Also clear the deployment dictionary
    for vehicle in st.session_state.deployment:
        for position in st.session_state.deployment[vehicle]:
            st.session_state.deployment[vehicle][position] = ""

# Navigation buttons
def navigation():
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button("📊 Summary View", key="nav_summary"):
            st.session_state.page = 'home'
            st.rerun()
    with col3:
        if st.button("✏️ Edit Deployment", key="nav_edit"):
            # Load current deployment when entering edit page
            load_deployment_from_supabase()
            st.session_state.page = 'edit'
            st.rerun()

# Home page with summary view
def home_page():
    st.markdown('<div class="main-header">SCDF TURNOUT DEPLOYMENT</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Summary View</div>', unsafe_allow_html=True)
    
    # Navigation
    navigation()
    
    # Get current deployment from Supabase
    current_deployment, assignments = get_current_deployment_from_supabase()
    
    if not current_deployment:
        st.markdown(
            '<div class="notification error">No deployment data found. Create a new deployment using the Edit button.</div>',
            unsafe_allow_html=True
        )
        return
    
    # Show deployment info
    st.markdown(f"**Last Updated:** {datetime.fromisoformat(current_deployment['last_updated']).strftime('%d %b %Y, %H:%M')}")
    
    # Organize assignments by vehicle
    vehicles = {}
    for assignment in assignments:
        vehicle = assignment['vehicle_code']
        if vehicle not in vehicles:
            vehicles[vehicle] = []
        vehicles[vehicle].append(assignment)
    
    # Display assignments in a clean format
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
            
            if vehicle_code in vehicles:
                # Sort by position code to ensure proper order
                sorted_assignments = sorted(
                    vehicles[vehicle_code], 
                    key=lambda x: order_position(x['position_code'])
                )
                
                for assignment in sorted_assignments:
                    position = assignment['position_code']
                    name = assignment['personnel_name']
                    
                    # Display position and name
                    st.markdown(
                        f'<div class="position-row">'
                        f'<div class="position-label">{position}</div>'
                        f'<div class="personnel-name">{name}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.markdown("No assignments")

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

# Edit page with deployment form
def edit_page():
    st.markdown('<div class="main-header">TURNOUT DEPLOYMENT</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Edit View</div>', unsafe_allow_html=True)
    
    # Navigation
    navigation()
    
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
            label_visibility="collapsed"
        )
        st.session_state.deployment['PL181']['RC'] = rc_name
        
        # DRC
        st.markdown('<div class="role-label">DRC</div>', unsafe_allow_html=True)
        drc_name = st.selectbox(
            "DEPUTY ROTA COMMANDER Rota ?",
            options=sample_names,
            key="PL181_DRC",
            label_visibility="collapsed"
        )
        st.session_state.deployment['PL181']['DRC'] = drc_name
        
        # PO
        st.markdown('<div class="role-label">PO</div>', unsafe_allow_html=True)
        po_name = st.selectbox(
            "SECTION COMMANDER Rota ?",
            options=sample_names,
            key="PL181_PO",
            label_visibility="collapsed"
        )
        st.session_state.deployment['PL181']['PO'] = po_name
        
        # SC
        st.markdown('<div class="role-label">SC</div>', unsafe_allow_html=True)
        sc_name = st.selectbox(
            "SECTION COMMANDER Rota ?",
            options=sample_names,
            key="PL181_SC",
            label_visibility="collapsed"
        )
        st.session_state.deployment['PL181']['SC'] = sc_name
        
        # FF1
        st.markdown('<div class="role-label">FF</div>', unsafe_allow_html=True)
        ff1_name = st.selectbox(
            "FIREFIGHTER Rota ?",
            options=sample_names,
            key="PL181_FF1",
            label_visibility="collapsed"
        )
        st.session_state.deployment['PL181']['FF1'] = ff1_name
        
        # FF2
        st.markdown('<div class="role-label">FF</div>', unsafe_allow_html=True)
        ff2_name = st.selectbox(
            "FIREFIGHTER Rota ?",
            options=sample_names,
            key="PL181_FF2",
            label_visibility="collapsed"
        )
        st.session_state.deployment['PL181']['FF2'] = ff2_name
        
        # FF3
        st.markdown('<div class="role-label">FF</div>', unsafe_allow_html=True)
        ff3_name = st.selectbox(
            "FIREFIGHTER Rota ?",
            options=sample_names,
            key="PL181_FF3",
            label_visibility="collapsed"
        )
        st.session_state.deployment['PL181']['FF3'] = ff3_name

    # LF181E
    with cols[1]:
        st.markdown('<div class="column-header">LF181E</div>', unsafe_allow_html=True)
        
        # PO
        st.markdown('<div class="role-label">PO</div>', unsafe_allow_html=True)
        po_name = st.selectbox(
            "SECTION COMMANDER Rota ?",
            options=sample_names,
            key="LF181E_PO",
            label_visibility="collapsed"
        )
        st.session_state.deployment['LF181E']['PO'] = po_name
        
        # SC
        st.markdown('<div class="role-label">SC</div>', unsafe_allow_html=True)
        sc_name = st.selectbox(
            "SECTION COMMANDER Rota ?",
            options=sample_names,
            key="LF181E_SC",
            label_visibility="collapsed"
        )
        st.session_state.deployment['LF181E']['SC'] = sc_name
        
        # FF1
        st.markdown('<div class="role-label">FF</div>', unsafe_allow_html=True)
        ff1_name = st.selectbox(
            "FIREFIGHTER Rota ?",
            options=sample_names,
            key="LF181E_FF1",
            label_visibility="collapsed"
        )
        st.session_state.deployment['LF181E']['FF1'] = ff1_name
        
        # FF2
        st.markdown('<div class="role-label">FF</div>', unsafe_allow_html=True)
        ff2_name = st.selectbox(
            "FIREFIGHTER Rota ?",
            options=sample_names,
            key="LF181E_FF2",
            label_visibility="collapsed"
        )
        st.session_state.deployment['LF181E']['FF2'] = ff2_name

    # CPL181E
    with cols[2]:
        st.markdown('<div class="column-header">CPL181E</div>', unsafe_allow_html=True)
        
        # PO
        st.markdown('<div class="role-label">PO</div>', unsafe_allow_html=True)
        po_name = st.selectbox(
            "SECTION COMMANDER Rota ?",
            options=sample_names,
            key="CPL181E_PO",
            label_visibility="collapsed"
        )
        st.session_state.deployment['CPL181E']['PO'] = po_name
        
        # SC
        st.markdown('<div class="role-label">SC</div>', unsafe_allow_html=True)
        sc_name = st.selectbox(
            "SECTION COMMANDER Rota ?",
            options=sample_names,
            key="CPL181E_SC",
            label_visibility="collapsed"
        )
        st.session_state.deployment['CPL181E']['SC'] = sc_name
        
        # FF1
        st.markdown('<div class="role-label">FF</div>', unsafe_allow_html=True)
        ff1_name = st.selectbox(
            "FIREFIGHTER Rota ?",
            options=sample_names,
            key="CPL181E_FF1",
            label_visibility="collapsed"
        )
        st.session_state.deployment['CPL181E']['FF1'] = ff1_name
        
        # FF2
        st.markdown('<div class="role-label">FF</div>', unsafe_allow_html=True)
        ff2_name = st.selectbox(
            "FIREFIGHTER Rota ?",
            options=sample_names,
            key="CPL181E_FF2",
            label_visibility="collapsed"
        )
        st.session_state.deployment['CPL181E']['FF2'] = ff2_name
        
        # FF3
        st.markdown('<div class="role-label">FF</div>', unsafe_allow_html=True)
        ff3_name = st.selectbox(
            "FIREFIGHTER Rota ?",
            options=sample_names,
            key="CPL181E_FF3",
            label_visibility="collapsed"
        )
        st.session_state.deployment['CPL181E']['FF3'] = ff3_name
        
        # FF4
        st.markdown('<div class="role-label">FF</div>', unsafe_allow_html=True)
        ff4_name = st.selectbox(
            "FIREFIGHTER Rota ?",
            options=sample_names,
            key="CPL181E_FF4",
            label_visibility="collapsed"
        )
        st.session_state.deployment['CPL181E']['FF4'] = ff4_name

    # A181D
    with cols[3]:
        st.markdown('<div class="column-header">A181D</div>', unsafe_allow_html=True)
        
        # PRM
        st.markdown('<div class="role-label">PRM</div>', unsafe_allow_html=True)
        prm_name = st.selectbox(
            "PARAMEDIC",
            options=sample_names,
            key="A181D_PRM",
            label_visibility="collapsed"
        )
        st.session_state.deployment['A181D']['PRM'] = prm_name
        
        # EMTD
        st.markdown('<div class="role-label">EMT (DRIVER)</div>', unsafe_allow_html=True)
        emtd_name = st.selectbox(
            "DRIVER",
            options=sample_names,
            key="A181D_EMTD",
            label_visibility="collapsed"
        )
        st.session_state.deployment['A181D']['EMTD'] = emtd_name
        
        # EMT1
        st.markdown('<div class="role-label">EMT</div>', unsafe_allow_html=True)
        emt1_name = st.selectbox(
            "EMT",
            options=sample_names,
            key="A181D_EMT1",
            label_visibility="collapsed"
        )
        st.session_state.deployment['A181D']['EMT1'] = emt1_name
        
        # EMT2
        st.markdown('<div class="role-label">EMT</div>', unsafe_allow_html=True)
        emt2_name = st.selectbox(
            "EMT",
            options=sample_names,
            key="A181D_EMT2",
            label_visibility="collapsed"
        )
        st.session_state.deployment['A181D']['EMT2'] = emt2_name

    # A182D
    with cols[4]:
        st.markdown('<div class="column-header">A182D</div>', unsafe_allow_html=True)
        
        # PRM
        st.markdown('<div class="role-label">PRM</div>', unsafe_allow_html=True)
        prm_name = st.selectbox(
            "PARAMEDIC",
            options=sample_names,
            key="A182D_PRM",
            label_visibility="collapsed"
        )
        st.session_state.deployment['A182D']['PRM'] = prm_name
        
        # EMTD
        st.markdown('<div class="role-label">EMT (DRIVER)</div>', unsafe_allow_html=True)
        emtd_name = st.selectbox(
            "DRIVER",
            options=sample_names,
            key="A182D_EMTD",
            label_visibility="collapsed"
        )
        st.session_state.deployment['A182D']['EMTD'] = emtd_name
        
        # EMT1
        st.markdown('<div class="role-label">EMT</div>', unsafe_allow_html=True)
        emt1_name = st.selectbox(
            "EMT",
            options=sample_names,
            key="A182D_EMT1",
            label_visibility="collapsed"
        )
        st.session_state.deployment['A182D']['EMT1'] = emt1_name
        
        # EMT2
        st.markdown('<div class="role-label">EMT</div>', unsafe_allow_html=True)
        emt2_name = st.selectbox(
            "EMT",
            options=sample_names,
            key="A182D_EMT2",
            label_visibility="collapsed"
        )
        st.session_state.deployment['A182D']['EMT2'] = emt2_name

    # Footer with action buttons
    st.markdown('<div class="footer-buttons"></div>', unsafe_allow_html=True)
    cols_btn = st.columns(3)

    # Save button
    with cols_btn[0]:
        if st.button("Save Deployment"):
            success = save_deployment_to_supabase()
            if success:
                st.success("Deployment updated successfully!")
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
            # Convert the deployment data to a format suitable for CSV
            csv_data = []
            for vehicle, roles in st.session_state.deployment.items():
                for role, name in roles.items():
                    if name:  # Only include filled positions
                        csv_data.append({
                            'Vehicle': vehicle,
                            'Position': role,
                            'Role_Description': role_descriptions.get(role, ''),
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
    # Load current deployment when app starts
    if 'initial_load' not in st.session_state:
        load_deployment_from_supabase()
        st.session_state.initial_load = True
        
    if st.session_state.page == 'home':
        home_page()
    elif st.session_state.page == 'edit':
        edit_page()

if __name__ == "__main__":
    main()
