import re
import urllib2
import urlparse
import BeautifulSoup

class Crawler(object):
    def __init__(self, base_url):
        self.base_url = base_url
        
    def isValidUrl(self, url): #make sure the <a> tag is for valid url
        regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        if regex.match(url) is not None:
            return True;
        return False
    
    def isBaseSame(self, page): #if the base domain is the same
        basedomain = urlparse.urlparse(self.base_url)
        domain = urlparse.urlparse(page)
        if basedomain.netloc == domain.netloc:
            return True
        #Todo add a check for the path exe csun.edu/pathways vs csun.edu
        
    def crawl(self):
        tocrawl=[self.base_url]
        crawled=[]
        while tocrawl:
            page=tocrawl.pop()
            if self.isBaseSame(page):
                try:
                    pagesource=urllib2.urlopen(page)
                    s=pagesource.read()
                    soup=BeautifulSoup.BeautifulSoup(s)
                    links=soup.findAll('a',href=True)
                    if page not in crawled:
                        for l in links:
                            if self.isValidUrl(l['href']):
                                tocrawl.append(l['href'])
                        crawled.append(page)
                except: #don't die on broken urls 
                    continue
        return crawled