import os
import time
import random
import requests
import urllib.request
from bs4 import BeautifulSoup

BASE_LINK = "http://www.allitebooks.com"
S_ARG = "/?s="
P_ARG = "/page/{}"

def read_links(filename):
    with open(filename, "r") as f:
        data = f.read().splitlines()
    return data

def get_books_details(keyword, max_pages=None):
    """Fetches books information returning dictionary conatinaing pairs id:link
    page: number of the last page to beconsidered, min 1
    keyword: e.g. <searched text>
    """
    
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
    
    # Gathernig the actual data: id:link pairs.
    output_data = {}
    book_id = 1
    for i in range(max_pages):
        link_page = BASE_LINK + P_ARG.format(i+1) + S_ARG + keyword
        soup = BeautifulSoup(requests.get(link_page).text, "html.parser")
        books = soup.findAll("article")
        for book in books:
            link_book = book.find("a", href=True)["href"]# + "\n"
            output_data[book_id] = link_book
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
        title = books[id].split("/")[-2]
        title = title.replace("-", " ").capitalize()
        print(str(id) + ".", "\"" + title + "\".")

def choose_books(books):
    """Asks user to choose books IDs to download
    Returns None if no ID was selected
    Otherwise returns dictionary with pairs id:link of chosen books.
    """
    
    response = input("Choose books to download (IDs seperated by commas) | [exit]: ")
    if not response or response.lower() == "exit":
        return None
    response = response.split(",")
    response = [abs(int(v.strip())) for v in response]
    response = list(set(response))
    output_data = {}
    for id in response:
        if id in books:
            output_data[id] = books[id]
    return output_data

# TEMP
books = get_books_details("python", 1)
#TEMP
def main():
    #TODO: Add input handling here
    #response = input("What books are you looking for: ")
    #return urllib.parse.quote(response, safe='')
    #response = get_input()
    
    if not books:
        print("No books found.")
    else:
        show_books(books)
        print()
        try:
            chosen_books = choose_books(books)
            if not chosen_books:
                print("byebye")
                return
        except ValueError as e:
            print("Only numbers please.")
        print("Selected {} book(s):".format(len(chosen_books)))
        show_books(chosen_books)
        for id in chosen_books:
            download_book(books[id])
    # Check if No results found
    # Check how many pages there are found
    # Ask if you want to proceed     

if __name__ == "__main__":
    main()
