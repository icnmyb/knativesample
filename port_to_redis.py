# -*- coding: utf-8 -*-

import redis
import datetime
from google.cloud import datastore
from google.oauth2 import service_account
from collections import namedtuple
import json
import traceback
import os
from dotenv import load_dotenv
import logging
from pytz import timezone

def getFromDatastore(now):
    '''
    DataStoreから、直近2時間分のデータ(NG判定結果)を取得するための関数です。

    The purpose of this function is to get result of judging right and wrong.
    '''

    # サービスアカウント認証
    # creds = service_account.Credentials.from_service_account_file('uae-jp-development-1cc550a85cb8.json')
    client = datastore.Client(project=env['GCP_PROJECT'])

    JudgedSite = namedtuple('JudgedSite', ['urlhash', 'url', 'delivery_enable', 'insert_time', 'expire', 'unix'])

    # 該当のkindを取得するためのクエリ発行
    query = client.query(kind=env['DATASTORE_NGWORD_KIND'])

    # 現在時刻から2時間前までに格納されたエンティティを取得
    effectiveTime = now - datetime.timedelta(hours=2)
    query.add_filter('insert_time', '>=', effectiveTime)

    # クエリ実行結果をjudgedSitesに格納
    # urlhash → urlのハッシュ値(string)
    # delivery_enable → 配信可否判定結果(boolean)
    # insert_time → Datastoreに値を格納した日時(datetime)
    # expire → expireする日時(datetime)
    # unix → expireする時間(unixtime)
    judgedSites = [JudgedSite(urlhash=r.key.name,
                              url=r['url'],
                              delivery_enable=r['delivery_enable'],
                              insert_time=r['insert_time'],
                              expire=r['expire'],
                              unix=r['expire_unix'])
                   for r in query.fetch()]

    return judgedSites


def insertToRedis(judgedSites,now):
    '''
    DataStoreから取得した値をredisに格納するための関数です。
    key → 判定結果+URLのハッシュ値
    value → expireされる時間 (APIで配信可否を判定するときに、この時間と現在時刻を比較し配信可否を判定)

    The purpose of this function is to store the value got from the DataStore in the redis.

    ・redisの情報
    　アドレス→10.146.0.57
    　port番号→6379
    　expire→31日
    '''

    # redis接続
    __conn = redis.StrictRedis(host=env['REDIS_HOST_MASTER'], port=env['REDIS_PORT_MASTER'], db=0)

    # expireは31日
    expireTime = 31*24*60*60
    i = 0
    try:
        # パイプライニング
        with __conn.pipeline() as pipe:

            for JudgedSite in judgedSites:

                # delivery_enableの状態によってkeyの名前を設定
                key = 'NGWORD_' + JudgedSite.urlhash
                # valueはjson
                value = {'expire_unix': JudgedSite.unix, 'delivery_enable': JudgedSite.delivery_enable, 'insert_time': JudgedSite.insert_time.strftime('%Y-%m-%d %H:%M:%S')}
                __conn.set(key, json.dumps(value), ex=expireTime)
                i += 1
            key = 'NGWORD_LASTUPDATE'
            value = now
            __conn.set(key, value, ex=expireTime)
            pipe.execute()

    except (redis.exceptions.ConnectionError, redis.exceptions.BusyLoadingError):
        logging.exception("挿入に失敗しました")

    print("redisに", i, "件挿入しました。")

if __name__ == '__main__':
    try:
        dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
        load_dotenv(dotenv_path)
        env = os.environ
        # 現在の日時を取得
        now = datetime.datetime.now(timezone('Asia/Tokyo'))
        print(now,"start")
        judgedSites = getFromDatastore(now)
        print("DataStoreから", len(judgedSites), "件のデータを取得しました")
        insertToRedis(judgedSites,now)
    except:
        logging.exception("正常に終了しませんでした")
