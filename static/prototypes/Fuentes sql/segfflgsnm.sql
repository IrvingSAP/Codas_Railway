CREATE TABLE &LIB/SEGFFLGSNM (
 FECHASIS          TIMESTAMP         ,
 PGM               CHAR        (10)  ,
 CODERROR          CHAR        (7) NOT NULL DEFAULT '' ,
 DESERROR          CHAR        (80)  ,
 ENVDATOS          VARCHAR     (32000)
)
RCDFMT   RLGSNM;

LABEL ON TABLE &LIB/SEGFFLGSNM  Is
'LOG DE ENVIO DE CORREOS ';

LABEL ON &LIB/SEGFFLGSNM (
FECHASIS           Text Is  'FECHA SISTEMA',
PGM                Text Is  'PROGRAMA',
CODERROR           Text Is  'COD. ERROR ',
DESERROR           Text Is  'DESCRIPCION ERROR',
ENVDATOS           Text Is  'ENVIO DE DATOS');

LABEL ON COLUMN &LIB/SEGFFLGSNM (
FECHASIS                Is  'FECHA SISTEMA',
PGM                     Is  'PROGRAMA',
CODERROR                Is  'COD. ERROR ',
DESERROR                Is  'DESCRIPCION ERROR',
ENVDATOS                Is  'ENVIO DE DATOS');
