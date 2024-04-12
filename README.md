# export-kobo

A Python tool to export annotations and highlights from a Kobo SQLite file.

## Usage
```bash
$ # export kobo highlights and annotations to notion
$ python3 export.py -t export

$ # get book titles from kobo and write to "title.txt"
$ python3 export.py -t getBooks
```
## Installation

1. After clone the repo, create a virtual environment and install necessary library
   ```bash
   $ pipenv shell
   $ pipenv install
   ```

2. Copy in the same directory the ``KoboReader.sqlite`` file
   from the ``.kobo/`` hidden directory of the USB drive
   that appears when you plug your Kobo device to the USB port of your PC.
   You might need to enable the ``View hidden files`` option
   in your file manager to see the hidden directory. 
   For examp, in mac system, the path would be ``/Volumes/KOBOeReader/.kobo/KoboReader.sqlite``

3. Modify ``.env.example`` to ``.env`` and setup Notion related environment variable ``NOTION_KEY`` and ``NOTION_DB_ID``

4. Config ``config.json``. List books title which you plan to export annotations and highlights, For example
    ```
    "title":[
        "明日，明日，又明日"
    ]
    ```

5. Run the script
    ```bash
    $ python3 export.py -t export
    ```

## License

**export-kobo** is released under the MIT License.



