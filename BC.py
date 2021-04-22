"""
Ellie Dove (edove1@umbc.edu)
3/21/2021

Basic, single-file blockchain implementation.
Based on hackernoon/dvf's Flask implementation

By using hashes of each prev block, we can give each block immunity to attack
(if one block is ruined - any future hashes will be too)

Current POW Algorithm: Very basic - 4th root of len(chain)

NOT FOR SECURE USE! Only a toy example used to memorize principles of the DS.
Designed for python3.
"""
import hashlib
import json
from textwrap import dedent
from time import time
from uuid import uuid4
from flask import Flask, jsonify, request

STARTING_ZEROS = 3
FIRST_PROOF = 100
ZERO_CHAR = '0'

"""
BLOCK FORMAT (dict)
block = {
    'index' = (int)
    'timestamp' = (float) #current system time
    'transactions':[
        {
            'sender': (str) <sender address>,
            'recipient': (str) <recip. address>,
            'amount': (int) amount of fake currency
        }
    ],
    'proof': (int) hashed proof of work/stake
    'prev_hash': (str) <hash of PREVIOUS BLOCK>
}
"""


class Chain(object):
    def __init__(self):
        """
        Init for actual Chain, stores transactions
        """
        self.chain = [] # List used to store entire chain of block objects
        self.curr_transactions = [] # List to store moving transactions
        self.create_block(prev_hash=1, proof=FIRST_PROOF) # Genesis

    def create_block(self, proof, prev_hash = None):
        """
        Creates new block (see block format above) to store in chain
        :param self:
        :param proof: int - proof from POW function
        :param: prev_hash: str - hash of prev block, won't exist for genesis
        :return: dict - Block object just added
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(), # Just use system time
            'transactions': self.curr_transactions,
            'proof': proof,
            'prev_hash': prev_hash or self.hash(self.chain[-1]), # Both must match
        }

        # Clear queue of transactions
        self.curr_transactions = []

        # Add block and return
        self.chain.append(block)
        return block

    def create_trans(self, sender, recip, amount):
        """
        Adds transaction to curr_transactions
        :param self:
        :param sender: str - ADDRESS of sender
        :param recip: str - ADDRESS of recipient
        :param amount: int - amount of Fake CurrencyTM
        """
        self.curr_transactions.append({
            'sender': sender,
            'recipient': recip,
            'amount': amount,
        })

        # return the index of the *next* block
        return self.prev_block['index'] + 1

    @staticmethod
    def hash(block):
        """
        Hash function - actually hashes the block itself using SHA256
        :param block: dict - block object
        :return: str - hashed block
        """
        # Simply ordering the dictionary before we hash it, to ensure consistency
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest() # sha256 should be good enough here

    @property
    def prev_block(self):
        """
        PROPERTY
        Fetches last block in the Chain obj
        """
        return self.chain[-1]

    def prove_work(self, last_proof):
        """
        Real magic - simple POW algorithm

        "Find p' S.T. hash(pp') has 3 leading zeros"
        p' = new proof
        p = prev proof
        :param last_proof: int - last "answer" proof
        :return: int - new proof
        """
        proof = 0
        valid = False
        # Brute-force until we find the correct hash to get 0 leading 0s
        # Future advancement is alterring this to increment on len(chain)
        while not valid:
            curr_guess = f'{last_proof, proof}'.encode()
            guess_hash = hashlib.sha256(curr_guess).hexdigest() # hash pp' and store
            zero_info = self.get_zero_amount()
            if (guess_hash[:zero_info[0]] == zero_info[1]): # Check for leading 0s
                return proof
            proof += 1

    def get_zero_amount(self):
        """
        Determines how many leading 0s are needed to prove
        :return: list - [int, str of 0s]
        """
        rt_len = len(self.chain) ** (1/4) # Take 4th root
        int_needed = int(rt_len) + STARTING_ZEROS # Round off to be sure
        zeros = ZERO_CHAR * int_needed


        return [int_needed, zeros]




"""
Regular functions begin here
Flask implementation magic:
"""
# Start flask
app = Flask(__name__)

# Make unique address for flask node
node_iden = str(uuid4()).replace('-', '')

# Initialize chain
blockchain = Chain()

@app.route('/mine', methods=['GET'])
def mine():
    """
    Basic path to follow for miners
    """

    last_block = blockchain.prev_block
    last_proof = last_block['proof']
    proof = blockchain.prove_work(last_proof)

    blockchain.create_trans(
        sender="0",
        recip=node_iden,
        amount=1,
    )

    # Create new block based on previous hash
    previous_hash = blockchain.hash(last_block)
    block = blockchain.create_block(proof, previous_hash)

    # Response to send back
    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'prev_hash': block['prev_hash'],
    }
    return jsonify(response), 200

@app.route('/transactions/new_trans', methods=['POST'])
def create_trans():
    """
    Forges transaction based on values dict
    """
    values = request.get_json()

    required = ['sender', 'recipient', 'amount']
    if not all(each in values for each in required):
        return "Missing values", 400

    # Create a new Transaction
    index = blockchain.create_trans(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port = 5000)








