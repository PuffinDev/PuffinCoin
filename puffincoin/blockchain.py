#!/usr/bin/python
# -*- coding: utf-8 -*-

import hashlib
import json
from datetime import datetime
import time
import requests
import urllib.request

import nacl.encoding
import nacl.signing

class Blockchain():
    def __init__(self):
        self.VER = "0.5.0"

        self.chain = [self.add_genesis_block()]
        self.pending_transactions = []
        self.difficulty = 6
        self.miner_reward = 5
        self.block_size = 10
        self.peers = set([])
        self.public_ip = self.get_public_ip()

    def __str__(self):
        return_str = ''
        for block in self.chain:
            try:
                return_str += block.__str__() + '\n'
            except TypeError:
                pass

        return return_str

    #NETWORKING

    def add_nodes(self, nodes):
        """
        Appends new nodes to self.peers

        :param nodes: Addresses of the nodes to add (list)
        :return: True if sucessfully added over 1 node
        """

        connected_nodes_amt = 0

        for node in nodes:
            if self.public_ip in node or node in self.peers:
                continue


            try:
                ver = requests.get("http://" + node + "/version", timeout=4).text
            except Exception:
                print("[INFO] Could not recive version from: " + "http://" + node + "/version")
                continue

            if ver == self.VER:
                self.peers.add(node)
                try: #Register as a node
                    requests.post("http://" + node + "/register", self.public_ip + ":8222", timeout=4)
                    connected_nodes_amt += 1
                except Exception:
                    print("[INFO] Could register at: " + "http://" + node + "/register")
                    continue
            
            else:
                try:
                    release, feature, patch = ver.split(".")
                    own_release, own_feature, own_patch = self.VER.split(".")
                except Exception:
                    print("[INFO] Could not parse version: " + ver)
                    continue


                if release > own_release:
                    update = True
                elif feature > own_feature:
                    update = True
                elif patch > own_patch:
                    update = True
                else:
                    update = False
                
                if len(self.peers) == 0:

                    if update:
                        print("[INFO] You are not on the latest version of PuffinCoin. Visit https://github.com/PuffinDev/PuffinCoin to update. IMPORTANT: save the wallet.json file.")
                        time.sleep(500)
                        exit()
                    else:
                        print("[INFO] Seed node is using an outdated version of PuffinCoin.")
                        time.sleep(500)
                        exit()

                else:
                    if update:
                        print("[INFO] Could not add node, please update to the latest version of PuffinCoin")
                    else:
                        print("[INFO] Node is using outdated version of PuffinCoin.")

        if connected_nodes_amt > 0:
            return True
        else:
            return False


    def get_public_ip(self):
        return requests.get('https://api.ipify.org').text

    def remove_nodes(self, nodes):
        """
        Removes existing nodes from self.peers

        :param nodes: Addresses of the nodes to remove (list)
        :return: None
        """

        for node in nodes:
            try:
                self.peers.remove(node)
            except KeyError:
                pass

    def update_chain(self):
        """
        Replaces chain with longest in network

        :return: None
        """

        #Get new peers
        new_peers = []

        peers = self.peers
        for node in peers:
            try:
                response = requests.get(f'http://{node}/peers', timeout=4)
            except:
                continue

            if response.status_code == 200:
                for node in response.json():
                    if not node in self.peers:
                        if not self.public_ip in node:
                            new_peers.append(node)

        self.add_nodes(new_peers)



        #Update blockchain
        for node in self.peers:
            own_chain_length = len(self.chain)

            try:
                response = requests.get(f'http://{node}/chain', timeout=4)
            except:
                continue

            if response.status_code == 200:
                length = len(response.json()['chain'])
                chain = self.from_json(response.json()['chain'])

                if length > own_chain_length and self.is_valid(chain, self):
                    self.chain = chain


            #Recieve pending transactions
            try:
                response = requests.get(f'http://{node}/transactions', timeout=4)
            except:
                continue
        
            if response.status_code == 200:
                try:
                    transactions = self.pending_transactions_from_json(response.json())
                except json.JSONDecodeError:
                    print("Could not decode json:")
                    print(response.text)
                    continue

                for tx in transactions:
                    exists = False
                    for pending_tx in self.pending_transactions:
                        if pending_tx.hash == tx.hash:
                            exists = True
                            break
                    
                    if not exists:
                        self.pending_transactions.append(tx)


            #Remove mined transactions
            for block in self.chain:
                for block_tx in block.transactions:
                    for pending_tx in self.pending_transactions:
                        if block_tx.hash == pending_tx.hash:
                            self.pending_transactions.remove(pending_tx)

    def is_valid(self, chain, own_chain):
        """
        Checks if a chain is valid

        :param chain: The chain to be validated
        :param own_chain: The local chain
        :return: None
        """

        for i in range(1, len(chain)):
            block = chain[i]
            last_block = chain[i-1]
            
            if not block.index == 0: #Don't check genesis block
                if block.prev != last_block.hash: 
                    #print("[ERROR] Block hash is invalid")
                    return False
                
                if block.hash != block.hash_block():
                    #print("[ERROR] Block hash is not valid")
                    return False

                if not block.valid_transactions(own_chain): 
                    #print("[ERROR] Block transactions are not valid")
                    return False

        return True
                
    #BLOCKCHAIN UTILS

    def add_genesis_block(self):
        """
        Creates genesis block
        
        :return: genesis block
        """

        transactions = []
        genesis_block = Block(transactions, datetime.now().strftime("%d-%m-%Y %H:%M:%S"), 0)
        genesis_block.prev = ""
        return genesis_block

    def get_last_block(self):
        """
        Return the latest block on the blockchain

        :return: Last block
        """

        return self.chain[-1]

    def mine_transactions(self, miner):
        """
        Creates new blocks including pending transactions with PoW

        :return: None 
        """

        pt_len = len(self.pending_transactions)
        for i in range(0, pt_len, self.block_size):
            end = i + self.block_size
            if i >= pt_len:
                end = pt_len
            transactions = self.pending_transactions[i:end]

            block = Block(
                transactions,
                datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                len(self.chain)
                )

            block.prev = self.get_last_block().hash
            block.mine(self.difficulty)
            self.chain.append(block)
            print("Mined block %s!" %(block.index))
            print("Hash: " + block.hash)

            for tx in self.pending_transactions[i:end]: #Remove transactions
                self.pending_transactions.remove(tx)

        self.pending_transactions.append(Transaction("Miner Reward", miner, self.miner_reward))


    def add_transaction(self, private_key, sender, reciever, amount):
        """
        Create new transaction object and append it to pending transactions

        :param sender: Sender's public key (wallet address)
        :param reciever: Reciever's public key (wallet address)
        :param amount: Amount of PFC to be transfered
        :return: None
        """

        transaction = Transaction(sender, reciever, amount)
        transaction.sign(private_key)

        if not transaction.is_valid(self):
            print("[ERROR] Transaction is not valid")
        else:
            self.pending_transactions.append(transaction)

    def get_balance(self, wallet):
        """
        Gets balance of a wallet

        :param wallet: wallet address (public key)
        :return: balance
        """

        bal = 0
        for block in self.chain:
            for transaction in block.transactions:
                if transaction.reciever == wallet:
                    bal += int(transaction.amount)
                if transaction.sender == wallet:
                    bal -= int(transaction.amount)

        return bal

    def transaction_index_from_hash(self, _hash):
        """
        Gets the index of a transaction

        :param _hash: The hash of the transaction
        :return: index of transaction (int)
        """

        i = 0
        for block in self.chain:
            for tx in block.transactions:
                if tx.hash == _hash:
                    return i
                else:
                    i += 1
        return len(self.chain)
    
    def get_balance_before_transaction(self, wallet, tx_index):
        """
        Gets the balance of a wallet before a spesific transaction

        :param wallet: The wallet address
        :param tx_index: The index of the transaction to check before
        :return: balance (int)
        """

        print("I: " + str(tx_index))
        i = 0
        bal = 0
        for block in self.chain:
            for transaction in block.transactions:
                if not i >= tx_index:
                    if transaction.reciever == wallet:
                        bal += int(transaction.amount)
                    if transaction.sender == wallet:
                        bal -= int(transaction.amount)
                else:
                    return bal
                i += 1
        return bal

    def get_transaction_history(self, wallet):
        """
        Returns all transactions to or from a wallet

        :param wallet: The wallet address
        :return: Transactions (list)
        """
        
        transactions = []
        for block in self.chain:
            for transaction in block.transactions:
                if transaction.sender == wallet or transaction.reciever == wallet:
                    transactions.append(transaction)
        
        return transactions



    def generate_keys(self):
        """
        Create public and private RSA keys
        
        :return: Dict containing public and private keys
        """

        private_key = nacl.signing.SigningKey.generate()
        public_key = private_key.verify_key

        keys = {
            "private_key": private_key.encode(encoder=nacl.encoding.HexEncoder).decode(),
            "public_key": public_key.encode(encoder=nacl.encoding.HexEncoder).decode(),
        }

        with open("wallet.json", "w") as f:
            json.dump(keys, f)

        return keys

    #JSON

    def to_json(self):
        """
        Convert blockchain to json

        :return: json blockchain
        """

        blockchain_json = []

        for block in self.chain:
            block_json = {
                'index': block.index,
                'time': block.time,
                'prev': block.prev,
                'nonse': block.nonse,
                'hash': block.hash,
                'transactions': []
            }

            for transaction in block.transactions:
                #block_json['transactions'].append(
                    
                payload = {
                    'sender': transaction.sender,
                    'reciever': transaction.reciever,
                    'amount': transaction.amount,
                    'time': transaction.time,
                    'hash': transaction.hash
                }

                try:
                    payload['signature'] = transaction.signature
                except AttributeError:
                    pass

                block_json['transactions'].append(payload)
            
            blockchain_json.append(block_json)

        return blockchain_json

    def from_json(self, blockchain_json):
        """
        Convert json to blockchain objects (Block, Transaction)

        :param blockchain_json: json blockchain
        :return: blockchain
        """

        blockchain = []
        for block_json in blockchain_json:

            transactions = []
            for transaction_json in block_json['transactions']:
                transaction = Transaction(
                    transaction_json['sender'],
                    transaction_json['reciever'],
                    transaction_json['amount']
                    )

                transaction.time = transaction_json['time']
                transaction.hash = transaction_json['hash']

                try:
                    transaction.signature = transaction_json['signature']
                except:
                    pass

                transactions.append(transaction)
            
            block = Block(transactions, block_json['time'], block_json['index'])
            block.hash = block_json['hash']
            block.prev = block_json['prev']
            block.nonse = block_json['nonse']
            blockchain.append(block)

        return blockchain

    def pending_transactions_json(self):
        """
        Converts self.pending_pransactions to json data

        :return: Json transactions
        """

        transactions = []
        for transaction in self.pending_transactions:
            payload = {
                'sender': transaction.sender,
                'reciever': transaction.reciever,
                'amount': transaction.amount,
                'time': transaction.time,
                'hash': transaction.hash
            }

            try:
                payload['signature'] = transaction.signature
            except AttributeError:
                pass

            transactions.append(payload)

        return transactions

    def pending_transactions_from_json(self, transactions_json):
        """
        Converts a list of json transactions to transaction objects

        :param transactions_json: List of transaction dicts
        :return: Transactions
        """

        transactions = []
        for transaction_json in transactions_json:
            transaction = Transaction(
                    transaction_json['sender'],
                    transaction_json['reciever'],
                    transaction_json['amount']
                    )

            transaction.time = transaction_json['time']
            transaction.hash = transaction_json['hash']

            try:
                transaction.signature = transaction_json['signature']
            except:
                pass

            transactions.append(transaction)

        return transactions



