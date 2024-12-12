import torch
import torch.nn as nn
import torch.optim as optim

# Define the neural network model
class VehicleModel(nn.Module):
    def __init__(self):
        super(VehicleModel, self).__init__()
        self.fc1 = nn.Linear(2, 10)  # Input layer (e.g., speed, distance)
        self.fc2 = nn.Linear(10, 1)  # Output layer (e.g., obstacle detected or not)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)
        return x

# Function to initialize optimizer and loss function for each vehicle
def get_optimizer_and_loss(model):
    optimizer = optim.SGD(model.parameters(), lr=0.01)
    loss_function = nn.MSELoss()  # Mean squared error loss for simplicity
    return optimizer, loss_function
