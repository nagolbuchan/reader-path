// One-shot rename for databases written with the old snake_case properties.
// Run manually in Neo4j Browser / cypher-shell. Do not apply on startup.

MATCH (c:Course)
WHERE c.course_id IS NOT NULL AND c.courseId IS NULL
SET c.courseId = c.course_id
REMOVE c.course_id;

MATCH (c:Course)
WHERE c.created_at IS NOT NULL AND c.createdAt IS NULL
SET c.createdAt = c.created_at
REMOVE c.created_at;

MATCH (m:Module)
WHERE m.module_id IS NOT NULL AND m.moduleId IS NULL
SET m.moduleId = m.module_id
REMOVE m.module_id;

MATCH (m:Module)
WHERE m.created_at IS NOT NULL AND m.createdAt IS NULL
SET m.createdAt = m.created_at
REMOVE m.created_at;

MATCH (a:Assignment)
WHERE a.assignment_id IS NOT NULL AND a.assignmentId IS NULL
SET a.assignmentId = a.assignment_id
REMOVE a.assignment_id;

MATCH (a:Assignment)
WHERE a.created_at IS NOT NULL AND a.createdAt IS NULL
SET a.createdAt = a.created_at
REMOVE a.created_at;

MATCH (b:Book)
WHERE b.book_id IS NOT NULL AND b.bookId IS NULL
SET b.bookId = b.book_id
REMOVE b.book_id;

MATCH (b:Book)
WHERE b.created_at IS NOT NULL AND b.createdAt IS NULL
SET b.createdAt = b.created_at
REMOVE b.created_at;

MATCH (b:Book)
WHERE b.catalogKey IS NULL AND b.bookId IS NOT NULL
SET b.catalogKey = 'book:' + b.bookId;

MATCH (t:Topic)
WHERE t.topicId IS NULL AND t.slug IS NOT NULL
SET t.topicId = t.slug;

MATCH (t:Topic)
WHERE t.name IS NULL AND t.slug IS NOT NULL
SET t.name = t.slug;

MATCH (u:User)
WHERE u.created_at IS NOT NULL AND u.createdAt IS NULL
SET u.createdAt = u.created_at
REMOVE u.created_at;

MATCH (u:User)
WHERE u.displayName IS NULL AND u.name IS NOT NULL
SET u.displayName = u.name;

MATCH (a:Author)
WHERE a.authorId IS NULL
SET a.authorId = randomUUID(), a.sortName = a.name;
