import requests
from bs4 import BeautifulSoup, NavigableString
import re
import difflib
from pathlib import Path

import argparse
import difflib
import sys
fetched = 0

def scrappni_link(link):
    global fetched
    fetched+=1
    subpage = requests.get(link)
    soupsubpage = BeautifulSoup(subpage.content, 'html.parser')
    # print(soup.prettify())

    nazev_op = soupsubpage.find("article").find_all("h1")[0].string
    odkaz = soupsubpage.find("article").find_all("a")[0]["href"]
    publikovano = soupsubpage.find(class_="entryDate").text
    print("{}: {}".format(fetched, nazev_op))

    #print("Nazev: \n{} Publikovano: \n{}\nOdkaz: \n{}\n".format(nazev_op, publikovano, odkaz))
    return "{}\n".format(nazev_op)

    return "Nazev: \n{} Publikovano: \n{}\nOdkaz: \n{}\n".format(nazev_op, publikovano, odkaz)
    #return nazev_op,  publikovano,  odkaz
def stahni():
    page = requests.get("https://koronavirus.mzcr.cz/mapa-webu/")
    soup = BeautifulSoup(page.content, 'html.parser')

    #print(soup.prettify())
    out = ""
    kategorie = soup.select('#page > div > ul.wsp-posts-list > li:nth-child(1) > ul')
    for k in kategorie[0].contents:
       try:
           for i in k:
               #print(i.attrs["href"])
               out += scrappni_link(i.attrs["href"])
               #print(i.attrs["aria-label"])
       except AttributeError:
           pass


    split_strings = ""
    n = 160
    for line in out.split("\n"):
        while(len(line) > n): # split
            split_strings += line[:n] + "\n"
            line = line[n:]
        split_strings += line + "\n"

    print(split_strings)
    #return split_strings

    return out


def return_diff(old_file: Path, new_file: Path):
    out = ""
    file_1 = open(old_file).readlines()
    file_2 = open(new_file).readlines()
    out =  difflib.context_diff(file_1, file_2)
    delta = ''.join(out)


    return delta

def create_diff(old_file: Path, new_file: Path, output_file: Path = None):
    file_1 = open(old_file).readlines()
    file_2 = open(new_file).readlines()

    if output_file:
        delta = difflib.HtmlDiff().make_file(
            file_1, file_2, old_file.name, new_file.name
        )
        with open(output_file, "w") as f:
            f.write(delta)
    else:
        delta = difflib.statistika(file_1, file_2, old_file.name, new_file.name)
        sys.stdout.writelines(delta)


def main():
    text_file = open("./projektrouska/aktualnost/aktualni.txt", "w")
    n = text_file.write(stahni())
    text_file.close()

    old_file = Path('./projektrouska/aktualnost/v_databazi.txt')
    new_file = Path('./projektrouska/aktualnost/aktualni.txt')

    res =  return_diff(old_file, new_file)
    return res
    #output_file = Path('vystup.html')
    #create_diff(old_file, new_file, output_file)


if __name__ == "__main__":

    main()

