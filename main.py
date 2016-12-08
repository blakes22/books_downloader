import os
import re
import time
import random
import requests
import urllib.request
from bs4 import BeautifulSoup

BASE_LINK = "http://www.allitebooks.com"
S_ARG = "/?s="
P_ARG = "/page/{}"

def get_books_details(keyword, max_pages=False):
    """Fetches books information returning dictionary conatinaing dict id:{link,title}
    page: number of the last page to beconsidered, min 1
    keyword: e.g. <searched text>
    """
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
    output_data = {}
    test = {}
    book_id = 1
    for i in range(max_pages):
        link_page = BASE_LINK + P_ARG.format(i+1) + S_ARG + keyword
        soup = BeautifulSoup(requests.get(link_page).text, "html.parser")
        books = soup.findAll("article")
        for book in books:
            entry = book.find("h2", class_="entry-title").a
            link_book = entry["href"]
            title = entry.text
            output_data[book_id] = {"link":link_book, "title":title}
            book_id = book_id + 1
    return output_data        

def download_book(link):
    """Downloads .pdf file from given book link. 
    """

    PATH = os.getcwd() + "/books/"
    
    soup = BeautifulSoup(requests.get(link).text, "html.parser")
    pdf_link = soup.find("span", class_ = "download-links").a['href']
    title = soup.find("h1", class_ = "single-title").text

    # Assertion for correct format of last part of the link. 
    pdf_link = pdf_link.split("/")
    pdf_link[-1] = urllib.parse.quote(pdf_link[-1], safe='')
    pdf_link = "/".join(pdf_link)

    # Creates contener for books.
    try:
        os.makedirs(PATH)
    except OSError:
        pass
    
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
    print("ID","Title")
    for id in books:
        title = books[id]["title"]
        print(str(id) + ".", "\"" + title + "\".")

def choose_books(books):
    """Handles a user choice after books were found.
    Returns chosen_books in the same format or None if aborted."""
    
    print("""To download books provide IDs in following formats:
    '1,6,8,9' - one o more IDs separated by commas.
    '2-7,10-15' - one or more ranges of IDs.
    '1,4,2-7,12,25,9-10' - mix of two above.

    Additional options:
    'all' - download all found books.
    [blank] - abort.
    """)
    
    while True:
        response = input("IDs: ")

        if not response:
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
    """Helper function, filters books by id given by a user.
    Returns None if no ID was given (e.g wrong format)
    Otherwise returns dictionary with pairs id:link of chosen books.
    """

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
    
    output_data = {}
    for id in ids:
        if id in books:
            output_data[id] = books[id]

    return output_data

def confirm_download(chosen_books):
    """Helper function, handles download confirmation."""

    print("Selected {} book(s):".format(len(chosen_books)))
    show_books(chosen_books)
    while True:
        response = input("Do you want to proceed? [y/n]:")
        if response.lower() == "y":
            for id in chosen_books:
                download_book(chosen_books[id]["link"])
            return True
        elif response.lower() == "n":
            return False

def main_loop():
    while True:
        response = input("What books are you looking for [blank to exit]: ")
        if not response:
            return 0
        
        books = get_books_details(response)
        if not books:
            print("No books found.")
            continue
        else:
            while True:
                show_books(books)
                print()
                chosen_books = choose_books(books)
                if not chosen_books:
                    break
                else:
                    confirmed = confirm_download(chosen_books)
                    if confirmed:
                        break
               

if __name__ == "__main__":
    main_loop()

