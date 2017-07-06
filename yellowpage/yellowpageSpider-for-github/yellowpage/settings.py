# -*- coding: utf-8 -*-

# Scrapy settings for yellowpage project


BOT_NAME = 'yellowpage'

SPIDER_MODULES = ['yellowpage.spiders']
NEWSPIDER_MODULE = 'yellowpage.spiders'


DEFAULT_REQUEST_HEADERS = {
   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
   'Accept-Language': 'zh-CN,zh;q=0.8',
}

# Disable cookies (enabled by default)
COOKIES_ENABLED=False

# Tricky way to handle different pipelines for different spiders
ITEM_PIPELINES = {
    #'yellowpage.pipelines.ContentmanagementPipeline':200,
    'yellowpage.pipelines.YellowpagePipeline': 400,
    'yellowpage.pipelines2.YellowpagePipeline': 500,
}


DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'yellowpage.downloadermiddlewares.rotate_useragent.RotateUserAgentMiddleware':400,
    #'scrapy.downloadermiddlewares.retry.RetryMiddleware':500,
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware':None,
    'yellowpage.downloadermiddlewares.rotate_proxy.ProxyMiddleware':750,
        
}

DOWNLOAD_DELAY = 0.1

# This setting is also affected by the RANDOMIZE_DOWNLOAD_DELAY setting (which is enabled by default). By default, Scrapy doesn’t wait a fixed amount of time between requests, but uses a random interval between 0.5 and 1.5 * DOWNLOAD_DELAY.


# The download delay setting will honor only one of:
CONCURRENT_REQUESTS = 20
CONCURRENT_REQUESTS_PER_DOMAIN = 8
CONCURRENT_REQUESTS_PER_IP = 0

# Retry middleware setting
RETRY_ENABLED = True
# Retry many times since proxies often fail
RETRY_TIMES = 20     
# Retry on most error codes since proxies fail for different reasons
RETRY_HTTP_CODES = [400, 403, 404, 408, 500, 502, 503, 504]