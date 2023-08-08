"""
Module to calculate Solar PV component requirements
"""

import re


def inverter_spec(load: int, products: dict) -> str:
    req_capacity = (load / 0.69) / 1000  # Required capacity in kVA

    suitable_inverter = None
    for inverter, description in products.items():
        if "Inverter" in inverter:
            capacity = float(re.search(r'\d+(\.\d+)?', inverter).group())
            if capacity >= req_capacity:
                suitable_inverter = inverter
                break

    return suitable_inverter


def battery_bank_spec(load: int,
                      duration: int,
                      inverter_spec: str, 
                      b_type: str = "Battery 220Ah 12V Tubular",
                      DoD: float = 0.7,
                      b_eff: float = 0.9,
                      b_volt: int = 12) -> tuple:
    
    sys_voltage = int(re.search(r'\b(\d+)V\b', inverter_spec).group(1))
    battery_multiples = sys_voltage/b_volt
    consumption = load * duration
    req_capacity = (consumption)/(DoD * b_eff)

    ah_rating = int(re.search(r'\b(\d+)Ah?\b', b_type).group(1))

    b_capacity = b_volt * ah_rating

    num_batteries = req_capacity / b_capacity

    # Round num_batteries to the nearest integer and ensure 
    # it is divisible by battery_multiples (excluding 1)
    rounded_batteries = round(num_batteries)
    if rounded_batteries != 1 and rounded_batteries % battery_multiples != 0:
        rounded_batteries += 1

    return (b_type, rounded_batteries, consumption)


def array_spec(panel_type: str,
               consumption: int, 
               inverter_spec: str,
               offgrid: bool,
               peak_sun_hrs: int = 5,
               panel_eff: int = 0.75) -> tuple:
    
    sys_volt = int(re.search(r'\b(\d+)V\b', inverter_spec).group(1))
 
    panel_watt = int(re.findall(r'\b(\d+)W\b', panel_type)[0])
    panel_volt = int(re.findall(r'\b(\d+)V\b', panel_type)[0])
    
    panel_multiples = sys_volt/panel_volt

    req_capacity = consumption/(peak_sun_hrs * panel_eff)

    # Check if the system is offgrid and adjust  required capacity
    if offgrid==False:
        req_capacity = req_capacity/2
        

    num_panels = req_capacity/panel_watt

    # Round num_panels to the nearest integer and ensure 
    # it is divisible by panel_multiples (excluding 1)
    rounded_panels = round(num_panels)
    if rounded_panels != 1 and rounded_panels % panel_multiples != 0:
        rounded_panels += 1
    elif rounded_panels==0:
        rounded_panels += 1

    controller_capacity = (rounded_panels * panel_watt)/sys_volt

    return (panel_type, rounded_panels, controller_capacity)


def find_combination(p, q, r):
    best_combination = (float('inf'), float('inf'))

    for pi in p:
        for qi in q:
            min_value = min(pi, qi)
            product = pi * qi
            if product >= r and min_value < min(best_combination):
                best_combination = (pi, qi)

    return best_combination


def controller_spec(controller_capacity: float,
                    controller_type: str,
                    products: dict) -> tuple:

    # Create separate lists to store MPPT and PWM charge controllers capacities
    mppt_controllers = []
    pwm_controllers = []

    mppt_names = []
    pwm_names = []

    # Iterate through the products dictionary to categorize controllers based on type
    for product_name, product_desc in products.items():
        if "MPPT" in product_desc:
            mppt_controllers.append(float(re.search(r'\b(\d+)A\b', product_desc).group(1)))
            mppt_names.append(product_name)
        elif "PWM" in product_desc:
            pwm_controllers.append(float(re.search(r'\b(\d+)A\b', product_desc).group(1)))
            pwm_names.append(product_name)

    # Select the closest capacity from the respective controller type list
    if controller_type == "MPPT":
        selected_capacity_list = mppt_controllers
    elif controller_type == "PWM":
        selected_capacity_list = pwm_controllers
    else:
        raise ValueError("Invalid controller_type. Use 'MPPT' or 'PWM'.")

    # Sort the selected_capacity_list in ascending order
    selected_capacity_list.sort()

    # Find best combination of controller capacity and number of units
    multi_range = list(range(5))
    capacity, num_controllers = find_combination(selected_capacity_list,
                                                 multi_range,
                                                 controller_capacity)
    # Get controller name
    if controller_type == "MPPT":
        controller_name = [name for name in mppt_names if str(int(capacity)) in name][0]
    elif controller_type == "PWM":
        controller_name = [name for name in pwm_names if str(int(capacity)) in name][0]
    else:
        raise ValueError("Invalid controller_type. Use 'MPPT' or 'PWM'.")

    # Return the best combination
    return controller_name, num_controllers
