#!/usr/bin/env python
#coding=utf-8

import datetime
import sqlite3
import requests
import json
import re
import os

database = sqlite3.connect("tenhou.db", check_same_thread = False)
cursor = database.cursor()

ref_regex = re.compile(r"(\d{10}gm-\w{4}-\d{4,5}-\w{8})")

#init database


with open("init.sql", "r") as sqlFile:
    init_Sql = sqlFile.read().split(";")
for cmd in init_Sql:
    cursor.execute(cmd.strip())
database.commit()

ruleDic = {
    u"0007": u"般东",
    u"000f": u"般南",
    u"0003": u"般东喰",
    u"0001": u"般南喰",
    u"0007": u"般东喰赤",
    u"0009": u"般南喰赤",
    u"0041": u"般东喰赤速",
    u"0049": u"般南喰赤速",
    u"00c1": u"上东喰赤速",
    u"0089": u"上南喰赤",
    u"0061": u"特东喰赤速",
    u"0029": u"特南喰赤",
    u"00e1": u"凤东喰赤速",
    u"00a9": u"凤南喰赤",
}
errorCode = u"未知模式"
def get_info_from_ref(ref):
    date = datetime.datetime.strptime(ref[0:10], "%Y%m%d%H")
    ruleCode = ref[13:17]
    ruleStr = ruleDic.get(ruleCode, errorCode)
    lobby = ref[18:22]
    return dict(date     = date, 
                ruleCode = ruleCode, 
                ruleStr  = ruleStr, 
                lobby    = lobby)

def downloadLog(url):
    ref = ref_regex.findall(url)
    if not ref:
        raise Exception("Unexpected URL: %s" % url)
    reqUrl = r"http://tenhou.net/5/mjlog2json.cgi?" + ref[0]
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "zh-CN,zh;q=0.8",
        "Connection": "keep-alive",
        "Pragma": "no-cache", 
        "Cache-Control": "no-cache", 
        "If-Modified-Since": "Thu, 01 Jun 1970 00:00:00 GMT", 
        "Host": "tenhou.net", 
        "Referer": reqUrl, 
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36", 
    }
    req = requests.get(reqUrl, headers = headers)
    if req.status_code != 200:
        raise Exception("Can not connect with %s" % url)
    if req.text.strip() == "INVALID PATH":
        raise Exception("Return Unexpected text: %s" % req.text.strip())
    obj = req.json()
    while(not obj["name"][-1]):
        obj["name"].pop()
    if len(obj["name"]) != 4:
        raise Exception("Not 4 Player Game, skipped.")
    return obj, req.text

def addLog(ref):
    temp = cursor.execute(r'select ref from logs where ref = ?',(ref,)).fetchall()
    if not temp:
        obj, text = downloadLog(r"http://tenhou.net/0/mjlog2json.cgi?" + ref)
        info = get_info_from_ref(ref)
        cursor.execute(r"insert into logs (ref, json, gameat, rulecode, lobby, createat) values (?, ?, ?, ?, ?, ?)", 
                       (obj["ref"], text, info["date"], info["ruleCode"], info["lobby"], datetime.datetime.now()))
        for name in obj["name"]:
            cursor.execute(r"insert into logs_name (ref, name) values (?, ?)", 
                           (obj["ref"], name))
            cursor.execute(r"delete from statistics_cache where name = ?", (name, ))
        database.commit()
        return get_Json(obj["ref"])
    else:
        return get_Json(temp[0][0])

def addLogs(refString):
    refs = ref_regex.findall(refString)
    if refs:
        for ref in refs:
            try:
                yield (True, addLog(ref))
            except Exception, e:
                yield (False, e)
    return

def get_refs(name, after = None, before = None, lobby = None, ruleCode = None, limit = 10):
    sqlparam = [name]
    queryParam = ["name = ?"]
    if not after is None:
        sqlparam.append(after)
        queryParam.append("gameat > ?")
    if not before is None:
        sqlparam.append(before)
        queryParam.append("gameat < ?")
    if (not lobby is None) and lobby:
        sqlparam.append(lobby)
        queryParam.append("lobby = ?")
    if not ruleCode is None:
        sqlparam.append(ruleCode)
        queryParam.append("rulecode = ?")
    sqlparam.append(limit)
    sqlcmd   = """
    select logs.ref 
    from logs inner join logs_name 
        on logs.ref = logs_name.ref 
    where %s
    order by logs.createat desc
    limit ?;
    """ % " and ".join(queryParam)

    resLst = list()
    for row in cursor.execute(sqlcmd, sqlparam).fetchall():
        resLst.append(row[0])
    return resLst

def get_lastRefs(limit = 10):
    resLst = list()
    resSet = set()
    for row in cursor.execute(r"Select distinct ref from logs order by createat desc limit ?", (limit, )).fetchall():
        if not row[0] in resSet:
            resLst.append(row[0])
            resSet.add(row[0])
    return resLst

def get_Json(ref):
    temp = cursor.execute(r"Select json From logs where ref = ? limit 1", (ref, )).fetchall()
    if temp:
        js = json.loads(temp[0][0])
        info = get_info_from_ref(ref)
        js["date"] = info["date"]
        js["ruleCode"] = info["ruleCode"]
        js["ruleStr"] = info["ruleStr"]
        js["playerSum"] = len(js["name"])
        js["scs"] = js["sc"][::2]
        js["scp"] = js["sc"][1::2]
        return js
    else:
        return None

def get_Jsons(refs):
    resLst = list()
    for ref in refs:
        resLst.append(get_Json(ref))
    return resLst

def get_OriText(ref):
    temp = cursor.execute(r"Select json From logs where ref = ? limit 1", (ref, )).fetchall()
    if temp:
        return temp[0][0]
    else:
        addLog(ref)
        return get_OriText(ref)

def get_statistics_cache(hashs):
    temp = cursor.execute(r"select json from statistics_cache where hash = ? limit 1", (hashs, )).fetchall()
    if temp:
        return temp[0][0]
    else:
        return None

def set_statistics_cache(name, hashs, json):
    cursor.execute(r"insert into statistics_cache(name, hash, json) values (?, ?, ?)", (name, hashs, json))
    database.commit()

def get_hotIDs(limit = 50, morethan = 30):
    return cursor.execute("""
        select Name,CNT from (
            select distinct logs_name.name as Name, COUNT(*) as CNT 
            from logs_name join logs 
                on logs_name.ref = logs.ref
            group by logs_name.name
            order by CNT desc
        ) where CNT >= ? and not(name='NoName')
        order by CNT desc
        limit ?""", (morethan, limit, )).fetchall()
        
if __name__ == "__main__":
    for js in get_Jsons(get_refs(name = "Rnd495")):
        print js["ref"], (" vs ".join(js["name"])).encode("utf-8")