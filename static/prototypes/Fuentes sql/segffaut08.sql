Create Table &LIB/SEGFFAUT08
(TFLOAT        FLOAT(24)  NOT NULL WITH DEFAULT
,TINT            INT           NOT NULL DEFAULT 0
,TREAL    REAL            NOT NULL DEFAULT
,TTIMESTAMP   TIMESTAMP    NOT NULL DEFAULT CURRENT TIMESTAMP
,TTIME        TIME  NOT NULL WITH DEFAULT
,TDATE        DATE      NOT NULL WITH DEFAULT
,TDEC     DEC  (8, 2)   NOT NULL DEFAULT 0
) RcdFmt SEG08R;

Label On Table &LIB/SEGFFAUT08 Is 'TIPOS DE DATOS PARA PRUEBAS LZ ';
Label On  &LIB/SEGFFAUT08
(TFLOAT         TEXT IS 'TFLOAT     '
,TINT             TEXT IS 'INT'
,TREAL            TEXT IS 'TREAL'
,TTIMESTAMP       TEXT IS 'TTIMESTAMP'
,TTIME            TEXT IS 'TIME'
,TDATE            TEXT IS 'TDATE     '
,TDEC             TEXT IS 'DECIMAL     '
 );

Label On Column &LIB/SEGFFAUT08
(TFLOAT              Is 'T_FLOAT    '
,TINT                  IS 'T_INT'
,TREAL                 IS 'T_REAL'
,TTIMESTAMP            IS 'T_TIMESTAMP'
,TTIME                 IS 'T_TIME    '
,TDATE                 IS 'T_DATE    '
,TDEC                  IS 'T_DECIMAL'
 );
