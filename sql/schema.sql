PRAGMA foreign_keys = ON;

CREATE TABLE users(
	  username VARCHAR(20) NOT NULL,
	  fullname VARCHAR(40) NOT NULL,
		email VARCHAR(40) NOT NULL,
		orgName VARCHAR(40) NOT NULL,
		password VARCHAR(256) NOT NULL,
		hours VARCHAR(40) NOT NULL,
	  PRIMARY KEY(username)
);

CREATE TABLE orgs(
	  username VARCHAR(20) NOT NULL,
	  orgName VARCHAR(40) NOT NULL,
	  PRIMARY KEY(orgName)
);

<<<<<<< HEAD

CREATE TABLE tutors(
	  username VARCHAR(20) NOT NULL,
	  subject VARCHAR(40) NOT NULL,
	  time VARCHAR(80) NOT NULL,
	  PRIMARY KEY(username)
=======
CREATE TABLE requests(
	  postid INTEGER NOT NULL,
	  member VARCHAR(20) NOT NULL,
	  leader VARCHAR(40) NOT NULL,
	  service VARCHAR(40) NOT NULL,
	  filename VARCHAR(64) NOT NULL,
	  PRIMARY KEY(postid)
>>>>>>> a13a88a5b357d5ce4091c99247484845da5be53e
);