class Block():
    def __init__(self, transactions, time, index):
        self.index = index
        self.time = time
        self.transactions = transactions
        self.prev = ''
        self.nonse = 0
        self.hash = self.hash_block()

    def __str__(self):
        return_str = f"""
Index: {self.index}
Time: {self.time}
Hash: {self.hash}
Previous Hash: {self.prev}
Nonse: {self.nonse}
Transactions:\n"""

        for transaction in self.transactions:
            return_str += transaction.__str__() + "\n"

        return return_str

    def block_str(self):
        transaction_hashes = ''
        for transaction in self.transactions:
            transaction_hashes += transaction.hash

        return self.time + transaction_hashes + self.prev + str(self.nonse)

    def hash_block(self):
        """
        Hash data in block

        :return: Hash
        """

        transaction_hashes = ''
        for transaction in self.transactions:
            transaction_hashes += transaction.hash

        block_str = self.time + transaction_hashes + self.prev + str(self.nonse)

        encoded_block = hashlib.sha256(
            json.dumps(block_str, sort_keys=True).encode()
            ).hexdigest()

        return encoded_block

    def mine(self, difficulty):
        """
        Create proof of work for block

        :param difficulty: ammount of 0's needed in hash
        :return: None
        """

        while self.hash[0:difficulty] != '0' * difficulty:
            self.nonse += 1
            self.hash = self.hash_block()

    def valid_transactions(self, chain):
        i = 0
        for transaction in self.transactions:
            i += 1
            if transaction.is_valid(chain):
                continue
            else:
                return False
        return True

