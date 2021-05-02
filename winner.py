import time
import requests
import hashlib

nodes = 'https://cn.steems.top'


def get_winners(min_n, max_n, num_win, block_num):
    data = {"jsonrpc": "2.0", "method": "condenser_api.get_block", "params": [block_num], "id": 1}
    r = requests.post(url=nodes, json=data)
    rjson = r.json()
    transaction_ids = rjson["result"]['transaction_ids']

    hash = ""
    for i in transaction_ids:
        hash += i
    print(hash)

    res = hash
    winners = set()
    while len(winners) < num_win:
        res = hashlib.sha256(res.encode('utf-8')).hexdigest()
        winners.add(int(res, 16) % (max_n-min_n+1) + min_n)
    return winners

#{'season': 1, 'winners': {24, 9, 22, 6}, 'max_lucky_number': 29, 'open_block': 53353400} 第一期开奖信息
open_block=53353400#开奖区块号
min_lucky_number=0#最小奖卷号
max_lucky_number=29#最大奖卷号
winners=get_winners(min_lucky_number,max_lucky_number,4,open_block)
print(winners)
