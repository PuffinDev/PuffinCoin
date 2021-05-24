from threading import Thread
import logging
import time
import json
import socket

from puffincoin.node import Node
from puffincoin.blockchain import Blockchain
from puffincoin.portforward import forwardPort, get_my_ip


#Forward port
local_ip = get_my_ip()
result = forwardPort(8222, 8222, "192.168.1.1", local_ip, False, "TCP", 0, None, False)

if not result:
    print("[P2P ERROR] Could not forward port with UPnP. Make sure your router has it enebled.")
    time.sleep(10)
    exit()
else:
    print("[INFO] Forwarded port 3222 with UPnP")

print('\n')

#Create blockchain
blockchain = Blockchain()

n = Node(blockchain)
Thread(target=n.start).start() #Start node
Thread(target=n.update_chain_loop).start()

log = logging.getLogger('werkzeug') #Disable logging
log.disabled = True


#Try to open wallet
f = open("wallet.json", 'r')
try: #Read wallet file
    keys = json.loads(f.read())
except: #If there is no wallet, generate new one
    keys = blockchain.generate_keys()


time.sleep(1)
print("""
=================================================
______       __  __ _       _____       _       
| ___ \     / _|/ _(_)     /  __ \     (_)      
| |_/ /   _| |_| |_ _ _ __ | /  \/ ___  _ _ __  
|  __/ | | |  _|  _| | '_ \| |    / _ \| | '_ \ 
| |  | |_| | | | | | | | | | \__/\ (_) | | | | |
\_|   \__,_|_| |_| |_|_| |_|\____/\___/|_|_| |_|
                                                
=================================================                           

Welcome!

""")

while True:
    opt = input("""
MENU

w) Wallet
t) Transfer PFC
m) Mine PFC

d) Display blockchain
b) Check balance of wallet
p) Display pending transactions

>> """)

    print('\n')

    if opt.lower() == 'w': #Display public key (wallet address)
        print("Wallet: " + keys["public_key"])
        print("Current balance: " + str(blockchain.get_balance(keys["public_key"])) + "PFC")
        input()
    
    if opt.lower() == 't': #Add transaction
        amt = input("How much PFC would you like to send?: ")
        reciever = input("Paste the wallet address of the recipient: ")
        blockchain.add_transaction(keys["private_key"], keys["public_key"], reciever, amt)
        print("Transaction added!")
        input()

    if opt.lower() == 'b': #Check balance
        wallet = input("Paste a wallet address: ")
        print("Balance: " + str(blockchain.get_balance(wallet)) + "PFC")
        input()

    if opt.lower() == 'm': #Mine transactions
        print("Press CTRL+C to stop")
        print("Mining now...")
        while True:
            try: blockchain.mine_transactions(keys["public_key"])
            except KeyboardInterrupt: break
        input()

    if opt.lower() == 'd':
        print(blockchain)
        input()

    if opt.lower() == 'p':
        for transaction in blockchain.pending_transactions:
            print(transaction)
            input()
