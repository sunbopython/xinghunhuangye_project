# coding: utf-8
"""
Author  jerryAn
Time    2016.05.04
"""

import random
import logging
import re
from datetime import datetime, timedelta
import time
from twisted.web._newclient import ResponseNeverReceived,ParseError
from twisted.internet.error import TimeoutError,ConnectionRefusedError, ConnectError,ConnectionLost
import os.path


class ProxyMiddleware(object):
    """Customized Proxy Middleware"""
    # Change another proxy instead of passing to RetryMiddlewares when met these errors
    DONT_RETRY_ERRORS = (TimeoutError,ConnectionRefusedError, 
                        ResponseNeverReceived, ConnectError, ValueError)

    proxy_file = "utils/validProxy.txt"       # file with valided proxy

    def __init__(self):
        # proxy_list: A list of many proxies including its' port
        self.proxy_list = []
        # proxy: A Proxy for middleware to use
        self.proxy = None
        # the statistic of proxy within wimerWindow periods
        self.ProxyCount ={}

        # TODO  requestCount: Total request times
        # self.requestCount = 0        
        # TODO: requestThreshold: when certain request times matches, change another proxy
        # self.requestThreshold = 1000

        # starting time point 
        self.request_timerStartPoint = datetime.now() 
        # A period which divides the time elaspe between Nowtime and starting point
        self.change_interval = 360
        # timerWindow: change proxy within this window    
        self.timerWindow = 45 

        self.readProxyfile(self.proxy_file)

    def readProxyfile(self,proxyfile):
        """get proxy from file"""
        with open(proxyfile) as f:
            for line in f:
                if line not in self.proxy_list:
                    self.proxy_list.append('http://'+line.strip('\n'))
        return len(self.proxy_list)

    #def countMatch(self):
    #    """Count current request times, return True if it matches certain condition
    #    """
    #    self.requestCount = self.requestCount + 1
    #    logging.info("Current request times: %(requestCount)s, change threshold is %(requestThreshold)s",
    #                    {'requestCount':int(self.requestCount),
    #                    'requestThreshold':int(self.requestThreshold)
    #                    })
    #    return self.requestCount % self.requestThreshold == 0

    def timerMatch(self):
        """ A timer: return True if time elapse satisfied certain condition
        """
        
        # timetuple() change datetime obj to time stamp obj
        CurrentTime = datetime.now()
        currentStamp = time.mktime(CurrentTime.timetuple())
        startStamp = time.mktime(self.request_timerStartPoint.timetuple())
        tippingValue = currentStamp - startStamp

        logging.info("Time elaspe: %(tippingValue)f,Changing period: %(change_interval)s",
                    {'tippingValue':tippingValue,
                    'change_interval':self.change_interval})
 
        return tippingValue % self.change_interval < self.timerWindow

    def _inc_ProxyStatistic(self,passedProxy):
        """Make a statistics for proxies used within timerWidow 
        """
        self.ProxyCount[passedProxy] = self.ProxyCount[passedProxy] + 1
        logging.info("This proxy %(passedProxy)s has %(count)d successful times",
                        {'passedProxy':passedProxy,
                        'count':self.ProxyCount[passedProxy]})

    def fetchbestProxy(self,index=0):
        """Sort the successful times for all proxy, index stand for the sequence number of the sorted proxy
        """
        try:
            tupleList =sorted(self.ProxyCount.items(),key=lambda x:x[1],reverse= True)
            return tupleList[index][0]
        except Exception as e:
            logging.debug(e)
            logging.debug("Failed to fetch the best proxy, change to random one")
            return random.choice(self.proxy_list)

    def _change_proxy_new_request(self,request):
        """change a random proxy and return a new request with the new proxy
        """
        self.proxy =  random.choice(self.proxy_list)  
        new_request = request.copy()
        new_request.meta['proxy'] = self.proxy 
        new_request.dont_filter = True
        
        logging.debug("Changing proxy to %(proxy)s for processing %(url)s",
                        {'proxy':new_request.meta['proxy'], 'url':new_request})
        return new_request

    def process_request(self, request, spider):
        """ Add a proxy to request object, the proxy either comes from random choose or the bestone from sorted proxy list according to their successful times
        """
        # logging.info("Hello, I am %s" % self)
        if  self.timerMatch():              
            self.readProxyfile(self.proxy_file)      # refresh proxy
            self.proxy = random.choice(self.proxy_list)  
        else:
            self.proxy = self.fetchbestProxy()
        request.meta['proxy'] = self.proxy
        self.ProxyCount.setdefault(request.meta['proxy'],0)

        logging.info("Request %(request)s using proxy:%(proxy)s",
                        {'request':request, 'proxy':request.meta['proxy']})

    def process_response(self, request, response, spider):
        """ Check response.status, decide whether to change proxy
          If status is not 200, proxy should be changed because of invalidity.
          Make a same request using the new proxy.
        """
        # logging.info("Hello, I am %s" % self)
        if response.status !=200:
            logging.debug("Response status not handled, proxy:%(proxy)s failed for processing %(url)s",
                                {'proxy':request.meta['proxy'],'url':response})
            self.ProxyCount[request.meta['proxy']]=0
            return self._change_proxy_new_request(request)
        else:
            logging.info("Good proxy:%(proxy)s for processing %(url)s",
                            {'proxy':request.meta['proxy'],'url':response})
            self._inc_ProxyStatistic(request.meta['proxy'])
            return response

    def process_exception(self, request, exception, spider):
        """Handle some connection error, make another request when these error happens
        """
        # logging.info("Hello, I am %s" % self)
        if isinstance(exception,self.DONT_RETRY_ERRORS):
            logging.debug("Exception Happened here when using proxy:%(proxy)s for processing %(url)s",
                                {'proxy':request.meta['proxy'],'url':request})
            self.ProxyCount[request.meta['proxy']]=0 
            return self._change_proxy_new_request(request)