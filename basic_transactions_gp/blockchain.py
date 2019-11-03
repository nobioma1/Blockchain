import hashlib
import json
from time import time
from uuid import uuid4

from flask import Flask, jsonify, request


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()

        # Genesis Block
        self.new_block(previous_hash=1, proof=100)

    def new_block(self, proof, previous_hash=None):

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }

        # Reset the list of transactions
        self.current_transactions = []

        # Add the block to the chain
        self.chain.append(block)

        return block

    def hash(self, block):
        """
        Creates a SHA-256 hash of a Block

        :param block": <dict> Block
        "return": <str>
        """

        str_object = json.dumps(block, sort_keys=True)
        block_str = str_object.encode()

        raw_hash = hashlib.sha256(block_str)
        hex_hash = raw_hash.hexdigest()

        return hex_hash

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def valid_proof(block_string, proof):
        """
        Validates the Proof:  Does hash(block_string, proof) contain 6
        leading zeroes?  Return true if the proof is valid
        :param block_string: <string> The stringified block to use to
        check in combination with `proof`
        :param proof: <int?> The value that when combined with the
        stringified previous block results in a hash that has the
        correct number of leading zeroes.
        :return: True if the resulting hash is a valid proof, False otherwise
        """
        guess = f"{block_string}{proof}".encode()
        guess_hash = hashlib.sha256(guess).hexdigest()

        # return True or False
        return guess_hash[:6] == "000000"
    
    def new_transaction(self, sender, recipient, amount):
        """
        Creates a new transaction to go into the next mined Block

        :param sender: <str> Address of the Sender
        :param recipient: <str> Address of the Recipient
        :param amount: <int> Amount
        :return: <int> The index of the BLock that will hold this transaction
        """
        # append the sender, recipient and amount to the current transactions
        self.current_transactions.append({ 'sender': sender, 'recipient': recipient, 'amount': amount })
        # return the last blocks index + 1
        return self.last_block['index'] + 1


# Instantiate our Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()


@app.route('/mine', methods=['POST'])
def mine():
    data = request.get_json()
    if not data or (not 'proof' in data and not 'id' in data):
        return jsonify({'message': "'proof' and 'id' fields are required"}), 400

    block_str = json.dumps(blockchain.last_block, sort_keys=True)
    is_valid = blockchain.valid_proof(block_str, data.get('proof'))

    if is_valid:
        # Forge the new Block by adding it to the chain with the proof
        previous_hash = blockchain.hash(blockchain.last_block)
        block = blockchain.new_block(data.get('proof'), previous_hash)

        # reward the miner for work
        blockchain.new_transaction(sender="0", recipient=node_identifier, amount=1)

        response = {
            'message': "New Block Forged",
            'index': block['index'],
            'transactions': block['transactions'],
            'proof': block['proof'],
            'previous_hash': block['previous_hash'],
        }

        return jsonify(response), 200

    return jsonify({'error': "Invalid proof"}), 400


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'length': len(blockchain.chain),
        'chain': blockchain.chain,
    }
    return jsonify(response), 200


@app.route('/last_block', methods=['GET'])
def get_last_block():
    response = blockchain.last_block
    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    # get the values in json format
    values = request.get_json()
    # check that the required fields exist
    required_fields = ['sender', 'recipient', 'amount']

    if not all(k in values for k in required_fields):
        response = { 'message': 'Error Missing values' }
        return jsonify(response), 400

    # create a new transaction
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    # set the response object with a message that the transaction will be added at the index
    response = { 'message': f'Transaction will be added to Block {index}'}
    # return the response
    return jsonify(response), 201


# Run the program on port 5000
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
