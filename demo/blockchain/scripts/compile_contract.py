import solcx
from solcx import compile_standard
import json
import os

# Ensure Solidity compiler is installed
solcx.install_solc("0.8.0")

# Get the absolute path to this script's directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Define paths correctly
contract_path = os.path.join(current_dir, "../contracts/FundAllocation.sol")
compiled_path = os.path.join(current_dir, "../compiled/compiled_contract.json")

# Read the Solidity contract
with open(contract_path, "r") as file:
    contract_source_code = file.read()

# Compile the contract
compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {"FundAllocation.sol": {"content": contract_source_code}},
        "settings": {
            "outputSelection": {"*": {"*": ["abi", "evm.bytecode"]}},  # ✅ Corrected line
            "optimizer": {"enabled": True, "runs": 200},
        },
    },
    solc_version="0.8.0",
)


# Ensure the compiled directory exists
os.makedirs(os.path.dirname(compiled_path), exist_ok=True)

# Save compiled contract
with open(compiled_path, "w") as file:
    json.dump(compiled_sol, file, indent=4)

print("✅ Smart contract compiled successfully!")