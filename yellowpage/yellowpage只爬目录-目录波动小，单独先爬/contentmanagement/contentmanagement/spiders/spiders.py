# -*- coding: utf-8 -*-

from scrapy import  Request, Spider
from contentmanagement.items import IndustryItem, CategoryItem, ClassifyItem
import logging

#import sys
#reload(sys)
#sys.setdefaultencoding('utf-8')


class yellowpageSpider(Spider):
    name = "yellowpageCategory"
#    allowed_domains =["qincai.net"]
    start_urls =["http://www.qincai.net/iohohoioh/index.html"]

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
            # logging.info(item)

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
            categoryItem['categoryName'] = categorysels.xpath("a/text()").extract()[0]    #.decode("utf-8", 'ignore')
            categoryItem['categoryranking'] = index
            categoryItem['categoryurl'] = categorysels.xpath('a/@href').extract()[0]
            categoryItem['categorytotal'] = categorysels.xpath('span/text()').extract()[0]
            
            yield Request(categoryItem['categoryurl'],callback=self.parseClassify,meta={'item':item,'categoryItem':categoryItem,'categoryMax':categoryMax})
        # logging.info(item)

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
            classifyItem['classifyName'] = classifysels.xpath('a/text()').extract()[0]    #.decode("utf-8", 'ignore')
            classifyItem['classifyranking']= index
            classifyItem['classifyurl'] = classifysels.xpath('a/@href').extract()[0]
            classifyItem['classifytotal'] = classifysels.xpath('span/text()').extract()[0]
            categoryItem["classifyMember"].append(classifyItem)

        item['categoryMember'].append(categoryItem)
        logging.info(len(item['categoryMember']))
        if len(item['categoryMember'])==categoryMax:        
            logging.info(item)
            return item
