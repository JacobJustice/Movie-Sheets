import gspread
from oauth2client.service_account import ServiceAccountCredentials

import imdb
import Levenshtein
import time

# TODO: Make a config argument and config file so you can change this stuff

# great tutorial on using python for google sheets and using the google API
#   also covers how to get your credentials json
# https://www.twilio.com/blog/2017/02/an-easy-way-to-read-and-write-to-a-google-spreadsheet-in-python.html
path_to_credentials = '/home/jacob/Programs/Movie-Sheets/client_secret.json'
# used to access the correct spreadsheet
sheet_name = "Movies"
# used to show how many movies are similar to the input
DISTANCE_THRESHOLD = 8

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

"""
Opens a spreadsheet and returns a reference to it using google sheets credentials

@param sheet_name: string containing name of spreadsheet on Google Sheets
@return: sheet object
"""
def open_spreadsheet(sheet_name):
    # use creds to create a client to interact with the Google Drive API
    # for some reason you need to add this extra url in the scope but I don't know why fixes this error:
    #   https://stackoverflow.com/questions/49258566/gspread-authentication-throwing-insufficient-permission
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(path_to_credentials, scope)
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
            # TODO: check for keyboard interrupt
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
                # TODO: check for keyboard interrupt
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
                # TODO: check for keyboard interrupt
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
                # TODO: check for keyboard interrupt
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
    # TODO:
    # implement row modification

    print("Needs to be implemented!")
    pass


"""
Figures out which movie the user wants to interact with,
uses Levenshtein distance to help with typos

@return: string of movie title and index of it's position in the 
existing_titles list, if it exists there (-1 if it doesn't)

"""
def get_movie_title(sheet, existing_titles):
    movie_title = input("Which movie would you like to add/edit?\n")

    # If the title doesn't exactly match any of the titles (Levenshtein distance of 0)
    # display titles that are similar (under a threshold) in order of most similar

    # generate list of tuples containing distance and location of titles in existing_titles
    distances = []
    acceptable_distances = []
    for i, title in enumerate(existing_titles):
        distances.append((Levenshtein.distance(movie_title.lower(), existing_titles[i].lower()), i))
        if distances[i][0] == 0:
            return movie_title, i
        elif distances[i][0] < DISTANCE_THRESHOLD:
            acceptable_distances.append(distances[i])
    acceptable_distances.sort()

    # print selection options
    print("\nIs your movie one of these?")
    print("1) None of these (add a new movie)")
    for i, movie in enumerate(acceptable_distances):
        print(i+2, ") ", existing_titles[acceptable_distances[i][1]], "; ", acceptable_distances[i][0])

    while True:
        try:
            #subtract 2 because of the offset used for intuitive displaying
            existing_selection = int(input()) - 2
            if existing_selection == -1:
                return movie_title, -1
            else:
                return existing_titles[acceptable_distances[existing_selection][1]], acceptable_distances[existing_selection][1]  
        except:
            # TODO: check for keyboard interrupt
            pass



def main():
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
