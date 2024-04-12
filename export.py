from dotenv import load_dotenv 
import sqlite3
import os
import pandas as pd
import argparse
import json
from notion_client import Client, APIErrorCode, APIResponseError

class KoboExport:
    def __init__(self, db_path):
        self.conn = None
        self.db_path = db_path
        self.create_connection()
        self.client_secret = os.getenv('NOTION_KEY')
        self.reading_db_id = os.getenv("NOTION_DB_ID")
        self.client = Client(auth=self.client_secret)
    
    def create_connection(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
        except Exception as e:
            print(e)

    ## Writing text to the specified Notion page ------------------------------------------------
    
    def write_text(self, page_id, text, type):
        try:
            self.client.blocks.children.append(
                block_id = page_id,
                children = [
                    {
                        "object": "block",
                        "type": type,
                        type: {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": text
                                    }
                                }
                            ]
                        }
                    }
                ]
            )
        except Exception as e:
            print(e)

    def query_parent_page(self, title):
        try:
            my_page = self.client.databases.query(
                **{
                    "database_id": self.reading_db_id,
                    "filter": {
                        "property": "Title",
                        "rich_text": {
                            "contains": title,
                        },
                    },
                }
            )
            if my_page:
                return my_page["results"][0]['id']
            else:
                return None
        except APIResponseError as error:
            print(error)


    def create_highlight_page(self, target_page_id):
        highlight_page = self.client.pages.create(
            **{
                "parent": {
                    "type": "page_id",
                    "page_id": target_page_id
                },
                "properties": {
                    "title": [
                        {
                            "text": {
                                "content": "Kobo Highlights"
                            }
                        }
                    ]
                }
            }
        )
        return highlight_page['id']
        
    def export_highlight_to_notion(self, title):
        parent_page_id = self.query_parent_page(title)
        if parent_page_id != None:
            print(f"step1: find parent page {parent_page_id}")
            target_page_id = self.create_highlight_page(parent_page_id)
            print(f"step2: create hightlight page {target_page_id}")

            books_in_file = pd.read_sql("select c.ContentId AS 'Content ID', c.Title AS 'Book Title' from content As c where c.Title like '%"+title+"%'", self.conn)
            if len(books_in_file):                           
                print(f"step3: find book in kobo db, title = {title}, books number = {len(books_in_file)}")
                #for i in range(0, len(books_in_file)):
                for i in range(0,len(books_in_file)):
                    bookmark_df = pd.read_sql("SELECT VolumeID AS 'Volume ID', Text AS 'Highlight', Annotation, DateCreated AS 'Created On', Type " + 
                                    "FROM Bookmark Where VolumeID = '" + books_in_file['Content ID'][i] + "'"
                                    " ORDER BY 4 ASC", self.conn)
                    print(f"step4: write highlight into notion, highlight number = {len(bookmark_df)}")

                    for j in range(0, len(bookmark_df)):
                        if bookmark_df['Highlight'][j] != None:
                            bookmark_df['Highlight'][j] = bookmark_df['Highlight'][j].strip()
                    
                    for x in range(0, len(bookmark_df)):
                        if bookmark_df['Type'][x] == 'highlight':
                            self.write_text(target_page_id, bookmark_df['Highlight'][x], 'paragraph')
                        else:
                            if bookmark_df['Annotation'][x] != None:
                                self.write_text(target_page_id, bookmark_df['Annotation'][x], 'quote')
                            if bookmark_df['Highlight'][x] != None:
                                self.write_text(target_page_id, bookmark_df['Highlight'][x], 'paragraph')
                    
        else:
            print("didn't find target page in reading DB")
    
    def get_book_titles(self):
        books_in_file = pd.read_sql("select DISTINCT c.BookTitle AS 'Book Title' from content As c", self.conn)
        titles = []
        for i in range(0, len(books_in_file)):
            if books_in_file['Book Title'][i] != None:
                titles.append(books_in_file['Book Title'][i])

        return titles

if __name__=="__main__":
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--task", help="specify which action (getBooks, export). Default is export")

    args = parser.parse_args()
    action  = "export"
    if args.task:
        action  = args.task
    
    project_dir = os.path.dirname(os.path.abspath(__file__))
    config_json = os.path.join(project_dir, 'config.json')
    with open(config_json) as file:
        project_config=json.load(file)
    db_file = os.path.join(project_dir, "KoboReader.sqlite")
    if not os.path.exists(db_file):
        print("Lack necessary KoboReader.sqlite. Need to copy KoboReader.sqlite to this folder.")
        exit(1)

    runner = KoboExport(db_file)
    print(f"execute action = {action}...")
    if action == "export":
        titles = project_config['titles']
        if len(titles)==0:
            print("You need to specify book titles in config.json first. If you don't know, you can run action(getBooks) to get titles")
        else:
            for title in titles:
                runner.export_highlight_to_notion(title)
    elif action == "getBooks":
        bookTitles = runner.get_book_titles()
        project_dir = os.path.dirname(os.path.abspath(__file__))
        title_file = config_json = os.path.join(project_dir, 'title.txt')
        with open(title_file, "w", encoding='utf-8') as file:
            json.dump(bookTitles, file, ensure_ascii=False)
        
