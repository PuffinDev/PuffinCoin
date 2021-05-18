#!/usr/bin/python
# -*- coding: utf-8 -*-

import hashlib
import json
from datetime import datetime
import requests

import nacl.encoding
import nacl.signing


class Blockchain():
    def __init__(self):
        self.chain = [self.add_genesis_block()]
        self.pending_transactions = []
        self.difficulty = 4
        self.miner_reward = 60
        self.block_size = 10
        self.peers = set([])

    def __str__(self):
        return_str = ''
        for block in self.chain:
            try:
                return_str += block.__str__() + '\n'
            except TypeError:
                pass

        return return_str

    def add_nodes(self, nodes):
        """
        Appends new nodes to self.peers

        :param nodes: Addresses of the nodes to add (list)
        :return: None
        """

        for node in nodes:
            self.nodes.add(node)

    def remove_nodes(self, nodes):
        """
        Removes existing nodes from self.peers

        :param nodes: Addresses of the nodes to remove (list)
        :return: None
        """

        for node in nodes:
            try:
                self.nodes.remove(node)
            except KeyError:
                pass

    def update_chain(self):
        """
        Replaces chain with longest in network

        :return: None
        """

        for node in self.peers:
            own_chain_length = len(self.chain)

            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = len(response.json()['chain'])
                chain = self.from_json(response.json()['chain'])

                print("Recieved chain of length %s from %s" %(length, node))

                if length > own_chain_length and self.is_valid(chain):
                    self.chain = chain
                


    def add_genesis_block(self):
        """
        Creates genesis block
        
        :return: genesis block
        """

        transactions = []
        genesis_block = Block(transactions, datetime.now().strftime("%d-%m-%Y %H:%M:%S"), 0)
        genesis_block.prev = ""
        return genesis_block

    def mine_transactions(self, miner):
        """
        Creates new blocks including pending transactions with PoW

        :return: None 
        """

        pt_len = len(self.pending_transactions)
        if pt_len > 1:
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

                last_hash = self.get_last_block().hash
                block.prev = last_hash
                block.mine(self.difficulty)
                self.chain.append(block)
                print("Mined block!")

            print("Finished mining.")
            self.pending_transactions.append(Transaction("Miner Reward", miner, self.miner_reward))
        else:
            print("Not enough transactions to mine.")

    def is_valid(self, chain):
        """
        Checks if a chain is valid

        :param chain: The chain to be validated
        :return: None
        """

        for i in range(1, len(chain)):
            block = chain[i]
            last_block = chain[i-1]
      
            if block.prev != last_block.hash: 
                print("[ERROR] Block hash is invalid")
                return False

            if not block.valid_transactions(chain): 
                print("[ERROR] Block transactions are not valid")
                return False

            if block.hash != block.hash_block(): 
                print("[ERROR] Block hash is not valid")
                return False

        return True

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

        return bal


    def get_last_block(self):
        """
        Return the latest block on the blockchain

        :return: Last block
        """

        return self.chain[-1]

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
                'hash': block.hash
            }

            block_json['transactions'] = []

            for transaction in block.transactions:
                block_json['transactions'].append({
                    'sender': transaction.sender,
                    'reciever': transaction.reciever,
                    'amount': transaction.amount,
                    'signature': transaction.signature,
                    'time': transaction.time,
                    'hash': transaction.hash
                })
            
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
                transaction.signature = transaction_json['signature']
                transactions.append(transaction)
            
            block = Block(transactions, block_json['time'], block_json['index'])
            block.hash = block_json['hash']
            block.prev = block_json['prev']
            block.nonse = block_json['nonse']
            blockchain.append(block)

        return blockchain


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

        print("Mining...")
        while self.hash[0:difficulty] != '0' * difficulty:
            self.nonse += 1
            self.hash = self.hash_block()

        print("Mined block " + str(self.index) + "!")

    def valid_transactions(self, chain):
        for transaction in self.transactions:
            if transaction.is_valid(chain):
                return True
            return False

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

        verify_key = nacl.signing.VerifyKey(self.sender, encoder=nacl.encoding.HexEncoder)

        signature_bytes = nacl.encoding.HexEncoder.decode(self.signature)

        try:
            verify_key.verify(bytes(self.hash, "ASCII"), signature_bytes)
        except nacl.exceptions.BadSignatureError:
            return False

        if int(self.amount) > Blockchain.get_balance(chain, self.sender):
            return False
        elif self.hash != self.hash_transaction():
            return False
        elif not self.signature or len(self.signature) == 0:
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
