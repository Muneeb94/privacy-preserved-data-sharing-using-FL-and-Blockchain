from web3 import Web3, HTTPProvider
import json
import time
import os
import traci


def check_current_veh_existence(current_vehicle_id):
    active_vehicles = traci.vehicle.getIDList()

    if current_vehicle_id in active_vehicles:
        return 1
    return 0

def change_vehicle_color(current_vehicle_id,following_vehicle_id):
    # Visualize the sharing by changing vehicle colors
    traci.vehicle.setColor(current_vehicle_id, (255, 0, 0))  # Red for emitter
    traci.vehicle.setColor(following_vehicle_id, (0, 255, 0))  # Green for receiver


def resume_vehicle_color():
    for vehicle in traci.vehicle.getIDList():
        # Set the color to yellow (R=255, G=255, B=0, Alpha=255)
        traci.vehicle.setColor(vehicle, (255, 255, 0, 255))

def check_junction(current_edge):
     if current_edge in [':n2_2', ':n2_3', ':n3_4' , ':n4_5', ':n5_6']:
        return 1  # Return the integer 1
     return 0 

def check_edge(following_edge):
    if following_edge in ['n1n2' , 'n2n3' , 'n3n4', 'n4n5', 'n5n6']:
        return 0
    return 1

def check_vehicle(following_vehicle_id , current_vehicle_id):
    if current_vehicle_id > following_vehicle_id:
        return 0
    else:
        return 1

# Use HTTPProvider
w3 = Web3(Web3.HTTPProvider("http://localhost:7545"))

event_signature = "DataUpdated(uint256,string,string)"  # Event signature
event_topic = w3.keccak(text=event_signature).hex()
print(f"Event Topic Hash: {event_topic}")

if not event_topic.startswith("0x"):
    event_topic = "0x" + event_topic
# Test connection
try:
    block_number = w3.eth.block_number
    print(f"Connected to the blockchain! Latest block: {block_number}")
except Exception as e:
    print(f"Could not connect to the blockchain: {e}")

# Load the contract ABI and address
def load_contract():
    print("[INFO] Loading contract ABI and address...")
    with open('SmartContract.abi') as f:
        abi = json.load(f)
    with open('address.txt') as f:
        contract_address = f.read().strip()
        print(f"[INFO] Contract loaded at address: {contract_address}")
    return w3.eth.contract(address=contract_address, abi=abi)


# Create a contract instance
contract = load_contract()

# Fetch logs manually using the computed topic hash
logs = w3.eth.get_logs({
    "fromBlock": 'earliest',  # Adjust the block range as necessary
    "toBlock": "latest",
    "address": contract.address,
    "topics": [event_topic]
})

# Print logs
if logs:
    for log in logs:
        print(f"Log: {log}")
else:
    print("No logs found for the specified event.")


previous_edge_map = []

def update_vehicle_initial_edge(vehicle_id):
   
    """Set the initial edge for each vehicle."""
      # Get the current edge and route of the vehicle when it starts
    current_edge = traci.vehicle.getRoadID(vehicle_id)
    current_route = traci.vehicle.getRouteID(vehicle_id)
    
    # Check if the vehicle is already in the map
    vehicle_entry = next((v for v in previous_edge_map if v["vehicle_id"] == vehicle_id), None)
    
    if vehicle_entry is None:
        # If the vehicle doesn't exist in the map, append it with the initial edge and route
        previous_edge_map.append({
            "vehicle_id": vehicle_id,
            "current_edge": current_edge,
            "current_route": current_route
        })
        print(f"[INFO] Vehicle {vehicle_id} starting on edge {current_edge} and route {current_route}")
    else:
        # If the vehicle exists, check if the current route has changed
        if vehicle_entry["current_route"] != current_route:
            # If the route is different, update the route and edge
            vehicle_entry["current_route"] = current_route
            vehicle_entry["current_edge"] = current_edge
            print(f"[INFO] Vehicle {vehicle_id} changed route to {current_route} and edge to {current_edge}")
        else:
            # If the route has not changed, just update the edge (optional)
            if vehicle_entry["current_edge"] != current_edge:
                vehicle_entry["current_edge"] = current_edge
                print(f"[INFO] Vehicle {vehicle_id} moved to new edge {current_edge} on same route {current_route}")
        # Optionally, log the current state
        print(f"[INFO] Vehicle {vehicle_id} is on route {vehicle_entry['current_route']} and edge {vehicle_entry['current_edge']}")


