import tornado
import asyncio
import sys
import sqlite3

allowed_origins = ["https://nth233.top", "https://fpg2012.github.io"]

create_table_sql = '''
CREATE TABLE IF NOT EXISTS counting_stars (
    url TEXT,
    ip  TEXT,
    PRIMARY KEY (url, ip)
)
'''
insert_sql = '''
INSERT INTO counting_stars VALUES(:url, :ip)
'''
select_sql = '''
SELECT COUNT(ip) FROM counting_stars WHERE url = :url AND ip = :ip
'''
count_sql = '''
SELECT COUNT(url) FROM counting_stars WHERE url = :url
'''
delete_sql = '''
DELETE FROM counting_stars WHERE url = :url AND ip = :ip
'''

class Database:
    
    def __init__(self, conn=None):
        if conn is None:
            conn = sqlite3.connect('data.db')
            cur = conn.cursor()
            cur.execute(create_table_sql)
        self.conn = conn
    
    def put(self, url: str, ip: str):
        # self.db.add((url, ip))
        cur = self.conn.cursor()
        cur.execute(insert_sql, {'url': url, 'ip': ip})
        self.conn.commit()

    def delete(self, url: str, ip: str):
        cur = self.conn.cursor()
        cur.execute(delete_sql, {'url': url, 'ip': ip})
        self.conn.commit()
    
    def get(self, url: str, ip: str) -> bool:
        cur = self.conn.cursor()
        result = cur.execute(select_sql, {'url': url, 'ip': ip})
        return result.fetchone()[0]

    def get_count(self, url: str) -> int:
        cur = self.conn.cursor()
        result = cur.execute(count_sql, {'url': url})
        return result.fetchone()[0]
    
    def save(self):
        self.conn.close()

db = None

class MyHandler(tornado.web.RequestHandler):

    def check_origin(self):
        origin = self.request.headers.get('Origin')
        if origin in allowed_origins:
            print(origin)
            self.set_header("Access-Control-Allow-Origin", origin)
            self.set_header("Access-Control-Allow-Headers", "x-requested-with")
            self.set_header('Access-Control-Allow-Methods', 'GET, PUT, DELETE, OPTIONS')
            return True
        return False

    def options(self):
        self.check_origin()
        self.set_status(204)
        self.finish()

class StarHandler(MyHandler):

    def get(self):
        if not self.check_origin():
            return
        try:
            url = self.get_argument('url')
            ip_address = self.request.headers.get("X-Real-IP") or self.request.remote_ip
            print((url, ip_address))
            liked = db.get(url, ip_address)
            self.write(str(liked))
            
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            self.set_status(500)

    def put(self):
        if not self.check_origin():
            return    
        try:
            url = self.get_argument('url')
            ip_address = self.request.headers.get("X-Real-IP") or self.request.remote_ip
            db.put(url, ip_address)
            self.set_status(200)
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            self.set_status(500)

    def delete(self):
        if not self.check_origin():
            return
        try:
            url = self.get_argument('url')
            ip_address = self.request.headers.get("X-Real-IP") or self.request.remote_ip
            db.delete(url, ip_address)
            self.set_status(200)
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            self.set_status(500)

class CountHandler(MyHandler):

    def get(self):
        if not self.check_origin():
            return
        try:
            url = self.get_argument('url')
            number = db.get_count(url)
            self.write(str(number))
            self.set_status(200)
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            self.set_status(500)

async def main():
    tornado.options.define("port", default=6039, help="port to listen on")
    tornado.options.parse_command_line()
    app = tornado.web.Application([
        (r'/', StarHandler),
        (r'/cnt', CountHandler),
    ])
    app.listen(tornado.options.options.port)
    
    await asyncio.Event().wait()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        conn = sqlite3.connect(sys.argv[1])
        db = Database(conn=conn)
    else:
        db = Database()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('shutting down gracefully')
    finally:
        db.save()