from time import time
from argparse import ArgumentParser
from flask import Flask
from flask import render_template
from flask import jsonify
from flask_cors import CORS


class Blockchain:

    def __init__(self):
        self.transactions = []
        self.chain = []
        # Create the genesis block
        self.create_block(0, '00')

    def create_block(self, nonce, previous_hash):
        """
        Add a block of transations to the blockchain
        :param nonce: int
        :param previous_hash: String
        :return: None
        """
        block = {
            'block_number': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.transactions,
            'nounce': nonce,
            'previous_hash': previous_hash
        }
        # Reset the current list of transactions
        self.transactions = []
        self.chain.append(block)


blockchain = Blockchain()
app = Flask(__name__)
CORS(app)


@app.route('/')
def index():
    return render_template('./index.html')


@app.route('/transaction/new', methods=['POST'])
def transaction_new():
    response = {'message': 'ok'}
    return jsonify(response), 201


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5001,
                        type=int, help='port to listen to')
    args = parser.parse_args()
    port = args.port
    app.run(host='127.0.0.1', port=port, debug=True)
