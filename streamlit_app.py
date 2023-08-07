import streamlit as st
import pandas as pd
import re
from src.data.product_prices import get_average_prices, products
from src.data.meta_data import appliances_power, states_postal_codes
from src.models.expert_system import (inverter_spec,
                                      battery_bank_spec,
                                      solar_spec,
                                      controller_spec)


def solar_sense_app():

    # General Configurations
    st.set_page_config(page_title="SolarSense.site",
                        page_icon=r"Sheba-AI.ico")
    st.title("Solar Sense")
    st.subheader("Build your own solar PV setup.\n")

    # Sidebar activities
    with st.sidebar:
        st.header("Steps\n")

    # Update product price list
    if 'product_prices' not in st.session_state:
        try:
            with st.spinner("Updating product prices"):
                _, st.session_state['product_prices'] = get_average_prices(products)
                st.info("Product prices up to date.")
                product_prices = st.session_state['product_prices']
        except:
            while 'product_prices' not in st.session_state:
                st.warning("Error updating product prices")
                if st.button("Try Again"):
                    with st.spinner("Updating product prices"):
                        _, st.session_state['product_prices'] = get_average_prices(products)
                        st.info("Product prices up to date.")
                        product_prices = st.session_state['product_prices']

    # Appliance Selection Section
    st.divider()
    st.header("Add Appliances to PV System")
    appliance = st.selectbox("Appliances", options=list(appliances_power.keys()))
    n_units = st.number_input(label="Number of Units", min_value=1)

    col1, col2 = st.columns([1, 1])

    
    # Initialize session state if not exists
    if 'selected_appliances' not in st.session_state:
        st.session_state.selected_appliances = pd.DataFrame(columns=["Appliance", "Quantity", "Est. Unit Rating (Watts)", "Est. Load (Watts)"])

    # array button
    add = col1.button("Add")
    # Update session state if the button is clicked
    if add:
        unit_pwr_rating = appliances_power[appliance]
        appliance_details = {
            "Appliance": appliance,
            "Quantity": n_units,
            "Est. Unit Rating (Watts)": unit_pwr_rating,
            "Est. Load (Watts)": unit_pwr_rating * n_units
        }
        st.session_state.selected_appliances = pd.concat([st.session_state.selected_appliances, pd.DataFrame([appliance_details])], ignore_index=True)

    remove_last_item = col2.button("Remove Last Item")
    if remove_last_item:
        if not st.session_state.selected_appliances.empty:
            removed_appliance = st.session_state.selected_appliances.iloc[-1]["Appliance"]
            st.session_state.selected_appliances = st.session_state.selected_appliances.drop(index=st.session_state.selected_appliances.index[-1])
            st.info(f"{removed_appliance} removed.")
        else:
            st.warning("No items to remove.")

    st.table(st.session_state.selected_appliances.reset_index(drop=True).assign(**{'S/N': lambda x: x.index + 1}).set_index('S/N'))
    st.subheader(f"Total Estimated Load: {sum(st.session_state.selected_appliances['Est. Load (Watts)'])} Watts")


    # Get Customization Details
    st.divider()
    st.header("Customize Battery Bank")

    st.subheader("Battery Type")
    battery_type = st.selectbox(label= "Choose...", options=[product for product in products.keys() if "Battery" in product])

    ah_rating = int(re.search(r'\b(\d+)Ah?\b', battery_type).group(1))
    if ah_rating < 150:
        st.warning("100Ah batteries are only reccommended for\
                   very small loads (<150W Total).")
    if "Tubular" in battery_type:
        st.info(body=":green[_**Tubular batteries require maintenance every 4-6 months._]", icon="ℹ️")

    st.subheader("Backup Hours")
    duration  = st.select_slider(label= "Choose...", options=list(range(1,25)))
    st.info(body=":green[_*The selected backup duration determines how long the system will last on full charge and battery bank size._]", icon="ℹ️")

    st.info(body=":orange[_*if you proceed without adding a solar array,\nthe system will charge with grid power only._]", icon="ℹ️")
    
    col3, col4 = st.columns([1,1])

    # Initialize session state if not exists
    if 'array' not in st.session_state:
        st.session_state.array = False

    # array button
    array = col3.button("Add Solar Array")
    # Update session state if the button is clicked
    if array:
        st.session_state.array = True

    # no array button
    no_array = col4.button("Remove Solar Array")
    # Update session state if the button is clicked
    if no_array:
        st.session_state.array = False

    # Display "Button clicked!" if the session state indicates it's clicked
    if st.session_state.array:

        st.divider()
        st.header("Customize Solar Array")
        st.subheader("Solar Panel Type")
        panel_type = st.selectbox(label= "Choose...", options=[product for product in products.keys() if "Mono" in product])

        st.subheader("Charge Controller Type")
        cc_type = st.selectbox(label= "Choose...", options=["MPPT", "PWM"])

        st.subheader("Solar Capacity")
        offgrid = st.selectbox(label= "Choose...", options=["Fully Off-Grid", "Hybrid"])
        if offgrid=="Fully Off-Grid":
            st.info(body=":orange[_*Off-Grid systems cost more,\
                    but will be 100% independent\
                    of grid electricity for battery bank recharge._]", icon="ℹ️")
        else:
            st.info(body=":green[_*Lower cost, mix of solar and\
                    grid electricity for battery bank recharge._]", icon="ℹ️")
            
        st.subheader("Installation Location")
        sun_hours = st.selectbox(label="State", options=states_postal_codes) 

    else:
        panel_type=None
        cc_type=None
        offgrid=None
        
    st.divider()
    st.header("Generate Requirement Quote")

if __name__=="__main__":
    solar_sense_app()

    
    



    



            

