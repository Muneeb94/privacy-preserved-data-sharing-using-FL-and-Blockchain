from web3 import Web3, HTTPProvider
import json
import traci
import math
import torch
from vehicleModel import VehicleModel, get_optimizer_and_loss
from blockchain_utils import update_aggregated_data_on_blockchain, listen_for_data_updates, update_vehicle_initial_edge
# import blockchain_utils
import threading

simulation_paused = [False]
# Start the SUMO simulation
traci.start(["sumo-gui", "-c", "Sumo.sumocfg"])



# Set up federated learning components
vehicle_models = {}
optimizers = {}
loss_functions = {}
aggregation_interval = 100  # Steps before aggregation
global_model = VehicleModel()  # Global model for aggregation

# Track where trained data should be used
def get_route_id():
    route_id = 'route0'
    vehicle_ids = traci.vehicle.getIDList()  # Get all active vehicle IDs
    # Group vehicles by route
    for vehicle_id in vehicle_ids:
        route_id = traci.vehicle.getRouteID(vehicle_id)
    return route_id

# Set the global variable using the function
target_track_id = get_route_id()

# Initialize local models for each vehicle
for vehicle_id in traci.vehicle.getIDList():
    model = VehicleModel()
    optimizer, loss_function = get_optimizer_and_loss(model)
    vehicle_models[vehicle_id] = model
    optimizers[vehicle_id] = optimizer
    loss_functions[vehicle_id] = loss_function

# Function to update vehicle models on a specific track with the aggregated model
def apply_aggregated_model_to_track(vehicle_ids, target_track_id ):
    for vehicle_id in vehicle_ids:
        route_id = traci.vehicle.getRouteID(vehicle_id)  # Get the route ID or track ID of the vehicle
        # print(f"[INFO] vehicle {route_id} on track {target_track_id} with aggregated model.")
        if route_id == target_track_id:
            vehicle_models[vehicle_id].load_state_dict(global_model.state_dict())
            # print(f"[INFO] Updated vehicle {vehicle_id} on track {target_track_id} with aggregated model.")

def get_leader_follower_pairs():
    vehicle_ids = traci.vehicle.getIDList()  # Get all active vehicle IDs
    route_groups = {}
    route_id = "route0"
    global target_track_id
    # Group vehicles by route
    for vehicle_id in vehicle_ids:
        route_id = traci.vehicle.getRouteID(vehicle_id)
        position = traci.vehicle.getLanePosition(vehicle_id)  # Position on the lane
        
        if route_id not in route_groups:
            route_groups[route_id] = []
        route_groups[route_id].append((vehicle_id, position))
    
    # Determine leader-follower pairs for each route
    leader_follower_pairs   = {}
    target_track_id         = route_id
    for route_id, vehicles in route_groups.items():
        # Sort vehicles by their position on the track
        vehicles.sort(key=lambda x: x[1], reverse=True)  # Sort by position (descending: leader first)
        
        # Pair vehicles as leader-follower
        pairs = [(vehicles[i][0], vehicles[i + 1][0]) for i in range(len(vehicles) - 1)]

        leader_follower_pairs[route_id] = pairs
        

    return leader_follower_pairs


# Start listening for blockchain data updates in a separate thread
blockchain_listener_thread = threading.Thread(target=listen_for_data_updates, args=(traci,target_track_id,simulation_paused))
blockchain_listener_thread.start()      




# previous_edge_map = {}
# Main simulation loop with federated learning and blockchain updates
step = 0
while traci.simulation.getMinExpectedNumber() > 0:
    if not simulation_paused[0]:
        # traci.simulationStep() 
        print(f"\nTime: {step} s ---------------------------------------------------------------------------->")
        step += 1
        traci.simulationStep()
        # leader_follower_pairs = get_leader_follower_pairs()
        # Get all vehicle IDs, excluding obstacles
        vehicle_ids = [v_id for v_id in traci.vehicle.getIDList() if v_id not in ("o1", "o2", "o3", "o4")]
        
        
            

        # Initialize any missing models for new vehicles dynamically
        for vehicle_id in vehicle_ids:
            update_vehicle_initial_edge(vehicle_id)
            if vehicle_id not in vehicle_models:
                model = VehicleModel()
                optimizer, loss_function = get_optimizer_and_loss(model)
                vehicle_models[vehicle_id] = model
                optimizers[vehicle_id] = optimizer
                loss_functions[vehicle_id] = loss_function
                print(f"Initialized model for new vehicle: {vehicle_id}")

        # Local training for each vehicle
        for vehicle_id in vehicle_ids:
            model = vehicle_models[vehicle_id]
            optimizer = optimizers[vehicle_id]
            loss_fn = loss_functions[vehicle_id]

            # Collect training data
            speed = traci.vehicle.getSpeed(vehicle_id)
            route_index = traci.vehicle.getRouteIndex(vehicle_id)
            X_train = torch.tensor([[speed, route_index]], dtype=torch.float32)
            y_train = torch.tensor([[1.0]])  # Label indicating an obstacle scenario

            # Train the model
            optimizer.zero_grad()
            output = model(X_train)
            loss = loss_fn(output, y_train)
            loss.backward()
            optimizer.step()

            print(f"Vehicle {vehicle_id}: Training completed with loss = {loss.item()}")

        # Federated aggregation every 'aggregation_interval' steps
        if step % aggregation_interval == 0:
            with torch.no_grad():
                # Aggregate models by averaging parameters
                global_state = global_model.state_dict()
                for key in global_state.keys():
                    global_state[key] = torch.mean(torch.stack([vehicle_models[v_id].state_dict()[key] for v_id in vehicle_ids]), dim=0)
                global_model.load_state_dict(global_state)

            # Sync each local model with the global model for all vehicles on the target track
            apply_aggregated_model_to_track(vehicle_ids, target_track_id)
            print(f"Federated aggregation completed at step {step}")

            # Send aggregated data (e.g., average speed) to the blockchain
            average_speed = sum(traci.vehicle.getSpeed(v_id) for v_id in vehicle_ids) / len(vehicle_ids)
            average_speed = int(average_speed * 10)  
            print(f"[DEBUG] Average Speed: {average_speed}")
            update_aggregated_data_on_blockchain(average_speed, track_id=target_track_id, vehicle_id="aggregated")

# Close the simulation
traci.close()
