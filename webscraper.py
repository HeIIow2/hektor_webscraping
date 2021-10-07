import urllib.request
from bs4 import BeautifulSoup
import re
import json
import os
from datetime import datetime

url_regex = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

with open('settings.json') as json_file:
    settings = json.load(json_file)

sites = settings['sites']

def get_soup(url: str):
    user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'

    headers = {'User-Agent': user_agent, }
    request = urllib.request.Request(url, None, headers)
    response = urllib.request.urlopen(request)

    return BeautifulSoup(response, "lxml")


def get_href(url: str):
    soup = get_soup(url)

    links = []
    for link in soup.findAll('a'):
        links.append(link.get('href'))

    return links


def get_headers(soup):
    headers = []
    for header in soup.findAll('h1'):
        headers.append(header.text)

    for header in soup.findAll('h2'):
        headers.append(header.text)

    for header in soup.findAll('h3'):
        headers.append(header.text)

    return headers


def get_text(soup):
    text = ""
    for p in soup.findAll('p'):
        text += p.text

    return text


def get_web_elem(url: str):
    soup = get_soup(url)

    headers = get_headers(soup)
    text = get_text(soup)

    if len(headers) == 0 and text == '':
        return {}
    return {'headers': headers, 'text': text}


def create_folder(path: str):
    if os.path.exists(path):
        print('today was already a folder created!')
        if not settings["run if folder exists"]:
            exit()
    else:
        os.makedirs(path)


now = datetime.now()
folder_path = 'data/' + now.strftime("%m.%d.%Y")
create_folder(folder_path)

for site_elem in sites:
    site, site_name = site_elem
    complete_data = []

    print(site)
    raw_links = get_href(site)
    links = []
    for link in raw_links:
        if re.match(url_regex, link) is None:
            links.append([site + link[1:], True])
        elif not settings["only subdomains"]:
            links.append([link, False])

    print(f'found {len(links)} on {site_name}')

    prev_percentage = 0
    print(f'progress [{prev_percentage}%; {0} from {len(links)}]')
    for i, link_elem in enumerate(links):
        link, is_sub = link_elem
        try:
            data = {"url": link, "success": True, "is sub": is_sub, "content": get_web_elem(link)}
            complete_data.append(data)
        except:
            if not settings["delete failed requests"]:
                data = {"url": link, "success": False, "is sub": is_sub, "content": {}}
                complete_data.append(data)

        if i != 0:
            percentage = int((i / len(links)) * 100)
            if percentage != prev_percentage:
                prev_percentage = percentage
                print(f'progress [{percentage}%; {i} from {len(links)}]')

    print(f'progress [{100}%; {len(links)} from {len(links)}]')

    with open(f'{folder_path}/{site_name}.json', 'w', encoding='utf-8') as fp:
        json.dump(complete_data, fp, ensure_ascii=False)

        print('')
        print(f'successfully dumped {site_name}.json at {folder_path}/{site_name}.json')
        print('')
        print('')
