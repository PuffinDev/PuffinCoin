from uuid import uuid4
import json
import threading

from flask import Flask
from tkinter import *
from blockchain import *


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


if __name__ == '__main__':
    app.run(debug=True, port=8222)
