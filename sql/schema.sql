PRAGMA foreign_keys = ON;

CREATE TABLE users(
	  username VARCHAR(20) NOT NULL,
	  fullname VARCHAR(40) NOT NULL,
		email VARCHAR(40) NOT NULL,
		orgName VARCHAR(40) NOT NULL,
		password VARCHAR(256) NOT NULL,
		hours INTEGER NOT NULL,
	  PRIMARY KEY(username)
);

CREATE TABLE orgs(
	  username VARCHAR(20) NOT NULL,
	  orgName VARCHAR(40) NOT NULL,
	  newMember INTEGER NOT NULL,
          pointReq INTEGER NOT NULL,
	  PRIMARY KEY(orgName)
);

CREATE TABLE pendingOrgs(
	  username VARCHAR(20) NOT NULL,
	  fullname VARCHAR(40) NOT NULL,
	  email VARCHAR(40) NOT NULL,
	  orgName VARCHAR(40) NOT NULL,
          hours INTEGER NOT NULL,
	  PRIMARY KEY(username)
	  FOREIGN KEY(username) REFERENCES users(username) ON UPDATE CASCADE
		ON DELETE CASCADE
);

CREATE TABLE tutors(
	  username VARCHAR(20) NOT NULL,
	  subject VARCHAR(40) NOT NULL,
	  time VARCHAR(80) NOT NULL,
	  PRIMARY KEY(username)
	  FOREIGN KEY(username) REFERENCES users(username) ON UPDATE CASCADE
		ON DELETE CASCADE
);

CREATE TABLE requests(
	  postid INTEGER NOT NULL,
	  member VARCHAR(20) NOT NULL,
	  leader VARCHAR(40) NOT NULL,
	  service VARCHAR(40) NOT NULL,
	  description VARCHAR(128) NOT NULL,
	  filename VARCHAR(64) NOT NULL,
	  PRIMARY KEY(postid)
	  FOREIGN KEY(member) REFERENCES users(username) ON UPDATE CASCADE
		ON DELETE CASCADE
);


CREATE TABLE posts(
	  postid INTEGER NOT NULL,
	  poster VARCHAR(20) NOT NULL,
	  service VARCHAR(40) NOT NULL,
	  name VARCHAR(30) NOT NULL,
	  description VARCHAR(128) NOT NULL,
	  link VARCHAR(128) NOT NULL,
	  PRIMARY KEY(postid)
);

CREATE TABLE pastRequests(
	  postid INTEGER NOT NULL,
	  member VARCHAR(20) NOT NULL,
	  service VARCHAR(40) NOT NULL,
	  points INTEGER NOT NULL,
	  description VARCHAR(256) NOT NULL,
	  PRIMARY KEY(postid)
);




