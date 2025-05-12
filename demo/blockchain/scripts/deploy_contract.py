from web3 import Web3
import json
import os

# Load compiled contract
current_dir = os.path.dirname(os.path.abspath(__file__))
compiled_contract_path = os.path.join(current_dir, "../compiled/compiled_contract.json")

with open(compiled_contract_path, "r") as file:
    compiled_contract = json.load(file)

# Extract contract details
contract_abi = compiled_contract["contracts"]["FundAllocation.sol"]["FundAllocation"]["abi"]
contract_bytecode = compiled_contract["contracts"]["FundAllocation.sol"]["FundAllocation"]["evm"]["bytecode"]["object"]

# Connect to Ethereum blockchain (Ganache or Infura)
ganache_url = "Http://127.0.0.1:7545"  # Local Ganache RPC URL
web3 = Web3(Web3.HTTPProvider(ganache_url))

if not web3.is_connected():
    raise Exception("❌ Failed to connect to the blockchain. Make sure Ganache is running.")

# Use the first account from Ganache
deployer_account = web3.eth.accounts[0]

# Create and deploy contract
contract = web3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)
tx_hash = contract.constructor().transact({"from": deployer_account})

# Wait for transaction to be mined
tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

# Get deployed contract address
contract_address = tx_receipt.contractAddress

# Save contract address
contract_address_path = os.path.join(current_dir, "../compiled/deployed_contract.json")
with open(contract_address_path, "w") as file:
    json.dump({"contract_address": contract_address}, file, indent=4)

print(f"✅ Smart contract deployed successfully at: {contract_address}")
