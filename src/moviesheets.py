import gspread
from oauth2client.service_account import ServiceAccountCredentials

import imdb
import Levenshtein
import time

"""
A row in the spreadsheet contains:
    title		string
    recommendation	string (yes, no, haven't seen)
    rating		float from 1-10
    notes		string
    imdb url		string url
    watch date		mm/dd/yyyy formatted string
    release year	int
"""

def open_spreadsheet(sheet_name):
    # use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('../client_secret.json', scope)
    client = gspread.authorize(creds)

    # Find a workbook by name and open the first sheet
    # Make sure you use the right name here.
    sheet = client.open(sheet_name).sheet1
    return sheet


"""
Adds a new row at the top of the spreadsheet

@param sheet: spreadsheet reference object
@param movie_title: string containing movie_title
"""
def add_new_row(sheet, movie_title):
    row = []
    row.append(movie_title)
    ia = imdb.IMDb()

    # get recommendation
    while True:
        try:
            recommendation_str = input("Would you recommend this movie?\n1) Yes\n2) No\n3) Haven't Seen\n")
            if recommendation_str[0] == str(1) or recommendation_str[0].lower() == 'y':
                recommendation = 'Yes'
                row.append(recommendation)
                break
            elif recommendation_str[0] == str(2) or recommendation_str[0].lower() == 'n':
                recommendation = 'No'
                row.append(recommendation)
                break
            elif recommendation_str[0] == str(3) or recommendation_str[0].lower() == 'h':
                recommendation = "Haven't Seen"
                row.append(recommendation)
                break
        except:
            pass
    print()

    # if you haven't seen the movie then you are adding it to the list for future reference
    # there should be no rating or Notes field in this case
    if recommendation != "Haven't Seen":
        # get rating
        while True:
            try:
                rating = float(input("How would you rate this movie?\nInput a number 1-10\n"))
                row.append(rating)
                break
            except:
                pass
        print()

        # get Notes
        notes = input("What else would you like to say about this movie?\nThis will go under the 'Notes' portion:\n")
        row.append(notes)
        print()
    else:
        #pad the row
        row.append("")
        row.append("")


    # get IMDB url
    print("Let's try to find this movie on IMDB...")
    movie_list = ia.search_movie(movie_title)[:5]
    print("The imdb search brought up these titles:")
    if len(movie_list) > 0:
        # print selection options
        for i, movie in enumerate(movie_list):
            print(i+1, ") ", movie['long imdb title'],"; ", end='', sep='')

            # throws an exception if there are no directors
            try:
                # slow option but it works and really helps narrow down what movie it is
                print(*ia.get_movie(movie.movieID)['directors'], sep=',')
            except:
                print("No director found")

        # get an index from the user
        while True:
            try:
                selection = int(input("Which of these is the film you're adding?\n"))
                if selection <= len(movie_list) and selection > 0:
                    imdb_url = "www.imdb.com/title/tt" + movie_list[selection-1].movieID
                    release_year = movie_list[selection-1]['year']
                    row[0] = movie_list[selection-1]['title']
                    row.append(imdb_url)
                    # append release year from IMDB
                    row.append(release_year)
                    break
            except:
                # continues to loop if they don't input an int
                # or it's greater than the number of selections
                pass
    else:
        print("Looks like it's not on IMDb :(")

    print()
    
    # get todays date
    if recommendation != "Haven't Seen":
        watch_date = time.strftime('%m/%d/%Y')
        print("Putting todays date:"
               ,watch_date
               ,"as the watch date")
        row.append(watch_date)
    else:
        row.append("")
    print()

    print("inserting row into spreadsheet...")
    sheet.insert_row(row, 3)
    print("All done!")


"""
Modifies a row

@param sheet: spreadsheet reference object
@param movie_title: string containing movie_title
@param index: index of 
"""
def modify_row(sheet, movie_title, index):
    pass


"""
Figures out which movie the user wants to interact with

@return: string of movie title and index of it's position in the 
existing_titles list, if it exists there (-1 if it doesn't)

"""
def get_movie_title(sheet, existing_titles):
    movie_title = input("Which movie would you like to add/edit?\n")

    # TODO:
    # use Levenshtein distance to compute if that title is similar or exactly 
    # the same as another title

    for i, title in enumerate(existing_titles):
        if title == movie_title:
            return movie_title, i

    return movie_title, -1


def main():
    # used to access the correct spreadsheet
    sheet_name = "Movies"
    sheet = open_spreadsheet(sheet_name)

    # Get list of existing movie titles
    existing_titles = sheet.col_values(1)[2:]

    # Get title of the movie, and index of it's position in list if it is there
    movie_title, existing_index = get_movie_title(sheet, existing_titles)

    if existing_index == -1:
        print("Adding", movie_title,"to the spreadsheet\n")
        add_new_row(sheet, movie_title)
    else:
        pass


if __name__ == "__main__":
    main()
