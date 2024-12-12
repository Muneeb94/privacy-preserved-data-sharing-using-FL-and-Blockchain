// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SmartContract {

    struct Vehicle {
        string id;
        uint256 speed;
        string[] route;
        string current_edge_id;
        uint256 route_index;
        string next_edge;
        string[] next_edge_vehicles;
    }

    uint256 public aggregatedSpeed;

    // Updated event to include track ID and vehicle ID
    event DataUpdated(uint256 newSpeed, string trackId, string vehicleId);

    // Function to update aggregated speed data and emit event with additional parameters
    function updateAggregatedData(uint256 _newSpeed, string memory _trackId, string memory _vehicleId) public {
        require(_newSpeed > 0, "Speed must be greater than 0");
        require(bytes(_trackId).length > 0, "Track ID must not be empty");
        require(bytes(_vehicleId).length > 0, "Vehicle ID must not be empty");
      
        aggregatedSpeed = _newSpeed;
        // Emit an event with the new speed, track ID, and vehicle ID
        emit DataUpdated(_newSpeed, _trackId, _vehicleId);
    }

    // Optional: Function to retrieve the latest aggregated data
    function getLatestAggregatedData() public view returns (uint256) {
        return aggregatedSpeed;
    }

    // Define a mapping to store vehicle data by bytes32 (hash of the string id)
    mapping (bytes32 => Vehicle) vehicles;

    // Function to retrieve vehicle speed by ID
    function getVehicleSpeed(string memory id) public view returns (uint256) {
        bytes32 idHash = keccak256(abi.encodePacked(id));
        require(bytes(vehicles[idHash].id).length > 0, "Vehicle not found");
        return vehicles[idHash].speed;
    }

    function getVehicleCurrentEdge(string memory id) public view returns (string memory) {
        bytes32 idHash = keccak256(abi.encodePacked(id));
        require(bytes(vehicles[idHash].id).length > 0, "Vehicle not found");
        return vehicles[idHash].current_edge_id;
    }

    function getVehicleRoute(string memory id) public view returns (string[] memory) {
        bytes32 idHash = keccak256(abi.encodePacked(id));
        require(bytes(vehicles[idHash].id).length > 0, "Vehicle not found");
        return vehicles[idHash].route;
    }

    function getVehicleRouteIndex(string memory id) public view returns (uint256) {
        bytes32 idHash = keccak256(abi.encodePacked(id));
        require(bytes(vehicles[idHash].id).length > 0, "Vehicle not found");
        return vehicles[idHash].route_index;
    }

    function getVehicleNextEdge(string memory id) public view returns (string memory) {
        bytes32 idHash = keccak256(abi.encodePacked(id));
        require(bytes(vehicles[idHash].id).length > 0, "Vehicle not found");
        return vehicles[idHash].next_edge;
    }

    function getVehicleNextEdgeVehicles(string memory id) public view returns (string[] memory) {
        bytes32 idHash = keccak256(abi.encodePacked(id));
        require(bytes(vehicles[idHash].id).length > 0, "Vehicle not found");
        return vehicles[idHash].next_edge_vehicles;
    }

    // Function to update vehicle data by ID
    function updateVehicleInfo(
        string memory id,
        uint256 speed,
        string[] memory route,
        string memory current_edge_id,
        uint256 route_index,
        string memory next_edge,
        string[] memory next_edge_vehicles
    ) public {
        bytes32 idHash = keccak256(abi.encodePacked(id));
        vehicles[idHash] = Vehicle(id, speed, route, current_edge_id, route_index, next_edge, next_edge_vehicles);
    }
}
