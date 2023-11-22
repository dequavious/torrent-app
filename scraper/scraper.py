import re
from dataclasses import dataclass
from random import choice

from bs4 import BeautifulSoup
from requests import Session
from requests.exceptions import ConnectionError
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from utils.process import thread_pool_results


def get_random_user_agent():
    user_agents = ["Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:38.0) Gecko/20100101 Firefox/38.0",
                   "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0",
                   "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.112 "
                   "Safari/537.36",
                   "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) "
                   "Version/9.0.2 Safari/601.3.9",
                   "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.155 "
                   "Safari/537.36",
                   "Mozilla/5.0 (Windows NT 5.1; rv:40.0) Gecko/20100101 Firefox/40.0",
                   "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR "
                   "3.0.4506.2152; .NET CLR 3.5.30729)",
                   "Mozilla/5.0 (compatible; MSIE 6.0; Windows NT 5.1)",
                   "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 2.0.50727)",
                   "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:31.0) Gecko/20100101 Firefox/31.0",
                   "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 "
                   "Safari/537.36",
                   "Opera/9.80 (Windows NT 6.2; Win64; x64) Presto/2.12.388 Version/12.17",
                   "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0",
                   "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0",
                   "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.81 "
                   "Safari/537.36",
                   "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/47.0.2526.106 Safari/537.36"
                   ]
    return choice(user_agents)


@dataclass
class Scraper:
    site = 'https://www.1337x.to'
    page = None
    torrents = []

    def __post_init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.get(self.site)

        with Session() as self.session:
            self.session.headers = {
                "User-Agent": get_random_user_agent()}
            self.session.get(self.site)

    def __del__(self):
        self.driver.quit()

    def get_magnet_link(self, link):
        r = self.session.get(link)
        while not r.ok:
            r = self.session.get(link)
        html = r.content
        dom = BeautifulSoup(html, 'html.parser')
        try:
            return dom.find('a', {'href': re.compile(r'^magnet:\?xt=urn:btih:.*$')}).attrs['href']
        except AttributeError as e:
            print("_get_magnet_link", e)

    def _get_torrent_info(self, row):
        element = row.find('td', class_=re.compile(r'^.*name')).find_all('a')[-1]
        name = element.text
        link = f"{self.site}{element.attrs['href']}"
        seeds = int(row.find('td', class_=re.compile(r'^.*seeds')).text)
        leech = int(row.find('td', class_=re.compile(r'^.*leeches')).text)
        size = re.sub(r'\s|\d+$', '', row.find('td', class_=re.compile(r'^.*size')).text)
        return {
            'name': name,
            'link': link,
            'seeds': seeds,
            'leech': leech,
            'size': size
        }

    def scrape(self, search, page_nr=1):
        url = f'{self.site}/search/'
        terms = search.split()
        url += '+'.join(terms)
        url += f'/{page_nr}/'

        self.driver.get(url)

        html = self.driver.page_source
        self.page = BeautifulSoup(html, 'html.parser')

        try:
            table = self.page.find('tbody')
            rows = table.find_all('tr')

            self.torrents = list(map(
                lambda future: future.result(), thread_pool_results(self._get_torrent_info, rows)
            ))
        except (ConnectionError, AttributeError) as e:
            print("scrape", e)
            self.torrents = []

    @property
    def nr_pages(self):
        try:
            list_items = self.page.find('div', class_='pagination').find('ul').find_all('li')
            if len(list_items) > 1:
                link = list_items[-1].find('a').attrs['href']
                return int(re.findall(r'\d+', link)[-1])
            else:
                return 1
        except (AttributeError, IndexError) as e:
            print("nr_pages", e)
            return 1

