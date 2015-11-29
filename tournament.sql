-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.

-- Drop all existing connections to 'tournament' database except your own.
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'tournament'
  AND pid <> pg_backend_pid();

DROP DATABASE IF EXISTS tournament;
CREATE DATABASE tournament;
\c tournament;

DROP TABLE IF EXISTS match_history;
DROP TABLE IF EXISTS players;
DROP VIEW IF EXISTS omw;

-- Create a table to store all players and their key statistics.
CREATE TABLE players(
    id SERIAL UNIQUE PRIMARY KEY,
    name TEXT NOT NULL,
    wins INT NOT NULL DEFAULT 0,
    losses INT NOT NULL DEFAULT 0,
    matches_played INT NOT NULL DEFAULT 0
    );

-- Create a table to store the match history of the tournament.
CREATE TABLE match_history(
    match_id SERIAL PRIMARY KEY,
    winner_id INT REFERENCES players(id),
    loser_id INT NOT NULL
    CHECK (winner_id <> loser_id)
    );

-- Create a view to calculate and retrieve player OMWs.
CREATE VIEW omw AS SELECT id, CAST(sum(ss.sum) AS int) AS omw
FROM(
    SELECT a.id, sum(c.wins)
    FROM players AS a, match_history AS b, players
        AS c WHERE a.id = b.winner_id AND b.loser_id = c.id
    GROUP BY a.id

    UNION

    SELECT a.id, sum(c.wins) FROM players AS a, match_history AS b, players AS c
        WHERE a.id = b.loser_id AND b.winner_id = c.id GROUP BY a.id
    ) ss
GROUP BY id
ORDER BY omw;

