Create Table &LIB/SEGFFAUT03
(TTIME           TIME  NOT NULL WITH DEFAULT
,TCLOB           CLOB   (100)    NOT NULL DEFAULT
,TDBCLOB         DBCLOB   (60)     NOT NULL DEFAULT
,TCHAR           CHAR (50)     NOT NULL DEFAULT ''
,TCHAR2          CHAR (300) CCSID 284 NOT NULL WITH DEFAULT ''
,TVARCHAR        VARCHAR (70)



) RcdFmt SEG03R;

Label On Table &LIB/SEGFFAUT03 Is 'TIPOS DE DATOS PARA PRUEBAS LZ ';
Label On  &LIB/SEGFFAUT03
(TTIME            TEXT IS 'TTIME     '
,TCLOB            TEXT IS 'TCLOB'
,TDBCLOB          TEXT IS 'TDBCLOB'
,TCHAR            TEXT IS 'CHAR'
,TCHAR2           TEXT IS 'CHAR'
,TVARCHAR         TEXT IS 'VARCHAR'

 );

Label On Column &LIB/SEGFFAUT03
(TTIME              Is 'T_TIME    '
,TCLOB              IS 'T_CLOB'
,TDBCLOB            IS 'T_DBCLOB'
,TCHAR                 IS 'T_CHAR'
,TCHAR2                IS 'T_TCHAR2'
,TVARCHAR              IS 'T_VARCHAR'
 );