# def update_vehicle_edge(vehicle_id):
#     """Update the vehicle's current edge and track transitions."""
#     current_edge = traci.vehicle.getRoadID(vehicle_id)

#     # Check if the vehicle has transitioned to a new edge
#     previous_edge = previous_edge_map.get(vehicle_id)
    
#     # Update the previous edge map with the current edge
#     previous_edge_map[vehicle_id] = current_edge

#     return previous_edge, current_edge

def check_vehicle_edge_transition(vehicle_id):
    """Check if a vehicle has transitioned to a new edge (from previous edge to current)."""
    # Get the current edge
    current_edge = traci.vehicle.getRoadID(vehicle_id)
    return current_edge
    # # Update the vehicle's edge for the next simulation step
    # update_vehicle_edge(vehicle_id)
    
    # # Get the previous edge from the map
    # previous_edge = previous_edge_map.get(vehicle_id, None)

    # Check if the vehicle has transitioned to a new edge
    # if previous_edge and previous_edge != current_edge:
    #     print(f"[INFO] Vehicle {vehicle_id} has moved from edge {previous_edge} to edge {current_edge}.")
    #     return previous_edge, current_edge
    # else:
    #     return None, current_edge

def get_vehicle_route_edge(vehicle_id):
    """Get the current route and edge for a given vehicle."""
    current_route = traci.vehicle.getRouteID(vehicle_id)  # Get the current route ID of the vehicle
    current_edge = traci.vehicle.getRoadID(vehicle_id)   # Get the current edge the vehicle is on
    
    return current_route, current_edge


# Function to send aggregated FL data to the blockchain
def update_aggregated_data_on_blockchain(average_speed, track_id, vehicle_id):
    print(f"[INFO] Preparing to send aggregated data to the blockchain for track '{track_id}' and vehicle '{vehicle_id}' with speed {average_speed}")
    try:
        # Adding more fields like track_id and vehicle_id
        tx_hash = contract.functions.updateAggregatedData(
            int(average_speed),
            track_id,
            vehicle_id
      
        ).transact({
            'from': w3.eth.accounts[0],  # Ensure this account has enough balance
            'gas': 3000000
        })
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(receipt)
        # Check logs in the receipt
        if len(receipt['logs']) == 0:
            print("No logs found in the transaction receipt.")
        else:
            print(f"Logs: {receipt['logs']}")
        print(f"Transaction mined in block {receipt.blockNumber}, storing aggregated speed: {average_speed}")

     
    except Exception as e:
        print(f"Error sending transaction to blockchain: {str(e)}")



def get_following_vehicles(traci, emitting_vehicle_id, track_id):

   
    # Get all vehicles on the same track or route
    vehicle_ids = traci.vehicle.getIDList()
    following_vehicles = []   
    # following_edges = []

    for vehicle_id in vehicle_ids:
        # Check if the vehicle is on the same track
        if traci.vehicle.getRouteID(vehicle_id) == track_id and vehicle_id != emitting_vehicle_id:
            current_edge = check_vehicle_edge_transition(vehicle_id)
            # following_edges.append({
            #     "previous_edge":previous_edge,
            #     "current_edge": current_edge
            # })
            # current_route, current_edge = get_vehicle_route_edge(vehicle_id)
            following_vehicles.append({
                "vehicle_id": vehicle_id,
                "current_edge": current_edge,
                "current_route": track_id
            })
    return following_vehicles



