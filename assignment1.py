import os
import json
import hashlib
import time

# Constants
COINBASE_TX = {
    "txid": "coinbase",
    "vout": [{
        "scriptpubkey": "51202219ab3fa8a1d392f883d388d504e62e450e1f442fd1e61558b008fbf36f01a2",
        "value": 50  # Reward
    }]
}
DIFFICULTY_TARGET = "0000ffff00000000000000000000000000000000000000000000000000000000"
PREV_BLOCK_HASH = "0000111100000000000000000000000000000000000000000000000000000000"
VERSION = 1

def load_transactions(mempool_folder):
    transactions = []
    for filename in os.listdir(mempool_folder):
        if filename.endswith('.json'):
            filepath = os.path.join(mempool_folder, filename)
            with open(filepath, 'r') as file:
                tx = json.load(file)
                transactions.append(tx)
    return transactions

def validate_transaction(tx):
    for vin in tx['vin']:
        if 'prevout' not in vin or 'value' not in vin['prevout'] or 'vout' not in tx:
            return False
        prev_value = vin['prevout']['value']
        total_vout_value = sum(vout['value'] for vout in tx['vout'])
        if prev_value <= total_vout_value:
            return False
        if not vin['txid']:
            return False
    return True

def calculate_merkle_root(txids):
    if not txids:
        return ''
    while len(txids) > 1:
        if len(txids) % 2 != 0:
            txids.append(txids[-1])
        new_txids = []
        for i in range(0, len(txids), 2):
            combined = txids[i] + txids[i+1]
            new_txid = hashlib.sha256(hashlib.sha256(combined.encode('utf-8')).digest()).hexdigest()
            new_txids.append(new_txid)
        txids = new_txids
    return txids[0]

def mine_block(block_header):
    nonce = 0
    while True:
        header_str = f"{block_header['version']}{block_header['prev_block_hash']}{block_header['merkle_root']}{block_header['timestamp']}{block_header['difficulty_target']}{nonce}"
        block_hash = hashlib.sha256(hashlib.sha256(header_str.encode('utf-8')).digest()).hexdigest()
        if block_hash < DIFFICULTY_TARGET:
            block_header['nonce'] = nonce
            block_header['block_hash'] = block_hash
            return block_header
        nonce += 1

def create_block(mempool_folder):
    transactions = load_transactions(mempool_folder)
    valid_transactions = [tx for tx in transactions if validate_transaction(tx)]
    
    # Prepare the coinbase transaction and transaction ids
    valid_transactions.insert(0, COINBASE_TX)
    txids = []
    for tx in valid_transactions:
        if 'txid' in tx:
            txids.append(tx['txid'])
        else:
            txids.append('coinbase')
    
    # Calculate merkle root
    merkle_root = calculate_merkle_root(txids)
    
    # Create block header
    block_header = {
        "version": VERSION,
        "prev_block_hash": PREV_BLOCK_HASH,
        "merkle_root": merkle_root,
        "timestamp": int(time.time()),
        "difficulty_target": DIFFICULTY_TARGET,
        "nonce": 0
    }
    
    # Mine the block
    mined_block = mine_block(block_header)
    
    # Write output to file
    with open('output.txt', 'w') as f:
        f.write(json.dumps(mined_block) + '\n')
        f.write(json.dumps(COINBASE_TX) + '\n')
        for txid in txids:
            f.write(txid + '\n')

if __name__ == "__main__":
    mempool_folder = 'mempool'
    create_block(mempool_folder)
