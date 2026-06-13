Create Table &LIB/SEGFFAUT32
(TTIME        TIME  NOT NULL WITH DEFAULT
,TSMALLINT       SMALLINT     NOT NULL WITH DEFAULT
,TBIGINT         BIGINT       NOT NULL WITH DEFAULT
,TNUMERIC        NUMERIC (20)  NOT NULL WITH DEFAULT
,TNUMERICD       NUMERIC (15,4)   NOT NULL WITH DEFAULT
,TDOUBLE         DOUBLE          NOT NULL DEFAULT
,TCLOB           CLOB   (100)    NOT NULL DEFAULT
,TDBCLOB         DBCLOB   (60)     NOT NULL DEFAULT
,TCHAR           CHAR (50)     NOT NULL DEFAULT ''
,TCHAR2          CHAR (300) CCSID 284 NOT NULL WITH DEFAULT ''
,TVARCHAR        VARCHAR (70)
,TINT            INT           NOT NULL DEFAULT 0
,TXML            XML        NOT NULL WITH DEFAULT
,TREAL           REAL            NOT NULL DEFAULT
) RcdFmt SEG32R;

Label On Table &LIB/SEGFFAUT32 Is 'TIPOS DE DATOS PARA PRUEBAS LZ ';
Label On  &LIB/SEGFFAUT32
(TTIME         TEXT IS 'TTIME     '
 ,TSMALLINT        TEXT IS 'TSMALLINT     '
 ,TBIGINT          TEXT IS 'TBIGINT       '
 ,TNUMERIC         TEXT IS 'TNUMERIC     '
 ,TNUMERICD        TEXT IS 'TNUMERIC DEC '
 ,TDOUBLE          TEXT IS 'TDOUBLE'
 ,TCLOB            TEXT IS 'TCLOB'
 ,TDBCLOB          TEXT IS 'TDBCLOB'
 ,TCHAR            TEXT IS 'TCHAR'
 ,TCHAR2           TEXT IS 'TCHAR2'
 ,TVARCHAR         TEXT IS 'TVARCHAR'
 ,TINT             TEXT IS 'INT'
 ,TXML             TEXT IS 'TXML'
 ,TREAL            TEXT IS 'TREAL'
 );

Label On Column &LIB/SEGFFAUT32
(TTIME              Is 'T_TIME    '
 ,TSMALLINT             IS 'T_SMALLINT'
 ,TBIGINT               IS 'T_BIGINT  '
 ,TNUMERIC              IS 'T_NUMERIC    '
 ,TNUMERICD             IS 'T_NUMERIC DEC'
 ,TDOUBLE               IS 'T_DOUBLE'
 ,TCLOB                 IS 'T_CLOB'
 ,TDBCLOB               IS 'T_DBCLOB'
 ,TCHAR                 IS 'T_CHAR'
 ,TCHAR2                IS 'T_TCHAR2'
 ,TVARCHAR              IS 'T_VARCHAR'
 ,TINT                  IS 'T_INT'
 ,TXML                  IS 'T_XML'
 ,TREAL                 IS 'T_REAL'
 );
