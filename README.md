# Blockchain-Based State Government Scheme Monitoring System

A decentralized web application developed using **Django** and **Ethereum blockchain (Ganache)** for monitoring and managing **state government welfare scheme fund allocations**. This system ensures secure, traceable, and transparent fund approvals using blockchain transactions.

## 🔍 Overview

This platform facilitates:
- Transparent fund approvals.
- Ethereum blockchain integration (INR to ETH and back).
- Role-based dashboards for Government, Organizations, and Users.
- Real-time transaction logging and analytics.

## 🛠️ Tech Stack

- **Frontend**: HTML, CSS, Bootstrap
- **Backend**: Django (Python)
- **Blockchain**: Ethereum (Ganache, Web3.py)
- **Database**: SQLite (Django default)

 🔐 Features

**State Government Dashboard**
- View, approve, or reject organization fund requests.
- Monitor all transactions.
- Dashboard metrics for disbursed/pending funds and ETH values.

**Organization Dashboard**
- Request funds from the government.
- Approve/reject user fund requests.
- Track current funds and transactions.

 **User Dashboard**
- Request funds from organizations.
- View request history and status.

**Blockchain Integration**
- Blockchain transaction created for every approved request.
- Fund conversions: INR ➡ ETH ➡ INR.
- Transactions are logged and displayed on respective dashboards.

Setup Instructions

1. **Clone the repo**
git clone https://github.com/Himavarsitha/Django-based-blockchain-integrated-fund-management-system.git
cd Django-based-blockchain-integrated-fund-management-system

2.**Create and activate virtual environment**

python -m venv venv

source venv/bin/activate  # On Windows: venv\Scripts\activate

3.**Install dependencies**

**Install Required Python Packages**

This project depends on various Python libraries such as web3, Django, and solcx for blockchain and web integration. Please install them manually using pip:
_pip install django web3 py-solc-x mysqlclient_

Solidity Compiler (solcx)
Make sure you also install a Solidity compiler version:
_from solcx import install_solc
install_solc('0.8.0')_
Adjust the version according to your smart contract's requirements.

**Configure MySQL Database**

This project uses MySQL instead of the default SQLite database. Make sure you have MySQL installed and running.
In your settings.py file, update the DATABASES section with your own MySQL credentials:

_DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'your_database_name',
        'USER': 'your_mysql_username',
        'PASSWORD': 'your_mysql_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}_
🔔 Note: Don’t forget to create the database in MySQL before running migrations.

4.**Start Ganache**

Run Ganache on your system and copy the RPC URL (e.g., http://127.0.0.1:7545)
Create .env file
PRIVATE_KEY=your_ethereum_private_key
WALLET_ADDRESS=your_wallet_address
WEB3_PROVIDER=http://127.0.0.1:7545

5.**Run migrations and start server**

python manage.py makemigrations
python manage.py migrate
python manage.py runserver
