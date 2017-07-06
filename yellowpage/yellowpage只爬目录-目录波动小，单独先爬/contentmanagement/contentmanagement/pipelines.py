# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import sqlite3 as lite


con = None # this is the db connection object. 

class ContentmanagementPipeline(object):
    """ Store item into three tables within Contentmanagement.db

        Three tables are Industry, Category, Classify,respectively
        Industry stands for 35 separate industries-(level 1)
        Category stands for around 1400 separate categories-(level 2)
        Classify stands for around 6000 separate classifications-(level 3) 

    """

    def __init__(self):
        self.setupDBcon()
        self.createTable()

    def process_item(self, item, spider):
        self.storeInDB(item)
        return item

    def storeInDB(self,item):
        # We store industryInfo into corresponding table, then fetch the sequence column
        # standed by 'industryranking' as industryID( because when in multithread cases,
        # the item is not fetched by normal sequence)
        # item['categoryMemeber'] is a list as folllowing structure
        #    [category1, category2, categoy3, ...]
        # catesel['classifyMember'] that also is category['classifyMember'] is a list as folllowing
        #    [classify1, classify2, classify3, ...]

        self.storeIndustryInfoInDb(item)
        industryID = item['industryranking']          # lastrowid is not proper here
        for catesel in item['categoryMember']:       
            self.storeCategoryInfoInDb(catesel,industryID)
            categoryID = catesel['categoryranking']
            for classifysel in catesel['classifyMember']:
                self.storeClassifyInfoInDb(classifysel,industryID,categoryID)

    def setupDBcon(self):
        self.con = lite.connect('Contentmanagement.db')
        self.cur = self.con.cursor()

    def createTable(self):
        """create three level tables"""
        self.createIndustryTable()
        self.createCategoryTable()
        self.createClassifyTable()

    def createIndustryTable(self):
        self.cur.execute('''DROP TABLE IF EXISTS Industry''')
        self.cur.execute('''CREATE TABLE IF NOT EXISTS Industry( id INTEGER PRIMARY KEY NOT NULL,\
            industryName TEXT,\
            industryurl TEXT,\
            industryranking INTEGER,\
            industrytotal INTEGER\
            )''')
        
    def createCategoryTable(self):
        self.cur.execute('''DROP TABLE IF EXISTS Category''')
        self.cur.execute('''CREATE TABLE IF NOT EXISTS Category( id INTEGER PRIMARY KEY NOT NULL,\
            industryID INTEGER NOT NULL,\
            categoryName TEXT,\
            categoryurl TEXT,\
            categoryranking INTEGER,\
            categorytotal INTEGER\
            )''')

    def createClassifyTable(self):
        self.cur.execute('''DROP TABLE IF EXISTS Classify''')
        self.cur.execute('''CREATE TABLE IF NOT EXISTS Classify( id INTEGER PRIMARY KEY NOT NULL,\
            industryID INTEGER NOT NULL,\
            categoryID INTEGER NOT NULL,\
            classifyName TEXT,\
            classifyurl TEXT,\
            classifyranking INTEGER,\
            classifytotal INTEGER\
            )''')

    def storeIndustryInfoInDb(self, item):
        """Store 35 industry information to Industry table( first level) """
        self.cur.execute("INSERT INTO Industry(\
            industryName, \
            industryurl, \
            industryranking,\
            industrytotal\
            ) \
        VALUES( ?, ?, ?,?)", \
        ( \
            item.get('industryName', ''), 
            item.get('industryurl', ''), 
            item.get('industryranking'),
            item.get('industrytotal') 
        ))
        self.con.commit()  

    def storeCategoryInfoInDb(self,item,industryID):
        """Store thousand of Category info to Category table( second level)"""
        self.cur.execute("INSERT INTO Category(\
            industryID,\
            categoryName, \
            categoryurl, \
            categoryranking,\
            categorytotal\
            ) \
        VALUES( ?, ?, ?,?,?)", \
        (\
            industryID,
            item.get('categoryName', ''), 
            item.get('categoryurl', ''), 
            item.get('categoryranking'),
            item.get('categorytotal') 
        ))
        self.con.commit()  

    def storeClassifyInfoInDb(self, item,industryID,categoryID):
        """Store thousand of Classify info to Classify table( third level)"""
        self.cur.execute("INSERT INTO Classify(\
            industryID,\
            categoryID,\
            classifyName, \
            classifyurl, \
            classifyranking,\
            classifytotal\
            ) \
        VALUES( ?, ?, ?,?,?,?)", \
        ( \
            industryID,
            categoryID,
            item.get('classifyName', ''),
            item.get('classifyurl', ''), 
            item.get('classifyranking'),
            item.get('classifytotal')
        ))
        self.con.commit()  

    def __del__(self):
        self.closeDB()

    def closeDB(self):
        self.con.close()