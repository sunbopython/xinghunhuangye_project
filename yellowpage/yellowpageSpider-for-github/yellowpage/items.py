# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Field, Item


# The following three classes are for catalog Spider
# they stand for different level of catalog
# 
class IndustryItem(Item):
    """for industry Item: level 1 catalog"""
    
    industryName = Field() 
    industryranking = Field()
    industryurl = Field()
    industrytotal = Field()
    categoryMember = Field()    # list consists of categoryItem object


class CategoryItem(Item):
    """for category Item: level 2 catalog"""

    categoryName = Field()
    categoryranking = Field()
    categoryurl = Field()
    categorytotal = Field()
    classifyMember = Field()    # list consists of ClassifyItem object


class ClassifyItem(Item):
    """for classifyItem: level 3 catalog"""

    classifyName = Field()
    classifyranking = Field()
    classifyurl = Field()
    classifytotal = Field()


# The following class is for yellowpage Spider
# it includes company related information
# 
class YellowpageItem(Item):
    # define the fields for your item here like:
    # name = scrapy.Field()

    industryID = Field()                # 行业分类
    categoryID = Field()                # 行业再分
    classifyID = Field()                # 产品细分
    name = Field()                      # 企业名
    url = Field()                       # 星魂网对应的url
    legalRepresentative = Field()       # 法人代表
    registedCapital = Field()           # 注册资本
    businessModel = Field()             # 经营模式
    employNum = Field()                 # 员工数量
    majorMarket = Field()               # 主要市场
    customerType = Field()              # 客户类型
    industry = Field()                  # 所属行业
    productionInfo = Field()            # 产品信息
    industryInfo = Field()              # 行业信息
    districtInfo = Field()              # 区位信息
    relatedLink = Field()               # 相关链接
    companyTag = Field()                # 企业标签
    updateTime = Field()                # 最后更新
    viewNum = Field()                   # 浏览次数      
    description = Field()               # 企业描述
    contactPerson = Field()             # 联系人
    webSite = Field()                   # 网站
    postNum = Field()                   # 邮编
    location = Field()                  # 地址
    phone = Field()                     # 电话
    fax = Field()                       # 传真