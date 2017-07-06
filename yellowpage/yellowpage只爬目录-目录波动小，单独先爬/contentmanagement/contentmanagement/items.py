# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class IndustryItem(Item):
    
    industryName = Field() 
    industryranking = Field()
    industryurl = Field()
    industrytotal = Field()
    categoryMember = Field()    # a list  of categoryItem object


class CategoryItem(Item):
    
    categoryName = Field()
    categoryranking = Field()
    categoryurl = Field()
    categorytotal = Field()
    classifyMember = Field()    # a list of ClassifyItem object


class ClassifyItem(Item):

    classifyName = Field()
    classifyranking = Field()
    classifyurl = Field()
    classifytotal = Field()