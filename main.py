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


con = sqlite3.connect('tickets.db')
cur = con.cursor()



nodes = 'https://cn.steems.top'
keys='5K5sJ3d5yVnL'
master="nutbox.awesome"


bot_set = dict()
with open('set.json', 'r') as file:
    bot_set = json.loads(file.read())
season = bot_set['season']
open_block = bot_set['open_block']
last_lucky_number = bot_set['last_lucky_number']
block_num=bot_set['start_block']
print("start:",block_num)
print(season,open_block,last_lucky_number)

s = Steem(keys=keys, node=nodes)

#获得赛季中奖者
def get_season_winners(body):
    season=body.replace("!","")
    whois = 'select * from tickets where txid = "%s" ' % season
    cur.execute(whois)
    all = cur.fetchall()
    #print(all)
    if all==[]:
        return "No data"
    else:
        str=all[0][0]+","+all[0][2]+":"+all[0][4]
        return str
#获得用户奖卷信息
def get_player_tickets(player):
    whois = 'select * from tickets where owner = "%s" and type = "buy"' % player
    cur.execute(whois)
    all = cur.fetchall()
    if all == []:
        return []
    else:
        tickets=[]
        for i in all:
            lists=list(map(int,list(i[4].replace('[','').replace(']','').replace(" ","").split(','))))
            tickets += lists
        return sorted(tickets)
#开奖程序
def get_winners(min_n=0, num_win=4):
    master = "nutbox.awesome"
    data = {"jsonrpc": "2.0", "method": "condenser_api.get_account_history", "params": [master, -1, 1000], "id": 1}
    r = requests.post(nodes, json=data)
    rjson = r.json()["result"]
    for i in rjson[::-1]:
        ops = i[1]["op"]
        types = ops[0]
        if types == "transfer":
            from_who = ops[1]["from"]
            memo = ops[1]["memo"]
            # print(from_who,memo)
            if from_who == master and "lucky_number" in memo:
                # print(i)
                # print(ops)
                memo_json = eval(memo)
                max_lucky_number = memo_json["lucky_number"][-1]
                open_block = memo_json["open_block"]
                print(max_lucky_number, open_block)
                break
    #todo 一会测试完删掉这行
    #open_block = 53266004

    for i in range(5):
        data = {"jsonrpc": "2.0", "method": "condenser_api.get_block", "params": [open_block], "id": 1}
        r = requests.post(url=nodes, json=data)
        rjson = r.json()
        transaction_ids = rjson["result"]['transaction_ids']
        if transaction_ids == []:
            open_block += 1
        else:
            break

    hash = ""
    for i in transaction_ids:
        hash += i
    print(hash)

    res = hash
    winners = set()
    while len(winners) < num_win:
        res = hashlib.sha256(res.encode('utf-8')).hexdigest()
        winners.add(int(res, 16) % (max_lucky_number-min_n+1) + min_n)
    return winners

#检查事务是否存在，防重放
def check_txid(transaction_id):
    whois = 'select * from tickets where txid = "%s"' % transaction_id
    cur.execute(whois)
    all = cur.fetchall()
    if all == []:
        return False
    else:
        return True

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
#回复
def posts(s,parent_author,parent_permlink,author,body):
    num = random.sample("abcdefghikstringasciiletteshiusoidsrs0123456789", 8)
    strs = ''
    permlink = strs.join(num)
    op = operations_diy.Comment(
        **{
            "parent_author": parent_author,
            "parent_permlink": parent_permlink,
            "author": author,
            "permlink": permlink,
            "title": "",
            "body": body,
            "json_metadata": '{"app":"steemcn/0.1"}'
        })

    tx = TransactionBuilder(steem_instance=s)
    tx.appendOps(op)
    # 把签名添加并签名
    tx.appendSigner(author, "active")
    tx.sign()
    re = tx.broadcast()
    print(re)
    return re

#todo 区块监控开始

