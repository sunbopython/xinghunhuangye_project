#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  jerryAn
Time    2016.05.04

"""

import logging
from scrapy.http import Request, HtmlResponse
from scrapy import Spider
from scrapy.spiders import CrawlSpider, Rule
from yellowpage.items import YellowpageItem, IndustryItem, CategoryItem, ClassifyItem
import sqlite3 as lite
import yellowpage.pipelines as pipelines
from scrapy.linkextractors import LinkExtractor
from scrapy.utils.spider import iterate_spider_output

c = None  # connect to the classfication database which has been crawled in advance 

#import sys
#reload(sys)
#sys.setdefaultencoding('utf-8')

class catalogSpider(Spider):
    """Crawl catalog information 
    """
    name = "catalog"
    #allowed_domains =["qincai.net"]
    start_urls =["http://www.qincai.net/iohohoioh/index.html"]
    _pipelines = set([
                    pipelines.ContentmanagementPipeline,
                    ])


    def parse(self,response):
        """get the 35 industry (first-level) related information
        """
        sels = response.xpath("//div[@class='rightbox']/div/ul/li[span]")
        for index, industrySel in enumerate(sels):     
            # We ignore the first line because of invald item
            if index <= 0:
                continue
            item = IndustryItem()
            item['industryName'] = industrySel.xpath("a/text()").extract()[0]
            item['industryranking'] = index
            item["industryurl"] = industrySel.xpath("a/@href").extract()[0]
            item["industrytotal"] = industrySel.xpath("span/text()").extract()[0]

            yield Request(item['industryurl'],callback=self.parseCategory,meta={'item':item})
            

    def parseCategory(self,response):
        """parse category (second-level) related information 
        """
        item = response.meta['item']
        item['categoryMember']=[]
        sels = response.xpath("//div[@class='rightbox']/div/ul/li[span]")
        categoryMax = len(sels)-1
        for index, categorysels in enumerate(sels):
            # We ignore the first line because of invald item
            if (index ==0):
                continue
            categoryItem = CategoryItem()
            categoryItem['categoryName'] = categorysels.xpath("a/text()").extract()[0].decode("utf-8", 'ignore')
            categoryItem['categoryranking'] = index
            categoryItem['categoryurl'] = categorysels.xpath('a/@href').extract()[0]
            categoryItem['categorytotal'] = categorysels.xpath('span/text()').extract()[0]
            
            yield Request(categoryItem['categoryurl'],callback=self.parseClassify,meta={'item':item,'categoryItem':categoryItem,'categoryMax':categoryMax})
        

    def parseClassify(self,response):
        """parse classication (third-level) related information"""
        item = response.meta['item']    #shadow copy
        categoryItem = response.meta['categoryItem']  #shadow copy
        categoryMax = response.meta['categoryMax']   #shadow copy
        categoryItem["classifyMember"] =[]
        sels = response.xpath("//div[@class='rightbox']/div/ul/li[span]")
        for index, classifysels in enumerate(sels):
            # We ignore the first line because of invald item
            if index ==0:
                continue
            classifyItem = ClassifyItem()
            classifyItem['classifyName'] = classifysels.xpath('a/text()').extract()[0].decode("utf-8", 'ignore')
            classifyItem['classifyranking']= index
            classifyItem['classifyurl'] = classifysels.xpath('a/@href').extract()[0]
            classifyItem['classifytotal'] = classifysels.xpath('span/text()').extract()[0]
            categoryItem["classifyMember"].append(classifyItem)

        item['categoryMember'].append(categoryItem)
        # logging.info(len(item['categoryMember']))
        if len(item['categoryMember'])==categoryMax:        
            logging.info(item)
            return item


class yellowpageSpider(CrawlSpider):
    """ Crawl company related information from specified website

        Prerequisites: A classifition database which has the website's whole category
    """
    name = "yellowpage"
    # website_possible_httpstatus_list = [400, 403, 404, 408, 500, 502, 503, 504]  #[500, 502, 503, 504]
    _pipelines = set([
                    pipelines.YellowpagePipeline
                    ])

    rules=(
        Rule(LinkExtractor(restrict_xpaths=('//div[@class="pagelist"]',)),
            callback='parse_index_response',
            follow=True),
        )


    def __init__(self):
        self._compile_rules()
        self.setupDBcon()

    def setupDBcon(self):                   
        """Connect to the classification database which we have already established"""
        self.c = lite.connect('all_classification.db')
        self.curs = self.c.cursor()

    def start_requests(self):               
        """Make request from every generated url"""
        for row in self.generateRow():
            yield Request(row[4], meta={'row': row})

    def generateRow(self):
        """Generate every url from table named Classify which comes from another database"""
        for id in range(35):
            for row in self.curs.execute('''SELECT * FROM Classify  WHERE industryID = {} ORDER BY 
                                        industryID,CategoryID,classifyranking '''.format(id+1)):
                yield row

    def parse_start_url(self,response):
        return self.parse_index_response(response)

    def _requests_to_follow(self, response):
        row = response.meta['row']
        if not isinstance(response, HtmlResponse):
            return
        seen = set()
        for n, rule in enumerate(self._rules):
            links = [l for l in rule.link_extractor.extract_links(response) if l not in seen]
            if links and rule.process_links:
                links = rule.process_links(links)
            for link in links:
                seen.add(link)
                r = Request(url=link.url, callback=self._response_downloaded, meta={'row': row})
                r.meta.update(rule=n, link_text=link.text)
                yield rule.process_request(r)

    def _response_downloaded(self, response):
        rule = self._rules[response.meta['rule']]
        return self._parse_response(response, rule.callback, rule.cb_kwargs, rule.follow)

    def _parse_response(self, response, callback, cb_kwargs, follow=True):
        if callback:
            cb_res = callback(response, **cb_kwargs) or ()
            cb_res = self.process_results(response, cb_res)
            for requests_or_item in iterate_spider_output(cb_res):
                yield requests_or_item

        if follow and self._follow_links:
            for request_or_item in self._requests_to_follow(response):
                yield request_or_item

    def parse_index_response(self, response):
        """ Make forward request for the url that is restricted to pagelist and 
            crawl some important information shown on index page 
        """
        row = response.meta['row']  
        for sel in response.xpath("//div[contains(@class,'itemlist')]/h2"):
            item = YellowpageItem()
            item['industryID'] = row[1]
            item['categoryID'] = row[2]
            item['classifyID'] = row[5]
            item['name'] = sel.xpath("a/text()").extract()[0]
            item['url'] = sel.xpath("a/@href").extract()[0]

            request = Request(item['url'], callback=self.companyParse)
            request.meta['item'] = item
            yield request

    def companyParse(self, response):    
        """ parse other company information from its' url"""

        item = response.meta['item']
        generalSels = response.xpath(
                    "//div[@class='content']/div[@class='general']/div/span[2]")   
        item['legalRepresentative'] = generalSels.extract()[0]
        item['registedCapital'] = generalSels.extract()[1]
        item['businessModel'] = generalSels.extract()[2]
        item['employNum'] = generalSels.extract()[3]
        item['majorMarket'] = generalSels.extract()[4]
        item['customerType'] = generalSels.extract()[5]
        item['industry'] = generalSels.extract()[6]
        item['productionInfo'] = generalSels.extract()[7]
        item['industryInfo'] = generalSels.extract()[8]
        item['districtInfo'] = generalSels.extract()[9]
        item['relatedLink'] = generalSels.extract()[10]
        item['companyTag'] = generalSels.extract()[11]
        item['updateTime'] = generalSels.extract()[12]
        item['viewNum'] = generalSels.extract()[13]

        # Description information box, this box may have null value 
        item['description'] = self.ifNotEmptyGetIndex(response.xpath(
                            "//div[@class='introduction']/div[@class='intro-item']").extract())     
        contactSels = response.xpath(
                            "//div[@class='contact']/div[@class='contact-item']/span[2]")             # contact information box
        item['contactPerson'] = contactSels.extract()[0]
        item['webSite'] = contactSels.extract()[1]
        item['postNum'] = contactSels.extract()[2]
        item['location'] = contactSels.extract()[3]
        item['phone'] = contactSels.extract()[4]
        item['fax'] = contactSels.extract()[5]

        return item

    def ifNotEmptyGetIndex(self, item, index=0):
        """Test if the item box is empty or not"""
        if item:  
            return item[index]
        else:
            return item

    def __del__(self):                                 
        self.closeDB()

    def closeDB(self):                 
        self.c.close()
