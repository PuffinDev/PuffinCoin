import json
import time

from flask import Flask

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

        @self.app.route('/peers', methods=['GET'])
        def send_peers():
            return json.dumps(list(self.blockchain.peers))

        @self.app.route('/transactions', methods=['GET'])
        def send_transactions():
            return json.dumps(self.blockchain.pending_transactions_json())

    def update_chain_loop(self):
        while True:
            self.blockchain.update_chain()
            time.sleep(1)

    def start(self, host="0.0.0.0", port=8222):
        self.app.run(host=host, port=port)
