-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.

DROP TABLE IF EXISTS match_history;
DROP TABLE IF EXISTS players;

-- Create a table to store all players and their key statistics.
CREATE TABLE players(
    id SERIAL UNIQUE,
    name TEXT NOT NULL,
    wins INT NOT NULL DEFAULT 0,
    losses INT NOT NULL DEFAULT 0,
    matches_played INT NOT NULL DEFAULT 0
    );

-- Create a table to store the match history of the tournament.
CREATE TABLE match_history(
    id INT REFERENCES players(id),
    op_id INT NOT NULL
    );

