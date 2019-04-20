import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

#engine = create_engine(os.getenv("DATABASE_URL"))
engine = create_engine("postgres://hlojtlqjgyszxx:0061b447e9dbc04cc25bc341745c006ae869096665107472c5f1eccf5446ec1e@ec2-54-228-252-67.eu-west-1.compute.amazonaws.com:5432/d4mg4mean0buf7")

db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv")
    reader = csv.reader(f)
    
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                    {"isbn": isbn, "title": title, "author": author, "year": year})
        print(f"Added book called {title} written by {author} in {year}. Isbn: {isbn}.")
    db.commit()

if __name__ == "__main__":
    main()
