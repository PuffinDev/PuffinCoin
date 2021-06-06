from threading import Thread
import logging
import time
import json
import socket

from puffincoin.node import Node
from puffincoin.blockchain import Blockchain
from puffincoin.portforward import forwardPort, get_my_ip
from puffincoin.utils import Utils

inputString = ""


def save_blockchain(blockchain):
    while True:
        try:
            with open("blockchain.json", "w") as f:
                payload = blockchain.to_json()
                json.dump(payload, f)
        except Exception:
            pass

        time.sleep(1)



#Forward port
local_ip = get_my_ip()
result = forwardPort(8222, 8222, "192.168.1.1", local_ip, False, "TCP", 0, None, False)

if not result:
    print("[P2P ERROR] Could not forward port with UPnP. Make sure your router has it enebled.")
    time.sleep(10)
    exit()
else:
    print("[INFO] Forwarded port 8222 with UPnP")


#Create blockchain
blockchain = Blockchain()

f = open("config.json", "r")
config = json.load(f)


#Load saved blockchain
try:
    data = json.load(open("blockchain.json", "r"))
    blockchain.chain = blockchain.from_json(data)
except Exception:
    pass


print("[INFO] Starting node...")
n = Node(blockchain)
Thread(target=n.start).start() #Start node
Thread(target=n.update_chain_loop).start()
Thread(target=save_blockchain, args=(blockchain,)).start()

log = logging.getLogger('werkzeug') #Disable logging
log.disabled = True
time.sleep(0.4)

print("[INFO] Adding seed node(s)...")

result = blockchain.add_nodes(config["seed_nodes"]) #Add seed nodes

if not result:
    print("\n[ERROR] Could not connect to any seed nodes.")
    print("If you continue, changes made to the blockchain may not be saved.")
    opt = input("Do you wish to continue? y/n :")
    if opt.lower() == 'n':
        exit()

print('\n')

#Try to open wallet
f = open("wallet.json", 'r')
try: #Read wallet file
    print("[INFO] Loading wallet...")
    keys = json.loads(f.read())
except: #If there is no wallet, generate new one
    print("[INFO] Generating wallet...")
    keys = blockchain.generate_keys()
    print("""
  ___ __  __ ___  ___  ___ _____ _   _  _ _____ _ 
 |_ _|  \/  | _ \/ _ \| _ \_   _/_\ | \| |_   _| |
  | || |\/| |  _/ (_) |   / | |/ _ \| .` | | | |_|
 |___|_|  |_|_|  \___/|_|_\ |_/_/ \_\_|\_| |_| (_)

  You MUST store the wallet.json file somewere else
  on your computer or you may loose your wallet!
  If you loose your wallet, just drag over the 
  file to restore your it.                                                                           

    """)


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

def menu():
    exit = False
    while not exit:
        opt = input("""
MENU

w) Wallet
t) Transfer PFC
h) Transaction history
m) Mine PFC
e) Exit the Program

1| Display blockchain
2| Check balance of a wallet
3| Display pending transactions
4| Display connected peers
5| Add a peer
6| PuffinCoin version
7| Test hashrate

>> """)

        print('\n')

        if opt.lower() == 'w': #Display public key (wallet address)
            print("Wallet: " + keys["public_key"])
            print("Current balance: " + str(blockchain.get_balance(keys["public_key"])) + "PFC")
            
        elif opt.lower() == 't': #Add transaction
            amt = input("How much PFC would you like to send?: ")
            reciever = input("Paste the wallet address of the recipient: ")
            blockchain.add_transaction(keys["private_key"], keys["public_key"], reciever, amt)
            print("Transaction added!")

        elif opt.lower() == 'm': #Mine transactions
            print("Press CTRL+C to stop")
            
            print("Mining now...")
            while True:
                try:
                    blockchain.mine_transactions(keys["public_key"])
                except KeyboardInterrupt:
                    break

        elif opt.lower() == 'h': #Transaction history
            transactions = blockchain.get_transaction_history(keys["public_key"])

            for transaction in transactions:
                print(transaction.__str__().replace(keys["public_key"], "You"))

        elif opt.lower() == '1': #Display blockchain
            print(blockchain)

        elif opt.lower() == '2': #Check balance
            wallet = input("Paste a wallet address: ")
            print("Balance: " + str(blockchain.get_balance(wallet)) + "PFC")

        elif opt.lower() == '3': #Pending transactions
            for transaction in blockchain.pending_transactions:
                print(transaction)

        elif opt.lower() == '4': #Display connected peers
            for node in blockchain.peers:
                print(node)

        elif opt.lower() == '5': #Add peer
            addr = input("Type the address of a PuffinCoin node: ")
            blockchain.add_nodes([addr])
            print("Added.")

        elif opt.lower() == '6': #Version
            print(blockchain.VER)

        elif opt.lower() == '7': #Test hashrate
            print("Testing...")

            rates = []
            for i in range(1,10):
                rates.append(Utils.test_hashrate())
            rate = sum(rates) / len(rates)

            print("Your hashrate: ~" + str(round(rate / 1000000, 4)) + " GH/s")
            hashes_for_pfc = 17000000
            
            block_time = hashes_for_pfc / rate
            print("Block time: ~" + str(round(block_time, 4)) + "s")

        
        elif opt.lower() == 'e':
            exit = True
            
        else:
            print("Invalid input! Please try again.")

menu()
quit()
