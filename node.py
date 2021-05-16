from uuid import uuid4
import json
import threading

from flask import Flask
from tkinter import *
from puffincoin.blockchain import *


app = Flask(__name__)
blockchain = Blockchain()


@app.route('/', methods=['GET'])
def home():
    return "PuffinCoin Node"

@app.route('/chain', methods=['GET'])
def send_chain():
    response = {
        'chain': blockchain.to_json()
    }

    return json.dumps(response)

@app.route('/transaction', methods=['GET'])
def new_tx():
   key = blockchain.generate_keys()
   blockchain.add_transaction("Bob", "Joe", 1000, key, key)
   blockchain.add_transaction("Joe", "Bob", 10, key, key)
   print(blockchain)
   return "Added."

if __name__ == '__main__':
    app.run(debug=True, port=8222)
