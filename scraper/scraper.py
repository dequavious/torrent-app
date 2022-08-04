import re
from threading import Thread

import numpy as np
import requests
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError


class Scraper:
    def get_magnet_link(self, link):
        while True:
            r = self.session.get(link)
            while not r.ok:
                r = self.session.get(link)
            html = r.content
            dom = BeautifulSoup(html, 'html.parser')
            try:
                return dom.find('a', {'href': re.compile(r'^magnet:\?xt=urn:btih:.*$')}).attrs['href']
            except AttributeError:
                pass

    def get_torrent_info(self, row, index):
        element = row.find('td', {'class': re.compile(r'^.*name.*$')})
        name = re.sub(r'\n', '', element.text)
        link = f"{self.site}{element.find_all('a')[1].attrs['href']}"
        seeds = int(row.find('td', {'class': re.compile(r'^.*seeds.*$')}).text)
        leech = int(row.find('td', {'class': re.compile(r'^.*leeches.*$')}).text)
        size = re.sub(r'\s', '', row.find('td', {'class': re.compile(r'^.*size.*$')}).text)

        self.torrents[index] = {
            'name': name,
            'link': link,
            'seeds': seeds,
            'leech': leech,
            'size': size,
        }

    def scrape(self, page):
        if 1 < page <= self.pages:
            self.dom = self.get_dom(page)

        try:
            table = self.dom.find('tbody')
            rows = table.find_all('tr')

            self.torrents = np.empty(len(rows), dtype=object)

            for i, row in enumerate(rows):
                Thread(target=self.get_torrent_info, args=(row, i), daemon=True).start()

            while (self.torrents == None).any():
                pass

        except (ConnectionError, AttributeError):
            self.torrents = []

    def get_dom(self, page):
        url = f'{self.site}/search/'
        terms = self.search.split()
        url += '+'.join(terms)
        url += f'/{page}/'
        try:
            r = self.session.get(url)
            while not r.ok:
                r = requests.get(url)
            html = r.content
            return BeautifulSoup(html, 'html.parser')
        except ConnectionError:
            return None

    def __init__(self, search_term):
        self.search = search_term
        self.site = 'https://www.1337x.to'

        with requests.Session() as self.session:
            self.session.headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/104.0.5112.81 Safari/537.36"}
            self.session.get(self.site)

        self.dom = self.get_dom(1)

        try:
            list_items = self.dom.find('div', class_='pagination').find('ul').find_all('li')
            if not list_items[-1].find('a').text == '>>':
                link = list_items[-1].find('a').attrs['href']
                self.pages = int(re.findall(r'\d+', link)[-1])
            else:
                self.pages = int(list_items[-2].find('a').text)
        except (AttributeError, IndexError):
            self.pages = 1

        self.torrents = []
