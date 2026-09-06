// Unique identity keys
CREATE CONSTRAINT user_userid IF NOT EXISTS
FOR (u:User) REQUIRE u.userId IS UNIQUE;

CREATE CONSTRAINT topic_topicid IF NOT EXISTS
FOR (t:Topic) REQUIRE t.topicId IS UNIQUE;

CREATE CONSTRAINT topic_name IF NOT EXISTS
FOR (t:Topic) REQUIRE t.name IS UNIQUE;

CREATE CONSTRAINT book_bookid IF NOT EXISTS
FOR (b:Book) REQUIRE b.bookId IS UNIQUE;

CREATE CONSTRAINT author_authorid IF NOT EXISTS
FOR (a:Author) REQUIRE a.authorId IS UNIQUE;

CREATE CONSTRAINT course_courseid IF NOT EXISTS
FOR (c:Course) REQUIRE c.courseId IS UNIQUE;

CREATE CONSTRAINT module_moduleid IF NOT EXISTS
FOR (m:Module) REQUIRE m.moduleId IS UNIQUE;

CREATE CONSTRAINT assignment_assignmentid IF NOT EXISTS
FOR (a:Assignment) REQUIRE a.assignmentId IS UNIQUE;

CREATE CONSTRAINT genre_genreid IF NOT EXISTS
FOR (g:Genre) REQUIRE g.genreId IS UNIQUE;

CREATE CONSTRAINT genre_name IF NOT EXISTS
FOR (g:Genre) REQUIRE g.name IS UNIQUE;

CREATE CONSTRAINT worldview_dimensionid IF NOT EXISTS
FOR (d:WorldviewDimension) REQUIRE d.dimensionId IS UNIQUE;

CREATE CONSTRAINT perspective_perspectiveid IF NOT EXISTS
FOR (p:Perspective) REQUIRE p.perspectiveId IS UNIQUE;

CREATE CONSTRAINT completedwork_workid IF NOT EXISTS
FOR (w:CompletedWork) REQUIRE w.workId IS UNIQUE;

// Lookup indexes (sparse catalog fields — not unique)
CREATE INDEX book_catalogkey IF NOT EXISTS
FOR (b:Book) ON (b.catalogKey);

CREATE INDEX book_isbn13 IF NOT EXISTS
FOR (b:Book) ON (b.isbn13);

CREATE INDEX book_isbn10 IF NOT EXISTS
FOR (b:Book) ON (b.isbn10);

CREATE INDEX book_googlebooksid IF NOT EXISTS
FOR (b:Book) ON (b.googleBooksId);

CREATE INDEX book_openlibraryid IF NOT EXISTS
FOR (b:Book) ON (b.openLibraryId);

CREATE INDEX author_name IF NOT EXISTS
FOR (a:Author) ON (a.name);
