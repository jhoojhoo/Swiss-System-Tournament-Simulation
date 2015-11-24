#!/usr/bin/env python
# 
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2
import random

def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""

    return psycopg2.connect("dbname=tournament")

def deleteMatches():
    """Remove all the match records from the database."""

    db = connect()
    c = db.cursor()
    query1 = '''UPDATE players SET wins = 0, losses = 0, matches_played = 0'''
    query2 = '''DELETE FROM match_history'''

    c.execute(query1)
    db.commit()

    c.execute(query2)
    db.commit()
    db.close()

def deletePlayers():
    """Remove all the player records from the database."""

    db = connect()
    c = db.cursor()
    query1 = '''DELETE FROM players'''
    c.execute(query1)
    db.commit()
    db.close()

def countPlayers():
    """Returns the number of players currently registered."""

    db = connect()
    c = db.cursor()
    query1 = '''SELECT count(*) FROM players'''
    c.execute(query1)
    rows = c.fetchall()
    db.close()
    return rows[0][0]

def registerPlayer(name):
    """Adds a player to the tournament database.
  
    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)
  
    Args:
      name: the player's full name (need not be unique).
    """
    db = connect()
    c = db.cursor()

    query1 = '''INSERT INTO players (name) VALUES (%s)'''
    c.execute(query1, (name,))

    db.commit()
    db.close()

def playerStandings():
    """Returns a list of the players and their win records, sorted by wins and then OMW.

    The first entry in the list should be the player in first place, or a
    player tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """
    db = connect()
    c = db.cursor()

    # SQL Query: Fetches the standings ordered by wins.
    query1 = '''SELECT id, name, wins, matches_played
                FROM players
                ORDER BY wins DESC
                '''
    c.execute(query1)
    standings = c.fetchall()
    db.close()

    # Loop through the standings and look for ties. If a tie exists,
    # reorder by OMW and swap if necessary.
    for i in range(0,len(standings)-1):
        if standings[i][2] == standings[i+1][2]:
            if (OMWcalculator(standings[i]) < OMWcalculator(standings[i+1])):
                temp = standings[i]
                standings[i] = standings[i+1]
                standings[i+1] = temp

    return standings

def reportMatch(winner, loser):
    """Records the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
    """
    db = connect()
    c = db.cursor()

    # Update the winning player's stats.
    query1 = '''UPDATE players SET
                    wins = wins + 1,
                    matches_played = matches_played + 1
                WHERE id = %s'''

    # Update the losing player's stats.
    query2 = '''UPDATE players SET
                    losses = losses + 1,
                    matches_played = matches_played + 1
                WHERE id = %s'''

    # Update the match history.
    query3 = '''INSERT INTO match_history VALUES (%s, %s)'''

    c.execute(query1, (winner,))
    c.execute(query2, (loser,))
    c.execute(query3,(winner,loser,))

    db.commit()
    db.close()

def reportBye(winner):
    """Records a bye match for a player.  Bye matches will be stored as
    an integer value of -1 in the match_history table.

    Args:
        winner: the id number of the player who is receiving the bye.

    """

    db = connect()
    c = db.cursor()

    # SQL Query: Update the player statistics.
    query1 = '''UPDATE players SET wins=wins+1, matches_played=matches_played+1 WHERE id = %s'''

    # SQL Query: Update the match_history. -1 value for bye matches.
    query2 = '''INSERT INTO match_history VALUES (%s, -1)'''

    c.execute(query1, (winner,))
    c.execute(query2, (winner,))

    db.commit()
    db.close()

def swissPairings():
    """Returns a list of pairs of players for the next round of a match.
  
    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player
    adjacent to him or her in the standings.
  
    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """
    db = connect()
    c = db.cursor()
    standings = playerStandings()

    ret = []

    # Create pairings and pop each created pair from the 'standings' as they
    # are made.  Continue until no players are left in the standings.
    while len(standings) > 0:
        j=1

        # If there are an odd number of players, assign the worst player a
        # bye.  Then continue to pair the other players.
        if len(standings)%2 != 0:

            # Check to see if the worst player already had a bye.  If
            # yes, give the bye game to the next worst player and pop them
            # from the standings.
            k=1
            while checkBye(standings[len(standings)- k][0]) and len(standings) - k >= 0:
                k+=1

            reportBye(standings[len(standings)- k][0])
            standings.pop(len(standings)-k)


        # Check to see if the pair is a rematch.  If yes, increment j to the
        # next possible match.  Otherwise create the pair and pop them from the
        # standings.
        while j < len(standings)-1 and rematchCheck(standings[0][0],standings[j][0]):
            j+=1

        temp = (standings[0][0], standings[0][1], standings[j][0],
                standings[j][1])
        standings.pop(0)
        standings.pop(j-1)

        ret.append(temp)

    db.close()
    return ret

