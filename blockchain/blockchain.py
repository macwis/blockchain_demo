import hashlib
import json
from argparse import ArgumentParser
from binascii import unhexlify
from collections import OrderedDict
from time import time
from uuid import uuid4

from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from flask import Flask
from flask import jsonify
from flask import render_template
from flask import request
from flask_cors import CORS

MINING_SENDER = 'The Blockchain'
MINING_REWARD = 1
MINING_DIFFICULTY = 2


class Blockchain:

    def __init__(self):
        self.transactions = []
        self.chain = []
        self.node_id = str(uuid4()).replace('-', '')
        # Create the genesis block
        self.create_block(0, '00')

    def create_block(self, nonce, previous_hash):
        """
        Add a block of transactions to the blockchain
        """
        block = {
            'block_number': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.transactions,
            'nonce': nonce,
            'previous_hash': previous_hash
        }
        # Reset the current list of transactions
        self.transactions = []
        self.chain.append(block)
        return block

    @staticmethod
    def verify_transaction_signature(sender_public_key, signature, transaction):
        public_key = RSA.importKey(unhexlify(sender_public_key))
        verifier = PKCS1_v1_5.new(public_key)
        h = SHA.new(str(transaction).encode('utf8'))
        try:
            verifier.verify(h, unhexlify(signature))
        except ValueError:
            return False
        return True

    def submit_transaction(self, sender_public_key, recipient_public_key, signature, amount):
        transaction = OrderedDict({
            'sender_public_key': sender_public_key,
            'recipient_public_key': recipient_public_key,
            'amount': amount
        })
        if sender_public_key == MINING_SENDER:
            # Reward for mining the block
            self.transactions.append(transaction)
            return len(self.chain) + 1
        else:
            # Transaction from wallet to another wallet
            signature_verification = self.verify_transaction_signature(sender_public_key, signature, transaction)
            if signature_verification:
                self.transactions.append(transaction)
                return len(self.chain) + 1
            else:
                return False

    @staticmethod
    def valid_proof(transactions, last_hash, nonce, difficulty=MINING_DIFFICULTY):
        guess = (str(transactions) + str(last_hash) + str(nonce)).encode('utf8')
        h = hashlib.new('sha256')
        h.update(guess)
        guess_hash = h.hexdigest()
        return guess_hash[:difficulty] == '0' * difficulty

    def proof_of_work(self):
        last_block = self.chain[-1]
        last_hash = self.hash(last_block)
        nonce = 0
        while self.valid_proof(self.transactions, last_hash, nonce) is False:
            nonce += 1
        return nonce

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True)
        h = hashlib.new('sha256')
        h.update(block_string.encode('utf8'))
        return h.hexdigest()

    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            if block['previous_hash'] != self.hash(last_block):
                return False
            transactions = block['transactions'][:-1]  # we clear out the reward transaction
            transaction_elements = ['sender_public_key',
                                    'recipient_public_key',
                                    'amount']
            transactions = [OrderedDict((k, transaction[k]) for k in transaction_elements)
                            for transaction in transactions]
            if not self.valid_proof(transactions,
                                    block['previous_hash'],
                                    block['nonce'],
                                    MINING_DIFFICULTY):
                return False
            last_block = block
            current_index += 1
        return True


blockchain = Blockchain()
app = Flask(__name__)
CORS(app)


@app.route('/')
def index():
    return render_template('./index.html')


@app.route('/transactions/get', methods=['GET'])
def transactions_get():
    response = {
        'transactions': blockchain.transactions
    }
    return jsonify(response), 200


@app.route('/chain', methods=['GET'])
def chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200


@app.route('/mine', methods=['GET'])
def mine():
    # Run the proof of work algorithm
    nonce = blockchain.proof_of_work()
    blockchain.submit_transaction(sender_public_key=MINING_SENDER,
                                  recipient_public_key=blockchain.node_id,
                                  signature='',
                                  amount=MINING_REWARD)
    last_block = blockchain.chain[-1]
    previous_hash = blockchain.hash(last_block)
    block = blockchain.create_block(nonce, previous_hash)
    response = {
        'message': 'New block created',
        'block_number': block['block_number'],
        'transactions': block['transactions'],
        'nonce': block['nonce'],
        'previous_hash': block['previous_hash']
    }
    return jsonify(response), 200


@app.route('/transaction/new', methods=['POST'])
def transaction_new():
    values = request.form
    required = ['confirmation_sender_public_key', 'confirmation_recipient_public_key',
                'transaction_signature', 'confirmation_amount']
    print(values, required)
    if not all(k in values for k in required):
        return 'Missing values', 400
    transaction_results = blockchain.submit_transaction(values['confirmation_sender_public_key'],
                                                        values['confirmation_recipient_public_key'],
                                                        values['transaction_signature'],
                                                        values['confirmation_amount'])
    if transaction_results:
        response = {'message': f'Transaction will be added to the Block {transaction_results}'}
        return jsonify(response), 201
    else:
        response = {'message': 'Invalid transaction/signature'}
        return jsonify(response), 406


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5001,
                        type=int, help='port to listen to')
    args = parser.parse_args()
    port = args.port
    app.run(host='127.0.0.1', port=port, debug=True)
