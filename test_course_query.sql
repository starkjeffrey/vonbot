-- Test query to extract course code from ClassId
SELECT TOP 10
    ClassId,
    -- Replace !$ with | then extract last part after final |
    REVERSE(LEFT(REVERSE(REPLACE(ClassId, '!$', '|')),
            CHARINDEX('|', REVERSE(REPLACE(ClassId, '!$', '|'))) - 1)) as CourseCode,
    LEFT(ClassId, CHARINDEX('!$', ClassId) - 1) as TermId
FROM AcademicCourseTakers
WHERE CHARINDEX('!$', ClassId) > 0
AND Attendance = 'Normal'
ORDER BY ClassId DESC
