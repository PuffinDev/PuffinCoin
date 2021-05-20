import json
import time

from flask import Flask
from tkinter import *


class Node():
    def __init__(self, blockchain):
        self.app = Flask(__name__)
        self.blockchain = blockchain


        @self.app.route('/', methods=['GET'])
        def home():
            return "PuffinCoin Node"

        @self.app.route('/chain', methods=['GET'])
        def send_chain():
            response = {
                'chain': self.blockchain.to_json()
            }

            return json.dumps(response)

    def update_chain_loop(self):
        while True:
            self.blockchain.update_chain()
            time.sleep(2)

    def start(self, port=8222):
        self.app.run(port=port)
