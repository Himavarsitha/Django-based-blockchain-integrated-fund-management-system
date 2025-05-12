import os
import json
from web3 import Web3
from dotenv import load_dotenv
from django.conf import settings
from myapp.models import Fund, Transaction, FundRequest
from decimal import Decimal

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Get Blockchain Provider
BLOCKCHAIN_PROVIDER = os.getenv("BLOCKCHAIN_PROVIDER", "HTTP://127.0.0.1:7545")
if not BLOCKCHAIN_PROVIDER:
    raise ValueError("BLOCKCHAIN_PROVIDER is not set in the .env file")

# Connect to blockchain
web3 = Web3(Web3.HTTPProvider(BLOCKCHAIN_PROVIDER))
if not web3.is_connected():
    raise ConnectionError("Failed to connect to the blockchain. Ensure Ganache is running.")

# Load compiled contract ABI and Bytecode
compiled_contract_path = os.path.join(os.path.dirname(__file__), "compiled/compiled_contract.json")
if not os.path.exists(compiled_contract_path):
    raise FileNotFoundError(f"Compiled contract JSON file not found at {compiled_contract_path}")

with open(compiled_contract_path, "r") as f:
    compiled_contract = json.load(f)

# Extract contract details safely
try:
    contract_data = compiled_contract["contracts"]["FundAllocation.sol"]["FundAllocation"]
    contract_abi = contract_data["abi"]
    contract_bytecode = contract_data["evm"]["bytecode"]["object"]
except KeyError as e:
    raise KeyError(f"Missing key in compiled contract JSON: {e}. Check the compilation output.")

# Load private key and public key from .env
private_key = os.getenv("WALLET_PRIVATE_KEY")
public_key = os.getenv("WALLET_PUBLIC_KEY")

if not private_key or not public_key:
    raise ValueError("WALLET_PRIVATE_KEY or WALLET_PUBLIC_KEY is missing in the .env file")

# ✅ Connect to existing contract if available
contract_address_path = os.path.join(os.path.dirname(__file__), "contract_address.json")
if os.path.exists(contract_address_path):
    with open(contract_address_path, "r") as f:
        contract_address = json.load(f).get("contract_address")
        if contract_address:
            contract = web3.eth.contract(address=contract_address, abi=contract_abi)
        else:
            contract = None
else:
    contract = None

# ✅ Deploy contract only if not already deployed
if contract is None:
    nonce_latest = web3.eth.get_transaction_count(public_key, 'latest')

    contract = web3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)
    transaction = contract.constructor().build_transaction({
        "from": public_key,
        "gas": 3000000,  # ✅ Increased for contract deployment
        "gasPrice": web3.to_wei('2', 'gwei'),
        "nonce": nonce_latest,
    })

    signed_txn = web3.eth.account.sign_transaction(transaction, private_key=private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

    # Save the contract address for future use
    contract_address = tx_receipt.contractAddress
    with open(contract_address_path, "w") as f:
        json.dump({"contract_address": contract_address}, f)

    contract = web3.eth.contract(address=contract_address, abi=contract_abi)

print(f"✅ Smart contract is deployed at: {contract_address}")

# Function to allocate funds on the blockchain
def allocate_funds_on_blockchain(fund_request_id):
    """Allocates funds to an organization using the blockchain."""
    try:
        fund_request = FundRequest.objects.get(id=fund_request_id)
        organization = fund_request.organization
        amount_in_wei = int(Web3.to_wei(str(fund_request.amount_requested), 'ether'))

        nonce = web3.eth.get_transaction_count(public_key, 'latest')

        # Call smart contract function to allocate funds
        transaction = contract.functions.approveFund(
            Web3.to_checksum_address(organization.wallet_address),
            amount_in_wei
        ).build_transaction({
            "from": public_key,
            "gas": 500000,
            "gasPrice": web3.to_wei('2', 'gwei'),
            "nonce": nonce
        })

        signed_txn = web3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        if tx_receipt["status"] == 1:
            print(f"✅ Blockchain allocation successful! Tx Hash: {tx_hash.hex()}")
            return tx_hash.hex()
        else:
            print("❌ Blockchain allocation failed.")
            return None

    except Exception as e:
        print(f"❌ Error in allocate_funds_on_blockchain: {e}")
        return None

# Function to send transactions
def send_transaction(from_address, to_address, amount_in_ether, private_key):
    balance_wei = web3.eth.get_balance(from_address)
    if balance_wei <= 0:
        print("❌ Wallet has no balance to send.")
        return None

    gas_price = web3.eth.gas_price
    estimated_gas = 21000  # Standard ETH transfer gas

    required_gas_fee = estimated_gas * gas_price

    # 🔐 Prevent negative values
    if balance_wei <= required_gas_fee:
        print("❌ Not enough ETH to cover gas fees.")
        return None

    max_sendable_wei = balance_wei - required_gas_fee
    max_sendable_ether = Web3.from_wei(max_sendable_wei, "ether")

    amount_in_ether = Decimal(amount_in_ether)
    if amount_in_ether > max_sendable_ether:
        print(f"⚠️ Reducing amount to max available: {max_sendable_ether} ETH")
        amount_in_ether = max_sendable_ether

    # 💥 Final safety check
    if amount_in_ether <= 0:
        print("❌ Invalid ETH amount: must be greater than 0")
        return None

    value_in_wei = int(Web3.to_wei(amount_in_ether, "ether"))

    transaction = {
        "from": from_address,
        "to": to_address,
        "value": value_in_wei,
        "gas": estimated_gas,
        "gasPrice": gas_price,
        "nonce": web3.eth.get_transaction_count(from_address),
    }

    signed_txn = web3.eth.account.sign_transaction(transaction, private_key)
    txn_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
    return txn_hash.hex()


# Function to check transaction status
def get_transaction_status(tx_hash):
    """Checks the blockchain transaction status."""
    try:
        receipt = web3.eth.get_transaction_receipt(tx_hash)
        if receipt is None:
            return "Transaction pending"
        return "Transaction successful" if receipt['status'] == 1 else "Transaction failed"
    except Exception as e:
        print(f"❌ Error getting transaction status: {e}")
        return "Error occurred"



def inr_to_eth(inr_amount):
    try:
        eth_conversion_rate = Decimal(os.getenv("ETH_CONVERSION_RATE", "200000"))
        if eth_conversion_rate <= 0:
            raise ValueError("Conversion rate must be greater than zero.")
        eth_amount = Decimal(inr_amount) / eth_conversion_rate
        return round(eth_amount, 8)  # round to 8 decimal places
    except Exception as e:
        print(f"❌ Error in INR to ETH conversion: {e}")
        return None

