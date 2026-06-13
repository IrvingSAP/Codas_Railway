Create Table &LIB/SEGFFAUT06
(TINTEGER        INTEGER      NOT NULL WITH DEFAULT
,TREAL    REAL            NOT NULL DEFAULT
,TINT            INT           NOT NULL DEFAULT 0
,TVARCHAR        VARCHAR (100)
) RcdFmt SEG06R;

Label On Table &LIB/SEGFFAUT06 Is 'TIPOS DE DATOS PARA PRUEBAS LZ ';
Label On  &LIB/SEGFFAUT06
(TINTEGER         TEXT IS 'TINTEGER     '
,TREAL            TEXT IS 'TREAL'
,TINT             TEXT IS 'INT'
,TVARCHAR         TEXT IS 'VARCHAR'
 );

Label On Column &LIB/SEGFFAUT06
(TINTEGER              Is 'T_INTEGER    '
,TREAL                 IS 'T_REAL'
,TINT                  IS 'T_INT'
,TVARCHAR              IS 'T_VARCHAR'
 );
