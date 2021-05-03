# -*- coding:utf-8 -*-
from beem.steem import Steem
from beem.account import Account
from beembase import operations as operations_diy
from beem.transactionbuilder import TransactionBuilder
from beembase.signedtransactions import Signed_Transaction
import hashlib
import time
from binascii import hexlify
import copy
import json
import requests
import random
import sqlite3
import re


con = sqlite3.connect('tickets.db')
cur = con.cursor()



nodes = 'https://cn.steems.top'
keys='5K5VnL'
master="nutbox.awesome"


open_season=1


s = Steem(keys=keys, node=nodes)

#转账
def transfer_token(s,master,to,amount,memo):
    transfers = {
        'from': master,
        'to': to,
        'amount': amount,
        'memo': memo
    }

    op = operations_diy.Transfer(**transfers)
    tx = TransactionBuilder(steem_instance=s)
    tx.appendOps(op)
    # 把签名添加
    tx.appendSigner(master, "active")
    tx.sign()
    re = tx.broadcast()
    return re



#开奖程序
master = "nutbox.awesome"
data = {"jsonrpc": "2.0", "method": "condenser_api.get_account_history", "params": ["season.all", -1, 1000], "id": 1}
r = requests.post(nodes, json=data)
rjson = r.json()["result"]
for i in rjson[::-1]:
    ops = i[1]["op"]
    types = ops[0]
    if types == "transfer":
        from_who = ops[1]["from"]
        memo = ops[1]["memo"]
        # print(from_who,memo)
        if from_who == master and ("'season': "+str(open_season)) in memo:
            #print(i)
            #print(memo)
            # print(ops)
            memo_json = eval(memo)
            season = memo_json["season"]
            winners = memo_json["winners"]
            max_lucky_number = memo_json["max_lucky_number"]
            open_block = memo_json["open_block"]
            #print(season,winners,max_lucky_number, open_block)
            break


#计算奖金:
first_prize=(max_lucky_number+1)*0.5
first_prize=('%.3f' % first_prize)
second_award=(max_lucky_number+1)*0.2
second_award=('%.3f' % second_award)
third_award=(max_lucky_number+1)*0.05
third_award=('%.3f' % third_award)
print(first_prize)
winners=list(winners)
print("获奖号码：",winners)

Foundation=(max_lucky_number+1)*0.1
Foundation=('%.3f' % Foundation)



data = {"jsonrpc": "2.0", "method": "condenser_api.get_account_history", "params": [master, -1, 1000], "id": 1}
r = requests.post(nodes, json=data)


rjson = r.json()["result"]
#一等奖
for i in rjson[::-1]:
    ops = i[1]["op"]
    types = ops[0]
    if types == "transfer":
        #print(ops)
        from_who = ops[1]["from"]
        to_who = ops[1]["to"]
        memo = ops[1]["memo"]
        if from_who == master and to_who != "season.all":
            try:
                memo_json = eval(memo)
                #print(memo_json)
                season_owner = memo_json["season"]
                owner = memo_json["owner"]
                lucky_number = memo_json["lucky_number"]
                #print(open_season, owner, lucky_number)
                if winners[0] in lucky_number and season_owner == open_season:
                    print("一等奖：",owner,lucky_number)
                    first_prize_winner=owner
                    break
            except Exception as e:
                #print(e)
                pass

#二等奖
for i in rjson[::-1]:
    ops = i[1]["op"]
    types = ops[0]
    if types == "transfer":
        #print(ops)
        from_who = ops[1]["from"]
        to_who = ops[1]["to"]
        memo = ops[1]["memo"]
        if from_who == master and to_who != "season.all":
            try:
                memo_json = eval(memo)
                #print(memo_json)
                season_owner = memo_json["season"]
                owner = memo_json["owner"]
                lucky_number = memo_json["lucky_number"]
                #print(open_season, owner, lucky_number)
                if winners[1] in lucky_number and season_owner == open_season:
                    print("二等奖：",owner,lucky_number)
                    second_award_winner=owner
                    break
            except Exception as e:
                #print(e)
                pass

#三等奖
open_numbers=2
third_award_winner=[]
for i in rjson[::-1]:
    ops = i[1]["op"]
    types = ops[0]
    if types == "transfer":
        #print(ops)
        from_who = ops[1]["from"]
        to_who = ops[1]["to"]
        memo = ops[1]["memo"]
        if from_who == master and to_who != "season.all":
            if open_numbers >= 4:
                break
            try:
                memo_json = eval(memo)
                #print(memo_json)
                season_owner = memo_json["season"]
                owner = memo_json["owner"]
                lucky_number = memo_json["lucky_number"]
                #print(open_season, owner, lucky_number)
                if winners[open_numbers] in lucky_number and season_owner == open_season:
                    print("三等奖：",owner,lucky_number)
                    third_award_winner.append(owner)
                    open_numbers+=1
            except Exception as e:
                #print(e)
                pass
print("-------------------")
print("赛季：",open_season,"开奖区块:",open_block)
print("一等奖：",first_prize,first_prize_winner)
print("二等奖：",second_award,second_award_winner)
print("三等奖：",third_award,third_award_winner)

go=input("发送奖励？y/n")
if go == "y":
    memo={"season":open_season,"first_prize":first_prize_winner,"lucky_number":winners[0],"open_block":open_block}
    re=transfer_token(s,master,first_prize_winner,str(first_prize)+" STEEM",str(memo))
    print(re)

    memo={"season":open_season,"second_award":second_award_winner,"lucky_number":winners[1],"open_block":open_block}
    re=transfer_token(s,master,second_award_winner,str(second_award)+" STEEM",str(memo))
    print(re)

    memo={"season":open_season,"third_award":third_award_winner[0],"lucky_number":winners[2],"open_block":open_block}
    re=transfer_token(s,master,third_award_winner[0],str(third_award)+" STEEM",str(memo))
    print(re)

    memo={"season":open_season,"third_award":third_award_winner[1],"lucky_number":winners[3],"open_block":open_block}
    re=transfer_token(s,master,third_award_winner[1],str(third_award)+" STEEM",str(memo))
    print(re)


    memo={"season":open_season,"Foundation":str(Foundation)+" STEEM","open_block":open_block}
    re=transfer_token(s,master,"season.all",str(Foundation)+" STEEM",str(memo))
    print(re)
