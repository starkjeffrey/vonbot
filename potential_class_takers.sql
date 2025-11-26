select id, name, lastenroll, ltrim(rtrim(batchidformaster)) batchid, 1 'POL201A' from Students
where selprogram = 87 and lastenroll > '2020/05/04' and bagraddate is not null and
/* substring(BatchIDForMaster, 1, 3) in ('BAD', 'FIN', 'TOU') and */
substring(BatchIDForMaster, 5, 3) >= '21M' and substring(BatchIDForMaster, 5, 3) <= '36E'

and id not in (
    select id from vw_BAlatestgrade where coursecode in 

    ('LAW-273', 'LAW-301A')

    and (grade < 'F' or (termid in ('2023T2') and grade in ('IP','I'))))
order by id desc