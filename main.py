"""
"allitebooks downloader"
version 1.0

This script allows you to search and download(in bulk) ebooks from allitebooks.com. 
All books that you download will be placed in ./books/ dir. 

Author: BonsaiMaster
"""

import os
import re
import time
import random
import requests
import urllib.request
from bs4 import BeautifulSoup

def get_books_details(keyword, max_pages=False):
    """Fetches books information returning dictionary
       conatinaing { <id>:{link,title} }
    page: (not accessable from the menu) number of the last page
          to be considered, min 1
    keyword: <searched text> e.g 'python for beginners' """

    BASE_LINK = "http://www.allitebooks.com"
    S_ARG = "/?s="
    P_ARG = "/page/{}"
    
    print("Searching for \"{}\" books...".format(keyword))
    keyword = urllib.parse.quote(keyword, safe='')
    soup = BeautifulSoup(requests.get(BASE_LINK + S_ARG + keyword).text,
                                     "html.parser")
    
    # Assertion if searched keyword gave any results.
    if soup.find("h1", text = "No Posts Found."):
        return None

    # Defining number of pages to look through.
    multiple_pages = soup.find("span", class_ = "pages")
    if multiple_pages:
        last_page = int(multiple_pages.text.split(" ")[2])
        if max_pages >= 1:
            if max_pages > last_page:
                max_pages = last_page
        else:
            max_pages = last_page
    else:
        max_pages = 1

    # Gathernig the actual data.
    found_books = {}
    book_id = 1
    for i in range(max_pages):
        link_page = BASE_LINK + P_ARG.format(i+1) + S_ARG + keyword
        soup = BeautifulSoup(requests.get(link_page).text, "html.parser")
        books = soup.findAll("article")
        for book in books:
            entry = book.find("h2", class_="entry-title").a
            link_book = entry["href"]
            title = entry.text
            found_books[book_id] = {"link":link_book, "title":title}
            book_id = book_id + 1
    return found_books        

def download_book(link):
    """Downloads .pdf file from given book-page link to ./books/ dir."""

    PATH = os.getcwd() + "/books/"

    # Defines basic information.
    soup = BeautifulSoup(requests.get(link).text, "html.parser")
    pdf_link = soup.find("span", class_ = "download-links").a['href']
    title = soup.find("h1", class_ = "single-title").text

    # Asserts correct format of last part of the link. 
    pdf_link = pdf_link.split("/")
    pdf_link[-1] = urllib.parse.quote(pdf_link[-1], safe='')
    pdf_link = "/".join(pdf_link)

    # Creates contener for books.
    try:
        os.makedirs(PATH)
    except OSError:
        pass

    # Downloads .pdf skipping already existings ones.
    if os.path.isfile(PATH + title + ".pdf"):
        print("File already exists:", title + ".pdf")
    else:
        print("Downloading file",  title + '.pdf...', end='')
        urllib.request.urlretrieve(pdf_link, PATH + title + ".pdf")
        print("done.")
        nap = random.uniform(1,3)
        print("Napping for {:3.2f}s".format(nap))
        time.sleep(nap)

def show_books(books):
    """Displays books."""

    print("ID","Title")
    for id in books:
        title = books[id]["title"]
        print(str(id) + ".", "\"" + title + "\".")

def choose_books(books):
    """Handles a user choice after books were found.
    Returns selected books or 'None' if aborted."""
    
    print("""To download books provide IDs in following formats:
    '1,6,8,9' - one o more IDs separated by commas.
    '2-7,10-15' - one or more ranges of IDs.
    '1,4,2-7,12,25,9-10' - mix of two above.

    Additional options:
    'all' - download all found books.
    'exit' or blank - abort.
    """)
    
    while True:
        response = input("IDs [exit]: ")

        if not response or response.lower() == "exit":
            return None
        elif response.lower() == "all":
            return books
        else:
            choice = filter_books(response, books)
            if choice:
                return choice
            else:
                print("No IDs recognized, try again.")
        
def filter_books(response, books):
    """Filters books by ID chosen by a user. Ignores wrong 
       formatted input.
    Returns 'None' if no ID was found in user reponse (wrong format),
    otherwise returns only selected books.
    """

    # Filters user response with regex and creates set of selected ids.
    response = response.split(",")
    ids = set()
    for v in response:
        v = v.replace(" ", "")
        if re.match("^\d+-\d+$", v):
            rng = v.split("-")
            rng = [int(x) for x in rng]
            if len(rng) == 2:
                [ids.add(x) for x in range(rng[0],rng[1]+1)]
        elif re.match("^\d+$", v):
            v = int(v)
            ids.add(v)

    if not ids:
        return None
    
    selected_books = {}
    ids = sorted(list(ids))
    for id in ids:
        if id in books:
            selected_books[id] = books[id]
    return selected_books

def confirm_download(selected_books):
    """Handles confirmation to download selected books."""

    print("Selected {} book(s):".format(len(selected_books)))
    show_books(selected_books)
    while True:
        response = input("Do you want to proceed? (y/n):")
        if response.lower() == "y":
            for id in selected_books:
                download_book(selected_books[id]["link"])
            return True
        elif response.lower() == "n":
            return False

def main_loop():
    """Menu logic"""

    # Main loop with the first choice for search. 
    while True:
        response = input("What books are you looking for? [exit]: ")
        if not response or response.lower() == "exit":
            return 0
        books = get_books_details(response)
        if not books:
            print("No books found.")
            continue
        else:
            # Second loop with the books selection. 
            while True:
                show_books(books)
                print()
                selected_books = choose_books(books)
                if not selected_books:
                    break
                else:
                    confirmed = confirm_download(selected_books)
                    if confirmed:
                        break
               

if __name__ == "__main__":
    main_loop()