def share_data_with_following_vehicles(traci,speed, emitting_vehicle_id, track_id,previous_edge_map):
    # Stop the simulation at this point
    # try:
    #     print(f"[INFO] Pause simulation for data sharing")
        
    #     stopSimulation()
    #     print(f"[ERROR] Could not pause simulation: {e}")    
    # following_vehicles = get_following_vehicles(traci,emitting_vehicle_id, track_id)
    # print(f"[INFO] i'm inside share data function")
    # Loop over the previous_edge_map
    for i, current_vehicle in enumerate(previous_edge_map):
        # Get the current edge and route of the current vehicle
        exisit_vehicle =  check_current_veh_existence(current_vehicle["vehicle_id"])
        if(exisit_vehicle == 1):
            current_vehicle_id = current_vehicle["vehicle_id"]
            current_edge = current_vehicle["current_edge"]
            current_route = current_vehicle["current_route"]
            
            # Check the comparison with all other vehicles in previous_edge_map
            for j, following_vehicle in enumerate(previous_edge_map):
                # Skip comparison with the same vehicle
                if i == j:
                    continue  # Same vehicle, no need to share data with itself
                
                # Get the edge and route of the vehicle to compare
                following_vehicle_id = following_vehicle["vehicle_id"]
                following_edge = following_vehicle["current_edge"]
                following_route = following_vehicle["current_route"]
                
                # Conditions for sharing data:
                # 1. Same route.
                # 2. Different edges.
                # 3. Current vehicle is ahead of the following vehicle.
                # 4. Following vehicle cannot be veh0 (leader).
                if current_route == following_route and current_edge != following_edge:
                    junction_edge = check_junction(current_edge)
                    edge_list = check_edge(following_edge)
                    check_following_vehicle = check_vehicle(following_vehicle_id , current_vehicle_id)
                    if check_following_vehicle == 1:
                        if current_edge > following_edge or junction_edge >  edge_list:
                            print(f"[INFO] Sharing data from vehicle {current_vehicle_id} on edge {current_edge} "
                                f"to vehicle {following_vehicle_id} on edge {following_edge}")
                            
                            change_vehicle_color(current_vehicle_id , following_vehicle_id)
                            
                            # Share aggregated data (e.g., speed)
                            traci.vehicle.setSpeed(following_vehicle_id, speed)
                        else:
                            print(f"[INFO] No sharing: {current_vehicle_id} cannot share data to {following_vehicle_id}")
                    else:
                        print(f"[INFO] Data is not Share with vehicles {following_vehicle_id} ")
                    # # Visualize the sharing by changing vehicle colors
                    #     traci.vehicle.setColor(current_vehicle_id, (0, 255, 0))  # Red for emitter
                    #     traci.vehicle.setColor(following_vehicle_id, (0, 255, 0))  # Green for receiver
            else:
             print(f"[INFO] Data is not Share with vehicles {current_vehicle_id} on track {track_id} are on same track and are on same edges")
        else:
            print(f"[INFO] vehicle Does not exist")
        

        



def listen_for_data_updates(traci ,track_id=None, simulation_paused = []):
    print("[INFO] Setting up event subscription for DataUpdated events...")

    try:

        event_filter = contract.events.DataUpdated.create_filter(argument_filters={},from_block="latest" )

        print("[INFO] Listening for data updates on the blockchain...")

        # Continuous loop to listen for new events
        while True:
            try:
                # Fetch new entries from the event filter
                new_events = event_filter.get_new_entries()
                for event in new_events:
                    # Extract data from the event
                    new_speed = event["args"]["newSpeed"]
                    event_track_id = event["args"]["trackId"]
                    event_vehicle_id = event["args"]["vehicleId"]

                    print(f"[INFO] New DataUpdated event detected! Speed: {new_speed}, Track ID: {event_track_id}, Vehicle ID: {event_vehicle_id}")
                    

                    # Aggregated data (this could be average speed, aggregated model weights, etc.)
                    aggregated_data = new_speed  # In a real scenario, this would be model data aggregation, not just speed
                    
                    
                    if event_track_id == track_id:
                        print(f"[ACTION] Sharing data for Track '{track_id}'")
                                 
                        simulation_paused[0] = True
                        share_data_with_following_vehicles(traci, new_speed, event_vehicle_id, track_id,previous_edge_map)
                        simulation_paused[0] = False
                        resume_vehicle_color()
                    


                    # If track_id is provided, filter by it
                    if track_id is None or event_track_id == track_id:
                        print(f"[ACCESS] Accessing aggregated data for Track '{event_track_id}' and Vehicle '{event_vehicle_id}' with Speed {new_speed}")
                        print(f"[ACTION] Sharing data with vehicle on the same track '{event_track_id}'")


            except Exception as e:
                print(f"[ERROR] Error fetching events: {e}")

            # Sleep for a short time before checking for new events
            time.sleep(2)

    except Exception as e:
        print(f"[ERROR] Listening for data updates failed: {e}")