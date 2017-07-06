# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import sqlite3 as lite
try:
    from HTMLParser import HTMLParser
except:
    from html.parser import HTMLParser
from .dbconnect import connection
from bs4 import BeautifulSoup
import functools
import logging


con = None # this is the db connection object. 

class ContentmanagementPipeline(object):
    """ Store catalog info into three tables within Contentmanagement.db

        Three tables are Industry, Category, Classify,respectively
        Industry stands for 35 separate industries-(level 1)
        Category stands for around 1400 separate categories-(level 2)
        Classify stands for around 6000 separate classifications-(level 3) 

    """

    def __init__(self):
        self.setupDBcon()
        self.createTable()

    def check_spider_pipeline(process_item_method):
        """decorator to check the pipeline attribute of spider, for
         whether or not it should be executed
         """
        @functools.wraps(process_item_method)
        def wrapper(self, item, spider):

            # message template for debugging
            msg = '%%s %s pipeline step' % (self.__class__.__name__,)

            # if class is in the spider's pipeline, then use the
            # process_item method normally.
            if self.__class__ in spider._pipelines:
                logging.info(msg % 'executing')
                return process_item_method(self, item, spider)

            # otherwise, just return the untouched item (skip this step in
            # the pipeline)
            else:
                logging.info(msg % 'skipping')
                return item

        return wrapper

    @check_spider_pipeline
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
        industryID = item['industryranking']          # lastrowid doesn't work here
        for catesel in item['categoryMember']:       
            self.storeCategoryInfoInDb(catesel,industryID)
            categoryID = catesel['categoryranking']
            for classifysel in catesel['classifyMember']:
                self.storeClassifyInfoInDb(classifysel,industryID,categoryID)

    def setupDBcon(self):
        self.con_catalog = lite.connect('Contentmanagement.db')
        self.cur = self.con_catalog.cursor()

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
        self.con_catalog.commit()  

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
        self.con_catalog.commit()  

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
        self.con_catalog.commit() 

    def __del__(self):
        self.closeDB()

    def closeDB(self):
        self.con_catalog.close()



class YellowpagePipeline(object):

    def __init__(self):
        self.setupDBcon()
        self.createTable()

    def process_item(self, item, spider):
        for key, value in item.items():
            # handle list and useless html tag
            if (isinstance(value,list)):
                if value:
                    templist = []
                    for obj in value:
                        temp = self.stripHTML(obj)  # handle useless tag
                        templist.append(temp)
                        templist =[i.strip() for i in templist if i] # get rid of empty list element
                    item[key]= templist
                else:
                    item[key]=""
            else:
                if not isinstance(value,int): 
                    item[key]= self.stripHTML(value)

        self.storeCompanyInDb(item)
        return item

    def setupDBcon(self):  
        """connect bjYellowpages database and setup cursor """
        self.cur, self.con = connection()

    def createTable(self): 
        """create Company table"""
        self.cur.execute('''DROP TABLE IF EXISTS Company''')
        self.cur.execute('''CREATE TABLE IF NOT EXISTS `Company`(id INT NOT NULL AUTO_INCREMENT,
            industryID TEXT,
            categoryID TEXT,
            classfiyID TEXT,
            name TEXT,
            url TEXT,
            legalRepresentative TEXT,
            registedCapital TEXT,
            businessModel TEXT,
            employNum TEXT,
            majorMarket TEXT,
            customerType TEXT,
            industry TEXT,
            productionInfo TEXT,
            industryInfo TEXT,
            districtInfo TEXT,
            relatedLink TEXT,
            companyTag TEXT,
            updateTime TEXT,
            viewNum TEXT,
            description TEXT,
            contactPerson TEXT,
            webSite TEXT,
            postNum TEXT,
            location TEXT,
            phone TEXT,
            fax TEXT,
            PRIMARY KEY (id) 
            )''')
 
    def storeCompanyInDb(self,item):                      
        """ store information to Company table """
        self.cur.execute('''INSERT INTO `Company`(
            `industryID` ,
            `categoryID`,
            `classfiyID` ,
            `name` ,
            `url` ,
            `legalRepresentative` ,
            `registedCapital` ,
            `businessModel` ,
            `employNum` ,
            `majorMarket` ,
            `customerType` ,
            `industry` ,
            `productionInfo` ,
            `industryInfo` ,
            `districtInfo` ,
            `relatedLink` ,
            `companyTag` ,
            `updateTime` ,
            `viewNum` ,
            `description` ,
            `contactPerson` ,
            `webSite` ,
            `postNum` ,
            `location` ,
            `phone` ,
            `fax`     
            )
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''', 
            (
            item.get('industryID'),
            item.get('categoryID'),
            item.get('classifyID'),
            item.get('name',''),
            item.get('url',''),
            item.get('legalRepresentative'),
            item.get('registedCapital'),
            item.get('businessModel'),
            item.get('employNum'),
            item.get('majorMarket'),
            item.get('customerType'),
            item.get('industry'),
            item.get('productionInfo'),
            item.get('industryInfo'),
            item.get('districtInfo'),
            item.get('relatedLink'),
            item.get('companyTag'),
            item.get('updateTime'),
            item.get('viewNum'),
            item.get('description'),
            item.get('contactPerson'),
            item.get('webSite'),
            item.get('postNum'),
            item.get('location'),
            item.get('phone'),
            item.get('fax')
            ))
        self.con.commit()

    def strip_tag(self,html):
        """strip off the useless html tag such as <br>..."""
        s = MLStripper()
        s.feed(html)
        return s.get_data()  

    def stripHTML(self,string):
        soup = BeautifulSoup(string,"lxml")
        return soup.get_text()


    def __del__(self):
        self.closeDB()

    def closeDB(self):
        self.con.close()


class MLStripper(HTMLParser):        
    """strip off the useless html tag such as <br>..."""
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []
    def handle_data(self,d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

