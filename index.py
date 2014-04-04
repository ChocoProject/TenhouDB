#!/usr/bin/env python
#coding=utf-8

import os
import math
import web
import json
import tenhouDB
import tenhouLog

import page_API


class GetIcon:
    def GET(self):
        return web.seeother("/static/favicon.ico")

class tenhouCreateLog:
    def GET(self):
        ref = web.input().get('ref', None)
        if not ref:
            return render.base( render.tenhouCreateLog(None) )
        try:
            res = tenhouDB.ref_regex.findall(ref)
            if res:
                if ref != res[0]:
                    web.seeother("../tenhouCreateLog?ref=%s" % res[0])
                tenhouDB.addLog(res[0])
                return render.base( render.tenhouCreateLog(render.logChart(ref)) )
            else:
                return render.base( render.tenhouCreateLog(u"无法识别的地址: %s" % ref) )
        except Exception, e:
            return render.base( render.tenhouCreateLog("Error: %s" % e) )

class tenhouCreateMutiLogs:
    def GET(self):
        return render.base( render.tenhouCreateMutiLogs() )

class teamworkStatistics:
    def GET(self):
        return render.base( render.teamworkStatistics() )

class lastLogs:
    def GET(self):
        refs = tenhouDB.get_lastRefs()
        return render.base( render.logList([tenhouDB.get_Json(ref) for ref in refs]) )

class playerLogs:
    def GET(self):
        name = web.input().get('name', "NoName")
        lobby = web.input().get('lobby', None)
        limit = web.input().get('limit', 100)
        limit = min(100, abs(limit))
        refs  = tenhouDB.get_refs(name = name, lobby = lobby, limit = 100)
        jsons = [tenhouDB.get_Json(ref) for ref in refs]
        return render.base( render.logList(jsons) )

class main_page:
    def GET(self):
        name = web.input().get('name', "")
        lobby = web.input().get('lobby', None)
        limit = web.input().get('limit', 100)
        limit = min(500, abs(limit))
        if name:
            refs = tenhouDB.get_refs(name = name, lobby = lobby, limit = 100)
        else:
            refs = tenhouDB.get_lastRefs()
        return render.base( render.main_page( render.logList([tenhouDB.get_Json(ref) for ref in refs]) ) )

class statistics:
    def GET(self):
        dic = web.input()
        dic["name"] = dic.get("name", "")
        dic["limit"] = dic.get("limit", "")
        dic["lobby"] = dic.get("lobby", "")
        dic["before"] = dic.get("before", "")
        dic["after"] = dic.get("after", "")
        return render.base( render.statistics(dic) )

class websiteLogs:
    def GET(self):
        lines = ["<h2>Website logs</h2>"]
        if os.path.exists("nohup.out"):
            with open("nohup.out", "r") as fl:
                for li in fl:
                    lines.append("<p>%s</p>" % li)
        else:
            lines.append("<p>error: log file is not found.</p>")
        return render.base( "<br>".join(lines) )

t_globals = {
    'datestr': web.datestr, 
}
render = web.template.render('templates', globals = t_globals)

urls  = ("/?", "main_page",
         "/main_page", "main_page",
         "/favicon.ico", "GetIcon",
         "/tenhouCreateLog/?", "tenhouCreateLog",
         "/lastLogs/?", "lastLogs", 
         "/playerLogs/?", "playerLogs",
         "/API/?", "API",
         "/tenhouCreateMutiLogs/?", "tenhouCreateMutiLogs",
         "/teamworkStatistics/?", "teamworkStatistics",
         "/statistics/?", "statistics",
         "/websiteLogs", "websiteLogs")
pages = {"main_page": main_page,
         "GetIcon": GetIcon,
         "tenhouCreateLog": tenhouCreateLog,
         "lastLogs": lastLogs, 
         "playerLogs": playerLogs,
         "API": page_API.page_API,
         "tenhouCreateMutiLogs": tenhouCreateMutiLogs,
         "teamworkStatistics": teamworkStatistics,
         "statistics": statistics,
         "websiteLogs": websiteLogs}
app   = web.application(urls, pages)



if __name__ == "__main__":
    app.run()