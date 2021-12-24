import sqlite



class db:
    def __init__(self):
        self.con = sqlite3.connect('./pingchan.db')
        self.con.row_factory = self.dict_factory
        self.cur = self.con.cursor()
        self._initDB()

        def dict_factory(cursor, row):
            d = {}
            for idx, col in enumerate(cursor.description):
                d[col[0]] = row[idx]
                return d

        def _initDB(self):
            # id ,name, privatekey, publickey, date
            self.cur.execute("CREATE TABLE if not exists pingcastle (id INTEGER PRIMARY KEY AUTOINCREMENT, name text,privatekey text,publickey text,date text)")

        def add_keypair(self, name, pub, pri):
            from datetime import date
            date = date.today()
            sql = "INSERT INTO pingcastle VALUES (?,?,?,?,?)"
            args = (None,name,pub,pri,date)
            self.cur.execute(sql,args)
            self.con.commit()
            return True
            
            
