from web3 import Web3

# HTTP provider URL (Ganache default URL is http://127.0.0.1:7545 for the GUI version)
ganache_url = "http://127.0.0.1:7545"

# Create an instance of Web3
web3 = Web3(Web3.HTTPProvider(ganache_url))

# Check if the connection is successful
if web3.is_connected():
    print("Connected to Ganache!")
else:
    print("Failed to connect to Ganache.")

# Example: Getting the first account from Ganache
accounts = web3.eth.accounts
print("Accounts on Ganache:", accounts)

# Example: Getting the balance of the first account
balance = web3.eth.get_balance(accounts[0])
print("Balance of first account:", web3.from_wei(balance, 'ether'), "ETH")