def checkBye(p1):
    """ Returns true if the input player has already had a bye match.

    Args:
        p1: Player to check if they had a bye.
    """

    db = connect()
    c = db.cursor()

    # SQL Query: Searches the player's match history for a -1 opponent (bye).
    query1 = '''SELECT count(*) FROM match_history
                WHERE (id = %s and op_id = -1) or (id = -1 and op_id = %s)
             '''
    c.execute(query1, (p1,p1,))
    count = c.fetchall()[0][0]

    if count==0:
        return False
    else:
        return True

def rematchCheck(p1, p2):
    """ Returns true or false based on whether the two players have played
    against each other in the tournament or not.

    Args:
        p1: First player.
        p2: Second player.

    Returns True if the match is a rematch.  False otherwise."""

    db = connect()
    c = db.cursor()

    # SQL Query: Return the number of matches that p1 and p2 were BOTH playing in.
    rematch_query = '''SELECT count(*) FROM match_history
                        WHERE (id = %s AND op_id = %s)
                        OR (id = %s AND op_id = %s)'''

    c.execute(rematch_query, (p1,p2,p2,p1,))
    ret = c.fetchall()

    # If p1 and p2 never played each other, return False.
    if ret[0][0] == 0:
        return False

    # Otherwise, return True.
    else:
        return True

    db.close()

def determineWinner(p1, p2):
    """
    Determines the winner of a given match.

    Args:
        p1: First player id.
        p2: Second player id.

    Returns a tuple of (winners id, losers id).
    """
    if random.random() > .5:
        return (p1,p2)
    else:
        return (p2,p1)

def OMWcalculator(p):
    """
    Calculates the OMW of an input player tuple (id, name, wins, matches)
    returned from the playerStandings() method.

    Args:
        p: Player tuple of which OMW is to be calculated for.

    Returns the OMW for the input player tuple.
    """
    db = connect()
    c = db.cursor()

    # SQL Query: Retrieve the total match history of a player.
    query1 = '''SELECT * FROM match_history WHERE id = %s or op_id = %s'''
    c.execute(query1, (p[0],p[0],))
    rows = c.fetchall()

    opponent_history = []

    for row in rows:

        # If player p is listed in the 'id' column for a specific match in
        # the match_history table, then add the 'op_id' to p's opponent history.
        # Skip bye matches (value=-1).
        if p[0]==row[0] and row[1]!=-1:
            opponent_history.append(row[1])

        # Otherwise, p is entered in the 'op_id' column and the opponent
        # is entered in the 'id' column.  Append the 'id' entry as the
        # opponent. Skip bye matches (value=-1).
        elif row[0]!=-1:
            opponent_history.append(row[0])

    omw = 0
    for opponent in opponent_history:
        query2 = '''SELECT wins FROM players WHERE id = %s'''
        c.execute(query2, (opponent,))
        wins = c.fetchall()
        omw += wins[0][0]

    return omw

'''***************************** TEST CASES *****************************'''
# Clear the tables.
deleteMatches()
deletePlayers()

# Create test players.
registerPlayer("Bill")
registerPlayer("Heather")
registerPlayer("Rob")
registerPlayer("Alicia")
registerPlayer("Jordan")
registerPlayer("Jess")
registerPlayer("Peony")
registerPlayer("Jane")
registerPlayer("Marlin")

# First round in the Swiss Tournament.
pairs = swissPairings()

# Simulate the final 3 rounds of the Swiss tournament.
for i in range(0,3):
    pairs = swissPairings()

    # For each pair, determine the winner and loser randomly and report/post
    # the results.
    for pair in pairs:
        results = determineWinner(pair[0],pair[2])
        reportMatch(results[0],results[1])


# Print the final standings.
standings = playerStandings()
print "***** FINAL STANDINGS ****"
for i in range(0, len(standings)):
    print str(i + 1), standings[i][1],
    if i==0:
        print " <----- CHAMP!"
    else:
        print ""
