Create Table &LIB/SEGFFAUT01
(TDEC       DEC  (8, 2)   NOT NULL DEFAULT 0
,TCHAR      CHAR (50)     NOT NULL DEFAULT ''
,TCHAR2     CHAR (300) CCSID 284 NOT NULL WITH DEFAULT ''
,TVARCHAR   VARCHAR (70)
,TINT       INT           NOT NULL DEFAULT 2
) RcdFmt SEG01R;

Label On Table &LIB/SEGFFAUT01 Is 'TIPOS DE DATOS PARA PRUEBAS LZ ';
Label On  &LIB/SEGFFAUT01
(TDEC          Text Is 'DECIMAL'
,TCHAR         Text Is 'CHAR'
,TCHAR2        Text Is 'CHAR'
,TVARCHAR         Text Is 'VARCHAR'
,TINT          Text Is 'INT'
 );

Label On Column &LIB/SEGFFAUT01
(TDEC               Is 'T_DECIMAL'
,TCHAR              Is 'T_CHAR'
,TCHAR2             Is 'T_TCHAR2'
,TVARCHAR           Is 'T_VARCHAR'
,TINT               Is 'T_INT'
 );
