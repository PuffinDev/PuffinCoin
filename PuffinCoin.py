from threading import Thread
import logging
import time
import json

from puffincoin.node import Node
from puffincoin.blockchain import Blockchain

blockchain = Blockchain() #Create blockchain

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
        blockchain.mine_transactions(keys["public_key"])
        input()

    if opt.lower() == 'd':
        print(blockchain)
        input()

    if opt.lower() == 'p':
        for transaction in blockchain.pending_transactions:
            print(transaction)
            input()
