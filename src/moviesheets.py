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


def get_recommendation():
    recommendation = ''
    # get recommendation
    while True:
        try:
            recommendation_str = input("Would you recommend this movie?\n1) Yes\n2) No\n3) Haven't Seen\n")
            if recommendation_str[0] == str(1) or recommendation_str[0].lower() == 'y':
                recommendation = 'Yes'
                break
            elif recommendation_str[0] == str(2) or recommendation_str[0].lower() == 'n':
                recommendation = 'No'
                break
            elif recommendation_str[0] == str(3) or recommendation_str[0].lower() == 'h':
                recommendation = "Haven't Seen"
                break
        except:
            # TODO: check for keyboard interrupt
            pass

    return recommendation


def get_rating():
    # get rating
    while True:
        try:
            rating = float(input("How would you rate this movie?\nInput a number 1-10\n"))
            break
        except:
            # TODO: check for keyboard interrupt
            pass
    print()
    return rating


def get_notes():
    notes = input("What else would you like to say about this movie?\nThis will go under the 'Notes' portion:\n")
    return notes


def get_imdb_and_release_year(movie_title):
    ia = imdb.IMDb()
    print("Let's try to find this movie on IMDB...")
    movie_list = ia.search_movie(movie_title)[:5]
    print("The imdb search brought up these titles:")
    imdb_url = ""
    release_year = "Not available on IMDB"
    correct_title = "N/A"
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
                    correct_title = movie_list[selection-1]['title']
                    break
            except:
                # TODO: check for keyboard interrupt
                # continues to loop if they don't input an int
                # or it's greater than the number of selections
                pass
    else:
        print("Looks like it's not on IMDb :(")

    return imdb_url, release_year, correct_title


def get_watch_date():
    watch_date = ""
    # get todays date
    watch_date = time.strftime('%m/%d/%Y')
    print("Putting todays date:"
           ,watch_date
           ,"as the watch date")
    print()
    return watch_date


"""
calls all other get_functions to construct row data

@param movie_title: for inserting at the beginning
@return list of all data to be inserted into a row
"""
def get_row(movie_title, modifying=False):
    row = []
    row.append(movie_title)

    recommendation = get_recommendation()
    row.append(recommendation)
    print()

    # if you haven't seen the movie then you are adding it to the list for future reference
    # there should be no rating or Notes field in this case
    if recommendation != "Haven't Seen":
        rating = get_rating()
        row.append(rating)

        # get Notes
        notes = get_notes()
        row.append(notes)
        print()
    else:
        #pad the row
        row.append("")
        row.append("")


    if not modifying:
        imdb_url, release_year, correct_title = get_imdb_and_release_year(movie_title)
        if correct_title != "N/A":
            row[0] = correct_title

        row.append(imdb_url)
        row.append(release_year)
        print()
    else:
        row.append(None)
        row.append(None)

    if recommendation != "Haven't Seen":
        watch_date = get_watch_date()
        row.append(watch_date)

    if modifying:
        return [row]
    else:
        return row


"""
Adds a new row at the top of the spreadsheet

@param sheet: spreadsheet reference object
@param movie_title: string containing movie_title
"""
def add_new_row(sheet, movie_title):
    row = get_row(movie_title)

    print("inserting row into spreadsheet...")
    sheet.insert_row(row, 3)
    print("All done!")


"""
small helper function

@param row_number: actual number of the row in google sheets
@return string containing the properly formatted range for a specified row of cells
"""
def get_row_range(row_number):
    return "A" + str(row_number) + ":" + "G" + str(row_number)


"""
Modifies a row

@param sheet: spreadsheet reference object
@param movie_title: string containing movie_title
@param index: index of row in existing_titles
"""
def modify_row(sheet, movie_title, index):
    #row number is index+1
    row_number = index+1

    # TODO:
    # implement row modification
    print(row_number, movie_title)

    # Ask what the user wants to modify:
    #     whole row
    #     recommendation
    #     rating
    #     notes
    #     imdb
    #     release year
    #     watch date

    while True:
        print("\nWhat would you like to modify about", movie_title, "'s entry?")
        print("1) The whole row")
        print("2) Recommendation")
        print("3) Rating")
        print("4) Notes")
        print("5) Imdb url")
        print("6) Release Year")
        print("7) Watch Date")
        print("8) Delete the row")
        print("9) Exit program")

        modify_str = -1
        # get user selection
        while True:
            try:
                modify_str = int(input())
                break
            except:
                # TODO: catch keyboard interrupt
                pass
        print()

        if modify_str == 1:
            # modify whole row
            sheet.update(get_row_range(row_number),get_row(movie_title, modifying=True))
        elif modify_str == 2:
            # modify recommendation only
            sheet.update('B'+str(row_number), get_recommendation())
        elif modify_str == 3:
            # modify rating only
            sheet.update('C'+str(row_number), get_rating())
        elif modify_str == 4:
            # modify notes only
            sheet.update('D'+str(row_number), get_notes())
        elif modify_str == 5:
            # TODO implement manual imdb_url submission
            print("Need to implement!")
        elif modify_str == 6:
            # TODO implement manual release_year submission
            print("Need to implement!")
        elif modify_str == 7:
            # TODO implement manual watch_date submission
            print("Need to implement!")
        elif modify_str == 8:
            while True:
                try:
                    print("Are you sure you want to delete the row for ",movie_title,"?",sep='')
                    delete_yesno = input()
                    if delete_yesno[0].lower() == 'y':
                        print("Deleting row...\n")
                        sheet.delete_row(row_number)
                    break
                except:
                    # TODO: check for keyboard interrupt
                    pass
            quit()
        elif modify_str == 9:
            quit()


"""
Figures out which movie the user wants to interact with,
uses Levenshtein distance to help with typos

@return: string of movie title and index of it's position in the 
existing_titles list, if it exists there (-1 if it doesn't)

@param sheet: spreadsheet reference object
@param existing_titles: list of movie titles
"""
def get_movie_title(sheet, existing_titles):
    movie_title = input("Which movie would you like to add/edit?\n")

    # If the title doesn't exactly match any of the titles (Levenshtein distance of 0)
    # display titles that are similar (under a threshold) in order of most similar

    # generate list of tuples containing distance and location of titles in existing_titles
    distances = []
    acceptable_distances = []
    for i, title in enumerate(existing_titles):
        distances.append((Levenshtein.distance(movie_title, existing_titles[i]), i))
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


def get_row_index(movie_title, existing_titles):
    return existing_titles.index(movie_title)+2


def main():
    sheet = open_spreadsheet(sheet_name)

    # Get list of existing movie titles
    existing_titles = sheet.col_values(1)[2:]
    existing_titles = [x.lower() for x in existing_titles]

    # Get title of the movie, and index of it's position in list if it is there
    movie_title, existing_index = get_movie_title(sheet, existing_titles)
    movie_list = movie_title.lower()

    if existing_index == -1:
        print("Adding", movie_title,"to the spreadsheet\n")
        add_new_row(sheet, movie_title)
    else:
        row_index = get_row_index(movie_title, existing_titles)
        modify_row(sheet, movie_title, row_index)
        pass


if __name__ == "__main__":
    main()
