import re
from threading import Thread

import numpy as np
import requests
from requests.exceptions import ConnectionError
from bs4 import BeautifulSoup


def get_magnet_link(link):
    while True:
        r = requests.get(link)
        while not r.ok or r == '':
            r = requests.get(link)
        html = r.content
        dom = BeautifulSoup(html, 'html.parser')
        try:
            return dom.find('a', {'href': re.compile(r'^magnet:\?xt=urn:btih:.*$')}).attrs['href']
        except AttributeError:
            pass


class Scraper:
    def get_torrent_info(self, row, index):
        element = row.find('td', class_='coll-1 name')
        name = re.sub(r'\n', '', element.text)
        link = f"{self.site}/{element.find_all('a')[1].attrs['href']}"
        seeds = int(row.find('td', class_='coll-2 seeds').text)
        leech = int(row.find('td', class_='coll-3 leeches').text)
        size = re.sub(r'\s', '', row.find('td', class_='coll-4 size mob-uploader').text)

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
        url += '%20'.join(terms)
        url += f'/{page}/'
        try:
            r = requests.get(url)
            while r is None or not r.ok:
                r = requests.get(url)
            html = r.content
            return BeautifulSoup(html, 'html.parser')
        except ConnectionError:
            return None

    def __init__(self, search_term):
        self.search = search_term
        self.site = 'https://www.1377x.to'

        self.dom = self.get_dom(1)

        try:
            list_items = self.dom.find('div', class_='pagination').find('ul').find_all('li')
            if not list_items[-1].find('a').text == '>>':
                self.pages = int(list_items[-1].find('a').text)
            else:
                self.pages = int(list_items[-2].find('a').text)
        except AttributeError:
            self.pages = 1

        self.torrents = []
