# Secure Purchase Order

![Secure Company Inc.](app/static/secure_company_inc.jpg)

## Description

This project is a secure purchase order management system for Secure Company Inc., developed with FastAPI, PostgreSQL, Bootstrap, and Docker,
featuring encrypted email communication compatible with OpenPGP capable clients. It automates PGP key management, secures
transactions with dual-signature protocols, and employs PGPy for cryptographic integrity, including verifiable
timestamps to ensure transaction authenticity.

## Run

### To run this project:

1. Clone this repository

2. Run these commands:

   On first run: ```docker compose up --build```

   Afterwards: ```docker compose up```
3. Create OpenPGP key for your Admin user (e.g. https://pgpkeygen.com/, RSA)
4. Update ```users.sql``` and ```private_keys.sql``` in ```/app/data/``` for the Admin user with your data and new
   keys (DO NOT CHANGE THE USER ID OR PASSWORD)
5. Run the SQL insert queries in /app/data/
6. Login as your Admin user (password is ```m```), then create new User, Supervisor, and Purchaser accounts (supervisor
   and purchaser need valid emails)
7. Log in as each and download each private key (option is in name dropdown, derived key to decrypt will be in the
   server log after you download)
8. Set up Supervisor and Purchaser emails in an OpenPGP capable email client (e.g. Thunderbird)
9. Download relevant public keys from Users tab
10. Add the private and public keys to Thunderbird
11. Enjoy.