class Transaction():
    def __init__(self, sender, reciever, amount):
        self.sender = sender
        self.reciever = reciever
        self.amount = amount
        self.time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        self.hash = self.hash_transaction()

    def __str__(self):
        return f"{self.sender} --> {self.reciever}  {self.amount}PFC"

    def hash_transaction(self):
        """
        Hash data in transaction

        :return: hash
        """

        transaction_str = str(self.sender) + str(self.reciever) + str(self.amount) + self.time

        encded_transaction = hashlib.sha256(
            json.dumps(
                transaction_str, sort_keys=True).encode()
            ).hexdigest()

        return encded_transaction

    def is_valid(self, chain):
        """
        Check if transaction is valid

        :return: True of False
        """

        if self.sender == 'Miner Reward':
            if self.amount > chain.miner_reward:
                print("reward too high")
                return False
            
        else:
            try:
                tx_index = chain.transaction_index_from_hash(self.hash)
                if int(self.amount) > chain.get_balance_before_transaction(self.sender, tx_index):
                    print("sender does not have enough balance")
                    return False


                verify_key = nacl.signing.VerifyKey(self.sender, encoder=nacl.encoding.HexEncoder)

                signature_bytes = nacl.encoding.HexEncoder.decode(self.signature)

                try:
                    verify_key.verify(bytes(self.hash, "ASCII"), signature_bytes)
                except nacl.exceptions.BadSignatureError:
                    print("bad signiture")
                    return False

            except AttributeError:
                print("no signature")
                return False

        if self.hash != self.hash_transaction():
            print("invalid hash")
            return False
        else:
            return True

    def sign(self, private_key):
        """
        Sign transaction

        :return: None
        """

        signing_key = nacl.signing.SigningKey(private_key, encoder=nacl.encoding.HexEncoder)
        signature = signing_key.sign(bytes(self.hash, 'ASCII')).signature
        self.signature = nacl.encoding.HexEncoder.encode(signature).decode("ASCII")