while True:
    try:
        print("Now:", block_num)
        data = {"jsonrpc": "2.0", "method": "condenser_api.get_block", "params": [block_num], "id": 1}
        r = requests.post(url=nodes, json=data)
        rjson = r.json()
        status_check=rjson["result"]
        if status_check == None:
            print("None , wait 3s")
            time.sleep(3)
            continue
        else:
            try:
                transaction_ids_check=status_check["transaction_ids"]
                if transaction_ids_check == []:
                    print("no transaction,wait,3s")
                    time.sleep(3)
                    block_num +=1
                    continue
            except Exception as e:
                print(e)

        result=rjson["result"]["transactions"]


        block_num_now=result[0]["block_num"]
        for i in result:
            operations=i["operations"][0]
            transaction_id=i["transaction_id"]
            if operations[0] == "transfer":
                owner = operations[1]["from"]
                to = operations[1]["to"]
                #print(owner,to,amount,memo)
                if to == master:
                    print("find!")
                    print(operations[1])
                    amount_str = operations[1]["amount"]
                    memo = operations[1]["memo"]
                    amount = float(amount_str.replace("STEEM",""))
                    # check_id
                    check = check_txid(transaction_id)
                    if check == True:
                        print("已有交易,跳过")
                    else:
                        if memo == "buy":
                            print("buy tickets")
                            if open_block - block_num_now <= 100:
                                try:
                                    print("season,Closed,back!")
                                    memos="BACK!,season:"+str(season)+",ststus:Closed"
                                    #re = Account(master, steem_instance=s).transfer(owner, amount, "STEEM",memos)
                                    re = transfer_token(s, master, owner, amount_str, memos)
                                    expiration=re["expiration"]
                                    print(transaction_id,expiration)
                                    print(re)
                                    cur.execute('REPLACE INTO tickets VALUES (?,?,?,?,?,?,?)',(transaction_id, expiration, "back", season, amount_str, owner, open_block))
                                    con.commit()
                                except Exception as e:
                                    print("back_buy,error:", e)
                                    expiration = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                                    cur.execute('REPLACE INTO errors VALUES (?,?,?,?,?,?)', (transaction_id + str(season), expiration, "back_buy", season, owner, str(e)))
                                    con.commit()
                            else:
                                try:
                                    numbers=int(amount)#2
                                    lucky_number = []
                                    for w in range(numbers):
                                        bot_set['last_lucky_number'] += 1
                                        lucky_number.append(bot_set['last_lucky_number'])
                                    tickets = {"season": season,  "lucky_number": lucky_number,"owner": owner,"open_block":open_block}
                                    re = transfer_token(s, master, owner, "0.001 STEEM", str(tickets))
                                    expiration = re["expiration"]
                                    print(transaction_id,expiration)
                                    print(re)
                                    cur.execute('REPLACE INTO tickets VALUES (?,?,?,?,?,?,?)', (transaction_id, expiration, "buy", season, str(lucky_number),owner,open_block))
                                    con.commit()
                                    with open('set.json', 'w', encoding='utf-8') as f1:
                                        f1.write(json.dumps(bot_set, indent=4, ensure_ascii=False))
                                except Exception as e:
                                    print("buy,error:", e)
                                    expiration = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                                    cur.execute('REPLACE INTO errors VALUES (?,?,?,?,?,?)', (transaction_id + str(season), expiration, "buy", season, owner, str(e)))
                                    con.commit()

                        else:
                            try:
                                print("back")
                                re = transfer_token(s, master, owner, amount_str, "No memo,back")
                                expiration = re["expiration"]
                                print(re,expiration)
                                cur.execute('REPLACE INTO tickets VALUES (?,?,?,?,?,?,?)',(transaction_id, expiration, "back", season, amount_str, owner, open_block))
                                con.commit()
                            except Exception as e:
                                print("no_memo_back,error:", e)
                                expiration = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                                cur.execute('REPLACE INTO errors VALUES (?,?,?,?,?,?)',(transaction_id + str(season), expiration, "back_nomemo", season, owner, str(e)))
                                con.commit()



            elif operations[0] == "comment":
                parent_author = operations[1]["parent_author"]
                if parent_author != "":
                    body = operations[1]["body"]
                    if "!tickets" == body:
                        try:
                            # check_id
                            check = check_txid(transaction_id)
                            if check == True:
                                print("已有交易,跳过")
                            else:
                                print(operations[1])
                                print(body)
                                print("回复！")
                                #parent_author=operations[1]["parent_author"]
                                parent_permlink = operations[1]["permlink"]
                                author = operations[1]["author"]
                                my_tickets=get_player_tickets(author)
                                body_new="Your tickets:"+str(my_tickets)
                                re=posts(s, author, parent_permlink, master, body_new)
                                expiration = re["expiration"]
                                cur.execute('REPLACE INTO tickets VALUES (?,?,?,?,?,?,?)',(transaction_id, expiration, "re_post", season, body_new, author, open_block))
                                con.commit()
                                time.sleep(3)
                        except Exception as e:
                            print("re_post,error:", e)
                            expiration = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                            try:
                                cur.execute('REPLACE INTO errors VALUES (?,?,?,?,?,?)',(transaction_id + str(season), expiration, "re_post", season, author, str(e)))
                            except:
                                cur.execute('REPLACE INTO errors VALUES (?,?,?,?,?,?)',(transaction_id + str(season), expiration, "re_post", season, "none", str(e)))
                            con.commit()
                    elif "!season" in body and len(body) < 15:
                        try:
                            # check_id
                            check = check_txid(transaction_id)
                            if check == True:
                                print("已有交易,跳过")
                            else:
                                print(operations[1])
                                print(body)
                                print("奖励查询，回复！")
                                # parent_author=operations[1]["parent_author"]
                                parent_permlink = operations[1]["permlink"]
                                author = operations[1]["author"]
                                my_tickets = get_player_tickets(author)
                                #获取得奖信息
                                body_new = get_season_winners(body)
                                re = posts(s, author, parent_permlink, master, body_new)
                                expiration = re["expiration"]
                                cur.execute('REPLACE INTO tickets VALUES (?,?,?,?,?,?,?)',(transaction_id, expiration, "re_post", season, body_new, author, open_block))
                                con.commit()
                                time.sleep(3)
                        except Exception as e:
                            print("re_post,error:", e)
                            expiration = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                            try:
                                cur.execute('REPLACE INTO errors VALUES (?,?,?,?,?,?)',(transaction_id + str(season), expiration, "re_post", season, author, str(e)))
                            except:
                                cur.execute('REPLACE INTO errors VALUES (?,?,?,?,?,?)',(transaction_id + str(season), expiration, "re_post", season, "none", str(e)))
                            con.commit()


        #print(block_num_now,type(block_num_now))

        #todo 测试完毕删掉这行
        #open_block=53266004

        if block_num_now == open_block:
            print("开奖")
            try:
                bot_set['season'] += 1
                bot_set['open_block'] += 86400
                bot_set['last_lucky_number'] = -1
                with open('set.json', 'w', encoding='utf-8') as f1:
                    f1.write(json.dumps(bot_set, indent=4, ensure_ascii=False))
                winners=get_winners()
                print("获奖者是:",winners)
                expiration = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                cur.execute('REPLACE INTO tickets VALUES (?,?,?,?,?,?,?)',("season"+str(season), expiration, "winners", season, str(winners), "winners", open_block))
                con.commit()
            except Exception as e:
                print("open_reward,error:",e)
                expiration = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                cur.execute('REPLACE INTO errors VALUES (?,?,?,?,?,?)',("open_reward,error" + str(season), expiration, "reward", season, "winners", str(e)))
                con.commit()

        block_num += 1
        bot_set['start_block'] = block_num
        with open('set.json', 'w', encoding='utf-8') as f1:
            f1.write(json.dumps(bot_set, indent=4, ensure_ascii=False))

    except Exception as e:
        print("block,error:", e)
        expiration = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        cur.execute('REPLACE INTO errors VALUES (?,?,?,?,?,?)',(str(block_num) + str(season), expiration, "block_error", season, "unkonw", str(e)))
        con.commit()
        time.sleep(3)




