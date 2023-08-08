import streamlit as st
import pandas as pd
import re
from src.data.product_prices import get_average_prices, products
from src.data.meta_data import appliances_power, states_postal_codes
from src.models.expert_system import (inverter_spec,
                                      battery_bank_spec,
                                      array_spec,
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
                st.session_state['product_prices'], _ = get_average_prices(products)
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
    else:
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

    if sum(st.session_state.selected_appliances['Est. Load (Watts)']):
        total_load = sum(st.session_state.selected_appliances['Est. Load (Watts)'])
    else:
        total_load = 0

    st.table(st.session_state.selected_appliances.reset_index(drop=True).assign(**{'S/N': lambda x: x.index + 1}).set_index('S/N'))
    st.subheader(f"Total Estimated Load: {total_load} Watts")


    # Get Customization Details

    # Battery Bank Customization
    st.divider()
    st.header("Customize Battery Bank")

    st.subheader("Battery Type")
    battery_type = st.selectbox(label= "Choose preferred battery type", options=[product for product in products.keys() if "Battery" in product])

    ah_rating = int(re.search(r'\b(\d+)Ah?\b', battery_type).group(1))
    if ah_rating < 150:
        st.warning("100Ah batteries are only reccommended for\
                   very small loads (<150W Total).")
    if "Tubular" in battery_type:
        st.info(body=":green[_**Tubular batteries require maintenance every 4-6 months._]", icon="ℹ️")

    st.subheader("Backup Hours")
    duration  = st.select_slider(label= "Select with slider", options=list(range(1,25)))
    st.info(body=":green[_*The selected backup duration determines how long the system will last on full charge and battery bank size._]", icon="ℹ️")

    
    # Solar Array Customization
    col3, col4 = st.columns([1,1])

    # Initialize session state if not exists
    if 'array' not in st.session_state:
        st.session_state.array = False
        st.info(body=":orange[_*if you proceed without adding a solar array,\nthe system will charge with grid power only._]", icon="ℹ️")
    
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
        st.info(body=":orange[_*if you proceed without adding a solar array,\nthe system will charge with grid power only._]", icon="ℹ️")

    # Display Solar Array options if the session state indicates it's clicked
    if st.session_state.array:

        st.divider()
        st.header("Customize Solar Array")
        st.subheader("Solar Panel Type")

        inverter_voltage = inverter_spec(total_load, products)
        if "12V" not in inverter_voltage:
            panel_type = st.selectbox(label= "Choose...", options=[product for product in products.keys() if "Mono" in product])
        else:
            panel_type = st.selectbox(label= "Choose...", options=[product for product in products.keys() if "W 12V" in product])
        st.subheader("Charge Controller Type")
        cc_type = st.selectbox(label= "Choose...", options=["MPPT", "PWM"])

        st.subheader("Solar Capacity")
        offgrid = st.selectbox(label= "Choose...", options=["Fully Off-Grid", "Hybrid"])
        if offgrid=="Fully Off-Grid":
            offgrid=True
            st.info(body=":orange[_*Off-Grid systems cost more,\
                    but will be 100% independent\
                    of grid electricity for battery bank recharge._]", icon="ℹ️")
        else:
            offgrid=False
            st.info(body=":green[_*Lower cost, mix of solar and\
                    grid electricity for battery bank recharge._]", icon="ℹ️")
            
        st.subheader("Installation Location")
        sun_hours = st.selectbox(label="State", options=states_postal_codes) 

    else:
        panel_type=None
        cc_type=None
        offgrid=None

    # Qoute Generation Section   
    st.divider()
    st.header("Requirement Quote")

    col5, col6 = st.columns([1,1])
    # Initialize session state if not exists
    if 'quote' not in st.session_state:
        st.session_state.quote = False
        st.info(body=":orange[_*if you proceed without adding a solar array,\nthe system will charge with grid power only._]", icon="ℹ️")
    
    # array button
    quote = col5.button("Get Quote")
    # Update session state if the button is clicked
    if quote:
        st.session_state.quote = True

    # no array button
    no_quote = col6.button("Clear Quote")
    # Update session state if the button is clicked
    if no_quote:
        st.session_state.quote = False

    if st.session_state.quote:
        if panel_type!=None and cc_type!=None and offgrid!=None:

            # Inverter Calculation and Quote
            inverter = inverter_spec(
                load=total_load,
                products=products
            )

            inverter_quote = {
                "Item": inverter,
                "Unit Price": int(product_prices[inverter]),
                "Units": 1,
                "Cost": int(product_prices[inverter])
            }
            
            # Battery Calc and Quote
            battery_bank = battery_bank_spec(
                load=total_load,
                duration=duration,
                inverter_spec=inverter,
                b_type=battery_type,
                # Add advanced setings parameters
            )

            battery_quote = {
                "Item": battery_bank[0],
                "Unit Price": int(product_prices[battery_bank[0]]),
                "Units": battery_bank[1],
                "Cost": int(battery_bank[1] * product_prices[battery_bank[0]])
            }

            # Solar Array Calc and Quote
            solar_array = array_spec(
                panel_type=panel_type,
                consumption=battery_bank[2],
                inverter_spec=inverter,
                offgrid=offgrid,
                # Add advanced setings parameters
            )

            solar_array_quote = {
                "Item": solar_array[0],
                "Unit Price": int(product_prices[solar_array[0]]),
                "Units": solar_array[1],
                "Cost": int(solar_array[1] * product_prices[solar_array[0]])
            }

            # Charge Controller Calc and Quote
            controller = controller_spec(
                controller_capacity=solar_array[2],
                controller_type=cc_type,
                products=products
            )

            controller_quote = {
                "Item": controller[0],
                "Unit Price": int(product_prices[controller[0]]),
                "Units": controller[1],
                "Cost": int(controller[1] * product_prices[controller[0]])
            }

            quote_data = pd.DataFrame([inverter_quote,
                                       battery_quote,
                                       solar_array_quote,
                                       controller_quote])

            # Wiring and Mounts Calc and Quote
            wiring_qoute = {
                "Item": "Wiring and Mounts",
                "Unit Price": int(sum(quote_data["Cost"]) * 0.05),
                "Units": "-",
                "Cost": int(sum(quote_data["Cost"]) * 0.05)
            }

            # Installation Calc and Quote
            installation_qoute = {
                "Item": "Professional Fees",
                "Unit Price": int(sum(quote_data["Cost"]) * 0.1),
                "Units": "-",
                "Cost": int(sum(quote_data["Cost"]) * 0.1)
            }

            fees_data = pd.DataFrame([wiring_qoute,
                                      installation_qoute])
            
            final_quote = pd.concat([quote_data, fees_data])
            total_cost = int(sum(final_quote["Cost"]))

            # Format display version
            final_quote_display = final_quote.applymap(lambda x: '{:,}'.format(x) if isinstance(x, int) else x)
            st.table(final_quote_display)

            st.subheader(f"Estimated total installation fee: ₦{total_cost:{','}}")
        
        else:
            # Inverter Calculation and Quote
            inverter = inverter_spec(
                load=total_load,
                products=products
            )

            inverter_quote = {
                "Item": inverter,
                "Unit Price": int(product_prices[inverter]),
                "Units": 1,
                "Cost": int(product_prices[inverter])
            }
            
            # Battery Calc and Quote
            battery_bank = battery_bank_spec(
                load=total_load,
                duration=duration,
                inverter_spec=inverter,
                b_type=battery_type,
                # Add advanced setings parameters
            )

            battery_quote = {
                "Item": battery_bank[0],
                "Unit Price": int(product_prices[battery_bank[0]]),
                "Units": battery_bank[1],
                "Cost": int(battery_bank[1] * product_prices[battery_bank[0]])
            }
        
            quote_data = pd.DataFrame([inverter_quote,
                                       battery_quote])
            # Wiring and Mounts Calc and Quote
            wiring_qoute = {
                "Item": "Wiring and Mounts",
                "Unit Price": int(sum(quote_data["Cost"]) * 0.02),
                "Units": "-",
                "Cost": int(sum(quote_data["Cost"]) * 0.05)
            }

            # Installation Calc and Quote
            installation_qoute = {
                "Item": "Professional Fees",
                "Unit Price": int(sum(quote_data["Cost"]) * 0.1),
                "Units": "-",
                "Cost": int(sum(quote_data["Cost"]) * 0.1)
            }

            fees_data = pd.DataFrame([wiring_qoute,
                                      installation_qoute])
            
            final_quote = pd.concat([quote_data, fees_data])
            total_cost = int(sum(final_quote["Cost"]))

            # Format display version
            final_quote_display = final_quote.applymap(lambda x: '{:,}'.format(x) if isinstance(x, int) else x)
            st.table(final_quote_display)

            st.subheader(f"Estimated total installation fee: ₦{total_cost:{','}}")


if __name__=="__main__":
    solar_sense_app()

    
    



    



            

