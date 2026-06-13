Create Table &LIB/SEGFFAUT26
(TNUMERIC        NUMERIC (20)  NOT NULL WITH DEFAULT
,TNUMERICD       NUMERIC (15,4) NOT NULL WITH DEFAULT
,TCHAR           CHAR (50)     NOT NULL DEFAULT ''
,TCHAR2          CHAR (300) CCSID 284 NOT NULL WITH DEFAULT ''
,TVARCHAR        VARCHAR (70)
,TINT            INT           NOT NULL DEFAULT 0
) RcdFmt SEG26R;

Label On Table &LIB/SEGFFAUT26 Is 'TIPOS DE DATOS PARA PRUEBAS LZ ';
Label On  &LIB/SEGFFAUT26
(TNUMERIC         TEXT IS 'TNUMERIC     '
,TNUMERICD        TEXT IS 'TNUMERIC DEC '
,TCHAR            TEXT Is 'CHAR'
,TCHAR2           Text Is 'CHAR'
,TVARCHAR         Text Is 'VARCHAR'
,TINT             Text Is 'INT'
 );

Label On Column &LIB/SEGFFAUT26
(TNUMERIC              Is 'T_NUMERIC    '
,TNUMERICD             Is 'T_NUMERIC DEC'
,TCHAR                 Is 'T_CHAR'
,TCHAR2                Is 'T_TCHAR2'
,TVARCHAR              Is 'T_VARCHAR'
,TINT                  Is 'T_INT'
 );
