PRAGMA foreign_keys = ON;

CREATE TABLE users(
	  username VARCHAR(20) NOT NULL,
	  fullname VARCHAR(40) NOT NULL,
		email VARCHAR(40) NOT NULL,
		orgName VARCHAR(40) NOT NULL,
		password VARCHAR(256) NOT NULL,
	  PRIMARY KEY(username)
);

CREATE TABLE orgs(
	  username VARCHAR(20) NOT NULL,
	  orgName VARCHAR(40) NOT NULL,
	  PRIMARY KEY(orgName)
);